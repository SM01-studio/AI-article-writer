#!/usr/bin/env python3
"""
AI Article Writer - GLM Service
GLM API 服务模块 - 使用智谱 AI 进行搜索和内容生成

使用 GLM-4 模型，支持联网搜索
"""

import os
import json
import requests
from typing import Dict, List, Optional, Callable
from datetime import datetime

class GLMService:
    """GLM API 服务"""

    def __init__(self):
        """初始化 GLM 服务"""
        self.api_key = os.environ.get("GLM_API_KEY", "")
        if not self.api_key:
            print("⚠️ GLM_API_KEY 环境变量未设置，GLM 服务将不可用")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-4"  # GLM-4 支持联网搜索
        self.search_model = "glm-4"  # 用于搜索的模型

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    def _call_api(
        self,
        messages: List[Dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: List[Dict] = None
    ) -> Dict:
        """
        调用 GLM API

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            tools: 工具列表（用于联网搜索等）

        Returns:
            API 响应
        """
        model = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if tools:
            payload["tools"] = tools

        try:
            print(f"[GLMService] 正在调用 API: {self.base_url}/chat/completions")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            print(f"[GLMService] API 调用成功")
            return result
        except requests.exceptions.Timeout:
            print(f"[GLMService] API 调用超时")
            return {"error": "API 调用超时", "choices": []}
        except requests.exceptions.RequestException as e:
            print(f"[GLMService] API 请求失败: {e}")
            return {"error": str(e), "choices": []}
        except Exception as e:
            print(f"[GLMService] API 调用异常: {e}")
            return {"error": str(e), "choices": []}

    def search(
        self,
        query: str,
        on_progress: Callable[[int, str], None] = None
    ) -> List[Dict]:
        """
        使用 GLM 进行联网搜索

        Args:
            query: 搜索查询
            on_progress: 进度回调

        Returns:
            搜索结果列表
        """
        if on_progress:
            on_progress(10, f"正在搜索: {query[:30]}...")

        print(f"[GLMService] 搜索: {query}")

        # GLM-4 的联网搜索工具
        tools = [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_query": query
                }
            }
        ]

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的研究助手。请搜索并提供关于用户查询的详细信息。返回结构化的搜索结果，包括来源标题、URL（如果有）和内容摘要。"
            },
            {
                "role": "user",
                "content": f"请搜索以下主题，并提供详细的搜索结果：\n\n{query}\n\n请以结构化的方式返回：\n1. 来源标题\n2. 内容摘要\n3. 关键信息点"
            }
        ]

        if on_progress:
            on_progress(30, "正在调用 GLM 搜索...")

        response = self._call_api(
            messages=messages,
            tools=tools,
            temperature=0.3
        )

        if on_progress:
            on_progress(70, "正在解析搜索结果...")

        # 解析响应
        sources = []
        if "choices" in response and response["choices"]:
            content = response["choices"][0].get("message", {}).get("content", "")

            # 将搜索结果转换为结构化格式
            # GLM 会返回文本形式的搜索结果，需要解析
            sections = content.split("\n\n")
            for i, section in enumerate(sections[:10]):
                if section.strip():
                    lines = section.strip().split("\n")
                    title = lines[0] if lines else f"搜索结果 {i+1}"
                    content_text = "\n".join(lines[1:]) if len(lines) > 1 else section

                    sources.append({
                        "type": "GLM-Search",
                        "title": title[:100],
                        "content": content_text[:500],
                        "summary": content_text[:200]
                    })

        if on_progress:
            on_progress(100, "搜索完成")

        print(f"[GLMService] 搜索完成: {len(sources)} 条结果")
        return sources

    def generate_outline(
        self,
        topic: str,
        research_data: Dict,
        length: str = "medium",
        audience: str = "general",
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        生成文章大纲

        Args:
            topic: 文章主题
            research_data: 调研数据
            length: 文章长度 (short/medium/long)
            audience: 目标读者 (tech/general/mixed)
            on_progress: 进度回调

        Returns:
            大纲数据
        """
        if on_progress:
            on_progress(10, "正在分析调研数据...")

        # 提取调研信息
        sources = research_data.get("sources", [])
        sources_summary = "\n".join([
            f"- {s.get('title', '未知')}: {s.get('summary', '')[:100]}"
            for s in sources[:10]
        ])

        # 根据长度确定章节数
        chapter_counts = {"short": 4, "medium": 6, "long": 8}
        target_chapters = chapter_counts.get(length, 6)

        audience_desc = {
            "tech": "技术人员，可以使用专业术语",
            "general": "大众读者，需要通俗易懂",
            "mixed": "混合读者，兼顾专业性和可读性"
        }.get(audience, "大众读者")

        if on_progress:
            on_progress(30, "正在生成大纲...")

        messages = [
            {
                "role": "system",
                "content": """你是一个大师级的科普文章大纲设计师。请根据调研信息生成专业、详细、结构化的文章大纲。

返回 JSON 格式：
{
  "chapters": [
    {
      "number": 0,
      "title": "章节标题（必须与主题紧密相关，不能用通用标题）",
      "description": "详细章节描述（80-150字，说明核心观点、详细解释、案例/数据、小结过渡）",
      "key_points": ["要点1", "要点2", "要点3"],
      "image_suggestion": "配图建议（可选）"
    },
    ...
  ],
  "word_count": "目标字数",
  "writing_style": "写作风格建议",
  "image_style": "配图风格关键词"
}

【核心要求】
1. 标题必须具体化，禁止使用泛泛的通用标题如"核心概念"、"技术原理"、"应用场景"
2. 标题要体现主题特色，例如主题是"GPT-4"，标题应该是"GPT-4的多模态能力"而非"核心能力"
3. 描述必须详细（80-150字），包含：
   - 核心观点（1-2句话）
   - 详细解释内容（2-3个要点）
   - 案例/数据支撑
   - 小结/过渡
4. key_points 必须列出3-5个具体要点
5. 逻辑要连贯，层层递进，有引人入胜的开头和有力的结尾

【文章结构参考】
- 第0章：引言（钩子+背景+预告，吸引读者）
- 第1-2章：基础概念（是什么、为什么重要）
- 第3-4章：核心内容（技术原理、关键特性）
- 第5章：应用实践（案例、数据）
- 最后章：结语（核心回顾+未来展望+行动建议）"""
            },
            {
                "role": "user",
                "content": f"""请为以下主题生成专业、详细的文章大纲：

主题: {topic}
目标章节数: {target_chapters}
目标读者: {audience_desc}

调研信息:
{sources_summary}

【重要】
1. 每个章节标题必须与"{topic}"这个具体主题紧密相关
2. 禁止使用"核心概念"、"技术原理"、"应用场景"等泛泛标题
3. 描述要详细（80-150字），包含核心观点、详细解释、案例数据、小结过渡
4. 必须包含 key_points 数组，列出3-5个具体要点"""
            }
        ]

        response = self._call_api(
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )

        if on_progress:
            on_progress(70, "正在解析大纲...")

        # 检查 API 是否出错
        if "error" in response and response.get("error"):
            print(f"[GLMService] API 返回错误: {response.get('error')}")
            # 使用默认结构
            chapters = []
        else:
            print(f"[GLMService] API 响应正常，正在解析...")

        # 解析响应
        chapters = []
        if "choices" in response and response["choices"]:
            content = response["choices"][0].get("message", {}).get("content", "")
            print(f"[GLMService] API 返回内容长度: {len(content)} 字符")

            # 尝试提取 JSON
            try:
                import re
                # 尝试多种 JSON 格式
                json_patterns = [
                    r'\{[\s\S]*"chapters"[\s\S]*\}',  # 包含 chapters 的对象
                    r'\{[\s\S]*\}',  # 任何 JSON 对象
                ]
                for pattern in json_patterns:
                    json_match = re.search(pattern, content)
                    if json_match:
                        outline_data = json.loads(json_match.group())
                        chapters = outline_data.get("chapters", [])
                        if chapters:
                            print(f"[GLMService] 成功解析大纲: {len(chapters)} 个章节")
                            break
            except json.JSONDecodeError as e:
                print(f"[GLMService] JSON 解析失败: {e}")
            except Exception as e:
                print(f"[GLMService] 解析大纲失败: {e}")

        # 如果没有解析到章节，使用默认结构
        if not chapters:
            print(f"[GLMService] 使用默认大纲结构")
            chapters = [
                {"number": 0, "title": "引言", "description": f"介绍{topic}的背景"},
                {"number": 1, "title": "核心概念", "description": f"解释{topic}的核心概念"},
                {"number": 2, "title": "技术原理", "description": f"{topic}的技术原理"},
                {"number": 3, "title": "应用场景", "description": f"{topic}的实际应用"},
                {"number": 4, "title": "发展趋势", "description": f"{topic}的未来趋势"},
                {"number": 5, "title": "总结", "description": "总结要点"},
            ]

        if on_progress:
            on_progress(100, "大纲生成完成")

        # 生成配图规划
        image_plan = {
            "style": "科技感, 深蓝色调, 几何图形, 渐变, 未来感, 4K",
            "cover": {
                "description": f"{topic} 概念可视化封面",
                "size": "1024x576"
            },
            "chapters": [f"{ch.get('title', '章节')} 配图" for ch in chapters]
        }

        return {
            "topic": topic,
            "chapters": chapters,
            "chapter_count": len(chapters),
            "word_count": {"short": "1500", "medium": "3000", "long": "8000"}.get(length, "3000"),
            "target_audience": audience,
            "image_plan": image_plan,
            "generated_by": "AI",
            "timestamp": datetime.now().isoformat()
        }

    def generate_draft(
        self,
        outline: Dict,
        research_data: Dict,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        生成文章初稿

        Args:
            outline: 文章大纲
            research_data: 调研数据
            on_progress: 进度回调

        Returns:
            初稿数据
        """
        topic = outline.get("topic", "未知主题")
        chapters = outline.get("chapters", [])

        # 🔧 修复：从大纲获取目标字数
        target_word_count = outline.get("word_count", "3000")
        if isinstance(target_word_count, str):
            target_word_count = int(target_word_count.replace("+", ""))

        # 计算每章节目标字数（扣除标题、引言等）
        total_chapters = len(chapters)
        if total_chapters > 0:
            words_per_chapter = max(200, (target_word_count - 200) // total_chapters)
        else:
            words_per_chapter = 500

        print(f"[GLM] 目标总字数: {target_word_count}, 章节数: {total_chapters}, 每章节约: {words_per_chapter} 字")

        if on_progress:
            on_progress(5, f"开始生成初稿... (目标: {target_word_count}字)")

        # 逐章节生成
        draft_content = f"# {topic}\n\n"
        draft_content += "> 本文由 AI Article Writer 自动生成\n\n"

        for i, chapter in enumerate(chapters):
            progress = 10 + int((i / total_chapters) * 80)
            chapter_title = chapter.get('title', '')
            chapter_desc = chapter.get('description', '')

            if on_progress:
                on_progress(progress, f"正在撰写: {chapter_title}")

            # 🔧 修复：根据目标字数动态调整每章节字数
            chapter_min = max(150, words_per_chapter - 100)
            chapter_max = words_per_chapter + 100

            # 生成章节内容
            messages = [
                {
                    "role": "system",
                    "content": f"你是一个专业的科普文章作者。请撰写章节内容，要求：\n1. 语言流畅，逻辑清晰\n2. 有具体案例或数据支撑\n3. 适合科普文章风格\n4. 字数严格控制在 {chapter_min}-{chapter_max} 字之间"
                },
                {
                    "role": "user",
                    "content": f"请为文章《{topic}》撰写章节 \"{chapter_title}\"。\n\n章节描述: {chapter_desc}\n\n请写 {chapter_min}-{chapter_max} 字的段落内容。"
                }
            ]

            response = self._call_api(
                messages=messages,
                temperature=0.7,
                max_tokens=max(1024, words_per_chapter * 2)
            )

            chapter_content = ""
            if "choices" in response and response["choices"]:
                chapter_content = response["choices"][0].get("message", {}).get("content", "")

            if not chapter_content:
                chapter_content = f"[{chapter_title}] 这部分内容将介绍{chapter_desc}。"

            draft_content += f"## {i}. {chapter_title}\n\n"
            draft_content += chapter_content
            draft_content += "\n\n"

        if on_progress:
            on_progress(95, "正在整理格式...")

        word_count = len(draft_content)

        if on_progress:
            on_progress(100, "初稿生成完成")

        return {
            "topic": topic,
            "content": draft_content,
            "word_count": word_count,
            "chapter_count": len(chapters),
            "generated_by": "AI",
            "timestamp": datetime.now().isoformat()
        }

    def process_feedback(
        self,
        current_content: Dict,
        feedback: str,
        content_type: str = "outline",
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        处理用户反馈，智能调整内容

        Args:
            current_content: 当前内容
            feedback: 用户反馈
            content_type: 内容类型 (outline/draft)
            on_progress: 进度回调

        Returns:
            调整后的内容
        """
        import re

        if on_progress:
            on_progress(10, "正在分析反馈...")

        if content_type == "draft":
            # 对于文章内容，使用智能局部修改逻辑
            return self._process_draft_feedback(current_content, feedback, on_progress)
        elif content_type == "outline":
            # 对于大纲，使用专门的逻辑
            return self._process_outline_feedback(current_content, feedback, on_progress)
        else:
            return current_content

    def _process_draft_feedback(
        self,
        draft: Dict,
        feedback: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        智能处理文章内容的用户反馈

        核心逻辑：
        1. AI 理解用户指令，定位到具体章节
        2. AI 只返回需要修改的部分
        3. 后端合并到原文
        """
        import re

        if on_progress:
            on_progress(20, "正在分析用户指令...")

        content = draft.get("content", "")
        topic = draft.get("topic", "未知主题")

        # 第一步：让 AI 理解用户指令并定位章节
        analyze_prompt = f"""你是一个专业的内容编辑助手。请分析用户的修改指令。

文章主题: {topic}

当前文章结构（仅章节标题）:
{self._extract_chapters_summary(content)}

用户指令: {feedback}

请返回 JSON 格式：
{{
    "action": "modify_section" | "rewrite_all" | "add_section" | "delete_section",
    "target_section": "章节编号（如 1, 2, 2.1 等），如果是全文则为 null",
    "instruction": "具体的修改指令摘要",
    "reason": "判断理由"
}}

判断规则：
- action="modify_section": 用户要求修改特定章节（如"扩写第二章"、"第一章太长请精简"）
- action="rewrite_all": 用户要求重写整篇文章
- action="add_section": 用户要求增加新章节
- action="delete_section": 用户要求删除某章节

只返回 JSON，不要其他内容。"""

        try:
            analyze_response = self._call_api(
                messages=[{"role": "user", "content": analyze_prompt}],
                temperature=0.1,
                max_tokens=200
            )

            if on_progress:
                on_progress(40, "正在定位修改位置...")

            action = "modify_section"
            target_section = None

            if analyze_response and "choices" in analyze_response:
                analyze_content = analyze_response["choices"][0].get("message", {}).get("content", "")
                json_match = re.search(r'\{[\s\S]*\}', analyze_content)
                if json_match:
                    analyze_data = json.loads(json_match.group())
                    action = analyze_data.get("action", "modify_section")
                    target_section = analyze_data.get("target_section")
                    print(f"[GLMService] 分析结果: action={action}, target={target_section}")

        except Exception as e:
            print(f"[GLMService] 指令分析失败: {e}")
            action = "modify_section"

        if on_progress:
            on_progress(60, "正在生成修改内容...")

        # 第二步：根据 action 执行不同的修改策略
        if action == "modify_section" and target_section:
            # 局部修改：只修改目标章节
            return self._modify_specific_section(draft, feedback, target_section, on_progress)
        elif action == "rewrite_all":
            # 全文重写
            return self._rewrite_entire_draft(draft, feedback, on_progress)
        elif action == "add_section":
            # 增加章节
            return self._add_new_section(draft, feedback, on_progress)
        elif action == "delete_section":
            # 删除章节
            return self._delete_section(draft, feedback, target_section, on_progress)
        else:
            # 默认：尝试智能修改
            return self._smart_modify_draft(draft, feedback, on_progress)

    def _extract_chapters_summary(self, content: str) -> str:
        """提取章节摘要"""
        import re
        chapters = []
        lines = content.split('\n')
        for line in lines:
            # 匹配 ## 1. 或 ## 2. 格式的章节标题
            match = re.match(r'^##\s*(\d+\.?\d*)\.?\s*(.+)$', line)
            if match:
                chapter_num = match.group(1)
                chapter_title = match.group(2).strip()
                chapters.append(f"{chapter_num} {chapter_title}")
        return '\n'.join(chapters) if chapters else "未检测到章节结构"

    def _modify_specific_section(
        self,
        draft: Dict,
        feedback: str,
        target_section: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """修改特定章节"""
        import re

        content = draft.get("content", "")
        topic = draft.get("topic", "未知主题")

        # 提取目标章节内容
        sections = self._split_content_by_sections(content)
        target_content = None
        target_title = ""

        for section_num, section_title, section_content in sections:
            if str(section_num).startswith(str(target_section)) or str(target_section) in str(section_num):
                target_content = section_content
                target_title = section_title
                break

        if not target_content:
            # 如果找不到精确匹配，使用智能修改
            return self._smart_modify_draft(draft, feedback, on_progress)

        if on_progress:
            on_progress(70, f"正在修改章节: {target_title}...")

        # 让 AI 修改这个章节
        modify_prompt = f"""你是一个专业的文章编辑。请根据用户指令修改指定的章节内容。

文章主题: {topic}
章节标题: {target_title}

当前章节内容:
{target_content}

用户指令: {feedback}

请直接返回修改后的完整章节内容（包含章节标题），不要添加任何解释或标记。
格式要求：
## {target_title}

[修改后的内容...]"""

        response = self._call_api(
            messages=[{"role": "user", "content": modify_prompt}],
            temperature=0.7,
            max_tokens=4096
        )

        if response and "choices" in response:
            new_section_content = response["choices"][0].get("message", {}).get("content", "")

            if on_progress:
                on_progress(90, "正在合并修改...")

            # 替换原文中的章节
            new_content = self._replace_section(content, target_section, new_section_content)

            if new_content:
                draft["content"] = new_content
                draft["word_count"] = len(new_content)
                draft["last_modified"] = datetime.now().isoformat()
                draft["modification_note"] = f"已修改章节 {target_title}"

                if on_progress:
                    on_progress(100, "修改完成")

                return draft

        if on_progress:
            on_progress(100, "修改完成")

        return draft

    def _split_content_by_sections(self, content: str) -> List[tuple]:
        """按章节分割内容，返回 [(章节号, 章节标题, 章节内容), ...]"""
        import re
        sections = []
        lines = content.split('\n')
        current_section = None
        current_num = None
        current_title = ""
        current_content_lines = []

        for line in lines:
            # 匹配 ## 1. 标题 格式
            match = re.match(r'^##\s*(\d+\.?\d*)\.?\s*(.+)$', line)
            if match:
                # 保存上一个章节
                if current_section is not None:
                    sections.append((current_num, current_title, '\n'.join(current_content_lines)))

                current_num = match.group(1)
                current_title = match.group(2).strip()
                current_content_lines = [line]
            else:
                if current_section is not None or current_num is not None:
                    current_content_lines.append(line)
                elif line.strip():
                    # 开头没有章节标题的内容
                    if not sections:
                        sections.append(("0", "引言", line))
                    else:
                        sections[0] = ("0", "引言", sections[0][2] + '\n' + line)

        # 保存最后一个章节
        if current_num:
            sections.append((current_num, current_title, '\n'.join(current_content_lines)))

        return sections

    def _replace_section(self, content: str, target_section: str, new_section: str) -> str:
        """替换指定章节"""
        import re
        lines = content.split('\n')
        result_lines = []
        in_target_section = False
        target_pattern = re.compile(rf'^##\s*{re.escape(target_section)}\.?\s*')

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是目标章节的开始
            if target_pattern.match(line):
                in_target_section = True
                # 插入新的章节内容
                result_lines.append(new_section)
                i += 1
                continue

            # 检查是否是下一个章节（结束当前目标章节）
            if in_target_section and re.match(r'^##\s*\d+', line):
                in_target_section = False

            # 如果不在目标章节内，保留原内容
            if not in_target_section:
                result_lines.append(line)

            i += 1

        return '\n'.join(result_lines)

    def _rewrite_entire_draft(
        self,
        draft: Dict,
        feedback: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """重写整篇文章"""
        content = draft.get("content", "")
        topic = draft.get("topic", "未知主题")

        if on_progress:
            on_progress(70, "正在重写全文...")

        rewrite_prompt = f"""你是一个专业的文章编辑。请根据用户指令重写整篇文章。

文章主题: {topic}

当前文章内容:
{content[:6000]}  # 限制长度避免 token 超限

用户指令: {feedback}

请直接返回重写后的完整文章内容，保持 Markdown 格式。"""

        response = self._call_api(
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.7,
            max_tokens=8192
        )

        if response and "choices" in response:
            new_content = response["choices"][0].get("message", {}).get("content", "")
            draft["content"] = new_content
            draft["word_count"] = len(new_content)
            draft["last_modified"] = datetime.now().isoformat()
            draft["modification_note"] = "已重写全文"

        if on_progress:
            on_progress(100, "重写完成")

        return draft

    def _add_new_section(
        self,
        draft: Dict,
        feedback: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """添加新章节"""
        import re
        content = draft.get("content", "")
        topic = draft.get("topic", "未知主题")

        if on_progress:
            on_progress(70, "正在添加新章节...")

        # 获取现有章节数
        sections = self._split_content_by_sections(content)
        new_section_num = len(sections) + 1

        add_prompt = f"""你是一个专业的文章编辑。请根据用户指令添加新章节。

文章主题: {topic}
现有章节数: {len(sections)}
新章节编号: {new_section_num}

用户指令: {feedback}

请生成新章节的内容，格式：
## {new_section_num}. [章节标题]

[章节内容...]

只返回新章节内容，不要其他内容。"""

        response = self._call_api(
            messages=[{"role": "user", "content": add_prompt}],
            temperature=0.7,
            max_tokens=2048
        )

        if response and "choices" in response:
            new_section = response["choices"][0].get("message", {}).get("content", "")
            # 添加到文章末尾
            draft["content"] = content + "\n\n" + new_section
            draft["word_count"] = len(draft["content"])
            draft["chapter_count"] = new_section_num
            draft["last_modified"] = datetime.now().isoformat()
            draft["modification_note"] = "已添加新章节"

        if on_progress:
            on_progress(100, "添加完成")

        return draft

    def _delete_section(
        self,
        draft: Dict,
        feedback: str,
        target_section: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """删除指定章节"""
        import re
        content = draft.get("content", "")

        if on_progress:
            on_progress(70, f"正在删除章节 {target_section}...")

        if target_section:
            lines = content.split('\n')
            result_lines = []
            in_target_section = False
            target_pattern = re.compile(rf'^##\s*{re.escape(target_section)}\.?\s*')

            for line in lines:
                # 检查是否是目标章节的开始
                if target_pattern.match(line):
                    in_target_section = True
                    continue

                # 检查是否是下一个章节（结束删除范围）
                if in_target_section and re.match(r'^##\s*\d+', line):
                    in_target_section = False

                # 如果不在删除范围内，保留内容
                if not in_target_section:
                    result_lines.append(line)

            new_content = '\n'.join(result_lines)
            draft["content"] = new_content
            draft["word_count"] = len(new_content)
            draft["last_modified"] = datetime.now().isoformat()
            draft["modification_note"] = f"已删除章节 {target_section}"

        if on_progress:
            on_progress(100, "删除完成")

        return draft

    def _smart_modify_draft(
        self,
        draft: Dict,
        feedback: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """智能修改：让 AI 理解指令并直接修改内容"""
        import re
        content = draft.get("content", "")
        topic = draft.get("topic", "未知主题")

        if on_progress:
            on_progress(70, "正在智能修改内容...")

        # 让 AI 直接修改并返回完整内容
        smart_prompt = f"""你是一个专业的文章编辑。请根据用户指令修改文章内容。

文章主题: {topic}

当前文章内容:
{content[:8000]}

用户指令: {feedback}

请直接返回修改后的完整文章内容（Markdown 格式），不要添加任何解释。
如果用户指令不明确或无法执行，请返回原文。"""

        response = self._call_api(
            messages=[{"role": "user", "content": smart_prompt}],
            temperature=0.7,
            max_tokens=8192
        )

        if response and "choices" in response:
            new_content = response["choices"][0].get("message", {}).get("content", "")
            # 简单验证：新内容不能太短
            if len(new_content) > len(content) * 0.3:
                draft["content"] = new_content
                draft["word_count"] = len(new_content)
                draft["last_modified"] = datetime.now().isoformat()
                draft["modification_note"] = "已智能修改"

        if on_progress:
            on_progress(100, "修改完成")

        return draft

    def _process_outline_feedback(
        self,
        outline: Dict,
        feedback: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """处理大纲的反馈修改 - 使用 AI 大模型智能处理所有类型的修改"""
        import re

        if on_progress:
            on_progress(20, "正在分析大纲修改...")

        # 获取当前大纲的完整信息
        current_chapters = outline.get("chapters", [])
        current_image_plan = outline.get("image_plan", {})
        current_word_count = outline.get("word_count", "3000")
        current_style = current_image_plan.get("style", "科技感, 深蓝色调")

        context = f"""你是一个专业的文章大纲设计师。请根据用户反馈智能修改大纲。

当前大纲信息:
- 章节: {json.dumps(current_chapters, ensure_ascii=False, indent=2)}
- 配图数量: {len(current_image_plan.get('chapters', []))} 张
- 配图风格: {current_style}
- 目标字数: {current_word_count}

用户反馈: {feedback}

请根据用户反馈智能修改大纲。你需要理解用户的意图并做出相应修改：
1. 章节：可以增加、删除、修改章节
2. 配图数量：根据章节数量自动调整
3. 配图风格：可以更换风格（如：手绘、科技感、卡通等）
4. 字数：可以调整目标字数

请返回修改后的完整大纲，JSON 格式：
{{
  "chapters": [
    {{"number": 0, "title": "章节标题", "description": "章节描述"}},
    ...
  ],
  "image_count": 配图数量,
  "image_style": "配图风格描述",
  "word_count": "目标字数"
}}

只返回 JSON 对象，不要其他内容。"""

        response = self._call_api(
            messages=[{"role": "user", "content": context}],
            temperature=0.5,
            max_tokens=2048
        )

        if on_progress:
            on_progress(80, "正在解析结果...")

        if response and "choices" in response:
            content = response["choices"][0].get("message", {}).get("content", "")
            # 尝试匹配 JSON 对象
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    if isinstance(result, dict):
                        # 更新章节
                        if "chapters" in result and isinstance(result["chapters"], list):
                            outline["chapters"] = result["chapters"]
                            outline["chapter_count"] = len(result["chapters"])

                        # 更新配图数量
                        if "image_count" in result:
                            image_count = result["image_count"]
                            outline.setdefault("image_plan", {})
                            outline["image_plan"]["chapters"] = [
                                f'第{i+1}章配图' for i in range(min(image_count, len(outline.get("chapters", []))))
                            ]

                        # 更新配图风格
                        if "image_style" in result:
                            outline.setdefault("image_plan", {})
                            outline["image_plan"]["style"] = result["image_style"]

                        # 更新字数
                        if "word_count" in result:
                            outline["word_count"] = str(result["word_count"])

                        outline["last_modified"] = datetime.now().isoformat()
                        return outline
                except json.JSONDecodeError:
                    pass

        if on_progress:
            on_progress(100, "修改完成")

        return outline

    def process_layout(
        self,
        draft_content: str,
        outline: Dict,
        images_data: Dict,
        topic: str,
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        智能排版处理 - 使用 GLM 进行内容优化

        Args:
            draft_content: 初稿内容
            outline: 大纲数据
            images_data: 配图数据
            topic: 文章主题
            on_progress: 进度回调

        Returns:
            排版后的内容数据
        """
        if on_progress:
            on_progress(10, "分析文章结构...")

        chapters = outline.get('chapters', [])
        images = images_data.get('images', [])
        image_style = images_data.get('style_keywords', '科技感, 蓝色调')

        # 构建图片信息
        image_info = ""
        if images:
            image_info = "可用配图:\n"
            for img in images:
                img_type = img.get('type', 'chapter')
                img_name = img.get('name', 'unknown')
                img_desc = img.get('description', '')
                image_info += f"- {img_name} ({img_type}): {img_desc}\n"

        # 构建 GLM prompt
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的排版编辑。你的任务是优化文章内容，使其更适合发布。

你需要完成以下任务：
1. 去除重复的段落标题（如果段落开头和标题重复）
2. 优化段落结构，确保阅读流畅
3. 确定每张配图的最佳插入位置（在相关段落之后）
4. 生成最终的结构化内容

返回 JSON 格式：
{
  "processed_content": "处理后的完整文章内容（Markdown格式）",
  "image_placements": [
    {"image": "cover.png", "position": "after_title", "description": "封面图位置"},
    {"image": "chapter-0.png", "position": "after_paragraph_3", "description": "第一章配图位置"}
  ],
  "layout_notes": ["排版说明1", "排版说明2"]
}

注意：
- 保持原文的核心内容不变
- 只优化结构和格式
- 配图应该放在相关内容之后
- 确保配图与内容的相关性"""
            },
            {
                "role": "user",
                "content": f"""请对以下文章进行智能排版：

主题: {topic}

章节结构:
{json.dumps(chapters, ensure_ascii=False, indent=2)}

{image_info}

原始内容:
{draft_content[:6000]}

请优化内容并确定配图位置。"""
            }
        ]

        if on_progress:
            on_progress(30, "正在调用 AI 进行智能排版...")

        print(f"[GLMService] 开始智能排版: {topic}")

        response = self._call_api(
            messages=messages,
            temperature=0.5,
            max_tokens=4096
        )

        if on_progress:
            on_progress(70, "正在解析排版结果...")

        # 解析响应
        result = {
            "processed_content": draft_content,
            "image_placements": [],
            "layout_notes": []
        }

        if "choices" in response and response["choices"]:
            content = response["choices"][0].get("message", {}).get("content", "")
            print(f"[GLMService] AI 排版响应长度: {len(content)} 字符")

            # 尝试提取 JSON
            try:
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if parsed.get("processed_content"):
                        result = parsed
                        print(f"[GLMService] 智能排版完成")
            except json.JSONDecodeError as e:
                print(f"[GLMService] JSON 解析失败: {e}")
            except Exception as e:
                print(f"[GLMService] 解析排版结果失败: {e}")

        if on_progress:
            on_progress(100, "排版完成")

        return result


# 全局实例
glm_service = GLMService()
