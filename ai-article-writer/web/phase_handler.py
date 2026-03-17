#!/usr/bin/env python3
"""
AI Article Writer - Phase Handler
阶段处理器 - 读取 SKILL 参考文档，执行各阶段逻辑

这是系统的"大脑"，所有处理逻辑都在这里

注意：在方案 B 架构中，此模块由 SKILL 程序调用，不是后端直接调用
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# 参考文档目录
REFERENCES_DIR = Path(__file__).parent.parent / "references"

class PhaseHandler:
    """阶段处理器 - 系统的核心大脑"""

    def __init__(self):
        """初始化，加载参考文档"""
        self.references = {}
        self._load_references()

    def _load_references(self):
        """加载 SKILL 参考文档"""
        reference_files = {
            'research': 'research-guide.md',
            'writing': 'writing-standards.md',
            'image': 'image-generation.md',
            'output': 'output-formats.md',
            'workflow': 'workflow.md'
        }

        for key, filename in reference_files.items():
            filepath = REFERENCES_DIR / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.references[key] = f.read()
                print(f"[PhaseHandler] 加载参考文档: {filename}")
            else:
                print(f"[PhaseHandler] 警告: 参考文档不存在 {filepath}")

    # ==================== Phase 1: 深度调研 ====================

    def process_research(self, topic: str, sources: List[Dict], options: Dict = None) -> Dict:
        """
        处理调研阶段 - 根据 research-guide.md 的方法论

        Args:
            topic: 调研主题
            sources: 搜索来源列表
            options: 额外选项（include_xiaohongshu, include_weixin 等）

        Returns:
            结构化的调研报告
        """
        options = options or {}

        # 按照 research-guide.md 的结构整理信息
        research_report = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),

            # 核心概念
            'core_concepts': self._extract_core_concepts(topic, sources),

            # 技术原理
            'technical_principles': self._extract_technical_principles(topic, sources),

            # 应用场景
            'applications': self._extract_applications(topic, sources),

            # 发展趋势
            'trends': self._extract_trends(topic, sources),

            # 争议与挑战
            'challenges': self._extract_challenges(topic, sources),

            # 原始来源
            'sources': sources,

            # 关键发现
            'key_findings': self._generate_key_findings(topic, sources),

            # 可信度评估
            'credibility': self._evaluate_credibility(sources)
        }

        return research_report

    def _extract_core_concepts(self, topic: str, sources: List[Dict]) -> List[Dict]:
        """提取核心概念"""
        concepts = []
        for source in sources:
            content = source.get('content', '') or source.get('summary', '')
            # 简单提取：从内容中提取关键句子
            if content:
                concepts.append({
                    'source': source.get('title', '未知来源'),
                    'type': source.get('type', 'WebSearch'),
                    'content': content[:500]  # 取前500字符作为概念描述
                })
        return concepts[:5]  # 最多5个核心概念

    def _extract_technical_principles(self, topic: str, sources: List[Dict]) -> List[Dict]:
        """提取技术原理"""
        principles = []
        tech_keywords = ['原理', '技术', '算法', '架构', '实现', 'principle', 'technical', 'how it works']

        for source in sources:
            title = source.get('title', '')
            content = source.get('content', '') or source.get('summary', '')

            # 检查是否包含技术关键词
            if any(kw in title.lower() or kw in content.lower()[:200] for kw in tech_keywords):
                principles.append({
                    'source': source.get('title', '未知来源'),
                    'content': content[:500]
                })

        return principles[:3]

    def _extract_applications(self, topic: str, sources: List[Dict]) -> List[Dict]:
        """提取应用场景"""
        applications = []
        app_keywords = ['应用', '案例', '场景', '实践', '使用', 'application', 'case', 'use case']

        for source in sources:
            title = source.get('title', '')
            content = source.get('content', '') or source.get('summary', '')

            if any(kw in title.lower() or kw in content.lower()[:200] for kw in app_keywords):
                applications.append({
                    'source': source.get('title', '未知来源'),
                    'type': source.get('type', 'WebSearch'),
                    'content': content[:500]
                })

        return applications[:5]

    def _extract_trends(self, topic: str, sources: List[Dict]) -> List[Dict]:
        """提取发展趋势"""
        trends = []
        trend_keywords = ['趋势', '未来', '展望', '发展', '预测', 'trend', 'future', 'outlook']

        for source in sources:
            title = source.get('title', '')
            content = source.get('content', '') or source.get('summary', '')

            if any(kw in title.lower() or kw in content.lower()[:200] for kw in trend_keywords):
                trends.append({
                    'source': source.get('title', '未知来源'),
                    'content': content[:500]
                })

        return trends[:3]

    def _extract_challenges(self, topic: str, sources: List[Dict]) -> List[Dict]:
        """提取争议与挑战"""
        challenges = []
        challenge_keywords = ['挑战', '问题', '困难', '争议', '风险', 'challenge', 'problem', 'issue', 'risk']

        for source in sources:
            title = source.get('title', '')
            content = source.get('content', '') or source.get('summary', '')

            if any(kw in title.lower() or kw in content.lower()[:200] for kw in challenge_keywords):
                challenges.append({
                    'source': source.get('title', '未知来源'),
                    'content': content[:500]
                })

        return challenges[:3]

    def _generate_key_findings(self, topic: str, sources: List[Dict]) -> List[str]:
        """生成关键发现"""
        findings = []

        # 基于来源数量和类型生成发现
        source_types = set(s.get('type', 'WebSearch') for s in sources)

        findings.append(f"已收集 {len(sources)} 个信息来源")
        findings.append(f"信息来源类型: {', '.join(source_types)}")
        findings.append(f"主题 '{topic}' 的核心概念已清晰定义")

        if len(sources) >= 5:
            findings.append("信息来源充足，可以进入大纲设计阶段")
        else:
            findings.append("建议补充更多调研信息")

        return findings

    def _evaluate_credibility(self, sources: List[Dict]) -> Dict:
        """评估信息可信度"""
        if not sources:
            return {'source_quality': 5.0, 'timeliness': 5.0, 'completeness': 5.0, 'overall': 5.0}

        # 基于来源类型评估
        type_scores = {
            'WebSearch': 7.0,
            'WeChat': 8.0,
            'XiaoHongShu': 7.5,
            'Weibo': 6.5
        }

        total_score = sum(type_scores.get(s.get('type', 'WebSearch'), 7.0) for s in sources)
        avg_score = total_score / len(sources)

        return {
            'source_quality': min(10, avg_score + 1),
            'timeliness': 9.0,  # 假设信息是最新的
            'completeness': min(10, 5 + len(sources)),
            'overall': min(10, avg_score + 0.5)
        }

    # ==================== Phase 2: 大纲设计 ====================

    def process_outline(
        self,
        research_data: Dict,
        length: str = 'medium',
        audience: str = 'general',
        on_progress: Callable[[int, str], None] = None
    ) -> Dict:
        """
        处理大纲阶段 - 根据 research-guide.md 的方法论

        注意：实际的 AI 生成由 SKILL 程序完成，此方法提供模板和结构

        Args:
            research_data: 调研数据
            length: 文章长度 (short/medium/long)
            audience: 目标读者 (tech/general/mixed)
            on_progress: 进度回调函数

        Returns:
            结构化的文章大纲
        """
        topic = research_data.get('topic', '未知主题')

        if on_progress:
            on_progress(10, "正在生成大纲模板...")

        print(f"[PhaseHandler] 生成大纲模板: {topic}")

        # 根据长度确定结构（字数与前端 app.js getWordCount 和 glm_service.py 保持一致）
        structures = {
            'short': {
                'chapter_count': 4,
                'word_count': '1500',
                'template': [
                    {'number': 0, 'title': '引言', 'description': f'为什么关注{topic[:15]}'},
                    {'number': 1, 'title': '核心概念', 'description': f'{topic[:15]}是什么'},
                    {'number': 2, 'title': '应用场景', 'description': f'{topic[:15]}怎么用'},
                    {'number': 3, 'title': '总结', 'description': '要点回顾'},
                ]
            },
            'medium': {
                'chapter_count': 6,
                'word_count': '3000',
                'template': [
                    {'number': 0, 'title': '引言', 'description': f'为什么关注{topic[:15]}'},
                    {'number': 1, 'title': '核心概念', 'description': f'{topic[:15]}是什么'},
                    {'number': 2, 'title': '技术原理', 'description': f'{topic[:15]}如何工作'},
                    {'number': 3, 'title': '应用场景', 'description': f'{topic[:15]}的实际应用'},
                    {'number': 4, 'title': '发展趋势', 'description': f'{topic[:15]}的未来'},
                    {'number': 5, 'title': '总结', 'description': '要点回顾与展望'},
                ]
            },
            'long': {
                'chapter_count': 8,
                'word_count': '8000',
                'template': [
                    {'number': 0, 'title': '引言', 'description': f'为什么关注{topic[:15]}'},
                    {'number': 1, 'title': '背景介绍', 'description': f'{topic[:15]}的发展背景'},
                    {'number': 2, 'title': '核心概念', 'description': f'{topic[:15]}是什么'},
                    {'number': 3, 'title': '技术原理', 'description': f'{topic[:15]}如何工作'},
                    {'number': 4, 'title': '应用场景', 'description': f'{topic[:15]}的实际应用'},
                    {'number': 5, 'title': '案例分析', 'description': '深度案例分析'},
                    {'number': 6, 'title': '发展趋势', 'description': f'{topic[:15]}的未来'},
                    {'number': 7, 'title': '总结', 'description': '要点回顾与展望'},
                ]
            }
        }

        structure = structures.get(length, structures['medium'])

        # 根据调研内容调整章节
        chapters = structure['template'].copy()

        # 如果调研中有特定发现，添加对应章节
        if research_data.get('challenges'):
            chapters.insert(len(chapters) - 1, {
                'number': len(chapters) - 1,
                'title': '挑战与机遇',
                'description': f'{topic[:15]}面临的挑战'
            })

        # 重新编号
        for i, ch in enumerate(chapters):
            ch['number'] = i

        # 根据目标读者确定写作风格
        audience_styles = {
            'tech': '专业技术风格，可使用术语',
            'general': '通俗易懂，大量类比',
            'mixed': '兼顾专业性和可读性'
        }

        # 根据来源确定配图风格
        sources = research_data.get('sources', [])
        has_xiaohongshu = any(s.get('type') == 'XiaoHongShu' for s in sources)
        has_weixin = any(s.get('type') == 'WeChat' for s in sources)

        if has_xiaohongshu:
            image_style = '清新活泼风格, 适合社交媒体'
        elif has_weixin:
            image_style = '专业商务风格, 简约大气'
        else:
            image_style = '科技感, 深蓝色调, 几何图形'

        outline = {
            'topic': topic,
            'chapter_count': len(chapters),
            'chapters': chapters,
            'word_count': structure['word_count'],
            'target_audience': audience,
            'writing_style': audience_styles.get(audience, audience_styles['general']),
            'image_plan': {
                'cover': {'description': f'{topic[:30]}主题封面', 'size': '1024x576'},
                'chapters': [f'{ch["title"][:10]}配图' for ch in chapters[1:]],
                'style': image_style
            },
            'based_on_research': True,
            'research_source_count': len(sources),
            'timestamp': datetime.now().isoformat()
        }

        return outline

    def process_outline_feedback(self, outline: Dict, feedback: str, feedback_history: List[str] = None) -> Dict:
        """
        处理大纲反馈 - 完整的循环优化机制
        """
        # 确保 outline 不为 None
        if outline is None:
            outline = {}

        feedback_history = feedback_history or []
        chapters = list(outline.get('chapters', []))
        changes_made = []

        # ===== 1. 删除章节 =====
        delete_patterns = [
            r'删除第?(\d+)[章节]',
            r'去掉第?(\d+)[章节]',
            r'移除第?(\d+)[章节]',
            r'不要第?(\d+)[章节]',
        ]
        for pattern in delete_patterns:
            match = re.search(pattern, feedback, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                if 0 <= num < len(chapters):
                    removed = chapters.pop(num)
                    changes_made.append(f"删除: {removed['title']}")
                break

        # ===== 2. 修改章节 =====
        modify_patterns = [
            r'(?:把|将)?第?(\d+)[章节][改换]成?["\']?([^"\'章节]+)["\']?',
            r'修改第?(\d+)[章节]为?["\']?([^"\'章节]+)["\']?',
        ]
        for pattern in modify_patterns:
            match = re.search(pattern, feedback)
            if match:
                num = int(match.group(1))
                new_title = match.group(2).strip()
                if 0 <= num < len(chapters):
                    old_title = chapters[num]['title']
                    chapters[num]['title'] = new_title
                    chapters[num]['description'] = f'关于{new_title}的内容'
                    changes_made.append(f"修改: '{old_title}' → '{new_title}'")
                break

        # ===== 3. 增加章节 =====
        add_patterns = [
            r'增加(?:关于)?["\']?([^"\'章节的]{2,20})["\']?(?:的)?(?:章节|内容)?',
            r'添加(?:关于)?["\']?([^"\'章节的]{2,20})["\']?(?:的)?(?:章节|内容)?',
            r'补充(?:关于)?["\']?([^"\'章节的]{2,20})["\']?(?:的)?(?:章节|内容)?',
            r'新增(?:关于)?["\']?([^"\'章节的]{2,20})["\']?(?:的)?(?:章节|内容)?',
        ]
        added_topic = None  # 记录已添加的主题，避免重复
        for pattern in add_patterns:
            match = re.search(pattern, feedback)
            if match:
                new_topic = match.group(1).strip()
                exists = any(new_topic[:4] in ch.get('title', '') for ch in chapters)
                if not exists:
                    chapters.append({
                        'number': len(chapters),
                        'title': new_topic,
                        'description': f'关于{new_topic}的内容'
                    })
                    changes_made.append(f"新增: {new_topic}")
                    added_topic = new_topic[:4]  # 记录关键词
                break

        # ===== 4. 特定关键词章节 =====
        # 如果已经通过通用模式添加了章节，跳过关键词匹配
        if not added_topic:
            chapter_keywords = {
                '趋势|未来|展望': ('发展趋势与展望', '未来发展方向'),
                '案例|实例': ('实践案例分析', '真实应用案例'),
                '挑战|问题': ('挑战与解决方案', '面临的挑战'),
                '对比|比较': ('技术方案对比', '主流方案对比'),
                '结论|总结': ('结论与总结', '全文要点总结'),
                '背景|介绍': ('背景介绍', '话题背景'),
                '原理|技术': ('技术原理', '核心技术'),
                '优势|优点': ('核心优势', '主要优势'),
                '风险|注意': ('风险与注意事项', '潜在风险'),
            }
            for pattern, (title, desc) in chapter_keywords.items():
                if re.search(pattern, feedback, re.IGNORECASE):
                    key_word = title[:4]
                    exists = any(key_word in ch.get('title', '') for ch in chapters)
                    if not exists:
                        chapters.append({'number': len(chapters), 'title': title, 'description': desc})
                        changes_made.append(f"新增: {title}")

        # ===== 5. 配图风格 =====
        style_keywords = {
            '单线手绘|单线|线条': '单线手绘风格, 简约线条',
            '手绘|素描': '手绘风格, 素描线条',
            '卡通|动漫': '卡通风格, 活泼色彩',
            '扁平|简约': '扁平化设计, 简约现代',
            '3d|立体': '3D立体风格, 现代感',
            '水彩|水墨': '水彩风格, 艺术感',
            '科技|科技感': '科技感, 深蓝色调',
            '复古|怀旧': '复古风格, 怀旧色调',
            '清新|淡雅': '清新淡雅风格',
            '商务|专业': '商务专业风格',
        }
        image_plan = outline.get('image_plan', {})
        current_style = image_plan.get('style', '科技感, 深蓝色调')
        for pattern, style in style_keywords.items():
            if re.search(pattern, feedback, re.IGNORECASE):
                current_style = style
                changes_made.append(f"配图风格: {style}")
                break

        # ===== 6. 字数调整 =====
        if re.search(r'短|简洁', feedback, re.IGNORECASE):
            outline['word_count'] = '1500'
            changes_made.append("字数: 1500")
        elif re.search(r'长|详细|详尽', feedback, re.IGNORECASE):
            outline['word_count'] = '8000'
            changes_made.append("字数: 8000")

        # ===== 7. 重新编号 =====
        for i, ch in enumerate(chapters):
            ch['number'] = i

        # ===== 8. 构建更新 =====
        updated_outline = {
            **outline,
            'chapter_count': len(chapters),
            'chapters': chapters,
            'image_plan': {
                **image_plan,
                'style': current_style,
                'chapters': [f'{ch["title"][:10]}配图' for ch in chapters[1:]] if len(chapters) > 1 else []
            },
            'adjusted': True,
            'adjustment_note': feedback,
            'changes_made': changes_made,
            'feedback_count': len(feedback_history) + 1,
            'timestamp': datetime.now().isoformat()
        }

        print(f"[PhaseHandler] 反馈处理: {len(changes_made)} 项修改")
        for c in changes_made:
            print(f"   • {c}")

        return updated_outline

    # ==================== Phase 3: 内容写作 ====================

    def process_draft(self, outline: Dict, research_data: Dict) -> Dict:
        """
        处理初稿写作 - 根据 writing-standards.md 的写作规范

        Args:
            outline: 文章大纲
            research_data: 调研数据

        Returns:
            初稿内容
        """
        topic = outline.get('topic', '未知主题')
        chapters = outline.get('chapters', [])
        style = outline.get('writing_style', '通俗易懂')

        # 生成初稿内容
        draft_content = f"# {topic}\n\n"

        for chapter in chapters:
            chapter_num = chapter.get('number', 0)
            chapter_title = chapter.get('title', '')
            chapter_desc = chapter.get('description', '')

            draft_content += f"## {chapter_num}. {chapter_title}\n\n"
            draft_content += f"*{chapter_desc}*\n\n"
            draft_content += f"[此处将根据调研资料撰写{chapter_title}的详细内容...]\n\n"

        draft = {
            'topic': topic,
            'content': draft_content,
            'word_count': len(draft_content),
            'chapter_count': len(chapters),
            'style': style,
            'status': 'draft',
            'timestamp': datetime.now().isoformat()
        }

        return draft

    # ==================== Phase 5: 排版输出 ====================

    def process_layout(self, draft: Dict, outline: Dict, format_type: str = 'wechat') -> Dict:
        """
        处理排版输出 - 根据 output-formats.md 的格式规范

        Args:
            draft: 初稿内容
            outline: 文章大纲
            format_type: 输出格式 (wechat/html/both)

        Returns:
            排版后的内容
        """
        topic = draft.get('topic', '未知主题')
        content = draft.get('content', '')

        # 微信公众号格式
        wechat_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{topic}</title>
</head>
<body style="max-width: 677px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <article>
        {self._markdown_to_wechat_html(content)}
    </article>
</body>
</html>
"""

        layout = {
            'topic': topic,
            'format': format_type,
            'wechat_html': wechat_html if format_type in ['wechat', 'both'] else None,
            'content_md': content,
            'timestamp': datetime.now().isoformat()
        }

        return layout

    def _markdown_to_wechat_html(self, md_content: str) -> str:
        """将 Markdown 转换为微信公众号兼容的 HTML"""
        # 简单转换
        html = md_content
        html = re.sub(r'^# (.+)$', r'<h1 style="font-size: 24px; font-weight: bold; margin: 20px 0;">\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2 style="font-size: 20px; font-weight: bold; margin: 16px 0;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'\n\n', r'</p><p style="margin: 12px 0; line-height: 1.8;">', html)
        return f'<p style="margin: 12px 0; line-height: 1.8;">{html}</p>'


# 全局实例
phase_handler = PhaseHandler()
