from typing import Any, List, Dict, Optional
import asyncio
import json
import os
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from fastmcp import FastMCP
import urllib.parse

# 初始化 FastMCP 服务器
mcp = FastMCP("xiaohongshu_scraper")

# 全局变量
BROWSER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# 确保目录存在
os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# 用于存储浏览器上下文
browser_context = None
main_page = None
is_logged_in = False
playwright_instance = None

# 搜索缓存（内存缓存，5分钟有效）
search_cache = {}
CACHE_TTL = 300  # 5分钟

def get_cache_key(keywords: str, limit: int) -> str:
    """生成缓存键"""
    return f"{keywords}_{limit}"

def get_cached_result(keywords: str, limit: int) -> Optional[str]:
    """获取缓存结果"""
    key = get_cache_key(keywords, limit)
    if key in search_cache:
        cached_time, result = search_cache[key]
        if (datetime.now().timestamp() - cached_time) < CACHE_TTL:
            print(f"✅ 使用缓存结果: {keywords}")
            return result
    return None

def set_cached_result(keywords: str, limit: int, result: str):
    """设置缓存结果"""
    key = get_cache_key(keywords, limit)
    search_cache[key] = (datetime.now().timestamp(), result)

async def ensure_browser():
    """确保浏览器已启动并登录 - 优化版"""
    global browser_context, main_page, is_logged_in, playwright_instance

    if browser_context is None:
        print("🚀 启动浏览器...")
        # 启动playwright
        playwright_instance = await async_playwright().start()

        # 使用持久化上下文来保存用户状态
        browser_context = await playwright_instance.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=False,  # 非隐藏模式，方便用户登录
            viewport={"width": 1280, "height": 800},
            timeout=30000,  # 减少到30秒
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-gpu'
            ]
        )

        # 创建一个新页面
        if browser_context.pages:
            main_page = browser_context.pages[0]
        else:
            main_page = await browser_context.new_page()

        # 设置页面级别的超时时间
        main_page.set_default_timeout(15000)  # 减少到15秒
        print("✅ 浏览器启动完成")

    # 检查登录状态
    if not is_logged_in:
        print("🔍 检查登录状态...")
        try:
            # 访问小红书首页
            await main_page.goto("https://www.xiaohongshu.com", timeout=15000, wait_until="domcontentloaded")

            # 等待页面加载（智能等待）
            try:
                await main_page.wait_for_selector('body', timeout=5000)
            except:
                pass

            # 检查是否已登录
            login_elements = await main_page.query_selector_all('text="登录"')
            if login_elements:
                print("⚠️ 需要登录")
                return False
            else:
                is_logged_in = True
                print("✅ 已登录")
                return True
        except Exception as e:
            print(f"❌ 检查登录状态失败: {e}")
            return False

    return True

@mcp.tool()
async def login() -> str:
    """登录小红书账号"""
    global is_logged_in

    await ensure_browser()

    if is_logged_in:
        return "已登录小红书账号"

    if not main_page:
        return "浏览器初始化失败，请重试"

    await main_page.goto("https://www.xiaohongshu.com", timeout=15000, wait_until="domcontentloaded")

    # 查找登录按钮并点击
    login_elements = await main_page.query_selector_all('text="登录"')
    if login_elements:
        await login_elements[0].click()

        message = "请在打开的浏览器窗口中完成登录操作。登录成功后，系统将自动继续。"

        # 等待用户登录成功
        max_wait_time = 120  # 减少到2分钟
        wait_interval = 3
        waited_time = 0

        while waited_time < max_wait_time:
            still_login = await main_page.query_selector_all('text="登录"')
            if not still_login:
                is_logged_in = True
                await asyncio.sleep(1)
                return "登录成功！"

            await asyncio.sleep(wait_interval)
            waited_time += wait_interval

        return "登录等待超时。请重试或手动登录后再使用其他功能。"
    else:
        is_logged_in = True
        return "已登录小红书账号"

@mcp.tool()
async def search_notes(keywords: str, limit: int = 5) -> str:
    """根据关键词搜索笔记 - 优化版

    Args:
        keywords: 搜索关键词
        limit: 返回结果数量限制
    """
    # 检查缓存
    cached = get_cached_result(keywords, limit)
    if cached:
        return cached

    login_status = await ensure_browser()
    if not login_status:
        return "请先登录小红书账号"

    if not main_page:
        return "浏览器初始化失败，请重试"

    print(f"🔍 搜索: {keywords}")

    # 构建搜索URL并访问
    encoded_keywords = urllib.parse.quote(keywords)
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={encoded_keywords}"

    try:
        # 优化：使用domcontentloaded而不是load，更快
        await main_page.goto(search_url, timeout=20000, wait_until="domcontentloaded")

        # 智能等待：等待搜索结果容器出现
        try:
            await main_page.wait_for_selector('section.note-item', timeout=8000)
            print("✅ 搜索结果已加载")
        except:
            # 如果等待失败，尝试短时间等待
            print("⏳ 等待页面渲染...")
            await asyncio.sleep(2)

        # 获取帖子卡片
        post_cards = await main_page.query_selector_all('section.note-item')
        print(f"找到 {len(post_cards)} 个帖子卡片")

        if not post_cards:
            # 尝试备用选择器
            post_cards = await main_page.query_selector_all('div[data-v-a264b01a]')
            print(f"使用备用选择器找到 {len(post_cards)} 个帖子卡片")

        post_links = []
        post_titles = []

        for card in post_cards[:limit]:
            try:
                # 获取链接
                link_element = await card.query_selector('a[href*="/search_result/"]')
                if not link_element:
                    continue

                href = await link_element.get_attribute('href')
                if href:
                    # 构建完整URL
                    if href.startswith('/'):
                        full_url = f"https://www.xiaohongshu.com{href}"
                    else:
                        full_url = href
                    post_links.append(full_url)

                # 获取标题
                title_element = await card.query_selector('span.title, div.title, a')
                if title_element:
                    title = await title_element.inner_text()
                    post_titles.append(title.strip() if title else "无标题")
                else:
                    post_titles.append("无标题")

            except Exception as e:
                print(f"解析卡片失败: {e}")
                continue

        if not post_links:
            result = f"未找到与 '{keywords}' 相关的笔记"
        else:
            # 构建结果
            result_lines = [f"搜索结果：\n"]
            for i, (link, title) in enumerate(zip(post_links, post_titles), 1):
                result_lines.append(f"{i}. {title}")
                result_lines.append(f"   链接: {link}\n")

            result = "\n".join(result_lines)

        # 缓存结果
        set_cached_result(keywords, limit, result)
        print(f"✅ 搜索完成，返回 {len(post_links)} 条结果")

        return result

    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return f"搜索失败: {str(e)}"

@mcp.tool()
async def get_note_content(url: str) -> str:
    """获取笔记内容 - 优化版

    Args:
        url: 笔记 URL
    """
    login_status = await ensure_browser()
    if not login_status:
        return "请先登录小红书账号"

    if not main_page:
        return "浏览器初始化失败，请重试"

    # 处理URL
    processed_url = url.strip()
    if not processed_url.startswith('http'):
        processed_url = 'https://' + processed_url

    print(f"📖 获取笔记: {processed_url}")

    try:
        await main_page.goto(processed_url, timeout=15000, wait_until="domcontentloaded")

        # 智能等待内容加载
        try:
            await main_page.wait_for_selector('div.note-content, div.detail-note-content', timeout=5000)
        except:
            await asyncio.sleep(1)

        # 获取标题
        title = ""
        try:
            title_element = await main_page.query_selector('h1.title, div.title')
            if title_element:
                title = await title_element.inner_text()
        except:
            pass

        # 获取内容
        content = ""
        try:
            content_element = await main_page.query_selector('div.note-content, div.detail-note-content, div.content')
            if content_element:
                content = await content_element.inner_text()
        except:
            pass

        # 获取点赞数和收藏数
        likes = "未知"
        collects = "未知"
        try:
            like_element = await main_page.query_selector('span.like-count, span.count')
            if like_element:
                likes = await like_element.inner_text()
            collect_element = await main_page.query_selector('span.collect-count')
            if collect_element:
                collects = await collect_element.inner_text()
        except:
            pass

        result = f"""标题: {title}
点赞数: {likes}
收藏数: {collects}

内容:
{content}

URL: {processed_url}
"""
        print(f"✅ 笔记内容获取完成")
        return result

    except Exception as e:
        print(f"❌ 获取笔记失败: {e}")
        return f"获取笔记失败: {str(e)}"

@mcp.tool()
async def post_comment(url: str, comment: str) -> str:
    """发布评论到指定笔记

    Args:
        url: 笔记 URL
        comment: 要发布的评论内容
    """
    login_status = await ensure_browser()
    if not login_status:
        return "请先登录小红书账号"

    if not main_page:
        return "浏览器初始化失败，请重试"

    # 处理URL
    processed_url = url.strip()
    if not processed_url.startswith('http'):
        processed_url = 'https://' + processed_url

    try:
        await main_page.goto(processed_url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 查找评论输入框
        comment_input = await main_page.query_selector('textarea.comment-input, textarea[placeholder*="评论"]')
        if not comment_input:
            return "未找到评论输入框"

        # 输入评论
        await comment_input.fill(comment)
        await asyncio.sleep(1)

        # 点击发送按钮
        send_button = await main_page.query_selector('button.send-btn, button:has-text("发送")')
        if send_button:
            await send_button.click()
            await asyncio.sleep(1)
            return f"评论发布成功: {comment}"
        else:
            return "未找到发送按钮"

    except Exception as e:
        return f"发布评论失败: {str(e)}"

@mcp.tool()
async def post_smart_comment(url: str, comment_type: str = "引流") -> str:
    """根据帖子内容发布智能评论

    Args:
        url: 笔记 URL
        comment_type: 评论类型（引流/点赞/咨询/专业）
    """
    # 首先获取笔记内容
    content = await get_note_content(url)

    # 根据类型生成评论建议
    comment_suggestions = {
        "引流": "根据笔记内容，建议评论：关注我获取更多相关内容，或私信交流~",
        "点赞": "根据笔记内容，建议评论：写得太好了，收藏了！",
        "咨询": "根据笔记内容，建议评论：请问有更详细的教程吗？",
        "专业": "根据笔记内容，建议评论：补充一点，从专业角度来看..."
    }

    suggestion = comment_suggestions.get(comment_type, comment_suggestions["引流"])

    return f"""笔记内容摘要:
{content[:500]}...

评论建议:
{suggestion}

请使用 post_comment 工具发布评论。
"""

async def analyze_note(url: str) -> str:
    """获取并分析笔记内容，返回笔记的详细信息

    Args:
        url: 笔记 URL
    """
    content = await get_note_content(url)
    return content

def main():
    """主函数"""
    import sys
    if "--stdio" in sys.argv:
        import asyncio
        asyncio.run(mcp.run_stdio_async())
    else:
        mcp.run()

if __name__ == "__main__":
    main()
