#!/usr/bin/env python3
"""
AI Article Writer - Task Queue System
任务队列系统，用于前端和AI助手之间的通信

工作流程：
1. 前端提交任务 → 创建任务文件（status: pending）
2. AI助手监控任务 → 执行任务 → 更新状态（status: processing → completed）
3. 前端轮询任务状态 → 获取结果
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum

# 任务目录
TASK_DIR = Path(__file__).parent / "tasks"
TASK_DIR.mkdir(exist_ok=True)

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"        # 等待处理
    PROCESSING = "processing"  # 正在处理
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败

class TaskType(str, Enum):
    """任务类型"""
    RESEARCH = "research"      # 深度调研
    OUTLINE = "outline"        # 大纲设计
    DRAFT = "draft"            # 内容写作
    IMAGES = "images"          # 配图生成
    LAYOUT = "layout"          # 排版输出

def get_task_file(task_id: str) -> Path:
    """获取任务文件路径"""
    return TASK_DIR / f"{task_id}.json"

def create_task(task_type: TaskType, session_id: str, **params) -> str:
    """
    创建新任务

    Args:
        task_type: 任务类型
        session_id: 会话ID
        **params: 任务参数

    Returns:
        task_id: 任务ID
    """
    task_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    task_data = {
        "task_id": task_id,
        "task_type": task_type.value if isinstance(task_type, TaskType) else task_type,
        "session_id": session_id,
        "status": TaskStatus.PENDING.value,
        "params": params,
        "result": None,
        "error": None,
        "progress": 0,  # 0-100
        "message": "任务已创建，等待处理...",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None
    }

    task_file = get_task_file(task_id)
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 任务已创建: {task_id} (类型: {task_type})")
    return task_id

def get_task(task_id: str) -> dict:
    """
    获取任务信息

    Args:
        task_id: 任务ID

    Returns:
        任务数据或None
    """
    task_file = get_task_file(task_id)
    if not task_file.exists():
        return None

    with open(task_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_task(task_id: str, **updates) -> bool:
    """
    更新任务状态

    Args:
        task_id: 任务ID
        **updates: 要更新的字段

    Returns:
        是否成功
    """
    task_data = get_task(task_id)
    if not task_data:
        return False

    task_data.update(updates)
    task_data["updated_at"] = datetime.now().isoformat()

    # 自动设置时间戳
    if updates.get("status") == TaskStatus.PROCESSING.value:
        task_data["started_at"] = datetime.now().isoformat()
    elif updates.get("status") in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
        task_data["completed_at"] = datetime.now().isoformat()

    task_file = get_task_file(task_id)
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)

    return True

def set_task_progress(task_id: str, progress: int, message: str = None):
    """
    设置任务进度

    Args:
        task_id: 任务ID
        progress: 进度 (0-100)
        message: 进度消息
    """
    updates = {"progress": min(100, max(0, progress))}
    if message:
        updates["message"] = message
    update_task(task_id, **updates)

def complete_task(task_id: str, result: dict):
    """
    标记任务完成

    Args:
        task_id: 任务ID
        result: 任务结果
    """
    update_task(
        task_id,
        status=TaskStatus.COMPLETED.value,
        result=result,
        progress=100,
        message="任务完成"
    )
    print(f"✅ 任务完成: {task_id}")

def fail_task(task_id: str, error: str):
    """
    标记任务失败

    Args:
        task_id: 任务ID
        error: 错误信息
    """
    update_task(
        task_id,
        status=TaskStatus.FAILED.value,
        error=error,
        message=f"任务失败: {error}"
    )
    print(f"❌ 任务失败: {task_id} - {error}")

def get_pending_tasks() -> list:
    """
    获取所有待处理的任务

    Returns:
        待处理任务列表
    """
    pending = []
    for task_file in TASK_DIR.glob("*.json"):
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
            if task.get("status") == TaskStatus.PENDING.value:
                pending.append(task)

    # 按创建时间排序
    return sorted(pending, key=lambda x: x.get("created_at", ""))

def list_recent_tasks(limit: int = 10) -> list:
    """
    列出最近的任务

    Args:
        limit: 返回数量限制

    Returns:
        任务列表
    """
    tasks = []
    for task_file in TASK_DIR.glob("*.json"):
        with open(task_file, 'r', encoding='utf-8') as f:
            tasks.append(json.load(f))

    # 按创建时间倒序
    return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("📋 任务队列系统测试")
    print("=" * 60)

    # 创建测试任务
    task_id = create_task(
        task_type=TaskType.RESEARCH,
        session_id="test_session",
        topic="测试主题",
        include_xiaohongshu=True,
        include_weixin=True
    )

    # 获取任务
    task = get_task(task_id)
    print(f"\n📄 任务信息:")
    print(f"   ID: {task['task_id']}")
    print(f"   类型: {task['task_type']}")
    print(f"   状态: {task['status']}")
    print(f"   消息: {task['message']}")

    # 更新进度
    set_task_progress(task_id, 30, "正在搜索小红书...")
    task = get_task(task_id)
    print(f"\n📊 进度更新: {task['progress']}% - {task['message']}")

    # 完成任务
    complete_task(task_id, {"sources": ["source1", "source2"]})
    task = get_task(task_id)
    print(f"\n✅ 最终状态: {task['status']}")

    print("\n" + "=" * 60)
    print("测试完成")
