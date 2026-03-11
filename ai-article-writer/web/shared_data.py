#!/usr/bin/env python3
"""
AI Article Writer - Shared Data Manager
共享数据管理器，用于AI助手和前端之间的数据交换
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 共享数据目录
SHARED_DIR = Path(__file__).parent / "shared"
SHARED_DIR.mkdir(exist_ok=True)

def get_session_file(session_id):
    """获取会话数据文件路径"""
    return SHARED_DIR / f"session_{session_id}.json"

def save_research_result(session_id, research_data):
    """
    保存调研结果（由AI助手调用）

    Args:
        session_id: 会话ID
        research_data: 调研数据，包含sources等
    """
    file_path = get_session_file(session_id)

    # 读取现有数据
    data = {}
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

    # 更新调研数据
    data['research_data'] = research_data
    data['last_updated'] = datetime.now().isoformat()

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 调研结果已保存: {file_path}")
    return True

def get_research_result(session_id):
    """
    获取调研结果（由前端API调用）

    Args:
        session_id: 会话ID

    Returns:
        调研数据或None
    """
    file_path = get_session_file(session_id)

    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get('research_data')

def create_session(session_id, topic, length='medium', audience='general'):
    """创建新会话"""
    file_path = get_session_file(session_id)

    data = {
        'session_id': session_id,
        'topic': topic,
        'length': length,
        'audience': audience,
        'current_phase': 0,
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 会话已创建: {file_path}")
    return True

def update_session(session_id, **kwargs):
    """更新会话数据"""
    file_path = get_session_file(session_id)

    if not file_path.exists():
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data.update(kwargs)
    data['last_updated'] = datetime.now().isoformat()

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True

def get_session(session_id):
    """获取完整会话数据"""
    file_path = get_session_file(session_id)

    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_sessions():
    """列出所有会话"""
    sessions = []
    for file in SHARED_DIR.glob("session_*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sessions.append({
                'session_id': data.get('session_id'),
                'topic': data.get('topic'),
                'created_at': data.get('created_at'),
                'current_phase': data.get('current_phase', 0)
            })
    return sorted(sessions, key=lambda x: x['created_at'], reverse=True)


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("📋 共享数据管理器测试")
    print("=" * 60)

    # 创建测试会话
    test_id = "test_" + datetime.now().strftime('%Y%m%d_%H%M%S')
    create_session(test_id, "测试主题", "medium", "general")

    # 保存调研结果
    test_research = {
        'topic': '测试主题',
        'sources': [
            {'type': 'WebSearch', 'title': '测试文章1', 'url': 'https://example.com/1'},
            {'type': 'WeChat', 'title': '微信文章1', 'source': '测试公众号'}
        ]
    }
    save_research_result(test_id, test_research)

    # 读取调研结果
    result = get_research_result(test_id)
    print(f"\n📖 读取到的调研结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n✅ 测试完成")
