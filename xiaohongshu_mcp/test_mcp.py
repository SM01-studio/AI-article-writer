import asyncio
from xiaohongshu_mcp import login, get_note_content

async def main():
    # 登录小红书
    print("正在登录小红书...")
    login_result = await login()
    print(f"登录结果: {login_result}")
    
    # 获取笔记内容
    url = "https://www.xiaohongshu.com/explore/685101f30000000012007399?xsec_token=ABHycGGcQ15MmF8-zYrhTrN0idr7hv2qrwrSRCXhIQeJk=&xsec_source=pc_feed"
    print(f"正在获取笔记内容，URL: {url}")
    content_result = await get_note_content(url)
    print(f"获取内容结果: {content_result}")

if __name__ == "__main__":
    asyncio.run(main()) 