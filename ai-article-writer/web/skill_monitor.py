#!/usr/bin/env python3
"""
SKILL Task Monitor - 任务监控脚本
由 SKILL 程序运行，持续监控任务队列并使用真实 MCP 工具处理

使用方法：
1. 在 SKILL 对话中运行此脚本
2. 脚本会持续监控 tasks/ 目录
3. 发现新任务时，打印任务信息
4. SKILL 看到后使用真实 MCP 工具处理
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from task_queue import (
    get_pending_tasks,
    update_task,
    set_task_progress,
    complete_task,
    fail_task,
    TaskStatus
)
from shared_data import save_research_result, create_session, update_session, get_session

def monitor_tasks(interval: int = 3, max_iterations: int = 100):
    """
    监控任务队列

    Args:
        interval: 检查间隔（秒）
        max_iterations: 最大迭代次数（防止无限循环）
    """
    print("=" * 60)
    print("🤖 SKILL Task Monitor - 任务监控器")
    print("=" * 60)
    print(f"⏱️  检查间隔: {interval}秒")
    print(f"📂 任务目录: {Path(__file__).parent / 'tasks'}")
    print("=" * 60)
    print("🚀 开始监控任务队列...")
    print("   发现任务时会打印任务信息，等待 SKILL 处理")
    print("=" * 60)
    print()

    iteration = 0
    while iteration < max_iterations:
        pending = get_pending_tasks()

        if pending:
            for task in pending:
                task_id = task['task_id']
                task_type = task['task_type']
                params = task.get('params', {})
                session_id = task.get('session_id', '')

                # 打印任务信息，让 SKILL 看到并处理
                print("\n" + "!" * 60)
                print("🔔 新任务到达！")
                print(f"   任务ID: {task_id}")
                print(f"   类型: {task_type}")
                print(f"   会话ID: {session_id}")
                print(f"   参数: {json.dumps(params, ensure_ascii=False)}")
                print("!" * 60)
                print("\n⏳ 等待 SKILL 处理...")
                print("   处理完成后请运行: python3 skill_monitor.py --mark-complete <task_id> <result_file>")
                print()

                # 标记为处理中，防止重复
                update_task(task_id, status=TaskStatus.PROCESSING.value)
                set_task_progress(task_id, 5, "SKILL 已接管任务...")

        time.sleep(interval)
        iteration += 1

    print("\n⏹️ 监控结束")

def mark_complete(task_id: str, result_json: str):
    """标记任务完成"""
    try:
        result = json.loads(result_json)
        complete_task(task_id, result)
        print(f"✅ 任务已完成: {task_id}")
    except Exception as e:
        print(f"❌ 标记完成失败: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=3, help='检查间隔')
    parser.add_argument('--max', type=int, default=100, help='最大迭代次数')
    parser.add_argument('--mark-complete', nargs=2, metavar=('TASK_ID', 'RESULT'), help='标记任务完成')

    args = parser.parse_args()

    if args.mark_complete:
        mark_complete(args.mark_complete[0], args.mark_complete[1])
    else:
        monitor_tasks(args.interval, args.max)
