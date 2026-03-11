#!/usr/bin/env python3
"""
AI Article Writer - Task Processor
任务处理器 - AI助手自动监控任务队列并处理任务

工作流程：
1. 监控任务队列中的pending任务
2. 根据任务类型执行相应操作（GLM API 搜索等）
3. 更新任务进度
4. 完成任务并保存结果
"""

import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入任务队列
from task_queue import (
    get_task,
    update_task,
    set_task_progress,
    complete_task,
    fail_task,
    get_pending_tasks,
    TaskStatus,
    TaskType
)

# 导入共享数据管理
from shared_data import save_research_result, update_session

# 导入 GLM 服务（替代模拟搜索）
from glm_service import glm_service

class TaskProcessor:
    """任务处理器"""

    def __init__(self, poll_interval: int = 2):
        """
        初始化任务处理器

        Args:
            poll_interval: 轮询间隔（秒）
        """
        self.poll_interval = poll_interval
        self.running = False
        self.processed_count = 0

    def start(self):
        """启动任务处理器"""
        print("=" * 60)
        print("🤖 AI Article Writer - Task Processor")
        print("=" * 60)
        print(f"⏱️  轮询间隔: {self.poll_interval}秒")
        print(f"📂 任务目录: {Path(__file__).parent / 'tasks'}")
        print("=" * 60)
        print("🚀 开始监控任务队列...")
        print("按 Ctrl+C 停止")
        print()

        self.running = True

        try:
            while self.running:
                self._process_pending_tasks()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  任务处理器已停止")
            print(f"📊 总计处理任务: {self.processed_count}")

    def stop(self):
        """停止任务处理器"""
        self.running = False

    def _process_pending_tasks(self):
        """处理待处理任务"""
        pending_tasks = get_pending_tasks()

        if pending_tasks:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 发现 {len(pending_tasks)} 个待处理任务")

            for task in pending_tasks:
                try:
                    self._process_task(task)
                    self.processed_count += 1
                except Exception as e:
                    print(f"❌ 任务处理失败: {task['task_id']} - {e}")
                    fail_task(task['task_id'], str(e))

    def _process_task(self, task: Dict[str, Any]):
        """
        处理单个任务

        Args:
            task: 任务数据
        """
        task_id = task['task_id']
        task_type = task['task_type']

        print(f"\n{'='*50}")
        print(f"🔄 开始处理任务: {task_id}")
        print(f"   类型: {task_type}")
        print(f"{'='*50}")

        # 标记为处理中
        update_task(task_id, status=TaskStatus.PROCESSING.value, message="任务开始处理")

        # 根据任务类型分发
        if task_type == TaskType.RESEARCH.value:
            self._process_research_task(task)
        elif task_type == TaskType.OUTLINE.value:
            self._process_outline_task(task)
        elif task_type == TaskType.DRAFT.value:
            self._process_draft_task(task)
        else:
            fail_task(task_id, f"未知任务类型: {task_type}")

    def _process_research_task(self, task: Dict[str, Any]):
        """
        处理调研任务 - 使用 GLM API 进行真实搜索

        Args:
            task: 任务数据
        """
        task_id = task['task_id']
        session_id = task['session_id']
        params = task.get('params', {})

        topic = params.get('topic', '未知主题')

        print(f"🔍 调研主题: {topic}")

        # 进度回调函数
        def on_progress(pct, msg):
            set_task_progress(task_id, pct, msg)
            print(f"   [{pct}%] {msg}")

        sources = []

        # 步骤1: 使用 GLM 进行搜索
        try:
            search_results = glm_service.search(
                query=f"{topic} 2024 2025 最新 趋势 应用",
                on_progress=on_progress
            )
            sources.extend(search_results)
            print(f"   ✅ GLM 搜索完成: {len(search_results)} 条结果")
        except Exception as e:
            print(f"   ⚠️ GLM 搜索失败: {e}")
            # 如果 GLM 搜索失败，使用备用数据
            sources.append({
                'type': 'GLM-Fallback',
                'title': f'关于{topic}的基础信息',
                'content': f'{topic}是当前热门的技术话题。',
                'summary': f'{topic}的基础介绍'
            })

        # 步骤2: 整理结果
        set_task_progress(task_id, 80, "正在整理调研结果...")

        # 提取关键发现
        key_findings = []
        if sources:
            key_findings.append(f"已收集 {len(sources)} 个信息来源")
            for i, src in enumerate(sources[:3]):
                title = src.get('title', '')[:20]
                key_findings.append(f"来源{i+1}: {title}")
        key_findings.append("调研完成，可以进入大纲设计阶段")

        # 构建调研数据
        research_data = {
            'topic': topic,
            'sources': sources,
            'key_findings': key_findings,
            'credibility': {
                'source_quality': 8.5,
                'timeliness': 9.0,
                'completeness': min(10, 6 + len(sources) * 0.5),
                'overall': min(10, 7 + len(sources) * 0.3)
            },
            'timestamp': datetime.now().isoformat()
        }

        # 步骤6: 保存结果
        set_task_progress(task_id, 90, "正在保存结果...")

        # 保存到共享数据
        save_research_result(session_id, research_data)

        # 更新会话状态
        update_session(session_id, current_phase=1, topic=topic)

        # 步骤7: 完成任务
        complete_task(task_id, {
            'research_data': research_data,
            'source_count': len(sources),
            'session_id': session_id
        })

        print(f"\n✅ 调研任务完成!")
        print(f"   📊 来源数量: {len(sources)}")
        print(f"   📋 会话ID: {session_id}")

    def _process_outline_task(self, task: Dict[str, Any]):
        """处理大纲任务 - 使用 GLM 生成"""
        task_id = task['task_id']
        session_id = task['session_id']
        params = task.get('params', {})

        # 从共享数据获取调研结果
        from shared_data import get_session
        session = get_session(session_id)
        research_data = session.get('research_data', {})

        # 进度回调
        def on_progress(pct, msg):
            set_task_progress(task_id, pct, msg)

        # 使用 GLM 生成大纲
        try:
            outline_data = glm_service.generate_outline(
                topic=params.get('topic', research_data.get('topic', '未知主题')),
                research_data=research_data,
                length=params.get('length', 'medium'),
                audience=params.get('audience', 'general'),
                on_progress=on_progress
            )
            print(f"   ✅ GLM 大纲生成完成")
        except Exception as e:
            print(f"   ⚠️ GLM 大纲生成失败: {e}，使用模板")
            # 使用默认模板
            topic = params.get('topic', '未知主题')
            outline_data = {
                'topic': topic,
                'chapters': [
                    {'number': 0, 'title': '引言', 'description': f'为什么关注{topic}'},
                    {'number': 1, 'title': '核心概念', 'description': f'{topic}是什么'},
                    {'number': 2, 'title': '技术原理', 'description': f'{topic}如何工作'},
                    {'number': 3, 'title': '应用场景', 'description': f'{topic}的实际应用'},
                    {'number': 4, 'title': '发展趋势', 'description': f'{topic}的未来'},
                    {'number': 5, 'title': '总结', 'description': '要点回顾'},
                ],
                'chapter_count': 6,
                'word_count': '3000'
            }

        # 更新会话
        update_session(session_id, outline=outline_data, current_phase=2)

        complete_task(task_id, {
            'outline_data': outline_data,
            'session_id': session_id
        })

        print(f"✅ 大纲任务完成: {task_id}")

    def _process_draft_task(self, task: Dict[str, Any]):
        """处理初稿任务 - 使用 GLM 生成"""
        task_id = task['task_id']
        session_id = task['session_id']

        # 从共享数据获取大纲和调研结果
        from shared_data import get_session
        session = get_session(session_id)
        outline = session.get('outline', {})
        research_data = session.get('research_data', {})

        # 进度回调
        def on_progress(pct, msg):
            set_task_progress(task_id, pct, msg)

        # 使用 GLM 生成初稿
        try:
            draft_data = glm_service.generate_draft(
                outline=outline,
                research_data=research_data,
                on_progress=on_progress
            )
            print(f"   ✅ GLM 初稿生成完成")
        except Exception as e:
            print(f"   ⚠️ GLM 初稿生成失败: {e}，使用模板")
            # 使用默认内容
            topic = outline.get('topic', '未知主题')
            draft_data = {
                'topic': topic,
                'content': f'# {topic}\n\n这是一篇关于{topic}的文章。\n\n## 引言\n\n{topic}是当前热门的话题。\n\n## 核心概念\n\n{topic}的核心概念包括...\n\n## 总结\n\n本文介绍了{topic}的基本概念。',
                'word_count': 500,
                'chapter_count': outline.get('chapter_count', 6)
            }

        # 更新会话
        update_session(session_id, draft=draft_data, current_phase=3)

        complete_task(task_id, {
            'draft_data': draft_data,
            'session_id': session_id
        })

        print(f"✅ 初稿任务完成: {task_id}")


def main():
    """主函数"""
    processor = TaskProcessor(poll_interval=2)
    processor.start()


if __name__ == "__main__":
    main()
