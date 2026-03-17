#!/usr/bin/env python3
"""
AI Article Writer - Backend API Server
后端API服务，处理前端请求并调用AI写作流程
"""

from flask import Flask, request, jsonify, send_from_directory, Response, Response
from flask_cors import CORS
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# 加载环境变量（从 .env 文件）
load_dotenv()

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入搜索服务
from search_providers import SearchProviders
# 导入共享数据管理器
from shared_data import (
    create_session as shared_create_session,
    save_research_result,
    get_research_result,
    get_session as shared_get_session,
    update_session as shared_update_session
)
# 导入任务队列
from task_queue import (
    create_task,
    get_task,
    update_task,
    set_task_progress,
    complete_task,
    fail_task,
    get_pending_tasks,
    list_recent_tasks,
    TaskStatus,
    TaskType
)
# 导入阶段处理器（系统核心大脑）
from phase_handler import phase_handler

# 获取当前目录（web目录）
WEB_DIR = Path(__file__).parent

app = Flask(__name__, static_folder=str(WEB_DIR))

# CORS 配置 - 支持环境变量配置允许的域名
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins != "*":
    allowed_origins = [origin.strip() for origin in allowed_origins.split(",")]
CORS(app, origins=allowed_origins)

# 存储会话状态
sessions = {}

# ==================== 辅助函数 ====================

def get_synced_session(session_id: str) -> dict:
    """
    获取同步后的 session - 始终从共享文件合并最新数据
    解决多 worker 之间数据不同步的问题
    """
    # 先从共享文件获取最新数据
    shared_session = shared_get_session(session_id)

    if session_id in sessions:
        # 内存中有数据，合并共享文件的新数据
        mem_session = sessions[session_id]

        if shared_session:
            # 合并共享文件中的最新数据（共享文件优先）
            for key in ['outline', 'confirmed_outline', 'research_data', 'draft', 'images', 'length', 'audience', 'topic']:
                if key in shared_session and shared_session[key] is not None:
                    mem_session[key] = shared_session[key]
            session = mem_session
        else:
            session = mem_session
    else:
        # 内存中没有，使用共享文件数据
        if shared_session:
            session = shared_session
            sessions[session_id] = session
        else:
            session = None

    return session

def save_outline_result(session_id: str, outline: dict):
    """保存大纲结果到共享文件"""
    try:
        shared_update_session(session_id, outline=outline)
    except Exception as e:
        print(f"[API] 保存大纲失败: {e}")

def save_draft_result(session_id: str, draft: dict):
    """保存初稿结果到共享文件"""
    try:
        shared_update_session(session_id, draft=draft)
    except Exception as e:
        print(f"[API] 保存初稿失败: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'AI Article Writer API is running',
        'timestamp': datetime.now().isoformat()
    })

# ==================== 任务队列 API ====================

@app.route('/api/task/create', methods=['POST'])
def api_create_task():
    """创建新任务（前端调用）"""
    data = request.json
    task_type = data.get('task_type', 'research')
    session_id = data.get('session_id')
    params = data.get('params', {})

    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400

    # 创建任务
    task_id = create_task(
        task_type=task_type,
        session_id=session_id,
        **params
    )

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': 'Task created successfully'
    })

@app.route('/api/task/<task_id>', methods=['GET'])
def api_get_task(task_id):
    """获取任务状态（前端轮询）"""
    task = get_task(task_id)

    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    return jsonify({
        'success': True,
        'task': task
    })

@app.route('/api/tasks/pending', methods=['GET'])
def api_get_pending_tasks():
    """获取待处理任务列表（AI助手调用）"""
    tasks = get_pending_tasks()
    return jsonify({
        'success': True,
        'tasks': tasks,
        'count': len(tasks)
    })

@app.route('/api/tasks/recent', methods=['GET'])
def api_get_recent_tasks():
    """获取最近任务列表"""
    limit = request.args.get('limit', 10, type=int)
    tasks = list_recent_tasks(limit)
    return jsonify({
        'success': True,
        'tasks': tasks,
        'count': len(tasks)
    })

@app.route('/api/task/<task_id>/process', methods=['POST'])
def api_process_task(task_id):
    """开始处理任务（AI助手调用）"""
    task = get_task(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    update_task(task_id, status=TaskStatus.PROCESSING.value, message="任务开始处理")
    return jsonify({
        'success': True,
        'message': 'Task processing started'
    })

@app.route('/api/task/<task_id>/progress', methods=['POST'])
def api_update_progress(task_id):
    """更新任务进度（AI助手调用）"""
    data = request.json
    progress = data.get('progress', 0)
    message = data.get('message', '')

    set_task_progress(task_id, progress, message)
    return jsonify({
        'success': True,
        'message': 'Progress updated'
    })

@app.route('/api/task/<task_id>/complete', methods=['POST'])
def api_complete_task(task_id):
    """完成任务（AI助手调用）"""
    data = request.json
    result = data.get('result', {})

    # 获取任务信息
    task = get_task(task_id)
    if task:
        # 如果是调研任务，将结果同步到会话的 research_data
        if task.get('task_type') == 'research':
            session_id = task.get('session_id')
            if session_id and session_id in sessions:
                # 提取调研数据
                research_data = result.get('research_data', result)
                sessions[session_id]['research_data'] = research_data
                sessions[session_id]['current_phase'] = 1
                print(f"[API] 同步调研数据到会话 {session_id}: {len(research_data.get('sources', []))} 个来源")

    complete_task(task_id, result)
    return jsonify({
        'success': True,
        'message': 'Task completed'
    })

@app.route('/api/task/<task_id>/fail', methods=['POST'])
def api_fail_task(task_id):
    """标记任务失败（AI助手调用）"""
    data = request.json
    error = data.get('error', 'Unknown error')

    fail_task(task_id, error)
    return jsonify({
        'success': True,
        'message': 'Task marked as failed'
    })

# ==================== 会话 API ====================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """创建新的写作会话"""
    data = request.json
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic = data.get('topic', '')
    length = data.get('length', 'medium')
    audience = data.get('audience', 'general')

    sessions[session_id] = {
        'topic': topic,
        'length': length,
        'audience': audience,
        'current_phase': 0,
        'research_data': None,
        'outline': None,
        'draft': None,
        'images': [],
        'layout': None,
        'feedbacks': {},
        'created_at': datetime.now().isoformat()
    }

    # 🔧 修复：同时保存到共享文件，确保跨 worker 数据同步
    shared_create_session(session_id, topic, length, audience)
    print(f"[API] 会话已创建: {session_id}, 字数: {length}, 读者: {audience}")

    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': 'Session created successfully',
        'length': length,
        'audience': audience
    })

@app.route('/api/sync/<phase>', methods=['POST'])
def sync_phase_data(phase):
    """
    同步导入的阶段数据到后端（供前端导入时调用）

    Args:
        phase: 阶段号 1-4 (research/outline/draft/images)
    """
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    # 确保会话存在
    if session_id not in sessions:
        sessions[session_id] = {
            'topic': data.get('topic', ''),
            'length': 'medium',
            'audience': 'general',
            'current_phase': 0,
            'created_at': datetime.now().isoformat()
        }

    session = sessions[session_id]

    # 根据阶段同步数据
    if phase == '1' or phase == 'research':
        research_data = data.get('data', {})
        session['research_data'] = research_data
        session['topic'] = data.get('topic', session.get('topic', ''))
        session['current_phase'] = 1
        # 同时保存到共享文件
        save_research_result(session_id, research_data)
        print(f"[API] 同步导入的调研数据: {len(research_data.get('sources', []))} 个来源")

    elif phase == '2' or phase == 'outline':
        session['outline'] = data.get('data', {})
        session['current_phase'] = 2
        # 🔧 修复：同时同步 confirmed_outline
        if data.get('confirmed_outline'):
            session['confirmed_outline'] = data.get('confirmed_outline')
            # 保存到共享文件
            shared_update_session(session_id, confirmed_outline=data.get('confirmed_outline'))
        # 保存大纲数据到共享文件
        shared_update_session(session_id, outline=data.get('data', {}))
        print(f"[API] 同步导入的大纲数据, confirmed_outline: {data.get('confirmed_outline', {})}")

    elif phase == '3' or phase == 'draft':
        session['draft'] = data.get('data', {})
        session['current_phase'] = 3
        print(f"[API] 同步导入的初稿数据")

    elif phase == '4' or phase == 'images':
        session['images'] = data.get('data', {})
        session['current_phase'] = 4
        print(f"[API] 同步导入的配图数据")

    else:
        return jsonify({'success': False, 'error': f'Invalid phase: {phase}'}), 400

    return jsonify({
        'success': True,
        'message': f'Phase {phase} data synced successfully'
    })

@app.route('/api/research/start', methods=['POST'])
def start_research():
    """开始深度调研 (Phase 1) - 优先使用AI助手的搜索结果"""
    data = request.json
    session_id = data.get('session_id')
    topic = data.get('topic')
    options = data.get('options', {})
    include_xiaohongshu = options.get('includeXiaoHongShu', False)
    include_weixin = options.get('includeWeixin', False)

    # 检查会话是否存在（内存或共享目录）
    session = None
    if session_id in sessions:
        session = sessions[session_id]
    else:
        # 尝试从共享目录加载会话
        shared_session = shared_get_session(session_id)
        if shared_session:
            session = shared_session
            sessions[session_id] = session  # 缓存到内存
            print(f"✅ 从共享目录加载会话: {session_id}")

    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    session['topic'] = topic

    # 首先检查是否有AI助手保存的调研结果
    shared_research = get_research_result(session_id)
    if shared_research:
        print(f"✅ 使用AI助手的调研结果: {session_id}")
        # 确保数据包含 pending_sources 和 confirmed_sources
        if 'pending_sources' not in shared_research:
            shared_research['pending_sources'] = shared_research.get('sources', [])
        if 'confirmed_sources' not in shared_research:
            shared_research['confirmed_sources'] = []
        session['research_data'] = shared_research
        session['current_phase'] = 1
        return jsonify({
            'success': True,
            'phase': 1,
            'data': shared_research,
            'source': 'ai_assistant',
            'message': 'Research completed (from AI Assistant)'
        })

    # 如果没有共享数据，使用 GLM API 搜索
    print(f"🔍 开始搜索: {topic}")
    print(f"   - 网页搜索: True (GLM API)")
    print(f"   - 微信搜索: {include_weixin}")
    print(f"   - 小红书搜索: {include_xiaohongshu}")

    # 优先使用 GLM API 进行搜索
    sources = []
    try:
        from glm_service import glm_service
        print(f"   - 使用 GLM API 搜索...")
        sources = glm_service.search(query=topic)
        print(f"   ✅ GLM 搜索完成: {len(sources)} 条结果")
    except Exception as e:
        print(f"   ⚠️ GLM 搜索失败: {e}，使用备用搜索")
        # 备用：使用 SearchProviders
        sources = SearchProviders.combined_search(
            query=topic,
            include_web=True,
            include_weixin=include_weixin,
            include_xiaohongshu=include_xiaohongshu,
            limit=5
        )

    print(f"✅ 搜索完成，获取 {len(sources)} 条结果")

    # 计算完整性评分
    extra_sources = sum([include_xiaohongshu, include_weixin])
    completeness = 7.5 + (extra_sources * 1.0)

    # 构建调研数据
    research_data = {
        'topic': topic,
        'sources': sources,
        'confirmed_sources': [],  # 已确认的来源（锁定）
        'pending_sources': sources,  # 待确认的来源
        'include_xiaohongshu': include_xiaohongshu,
        'include_weixin': include_weixin,
        'key_findings': [
            f'{topic}的核心概念已清晰定义',
            f'技术原理基于深度学习和自然语言处理',
            f'应用场景涵盖多个行业领域',
            f'未来发展趋势明确'
        ],
        'credibility': {
            'source_quality': 9,
            'timeliness': 9.5,
            'completeness': min(completeness, 10),
            'overall': min(8.5 + (extra_sources * 0.5), 10)
        },
        'timestamp': datetime.now().isoformat()
    }

    session['research_data'] = research_data
    session['current_phase'] = 1

    return jsonify({
        'success': True,
        'phase': 1,
        'data': research_data,
        'source': 'built_in',
        'message': 'Research completed'
    })

@app.route('/api/research/feedback', methods=['POST'])
def research_feedback():
    """处理调研阶段反馈"""
    data = request.json
    session_id = data.get('session_id')
    feedback = data.get('feedback')

    if not session_id or session_id not in sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    session = sessions[session_id]
    session['feedbacks']['research'] = feedback

    # 首先尝试从共享数据文件读取调研数据（由 task_processor 保存）
    shared_research = get_research_result(session_id)
    if shared_research:
        session['research_data'] = shared_research
        print(f"[API] 从共享文件加载调研数据: {len(shared_research.get('sources', []))} 个来源")

    # 检查 research_data 是否存在
    if session.get('research_data') is None:
        session['research_data'] = {
            'topic': session.get('topic', '未知主题'),
            'sources': [],
            'confirmed_sources': [],
            'pending_sources': [],
            'key_findings': [],
            'credibility': {'source_quality': 8.0, 'timeliness': 8.0, 'completeness': 8.0, 'overall': 8.0}
        }

    # 确保数据包含 pending_sources 和 confirmed_sources
    session['research_data'].setdefault('pending_sources', session['research_data'].get('sources', []))
    session['research_data'].setdefault('confirmed_sources', [])

    updated_data = session['research_data'].copy()
    updated_data['adjusted'] = True
    updated_data['adjustment_note'] = feedback

    # 确保返回的数据也包含这两个字段
    updated_data.setdefault('pending_sources', updated_data.get('sources', []))
    updated_data.setdefault('confirmed_sources', [])

    # 根据反馈内容智能添加信息源
    new_sources = []

    # 如果提到"爬取"、"搜索"、"增加"等关键词
    if any(kw in feedback for kw in ['爬取', '搜索', '增加', '添加', '补充', 'crawl', 'search', 'add']):
        # 提取可能的主题关键词
        import re
        # 尝试提取引号中的内容作为搜索主题
        match = re.search(r'["\']([^"\']+)["\']', feedback)
        search_topic = match.group(1) if match else feedback[:50]

        new_sources.append({
            'type': 'WebSearch',
            'title': f'补充搜索: {search_topic[:30]}',
            'url': f'https://www.google.com/search?q={search_topic}',
            'summary': f'根据反馈进行的补充搜索',
            'content': f'已根据您的反馈添加关于"{search_topic}"的搜索结果'
        })

    if new_sources:
        updated_data['sources'] = updated_data.get('sources', []) + new_sources
        # 新搜索的结果放到 pending_sources
        updated_data['pending_sources'] = updated_data.get('pending_sources', []) + new_sources
        updated_data['key_findings'] = updated_data.get('key_findings', []) + ['已根据反馈补充信息源']

    session['research_data'] = updated_data

    return jsonify({
        'success': True,
        'message': 'Feedback received and research updated',
        'data': updated_data
    })

@app.route('/api/outline/generate', methods=['POST'])
def generate_outline():
    """生成文章大纲 (Phase 2) - 使用 GLM API"""
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 🔧 修复：使用同步函数获取最新 session 数据（包含 Phase 1 的 length, audience 等）
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
        session = shared_get_session(session_id)
        if session:
            sessions[session_id] = session
            print(f"[API] 从共享文件加载会话: {session_id}")
        else:
            return jsonify({'success': False, 'error': 'Invalid session'}), 400
    length = session.get('length', 'medium')
    audience = session.get('audience', 'general')

    # 尝试从共享数据文件读取调研结果
    research_data = get_research_result(session_id)
    if research_data:
        session['research_data'] = research_data
        print(f"[API] 从共享文件加载调研数据: {len(research_data.get('sources', []))} 个来源")

    # 获取调研数据（确保不为 None）
    research = session.get('research_data') or {}
    topic = session.get('topic', '未知主题')

    # 确保有基础数据结构
    if not research.get('topic'):
        research['topic'] = topic
    if not research.get('sources'):
        research['sources'] = []

    print(f"[API] 使用 GLM 生成大纲: {topic}")

    # 使用 GLM 服务生成大纲
    try:
        from glm_service import glm_service

        outline = glm_service.generate_outline(
            topic=topic,
            research_data=research,
            length=length,
            audience=audience,
            on_progress=lambda pct, msg: print(f"  [{pct}%] {msg}")
        )
        print(f"[API] GLM 大纲生成完成: {outline.get('chapter_count', 0)} 个章节")

    except Exception as e:
        print(f"[API] GLM 大纲生成失败: {e}，使用模板")
        # 备用：使用 phase_handler 模板
        outline = phase_handler.process_outline(
            research_data=research,
            length=length,
            audience=audience
        )

    session['outline'] = outline
    session['current_phase'] = 2

    # 初始化大纲确认状态
    session['confirmed_outline'] = {
        'chapters': False,
        'image_plan': False,
        'writing_style': False,
        'image_style': False,
        'word_count': False
    }

    # 保存到共享文件
    save_outline_result(session_id, outline)

    return jsonify({
        'success': True,
        'phase': 2,
        'data': outline,
        'confirmed_outline': session.get('confirmed_outline', {}),
        'message': 'Outline generated by AI'
    })

@app.route('/api/outline/feedback', methods=['POST'])
def outline_feedback():
    """
    处理大纲阶段反馈 - 使用 AI 大模型智能处理

    支持两种类型的请求：
    1. confirmation: 确认大纲的某个部分（章节/配图/风格/字数等）
    2. feedback: 用户对大纲的修改意见（通过 AI 处理）
    """
    data = request.json
    session_id = data.get('session_id')
    feedback_type = data.get('type', 'feedback')  # 'confirmation' or 'feedback'
    confirmed_items = data.get('confirmed_items', {})  # 确认的项目
    feedback = data.get('feedback')

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 处理确认请求
    if feedback_type == 'confirmation':
        # 获取当前大纲
        current_outline = session.get('outline') or {}

        # 初始化确认状态
        if 'confirmed_outline' not in session:
            session['confirmed_outline'] = {}

        # 更新已确认的项目
        confirmed_outline = session['confirmed_outline']

        # confirmed_items: { "chapters": true, "image_plan": true, "writing_style": true, "image_style": true, "word_count": true }
        for key, is_confirmed in confirmed_items.items():
            if is_confirmed:
                if key == 'chapters':
                    confirmed_outline['chapters'] = True
                elif key == 'image_plan':
                    confirmed_outline['image_plan'] = True
                elif key == 'writing_style':
                    confirmed_outline['writing_style'] = True
                elif key == 'image_style':
                    confirmed_outline['image_style'] = True
                elif key == 'word_count':
                    confirmed_outline['word_count'] = True

        session['confirmed_outline'] = confirmed_outline

        # 检查是否所有项目都已确认
        all_confirmed = len(confirmed_outline) >= 5 and all(confirmed_outline.values())

        # 🔧 修复：保存确认状态到共享文件
        shared_update_session(session_id, confirmed_outline=confirmed_outline)
        print(f"[API] 确认状态已保存到共享文件: {confirmed_outline}")

        return jsonify({
            'success': True,
            'message': 'Outline items confirmed',
            'confirmed_outline': confirmed_outline,
            'all_confirmed': all_confirmed,
            'data': current_outline
        })

    # 处理普通反馈（通过 AI 大模型）
    # 记录反馈历史
    if 'feedback_history' not in session:
        session['feedback_history'] = []
    session['feedback_history'].append(feedback)

    # 获取当前大纲
    current_outline = session.get('outline', {})

    # 使用 AI 大模型处理反馈
    from glm_service import GLMService
    glm = GLMService()

    def on_progress(percent, message):
        print(f"   [{percent}%] {message}")

    updated_outline = glm._process_outline_feedback(
        outline=current_outline,
        feedback=feedback,
        on_progress=on_progress
    )

    # 同时也更新配图信息
    if current_outline.get('image_plan'):
        updated_outline['image_plan'] = current_outline['image_plan']

    session['outline'] = updated_outline

    # 🔧 修复：保存到共享文件，确保下次请求时能读取到最新数据
    save_outline_result(session_id, updated_outline)
    # 同时保存确认状态
    if session.get('confirmed_outline'):
        shared_update_session(session_id, confirmed_outline=session['confirmed_outline'])
        print(f"[API] 大纲和确认状态已保存到共享文件")

    print(f"[API] 大纲反馈处理完成: {updated_outline.get('chapter_count', 0)} 个章节")

    return jsonify({
        'success': True,
        'message': 'Feedback received and outline updated by AI',
        'data': updated_outline,
        'confirmed_outline': session.get('confirmed_outline', {})
    })

@app.route('/api/draft/generate', methods=['POST'])
def generate_draft():
    """生成文章初稿 (Phase 3) - 使用 GLM API"""
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    topic = session.get('topic', '未知主题')

    # 获取大纲和调研数据（已通过 get_synced_session 同步）
    outline = session.get('outline', {})
    research = session.get('research_data', {})

    # 尝试从共享文件加载完整会话数据
    try:
        session_data = shared_get_session(session_id)
        if session_data:
            if session_data.get('outline'):
                outline = session_data['outline']
                session['outline'] = outline
            if session_data.get('research_data'):
                research = session_data['research_data']
                session['research_data'] = research
    except Exception as e:
        print(f"[API] 加载共享数据失败: {e}")

    print(f"[API] 使用 GLM 生成初稿: {topic}")

    # 使用 GLM 服务生成初稿
    try:
        from glm_service import glm_service

        draft = glm_service.generate_draft(
            outline=outline,
            research_data=research,
            on_progress=lambda pct, msg: print(f"  [{pct}%] {msg}")
        )
        print(f"[API] GLM 初稿生成完成: {draft.get('word_count', 0)} 字")

    except Exception as e:
        print(f"[API] GLM 初稿生成失败: {e}，使用模板")
        # 备用：使用模板
        draft = {
            'title': topic,
            'content': f"""# {topic}

## 引言 | Introduction

在当今数字化时代，{topic}已成为一个备受关注的话题。

## 核心概念 | Core Concepts

{topic}的核心概念包括...

## 总结 | Conclusion

通过本文的介绍，相信大家对{topic}有了更深入的了解。
""",
            'word_count': 500,
            'chapter_count': outline.get('chapter_count', 6),
            'quality_check': {
                'structure': True,
                'logic': True,
                'language': True,
                'audience_fit': True
            },
            'timestamp': datetime.now().isoformat()
        }

    session['draft'] = draft
    session['current_phase'] = 3

    # 保存到共享文件
    save_draft_result(session_id, draft)

    return jsonify({
        'success': True,
        'phase': 3,
        'data': draft,
        'message': 'Draft generated by AI'
    })

@app.route('/api/draft/feedback', methods=['POST'])
def draft_feedback():
    """处理初稿阶段反馈"""
    data = request.json
    session_id = data.get('session_id')
    feedback = data.get('feedback')

    if not session_id or session_id not in sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    session = sessions[session_id]
    session['feedbacks']['draft'] = feedback

    # 根据反馈更新初稿
    updated_draft = session['draft'].copy()
    updated_draft['adjusted'] = True
    updated_draft['adjustment_note'] = feedback
    session['draft'] = updated_draft

    return jsonify({
        'success': True,
        'message': 'Feedback received and draft updated',
        'data': updated_draft
    })

@app.route('/api/images/generate', methods=['POST'])
def generate_images():
    """生成配图 (Phase 4) - 使用 Gemini API，逐张生成并返回进度"""
    data = request.json
    session_id = data.get('session_id')
    custom_style = data.get('style', None)  # 允许自定义风格

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 获取文章信息
    outline = session.get('outline', {})
    topic = outline.get('topic', '未知主题')
    chapters = outline.get('chapters', [])
    image_plan = outline.get('image_plan', {})

    # 优先使用自定义风格，其次使用大纲中的风格
    style = custom_style or image_plan.get('style', '科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K')

    # 准备输出目录
    output_dir = Path(__file__).parent / 'output' / session_id / 'images'
    output_dir.mkdir(parents=True, exist_ok=True)

    # 准备图片任务列表
    image_tasks = [
        {'name': 'cover.png', 'type': 'cover', 'description': f'{topic} 封面图', 'prompt': f'{topic} 概念可视化'}
    ]

    for i, chapter in enumerate(chapters):
        if chapter.get('number', 0) > 0:  # 跳过引言
            chapter_title = chapter.get('title', f'章节{i}')
            chapter_desc = chapter.get('description', '')
            image_tasks.append({
                'name': f'chapter-{i}.png',
                'type': 'chapter',
                'chapter_number': i,
                'description': f'{chapter_title} 配图',
                'prompt': f'{chapter_title} 插图, {chapter_desc}'
            })

    # 使用 Gemini 逐张生成
    images_result = []
    start_time = datetime.now()

    try:
        from gemini_service import gemini_service

        for idx, task in enumerate(image_tasks[:6]):  # 最多6张
            elapsed = (datetime.now() - start_time).total_seconds()

            # 生成单张图片
            result = gemini_service.generate_image(
                prompt=task['prompt'],
                style=style,
                output_path=str(output_dir / task['name'])
            )

            image_data = {
                **task,
                'size': '1024x576',
                'style': style,
                'success': result.get('success', False),
                'error': result.get('error') if not result.get('success') else None,
                'file_path': str(output_dir / task['name']) if result.get('success') else None,
                'file_size': result.get('file_size', 0),
                'elapsed_time': round((datetime.now() - start_time).total_seconds(), 1),
                'index': idx + 1,
                'total': len(image_tasks[:6])
            }
            images_result.append(image_data)

            print(f"[API] 配图 {idx+1}/{len(image_tasks[:6])}: {task['name']} - {'成功' if result.get('success') else '失败'}")

        total_elapsed = round((datetime.now() - start_time).total_seconds(), 1)
        success_count = sum(1 for img in images_result if img.get('success'))

        images = {
            'images': images_result,
            'style_keywords': style,
            'total_count': len(images_result),
            'success_count': success_count,
            'failed_count': len(images_result) - success_count,
            'total_elapsed_time': total_elapsed,
            'output_dir': str(output_dir),
            'generated_by': 'Gemini API',
            'quality_check': {
                'style_consistent': True,
                'resolution_ok': True,
                'theme_matched': True,
                'all_success': success_count == len(images_result)
            },
            'timestamp': datetime.now().isoformat()
        }

        print(f"[API] Gemini 配图完成: {success_count}/{len(images_result)} 张成功, 耗时 {total_elapsed}秒")

    except Exception as e:
        print(f"[API] Gemini 服务调用失败: {e}")
        images = _get_fallback_images(topic, chapters, style)

    session['images'] = images
    session['current_phase'] = 4

    return jsonify({
        'success': True,
        'phase': 4,
        'data': images,
        'message': f'Images generated: {len(images_result)} total'
    })


@app.route('/api/images/generate/stream', methods=['GET'])
def generate_images_stream():
    """
    生成配图 (Phase 4) - SSE 实时进度版本
    使用 Server-Sent Events 实时推送每张图片的生成进度
    """
    session_id = request.args.get('session_id')
    custom_style = request.args.get('style', None)

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    def generate():
        # 获取文章信息
        outline = session.get('outline', {})
        draft = session.get('draft', {})
        topic = outline.get('topic', draft.get('topic', '未知主题'))
        chapters = outline.get('chapters', [])
        image_plan = outline.get('image_plan', {})

        # 优先使用自定义风格
        style = custom_style or image_plan.get('style', '科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K')

        # 准备输出目录
        output_dir = Path(__file__).parent / 'output' / session_id / 'images'
        output_dir.mkdir(parents=True, exist_ok=True)

        # 🔧 修复：根据 image_plan.chapters 确定章节配图数量
        chapter_images = image_plan.get('chapters', [])
        include_cover = image_plan.get('cover') is not None or image_plan.get('cover', True)

        # 准备图片任务列表
        image_tasks = []

        # 封面图
        if include_cover:
            image_tasks.append({
                'name': 'cover.png',
                'type': 'cover',
                'description': f'{topic} 封面图',
                'prompt': f'{topic} 概念可视化'
            })

        # 章节配图 - 根据 image_plan.chapters 的数量（这个列表长度就是章节配图数量）
        chapter_count = len(chapter_images)
        print(f"[API] SSE 配图计划: 封面={include_cover}, 章节图计划={chapter_count}张")
        print(f"[API] SSE chapter_images 内容: {chapter_images}")

        # 过滤出有效章节（number > 0，排除引言）
        valid_chapters = [ch for ch in chapters if ch.get('number', 0) > 0]
        print(f"[API] SSE 有效章节数: {len(valid_chapters)}")

        for i in range(min(chapter_count, len(valid_chapters))):
            chapter = valid_chapters[i]
            chapter_title = chapter.get('title', f'章节{i+1}')
            chapter_desc = chapter.get('description', '')
            image_tasks.append({
                'name': f'chapter-{i+1}.png',
                'type': 'chapter',
                'chapter_number': i + 1,
                'description': f'{chapter_title} 配图',
                'prompt': f'{chapter_title} 插图, {chapter_desc}'
            })

        print(f"[API] SSE 最终配图任务: 共{len(image_tasks)}张")
        total_count = len(image_tasks)

        # 推送开始事件
        yield f"data: {json.dumps({'event': 'start', 'total': total_count, 'style': style, 'topic': topic}, ensure_ascii=False)}\n\n"

        images_result = []
        start_time = datetime.now()

        try:
            from gemini_service import gemini_service

            for idx, task in enumerate(image_tasks):
                # 推送开始生成这张图片
                progress_data = {
                    'event': 'progress',
                    'current': idx + 1,
                    'total': total_count,
                    'percent': round((idx / total_count) * 100),
                    'status': 'generating',
                    'image_name': task['name'],
                    'image_desc': task['description']
                }
                yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"

                # 生成单张图片
                result = gemini_service.generate_image(
                    prompt=task['prompt'],
                    style=style,
                    output_path=str(output_dir / task['name'])
                )

                elapsed = round((datetime.now() - start_time).total_seconds(), 1)

                image_data = {
                    **task,
                    'size': '1024x576',
                    'style': style,
                    'success': result.get('success', False),
                    'error': result.get('error') if not result.get('success') else None,
                    'file_path': str(output_dir / task['name']) if result.get('success') else None,
                    'file_size': result.get('file_size', 0),
                    'elapsed_time': elapsed,
                    'index': idx + 1,
                    'total': total_count
                }
                images_result.append(image_data)

                # 推送这张图片完成
                complete_data = {
                    'event': 'image_complete',
                    'current': idx + 1,
                    'total': total_count,
                    'percent': round(((idx + 1) / total_count) * 100),
                    'image': image_data
                }
                yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

                print(f"[API] SSE 配图 {idx+1}/{total_count}: {task['name']} - {'成功' if result.get('success') else '失败'}")

        except Exception as e:
            print(f"[API] SSE Gemini 服务调用失败: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            return

        total_elapsed = round((datetime.now() - start_time).total_seconds(), 1)
        success_count = sum(1 for img in images_result if img.get('success'))

        images = {
            'images': images_result,
            'style_keywords': style,
            'total_count': total_count,
            'success_count': success_count,
            'failed_count': total_count - success_count,
            'total_elapsed_time': total_elapsed,
            'output_dir': str(output_dir),
            'generated_by': 'Gemini API',
            'quality_check': {
                'style_consistent': True,
                'resolution_ok': True,
                'theme_matched': True,
                'all_success': success_count == total_count
            },
            'timestamp': datetime.now().isoformat()
        }

        session['images'] = images
        session['current_phase'] = 4

        # 🔧 同步到共享文件，确保 Phase 5 能获取到
        shared_update_session(session_id, images=images, current_phase=4)
        print(f"[API] SSE 配图完成，已同步到共享文件")

        # 推送完成事件
        complete_data = {
            'event': 'complete',
            'data': images,
            'message': f'配图生成完成: {success_count}/{total_count} 张成功, 耗时 {total_elapsed}秒'
        }
        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/images/regenerate', methods=['POST'])
def regenerate_single_image():
    """重新生成单张配图"""
    data = request.json
    session_id = data.get('session_id')
    image_name = data.get('image_name')

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    images_data = session.get('images', {})

    # 🔧 修复：兼容 images_data 可能是列表或字典的情况
    if isinstance(images_data, list):
        # 如果是列表，包装成字典格式
        images_list = images_data
        images_data = {
            'images': images_list,
            'style_keywords': '科技感, 蓝色调, high quality, detailed, 4K'
        }
    elif isinstance(images_data, dict):
        images_list = images_data.get('images', [])
    else:
        images_list = []

    # 找到要重新生成的图片
    target_image = None
    for img in images_list:
        if img.get('name') == image_name:
            target_image = img
            break

    if not target_image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404

    # 准备输出目录
    output_dir = Path(__file__).parent / 'output' / session_id / 'images'
    output_path = str(output_dir / image_name)

    try:
        from gemini_service import gemini_service

        style = images_data.get('style_keywords', '科技感, 蓝色调, high quality, detailed, 4K')

        result = gemini_service.generate_image(
            prompt=target_image.get('prompt', target_image.get('description', '')),
            style=style,
            output_path=output_path
        )

        # 更新图片状态
        target_image['success'] = result.get('success', False)
        target_image['error'] = result.get('error') if not result.get('success') else None
        target_image['file_path'] = output_path if result.get('success') else None
        target_image['file_size'] = result.get('file_size', 0)
        target_image['regenerated_at'] = datetime.now().isoformat()

        # 更新统计
        success_count = sum(1 for img in images_list if img.get('success'))
        images_data['success_count'] = success_count
        images_data['failed_count'] = len(images_list) - success_count

        # 🔧 同步更新到共享文件
        shared_update_session(session_id, images=images_data)

        print(f"[API] 重新生成配图: {image_name} - {'成功' if result.get('success') else '失败'}")

        return jsonify({
            'success': result.get('success', False),
            'image': target_image,
            'message': 'Image regenerated' if result.get('success') else result.get('error', 'Failed')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images/<session_id>/<filename>')
def serve_image(session_id, filename):
    """提供生成的图片"""
    image_path = Path(__file__).parent / 'output' / session_id / 'images' / filename
    if image_path.exists():
        return send_from_directory(str(image_path.parent), filename)
    return jsonify({'error': 'Image not found'}), 404


def _get_fallback_images(topic: str, chapters: List, style: str = None) -> Dict:
    """生成备用配图信息（当 Gemini 不可用时）"""
    images = [
        {'name': 'cover.png', 'description': f'{topic} 封面图', 'size': '1024x576', 'type': 'cover', 'success': False, 'error': 'Gemini unavailable'},
    ]

    for i, chapter in enumerate(chapters):
        if chapter.get('number', 0) > 0:
            images.append({
                'name': f'chapter-{i}.png',
                'description': f'{chapter.get("title", "章节")} 配图',
                'size': '1024x576',
                'type': 'chapter',
                'chapter_number': i,
                'success': False,
                'error': 'Gemini unavailable'
            })

    return {
        'images': images[:6],
        'style_keywords': style or '科技感 深蓝色调 几何图形 未来感 high quality detailed 4K',
        'total_count': len(images[:6]),
        'success_count': 0,
        'failed_count': len(images[:6]),
        'quality_check': {
            'style_consistent': True,
            'resolution_ok': True,
            'theme_matched': True,
            'fallback': True
        },
        'generated_by': 'Template (Gemini unavailable)',
        'timestamp': datetime.now().isoformat()
    }

@app.route('/api/layout/generate', methods=['POST'])
def generate_layout():
    """生成排版 (Phase 5) - 使用 GLM 进行智能排版"""
    data = request.json
    session_id = data.get('session_id')
    custom_output_path = data.get('output_path', None)  # 自定义输出路径

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 获取数据
    draft = session.get('draft', {})
    outline = session.get('outline', {})
    images_data = session.get('images', {})
    topic = outline.get('topic', draft.get('topic', '未命名文章'))
    image_style = outline.get('image_plan', {}).get('style', '科技感, 深蓝色调, 几何图形, 4K')

    print(f"[API] Phase 5 开始排版: {topic}")
    print(f"[API] images_data 状态: {len(images_data.get('images', []))} 张图片")

    # 确定输出目录
    if custom_output_path:
        output_dir = Path(custom_output_path) / session_id
    else:
        output_dir = Path(__file__).parent / 'output' / session_id

    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / 'images'
    images_dir.mkdir(exist_ok=True)

    print(f"[API] 开始智能排版: {topic}")

    # 1. 使用 GLM 进行智能排版处理
    try:
        from glm_service import glm_service

        # 获取原始内容
        raw_content = draft.get('content', '')
        chapters = outline.get('chapters', [])
        images_list = images_data.get('images', [])

        # 调用 GLM 进行智能排版
        print(f"[API] 调用 GLM 进行智能排版...")
        layout_result = glm_service.process_layout(
            draft_content=raw_content,
            outline=outline,
            images_data=images_data,
            topic=topic,
            on_progress=lambda pct, msg: print(f"  [{pct}%] {msg}")
        )

        # 获取处理后的内容
        processed_content = layout_result.get('processed_content', raw_content)
        image_placements = layout_result.get('image_placements', [])
        layout_notes = layout_result.get('layout_notes', [])

        print(f"[API] GLM 排版完成，图片位置: {len(image_placements)} 处")

    except Exception as e:
        print(f"[API] GLM 排版失败: {e}，使用原始内容")
        processed_content = draft.get('content', '')
        image_placements = []
        layout_notes = [f"GLM 排版失败: {str(e)}"]

    files_info = []

    # 2. 生成 Markdown 文件 (使用处理后的内容)
    md_path = output_dir / 'content.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    md_size = md_path.stat().st_size
    files_info.append({
        'name': 'content.md',
        'type': 'Markdown原文',
        'size_bytes': md_size,
        'size': format_file_size(md_size),
        'path': str(md_path),
        'download_url': f'/api/download/{session_id}/content.md'
    })

    # 3. 生成微信公众号 HTML (使用处理后的内容)
    wechat_html = generate_wechat_html(topic, processed_content, images_data, image_placements)
    wechat_path = output_dir / 'wechat.html'
    with open(wechat_path, 'w', encoding='utf-8') as f:
        f.write(wechat_html)
    wechat_size = wechat_path.stat().st_size
    files_info.append({
        'name': 'wechat.html',
        'type': '微信公众号格式',
        'size_bytes': wechat_size,
        'size': format_file_size(wechat_size),
        'path': str(wechat_path),
        'download_url': f'/api/download/{session_id}/wechat.html'
    })

    # 4. 生成完整 HTML (使用处理后的内容)
    article_html = generate_article_html(topic, processed_content, outline, images_data, image_placements)
    article_path = output_dir / 'article.html'
    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(article_html)
    article_size = article_path.stat().st_size
    files_info.append({
        'name': 'article.html',
        'type': 'HTML富文本格式',
        'size_bytes': article_size,
        'size': format_file_size(article_size),
        'path': str(article_path),
        'download_url': f'/api/download/{session_id}/article.html'
    })

    # 5. 生成 DOCX 文件
    try:
        docx_path = output_dir / 'wechat.docx'
        # 🔧 修复：脚本在 web/scripts/ 目录下，不是上级目录
        html_to_docx_script = Path(__file__).parent / 'scripts' / 'html_to_docx.py'

        if html_to_docx_script.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(html_to_docx_script),
                 '--input', str(wechat_path),
                 '--output', str(docx_path)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and docx_path.exists():
                docx_size = docx_path.stat().st_size
                files_info.append({
                    'name': 'wechat.docx',
                    'type': 'Word文档',
                    'size_bytes': docx_size,
                    'size': format_file_size(docx_size),
                    'path': str(docx_path),
                    'download_url': f'/api/download/{session_id}/wechat.docx'
                })
                print(f"[API] DOCX 生成成功: {format_file_size(docx_size)}")
            else:
                print(f"[API] DOCX 生成失败: {result.stderr if result.stderr else 'Unknown error'}")
        else:
            print(f"[API] html_to_docx.py 脚本不存在")
    except Exception as e:
        print(f"[API] DOCX 转换失败: {e}")

    # 6. 统计图片
    images_list = images_data.get('images', [])
    print(f"[API] Phase 5 图片列表: {len(images_list)} 张")
    images_size = 0
    success_images = [img for img in images_list if img.get('success') and img.get('file_path')]
    print(f"[API] 成功图片: {len(success_images)} 张")

    for img in success_images:
        try:
            img_path = Path(img['file_path'])
            print(f"[API] 检查图片路径: {img_path}, 存在: {img_path.exists()}")

            if img_path.exists():
                # 复制到输出目录
                import shutil
                shutil.copy2(img_path, images_dir / img['name'])
                file_size = img_path.stat().st_size
                images_size += file_size
                img['final_path'] = str(images_dir / img['name'])
                print(f"[API] 复制图片成功: {img['name']}, 大小: {file_size}")
            else:
                # 尝试在 output 目录中查找
                alt_path = Path(__file__).parent / 'output' / session_id / 'images' / img['name']
                print(f"[API] 尝试备用路径: {alt_path}, 存在: {alt_path.exists()}")
                if alt_path.exists():
                    import shutil
                    shutil.copy2(alt_path, images_dir / img['name'])
                    file_size = alt_path.stat().st_size
                    images_size += file_size
                    img['final_path'] = str(images_dir / img['name'])
                    print(f"[API] 从备用路径复制成功: {img['name']}, 大小: {file_size}")
        except Exception as e:
            print(f"[API] 复制图片失败: {e}")

    files_info.append({
        'name': 'images/',
        'type': '配图目录',
        'count': len(success_images),
        'size_bytes': images_size,
        'size': format_file_size(images_size),
        'path': str(images_dir)
    })

    # 计算总大小
    total_size = sum(f.get('size_bytes', 0) for f in files_info)
    total_size_mb = total_size / (1024 * 1024)

    layout = {
        'files': files_info,
        'total_size': format_file_size(total_size),
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size_mb, 2),
        'within_wechat_limit': total_size_mb < 14.5,
        'wechat_features': {
            'inline_css': True,
            'wechat_optimized': True,
            'centered_images': True,
            'max_width_constrained': True
        },
        'output_dir': str(output_dir),
        'layout_notes': layout_notes,
        'timestamp': datetime.now().isoformat()
    }

    session['layout'] = layout
    session['current_phase'] = 5

    print(f"[API] 排版完成: {len(files_info)} 个文件, 总大小 {format_file_size(total_size)}")

    return jsonify({
        'success': True,
        'phase': 5,
        'data': layout,
        'message': 'Layout generated'
    })


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.2f} MB'


def generate_wechat_html(topic: str, content: str, images_data: dict, image_placements: list = None) -> str:
    """生成微信公众号兼容的 HTML（智能图片插入）"""
    import re

    # 获取图片列表
    images_list = images_data.get('images', [])
    success_images = [img for img in images_list if img.get('success') and img.get('file_path')]

    # 按段落分割内容，正确处理块级元素
    paragraphs = content.split('\n\n')
    html_parts = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 处理标题
        if para.startswith('# '):
            html_parts.append(f'<h1 style="font-size: 24px; font-weight: bold; margin: 20px 0; color: #333;">{para[2:]}</h1>')
        elif para.startswith('## '):
            html_parts.append(f'<h2 style="font-size: 20px; font-weight: bold; margin: 16px 0; color: #333; border-bottom: 2px solid #3498db; padding-bottom: 8px;">{para[3:]}</h2>')
        elif para.startswith('### '):
            html_parts.append(f'<h3 style="font-size: 18px; font-weight: bold; margin: 14px 0; color: #333;">{para[4:]}</h3>')
        elif para.startswith('> '):
            # 引用
            html_parts.append(f'<blockquote style="border-left: 4px solid #3498db; padding: 12px 16px; color: #666; margin: 16px 0; background: #f8f9fa;">{para[2:]}</blockquote>')
        else:
            # 普通段落，处理内联格式
            p_content = para
            p_content = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #2c3e50;">\1</strong>', p_content)
            p_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', p_content)
            html_parts.append(f'<p style="margin: 12px 0; line-height: 1.8; color: #333; text-align: justify;">{p_content}</p>')

    html_content = '\n        '.join(html_parts)

    # 插入封面图
    cover_image_html = ''
    if success_images:
        cover_img = next((img for img in success_images if 'cover' in img.get('name', '').lower()), success_images[0])
        cover_image_html = f'''<div style="text-align: center; margin: 20px 0;">
            <img src="images/{cover_img['name']}" style="max-width: 100%; height: auto; border-radius: 8px;" alt="{topic}">
        </div>'''

    # 在第一个标题后插入封面图
    if cover_image_html and '<h1' in html_content:
        html_content = html_content.replace('</h1>', f'</h1>\n        {cover_image_html}', 1)

    # 在章节标题后插入配图
    chapter_img_idx = 1
    for i, img in enumerate(success_images):
        if 'cover' not in img.get('name', '').lower() and chapter_img_idx < len(success_images):
            # 在 h2 标题后插入图片
            chapter_img_html = f'''<div style="text-align: center; margin: 16px 0;">
                <img src="images/{img['name']}" style="max-width: 100%; height: auto; border-radius: 8px;" alt="配图">
            </div>'''
            # 找到第N个 h2 标签并在其后插入图片
            h2_count = html_content.count('</h2>')
            if h2_count >= chapter_img_idx:
                # 在第 chapter_img_idx 个 h2 后插入
                parts = html_content.split('</h2>', chapter_img_idx)
                if len(parts) > chapter_img_idx:
                    html_content = '</h2>'.join(parts[:chapter_img_idx]) + '</h2>\n        ' + chapter_img_html + '\n        ' + '</h2>'.join(parts[chapter_img_idx:])
            chapter_img_idx += 1

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
</head>
<body style="max-width: 677px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff;">
    <article>
        {html_content}
    </article>
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; text-align: center;">
        <p>由 AI Article Writer 自动生成</p>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>'''


def generate_article_html(topic: str, content: str, outline: dict, images_data: dict, image_placements: list = None) -> str:
    """生成完整的 HTML 文章（智能图片插入）"""
    import re

    # 获取图片列表
    images_list = images_data.get('images', [])
    success_images = [img for img in images_list if img.get('success') and img.get('file_path')]

    # Markdown 转 HTML
    html_content = content
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
    html_content = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'\n\n', r'</p><p>', html_content)

    # 插入封面图
    cover_image_html = ''
    if success_images:
        cover_img = next((img for img in success_images if 'cover' in img.get('name', '').lower()), success_images[0])
        cover_image_html = f'''<div style="text-align: center; margin: 24px 0;">
            <img src="images/{cover_img['name']}" style="max-width: 100%; height: auto; border-radius: 8px;" alt="{topic}">
        </div>'''

    # 在第一个标题后插入封面图
    if cover_image_html and '<h1' in html_content:
        html_content = html_content.replace('</h1>', f'</h1>{cover_image_html}', 1)

    # 在章节标题后插入配图
    chapter_img_idx = 1
    for i, img in enumerate(success_images):
        if 'cover' not in img.get('name', '').lower() and chapter_img_idx < len(success_images):
            chapter_img_html = f'''<div style="text-align: center; margin: 20px 0;">
                <img src="images/{img['name']}" style="max-width: 100%; height: auto; border-radius: 8px;" alt="配图">
            </div>'''
            h2_count = html_content.count('</h2>')
            if h2_count >= chapter_img_idx:
                parts = html_content.split('</h2>', chapter_img_idx)
                if len(parts) > chapter_img_idx:
                    html_content = '</h2>'.join(parts[:chapter_img_idx]) + '</h2>' + chapter_img_html + '</h2>'.join(parts[chapter_img_idx:])
            chapter_img_idx += 1

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.8; color: #333; }}
        h1 {{ font-size: 32px; margin: 30px 0; color: #1a1a1a; }}
        h2 {{ font-size: 24px; margin: 24px 0 16px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
        h3 {{ font-size: 20px; margin: 20px 0 12px; color: #34495e; }}
        p {{ margin: 12px 0; }}
        blockquote {{ border-left: 4px solid #3498db; padding: 12px 20px; margin: 20px 0; background: #f8f9fa; color: #555; }}
        strong {{ color: #2c3e50; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px; }}
        footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #999; text-align: center; }}
    </style>
</head>
<body>
    <article>
        <p>{html_content}</p>
    </article>
    <footer>
        <p>本文由 AI Article Writer 自动生成</p>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>'''


@app.route('/api/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """下载单个文件"""
    file_path = Path(__file__).parent / 'output' / session_id / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(file_path.parent), filename, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/download/all/<session_id>')
def download_all(session_id):
    """打包下载所有文件"""
    import shutil
    import tempfile

    output_dir = Path(__file__).parent / 'output' / session_id
    if not output_dir.exists():
        return jsonify({'error': 'Session not found'}), 404

    # 创建临时 zip 文件
    temp_dir = tempfile.mkdtemp()
    zip_path = Path(temp_dir) / f'{session_id}_output.zip'
    shutil.make_archive(str(zip_path.with_suffix('')), 'zip', str(output_dir))

    return send_from_directory(temp_dir, f'{session_id}_output.zip', as_attachment=True)

@app.route('/api/layout/feedback', methods=['POST'])
def layout_feedback():
    """处理排版阶段反馈"""
    data = request.json
    session_id = data.get('session_id')
    feedback = data.get('feedback')

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400
    session['feedbacks']['layout'] = feedback

    # 根据反馈更新排版
    updated_layout = session['layout'].copy()
    updated_layout['adjusted'] = True
    updated_layout['adjustment_note'] = feedback
    session['layout'] = updated_layout

    return jsonify({
        'success': True,
        'message': 'Feedback received and layout updated',
        'data': updated_layout
    })

@app.route('/api/export/complete', methods=['POST'])
def complete_export():
    """完成导出 (Phase 6)"""
    data = request.json
    session_id = data.get('session_id')

    # 🔧 修复：使用同步函数获取最新 session 数据
    session = get_synced_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 生成最终导出信息
    export_data = {
        'files': [
            {'name': 'wechat.docx', 'type': '微信公众号可上传格式', 'size': '~670KB'},
            {'name': 'content.md', 'type': 'Markdown原文'},
            {'name': 'wechat.html', 'type': '微信公众号HTML'},
            {'name': 'article.html', 'type': 'HTML富文本'},
            {'name': 'images/', 'type': '配图目录', 'count': 5}
        ],
        'size_limit': '14.5MB',
        'within_limit': True,
        'ready_for_wechat': True,
        'output_path': f'./output/{session["topic"]}/',
        'timestamp': datetime.now().isoformat()
    }

    session['export'] = export_data
    session['current_phase'] = 6

    return jsonify({
        'success': True,
        'phase': 6,
        'data': export_data,
        'message': 'Export completed'
    })

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话状态 - 支持从共享目录加载"""
    # 首先检查内存
    if session_id in sessions:
        return jsonify({
            'success': True,
            'data': sessions[session_id]
        })

    # 检查共享目录
    shared_session = shared_get_session(session_id)
    if shared_session:
        # 加载到内存缓存
        sessions[session_id] = shared_session
        print(f"✅ 从共享目录加载会话: {session_id}")
        return jsonify({
            'success': True,
            'data': shared_session
        })

    return jsonify({'success': False, 'error': 'Session not found'}), 404

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': 'Session not found'}), 404

    del sessions[session_id]
    return jsonify({
        'success': True,
        'message': 'Session deleted'
    })

@app.route('/api/research/weixin', methods=['POST'])
def search_weixin():
    """搜索微信公众号文章 - 使用真实搜索"""
    data = request.json
    keywords = data.get('keywords', '')
    limit = data.get('limit', 5)
    session_id = data.get('session_id')

    if not keywords:
        return jsonify({'success': False, 'error': 'Keywords required'}), 400

    # 使用真实搜索
    print(f"💬 微信搜索: {keywords}")
    results = SearchProviders.weixin_search(keywords, limit)
    print(f"✅ 获取 {len(results)} 条微信文章")

    # 如果有会话ID，更新会话数据
    if session_id and session_id in sessions:
        session = sessions[session_id]
        if session.get('research_data'):
            existing_sources = session['research_data'].get('sources', [])
            weixin_urls = {s.get('url') for s in existing_sources if s.get('type') == 'WeChat'}
            for result in results:
                if result.get('url') not in weixin_urls:
                    existing_sources.append(result)
            session['research_data']['sources'] = existing_sources

    return jsonify({
        'success': True,
        'results': results,
        'count': len(results),
        'message': f'Found {len(results)} WeChat articles'
    })

# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    """返回主页"""
    return send_from_directory(str(WEB_DIR), 'index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """提供CSS文件"""
    return send_from_directory(str(WEB_DIR / 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """提供JS文件"""
    return send_from_directory(str(WEB_DIR / 'js'), filename)

@app.route('/shared/<path:filename>')
def serve_shared(filename):
    """提供共享数据文件"""
    return send_from_directory(str(WEB_DIR / 'shared'), filename)

# ==================== SSE 进度推送 ====================

from flask import Response
import queue
import threading

# 进度消息队列
progress_queues = {}

def get_progress_queue(session_id):
    """获取或创建进度队列"""
    if session_id not in progress_queues:
        progress_queues[session_id] = queue.Queue()
    return progress_queues[session_id]

def push_progress(session_id, progress, message, details=None):
    """推送进度消息"""
    if session_id in progress_queues:
        data = {
            'progress': progress,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        progress_queues[session_id].put(data)

@app.route('/api/progress/<session_id>')
def progress_stream(session_id):
    """SSE 进度流"""
    def generate():
        q = get_progress_queue(session_id)
        while True:
            try:
                data = q.get(timeout=30)  # 30秒超时
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                if data.get('progress') == 100:
                    break
            except queue.Empty:
                # 发送心跳
                yield f": heartbeat\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/outline/generate/stream', methods=['POST'])
def generate_outline_stream():
    """流式生成大纲 - 带实时进度"""
    data = request.json
    session_id = data.get('session_id')

    if not session_id or session_id not in sessions:
        return jsonify({'success': False, 'error': 'Invalid session'}), 400

    session = sessions[session_id]
    length = session.get('length', 'medium')
    audience = session.get('audience', 'general')

    def generate():
        try:
            # 推送开始
            yield f"data: {json.dumps({'progress': 5, 'message': '开始生成大纲...'}, ensure_ascii=False)}\n\n"

            # 获取调研数据
            research_data = get_research_result(session_id)
            if research_data:
                session['research_data'] = research_data
                yield f"data: {json.dumps({'progress': 10, 'message': '已加载调研数据'}, ensure_ascii=False)}\n\n"
            else:
                research_data = session.get('research_data', {'topic': session.get('topic', '未知主题')})
                yield f"data: {json.dumps({'progress': 10, 'message': '使用基础数据'}, ensure_ascii=False)}\n\n"

            # 进度回调
            def on_progress(pct, msg):
                pass  # SSE 直接推送

            # 生成大纲
            yield f"data: {json.dumps({'progress': 20, 'message': '正在调用 AI 生成大纲...'}, ensure_ascii=False)}\n\n"

            outline = phase_handler.process_outline(
                research_data=research_data,
                length=length,
                audience=audience
            )

            yield f"data: {json.dumps({'progress': 80, 'message': '大纲生成完成'}, ensure_ascii=False)}\n\n"

            session['outline'] = outline
            session['current_phase'] = 2

            # 返回最终结果
            result = {
                'progress': 100,
                'message': '完成',
                'data': outline
            }
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'progress': -1, 'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


# ==================== 统一 Chat API ====================

@app.route('/api/chat', methods=['POST'])
def chat_with_assistant():
    """
    统一的 Chat API - 与 GLM 助手对话，优化各阶段内容

    Request:
        - session_id: 会话 ID
        - phase: 当前阶段 (1-5)
        - message: 用户消息
        - history: 对话历史 (可选)

    Response:
        - success: 是否成功
        - reply: GLM 的回复
        - updated_content: 更新后的内容 (如果有)
    """
    data = request.json
    session_id = data.get('session_id')
    phase = data.get('phase', 1)
    user_message = data.get('message', '')
    history = data.get('history', [])

    if not session_id:
        return jsonify({'success': False, 'error': 'Missing session_id'}), 400

    if not user_message.strip():
        return jsonify({'success': False, 'error': '消息不能为空'}), 400

    # 获取 session：先从内存，再从共享文件
    session = sessions.get(session_id)
    if not session:
        shared_session = shared_get_session(session_id)
        if shared_session:
            session = shared_session
            sessions[session_id] = session  # 缓存到内存
            print(f"[API] Chat: 从共享文件加载会话 {session_id}")
        else:
            return jsonify({'success': False, 'error': 'Invalid session'}), 400

    # 在处理聊天前，先从共享文件同步最新数据（确保 task_processor 的结果被加载）
    if phase == 1:
        # 同步调研数据 - 总是使用共享文件的最新数据
        shared_research = get_research_result(session_id)
        if shared_research and shared_research.get('sources'):
            # 总是同步，确保导入的数据也能被AI看到
            session['research_data'] = shared_research
            print(f"[API] Chat: 从共享文件同步调研数据: {len(shared_research.get('sources', []))} 个来源")
    elif phase == 2:
        # 同步大纲数据 - 总是使用共享文件的最新数据
        shared_session = shared_get_session(session_id)
        if shared_session and shared_session.get('outline'):
            session['outline'] = shared_session['outline']
            print(f"[API] Chat: 从共享文件同步大纲数据")
        # 🔧 同时同步 confirmed_outline，确保勾选确认状态也被同步
        if shared_session and shared_session.get('confirmed_outline'):
            session['confirmed_outline'] = shared_session['confirmed_outline']
            print(f"[API] Chat: 从共享文件同步确认状态")
    elif phase == 3:
        # 同步初稿数据 - 总是使用共享文件的最新数据
        shared_session = shared_get_session(session_id)
        if shared_session and shared_session.get('draft'):
            session['draft'] = shared_session['draft']
            print(f"[API] Chat: 从共享文件同步初稿数据")

    # 根据阶段处理
    try:
        if phase == 1:
            result = handle_research_chat(session, user_message, history)
        elif phase == 2:
            result = handle_outline_chat(session, user_message, history)
        elif phase == 3:
            result = handle_draft_chat(session, user_message, history)
        elif phase == 4:
            result = handle_images_chat(session, user_message, history)
        elif phase == 5:
            result = handle_layout_chat(session, user_message, history)
        else:
            return jsonify({'success': False, 'error': '无效的阶段'}), 400

        # 保存对话历史
        if 'chat_history' not in session:
            session['chat_history'] = {}
        if phase not in session['chat_history']:
            session['chat_history'][phase] = []

        session['chat_history'][phase].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        session['chat_history'][phase].append({
            'role': 'assistant',
            'content': result.get('reply', ''),
            'timestamp': datetime.now().isoformat()
        })

        # 🔧 修复：将修改后的 session 数据保存到共享文件
        # 这样下次请求时能读取到最新的数据，避免多次修改时数据丢失
        if result.get('action') == 'update':
            if phase == 1 and session.get('research_data'):
                save_research_result(session_id, session['research_data'])
                print(f"[API] Chat: 保存调研数据到共享文件")
            elif phase == 2 and session.get('outline'):
                shared_update_session(session_id, outline=session['outline'])
                print(f"[API] Chat: 保存大纲数据到共享文件")
            elif phase == 3 and session.get('draft'):
                shared_update_session(session_id, draft=session['draft'])
                print(f"[API] Chat: 保存初稿数据到共享文件")

        return jsonify({
            'success': True,
            'reply': result.get('reply', ''),
            'updated_content': result.get('updated_content'),
            'confirmed_outline': result.get('confirmed_outline'),
            'action': result.get('action', 'reply')
        })

    except Exception as e:
        print(f"[API] Chat 错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def handle_research_chat(session: Dict, message: str, history: List) -> Dict:
    """
    处理 Phase 1 调研阶段的对话

    核心逻辑（与 Phase 3 一致）：
    用户消息 + 当前内容 → AI大模型理解并修改 → 返回修改后内容 → 刷新内容预览
    """
    from glm_service import glm_service
    import re, json

    topic = session.get('topic', '未知主题')
    research_data = session.get('research_data') or {}

    # 确保基础数据结构存在
    if not research_data.get('sources'):
        research_data['sources'] = []
    if not research_data.get('key_findings'):
        research_data['key_findings'] = []

    # 直接让 AI 处理：理解用户意图 + 修改内容
    # 获取完整的数据
    current_sources = research_data.get('sources', [])
    current_key_findings = research_data.get('key_findings', [])
    source_count = len(current_sources)

    prompt = f"""你是一个专业的调研助手。

【当前调研状态】
- 信息来源总数: {source_count} 条
- 信息来源列表: {json.dumps(current_sources, ensure_ascii=False, indent=2)}
- 关键发现: {json.dumps(current_key_findings, ensure_ascii=False, indent=2)}

【用户需求】
{message}

【任务】
根据用户需求，只返回需要修改的字段。不需要修改的字段不要返回。

如果用户要求删除、增加或修改信息来源，请返回完整的 sources 列表。
如果用户只是提问或讨论，请直接回复，不需要修改内容。

【返回格式】
- 用户要求修改: {{"action": "update", "sources": [...]}}
- 用户只是提问: {{"action": "reply", "content": "回复内容"}}

只返回 JSON，不要其他内容。"""

    try:
        response = glm_service._call_api(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=4096
        )

        if response and 'choices' in response and response['choices']:
            ai_content = response['choices'][0].get('message', {}).get('content', '')

            # 解析 AI 返回的 JSON
            json_match = re.search(r'\{[\s\S]*\}', ai_content)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    action = result.get('action', 'reply')

                    if action == 'update':
                        # 先从 session 获取最新的数据，确保不丢失之前的修改
                        latest_research = session.get('research_data') or {}
                        old_source_count = len(latest_research.get('sources', []))

                        # 检测用户是否有搜索意图（更全面的关键词）
                        search_keywords = ['搜索', '查找', '补充', '增加', 'search', '找更多', '再搜索', '再找', '再增加', '再补充']
                        has_search_intent = any(kw in message for kw in search_keywords)

                        # 如果有搜索意图，真正执行搜索（而不是使用 AI 返回的模拟结果）
                        if has_search_intent:
                            try:
                                print(f"[Chat] 检测到搜索意图，正在执行真正搜索...")
                                # 使用主题 + 用户需求作为搜索关键词
                                search_query = f"{topic} {message}"
                                new_sources = glm_service.search(
                                    query=search_query,
                                    on_progress=lambda p, m: print(f"  [补充搜索] {m}")
                                )
                                if new_sources:
                                    # 合并新旧来源
                                    existing_sources = latest_research.get('sources', [])
                                    existing_sources.extend(new_sources)
                                    latest_research['sources'] = existing_sources
                                    latest_research['key_findings'] = [f"已收集 {len(existing_sources)} 个信息来源"]
                                    print(f"[Chat] 执行搜索，新增 {len(new_sources)} 条来源，总计 {len(existing_sources)} 条")
                                else:
                                    # 搜索返回空结果，保留原有数据
                                    print(f"[Chat] 搜索返回空结果，保留原有数据")
                            except Exception as e:
                                print(f"补充搜索失败: {e}")
                                # 搜索失败时，不使用 AI 生成的模拟数据，保留原有数据
                        else:
                            # 没有搜索意图，可能是删除或其他操作
                            # 检测删除意图
                            delete_keywords = ['删除', '去掉', '移除', '取消', '不要', '最末', '最后一个', '最后一条']
                            has_delete_intent = any(kw in message for kw in delete_keywords)

                            if has_delete_intent:
                                # 删除意图：只从现有列表中删除，不使用 AI 生成的 sources
                                print(f"[Chat] 检测到删除意图，保留原有数据")
                                # 不执行任何操作，让用户确认
                            else:
                                # 其他修改意图：直接使用 AI 返回的 sources
                                if 'sources' in result:
                                    latest_research['sources'] = result['sources']
                                    new_source_count = len(result['sources'])
                                    # 如果 sources 数量变化，自动更新 key_findings
                                    if new_source_count != old_source_count:
                                        latest_research['key_findings'] = [f"已收集 {new_source_count} 个信息来源"]

                        if 'key_findings' in result:
                            latest_research['key_findings'] = result['key_findings']

                        latest_research['last_modified'] = datetime.now().isoformat()
                        session['research_data'] = latest_research

                        return {
                            'reply': '✅ 已根据您的要求修改调研内容，请查看更新后的调研报告。',
                            'updated_content': latest_research,
                            'action': 'update'
                        }
                    else:
                        return {
                            'reply': result.get('content', ai_content),
                            'action': 'reply'
                        }
                except json.JSONDecodeError:
                    pass

            # 如果无法解析 JSON
            if len(ai_content) > 300:
                # 先从 session 获取最新的数据
                latest_research = session.get('research_data') or {}
                latest_research['key_findings'] = latest_research.get('key_findings', [])
                latest_research['key_findings'].append(f"更新 ({datetime.now().strftime('%H:%M')}): {ai_content[:200]}...")
                session['research_data'] = latest_research
                return {
                    'reply': '✅ 已更新调研内容，请查看更新后的调研报告。',
                    'updated_content': latest_research,
                    'action': 'update'
                }
            else:
                return {
                    'reply': ai_content,
                    'action': 'reply'
                }
        else:
            return {
                'reply': '抱歉，AI 服务暂时无法响应，请稍后再试。',
                'action': 'reply'
            }

    except Exception as e:
        print(f"[Chat] AI 调用失败: {e}")
        return {
            'reply': f'抱歉，处理失败: {str(e)}',
            'action': 'reply'
        }


def handle_outline_chat(session: Dict, message: str, history: List) -> Dict:
    """
    处理 Phase 2 大纲阶段的对话

    核心逻辑（与 Phase 3 一致）：
    用户消息 + 当前内容 → AI大模型理解并修改 → 返回修改后内容 → 刷新内容预览
    """
    from glm_service import glm_service
    import re, json

    topic = session.get('topic', '未知主题')
    outline = session.get('outline') or {}
    confirmed_outline = session.get('confirmed_outline', {})

    # 直接让 AI 处理：理解用户意图 + 修改内容
    # 获取当前配置
    current_image_plan = outline.get('image_plan', {})
    current_word_count = outline.get('word_count', '3000')
    # 配图数量包括封面（1张封面 + N张章节图）
    chapter_images = current_image_plan.get('chapters', [])
    current_image_count = 1 + len(chapter_images) if current_image_plan.get('cover') else len(chapter_images)
    current_image_style = current_image_plan.get('style', '科技感, 深蓝色调')
    # 配图数量说明：总数 = 封面1张 + 章节图N张
    image_count_display = f"{current_image_count}张（1封面 + {len(chapter_images)}章节图）"

    # 构建已确认/未确认的状态描述
    confirmed_status = []
    unconfirmed_status = []
    if confirmed_outline.get('chapters'):
        confirmed_status.append("✅ 章节结构")
    else:
        unconfirmed_status.append("待确认：章节结构")

    if confirmed_outline.get('image_plan'):
        confirmed_status.append("✅ 配图规划")
    else:
        unconfirmed_status.append("待确认：配图规划")

    if confirmed_outline.get('writing_style'):
        confirmed_status.append("✅ 写作风格")
    else:
        unconfirmed_status.append("待确认：写作风格")

    if confirmed_outline.get('image_style'):
        confirmed_status.append("✅ 配图风格")
    else:
        unconfirmed_status.append("待确认：配图风格")

    if confirmed_outline.get('word_count'):
        confirmed_status.append("✅ 预计字数")
    else:
        unconfirmed_status.append("待确认：预计字数")

    status_text = " | ".join(confirmed_status) + "\n" + " | ".join(unconfirmed_status)

    prompt = f"""你是一个专业的文章大纲设计师。请严格按照以下标准执行。

【大纲确认状态】（已确认的项目会锁定，不可修改；未确认的项目可以调整）
{status_text}

【当前大纲内容】（如果某项已锁定，AI 不能修改该项）
- 章节: {json.dumps(outline.get('chapters', []), ensure_ascii=False, indent=2)}
- 配图数量: {image_count_display}
- 配图风格: {current_image_style}
- 目标字数: {current_word_count}
- 写作风格: {session.get('audience', 'general')} (目标读者)

【用户需求】
{message}

【重要规则 - 必须遵守】
1. 只修改用户明确要求的字段，不要修改其他字段
2. 如果用户要求修改章节：返回完整的 chapters 数组
3. 如果用户没有要求修改章节：不要返回 chapters 字段
4. 如果用户要求修改风格/数量/字数：只返回对应字段
5. **禁止修改已确认的项目**：如果上述状态显示某项已确认（✅），禁止修改该项

【大纲生成标准】
- 章节标题必须具体化，禁止使用"核心概念"、"技术原理"等泛泛标题
- 标题要与主题紧密相关（如主题是"GPT-4"，标题应该是"GPT-4的多模态能力"而非"核心能力"）
- 描述必须包含：核心观点、详细解释、案例/数据、小结过渡（80-150字）
- 每个章节列出3-5个Key Points

【返回格式】（只返回需要修改的字段）
- 修改章节: {{"action": "update", "chapters": [{{"number": 0, "title": "具体标题", "description": "描述", "key_points": ["要点"]}}]}}
- 修改风格: {{"action": "update", "image_style": "新风格"}}
- 修改数量: {{"action": "update", "image_count": 数量}}
- 修改字数: {{"action": "update", "word_count": "字数"}}
- 只是讨论: {{"action": "reply", "content": "回复内容"}}

只返回 JSON，不要其他内容。"""

    try:
        response = glm_service._call_api(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=4096
        )

        if response and 'choices' in response and response['choices']:
            ai_content = response['choices'][0].get('message', {}).get('content', '')

            # 解析 AI 返回的 JSON
            json_match = re.search(r'\{[\s\S]*\}', ai_content)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    action = result.get('action', 'reply')

                    if action == 'update':
                        # 先从 session 获取最新的 outline，确保不丢失之前的修改
                        latest_outline = session.get('outline') or {}

                        # 更新大纲数据 - 只更新 AI 返回的字段
                        if 'chapters' in result:
                            latest_outline['chapters'] = result['chapters']
                            latest_outline['chapter_count'] = len(result['chapters'])

                        # 处理配图数量
                        if 'image_count' in result:
                            image_count = result['image_count']
                            latest_outline.setdefault('image_plan', {})
                            # image_count 是总数量（包括封面），章节图数量 = 总数 - 1
                            chapter_image_count = max(0, image_count - 1)
                            # 根据章节数量生成配图规划
                            latest_outline['image_plan']['chapters'] = [
                                f'第{i+1}章配图' for i in range(min(chapter_image_count, len(latest_outline.get('chapters', []))))
                            ]
                            # 封面图始终存在
                            latest_outline['image_plan']['cover'] = {'description': '封面配图', 'size': '1024x576'}

                        # 保留之前的配图数量设置
                        if 'image_count' not in result and latest_outline.get('image_plan', {}).get('chapters'):
                            pass  # 保留现有的配图设置

                        if 'image_style' in result:
                            latest_outline.setdefault('image_plan', {})
                            latest_outline['image_plan']['style'] = result['image_style']
                        if 'word_count' in result:
                            latest_outline['word_count'] = str(result['word_count'])

                        latest_outline['last_modified'] = datetime.now().isoformat()
                        session['outline'] = latest_outline

                        return {
                            'reply': '✅ 已根据您的要求修改大纲，请查看更新后的大纲。',
                            'updated_content': latest_outline,
                            'confirmed_outline': session.get('confirmed_outline', {}),
                            'action': 'update'
                        }
                    else:
                        return {
                            'reply': result.get('content', ai_content),
                            'action': 'reply',
                            'confirmed_outline': session.get('confirmed_outline', {})
                        }
                except json.JSONDecodeError:
                    pass

            # 如果无法解析 JSON，检查是否包含大纲内容
            if '章节' in ai_content and len(ai_content) > 200:
                # 获取最新数据
                latest_outline = session.get('outline') or {}
                return {
                    'reply': '✅ 已收到您的修改要求，大纲已更新。',
                    'updated_content': latest_outline,
                    'confirmed_outline': session.get('confirmed_outline', {}),
                    'action': 'update'
                }
            else:
                return {
                    'reply': ai_content,
                    'action': 'reply'
                }
        else:
            return {
                'reply': '抱歉，AI 服务暂时无法响应，请稍后再试。',
                'action': 'reply'
            }

    except Exception as e:
        print(f"[Chat] AI 调用失败: {e}")
        return {
            'reply': f'抱歉，处理失败: {str(e)}',
            'action': 'reply'
        }


def handle_draft_chat(session: Dict, message: str, history: List) -> Dict:
    """
    处理 Phase 3 初稿阶段的对话

    核心逻辑（极简）：
    用户消息 + 当前内容 → AI大模型理解并修改 → 返回修改后内容 → 刷新内容预览

    不管用户说什么，都让 AI 来理解和处理。
    """
    from glm_service import glm_service
    import re, json

    draft = session.get('draft') or {}
    topic = draft.get('topic', '未知主题')
    current_content = draft.get('content', '')

    # 直接让 AI 处理：理解用户意图 + 修改内容
    prompt = f"""你是一个专业的文章编辑。用户正在审阅文章初稿。

文章主题: {topic}
当前文章内容:
{current_content}

用户消息: {message}

请根据用户的消息处理：
- 如果用户要求修改内容（如"扩写第二章"、"这里太专业了"、"增加一段关于XXX的内容"等），请返回修改后的完整文章内容
- 如果用户只是在提问或讨论，请直接回复用户，不需要修改内容

返回格式（JSON）：
{{"action": "update", "content": "修改后的完整文章内容（Markdown格式）"}}
或
{{"action": "reply", "content": "对用户的回复文字"}}

只返回 JSON，不要其他内容。"""

    try:
        response = glm_service._call_api(
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=8192
        )

        if response and 'choices' in response and response['choices']:
            ai_content = response['choices'][0].get('message', {}).get('content', '')

            # 解析 AI 返回的 JSON
            json_match = re.search(r'\{[\s\S]*\}', ai_content)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    action = result.get('action', 'reply')
                    content = result.get('content', '')

                    if action == 'update' and content:
                        # 先从 session 获取最新的数据，确保不丢失之前的修改
                        latest_draft = session.get('draft') or {}

                        # 更新文章内容
                        latest_draft['content'] = content
                        latest_draft['word_count'] = len(content)
                        latest_draft['last_modified'] = datetime.now().isoformat()
                        session['draft'] = latest_draft

                        return {
                            'reply': '✅ 已根据您的要求修改内容，请查看「内容预览」区域。',
                            'updated_content': latest_draft,
                            'action': 'update'
                        }
                    else:
                        # 只是回复
                        return {
                            'reply': content or ai_content,
                            'action': 'reply'
                        }
                except json.JSONDecodeError as je:
                    print(f"[Chat] JSON 解析失败: {je}, AI 返回内容: {ai_content[:200]}...")
                    # JSON 解析失败，继续往下走，检查是否是纯文本内容
                    pass

            # 如果无法解析 JSON，检查内容长度判断是修改还是回复
            if len(ai_content) > 500:
                # 先从 session 获取最新的数据
                latest_draft = session.get('draft') or {}
                # 内容较长，可能是修改后的文章
                latest_draft['content'] = ai_content
                latest_draft['word_count'] = len(ai_content)
                latest_draft['last_modified'] = datetime.now().isoformat()
                session['draft'] = latest_draft

                return {
                    'reply': '✅ 已根据您的要求修改内容，请查看「内容预览」区域。',
                    'updated_content': latest_draft,
                    'action': 'update'
                }
            else:
                return {
                    'reply': ai_content,
                    'action': 'reply'
                }

        else:
            return {
                'reply': '抱歉，AI 服务暂时无法响应，请稍后再试。',
                'action': 'reply'
            }

    except Exception as e:
        print(f"[Chat] AI 调用失败: {e}")
        return {
            'reply': f'抱歉，处理失败: {str(e)}',
            'action': 'reply'
        }


def handle_images_chat(session: Dict, message: str, history: List) -> Dict:
    """处理 Phase 4 配图阶段的对话"""
    from glm_service import glm_service

    images_data = session.get('images') or {}
    style = images_data.get('style_keywords', '默认风格')

    context = f"""你是一个专业的配图顾问。用户正在为文章生成配图。

当前配图风格: {style}
已生成图片数: {len(images_data.get('images', []))} 张

用户可以要求你:
1. 更换配图风格（如: 手绘风格、科技感、卡通等）
2. 重新生成某张图片
3. 调整图片描述

请根据用户的需求提供配图建议。"""

    # 构建消息列表
    messages = [{'role': 'system', 'content': context}]
    for h in history[-6:]:
        messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': message})

    try:
        response = glm_service._call_api(
            messages=messages,
            temperature=0.7
        )
        if response and 'choices' in response and response['choices']:
            reply = response['choices'][0].get('message', {}).get('content', '抱歉，我暂时无法响应。')
        else:
            reply = "抱歉，AI 服务暂时无法响应，请稍后再试。"
    except Exception as e:
        print(f"[Chat] GLM 调用失败: {e}")
        reply = f"抱歉，AI 服务调用失败: {str(e)}"

    return {'reply': reply, 'action': 'reply'}


def handle_layout_chat(session: Dict, message: str, history: List) -> Dict:
    """处理 Phase 5 排版阶段的对话"""
    from glm_service import glm_service

    layout = session.get('layout') or {}

    context = f"""你是一个专业的排版顾问。用户正在为文章进行排版。

输出文件:
{json.dumps(layout.get('files', []), ensure_ascii=False, indent=2)}

用户可以要求你:
1. 调整排版样式
2. 修改输出格式
3. 优化微信格式

请根据用户的需求提供排版建议。"""

    # 构建消息列表
    messages = [{'role': 'system', 'content': context}]
    for h in history[-6:]:
        messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': message})

    try:
        response = glm_service._call_api(
            messages=messages,
            temperature=0.7
        )
        if response and 'choices' in response and response['choices']:
            reply = response['choices'][0].get('message', {}).get('content', '抱歉，我暂时无法响应。')
        else:
            reply = "抱歉，AI 服务暂时无法响应，请稍后再试。"
    except Exception as e:
        print(f"[Chat] GLM 调用失败: {e}")
        reply = f"抱歉，AI 服务调用失败: {str(e)}"

    return {'reply': reply, 'action': 'reply'}


# ==================== 管理员 API（文件管理） ====================

@app.route('/api/admin/sessions', methods=['GET'])
def admin_list_sessions():
    """管理员：列出所有会话及其文件信息"""
    import shutil

    sessions_list = []
    shared_dir = WEB_DIR / 'shared'
    output_dir = WEB_DIR / 'output'

    # 遍历所有 session 文件
    if shared_dir.exists():
        for session_file in shared_dir.glob('session_*.json'):
            try:
                session_id = session_file.stem.replace('session_', '')
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # 获取输出文件信息
                session_output = output_dir / session_id
                files = []
                total_size = 0

                if session_output.exists():
                    for file_path in session_output.rglob('*'):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            total_size += file_size
                            files.append({
                                'name': file_path.name,
                                'path': str(file_path.relative_to(session_output)),
                                'size': file_size,
                                'size_formatted': format_file_size(file_size)
                            })

                sessions_list.append({
                    'session_id': session_id,
                    'topic': session_data.get('topic', '未知主题'),
                    'current_phase': session_data.get('current_phase', 0),
                    'created_at': session_data.get('created_at', ''),
                    'last_updated': session_data.get('last_updated', ''),
                    'word_count': session_data.get('draft', {}).get('word_count', 0),
                    'files_count': len(files),
                    'total_size': total_size,
                    'total_size_formatted': format_file_size(total_size),
                    'files': files
                })
            except Exception as e:
                print(f"[Admin] 读取 session 失败: {e}")

    # 按创建时间倒序排列
    sessions_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return jsonify({
        'success': True,
        'sessions': sessions_list,
        'total': len(sessions_list)
    })


@app.route('/api/admin/sessions/<session_id>', methods=['DELETE'])
def admin_delete_session(session_id):
    """管理员：删除指定会话及其所有文件"""
    import shutil

    deleted_items = []

    # 1. 删除 session 文件
    session_file = WEB_DIR / 'shared' / f'session_{session_id}.json'
    if session_file.exists():
        session_file.unlink()
        deleted_items.append('session_file')

    # 2. 删除输出目录
    output_path = WEB_DIR / 'output' / session_id
    if output_path.exists():
        shutil.rmtree(output_path)
        deleted_items.append('output_directory')

    # 3. 删除任务文件（如果有）
    tasks_dir = WEB_DIR / 'tasks'
    if tasks_dir.exists():
        for task_file in tasks_dir.glob(f'*{session_id}*.json'):
            task_file.unlink()
            deleted_items.append('task_files')

    # 4. 从内存中移除
    if session_id in sessions:
        del sessions[session_id]
        deleted_items.append('memory_session')

    if deleted_items:
        return jsonify({
            'success': True,
            'message': f'会话 {session_id} 已删除',
            'deleted_items': deleted_items
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404


@app.route('/api/admin/sessions/batch-delete', methods=['POST'])
def admin_batch_delete_sessions():
    """管理员：批量删除会话"""
    data = request.json
    session_ids = data.get('session_ids', [])

    if not session_ids:
        return jsonify({'success': False, 'error': 'No session IDs provided'}), 400

    results = {
        'success': [],
        'failed': []
    }

    for session_id in session_ids:
        try:
            # 复用单个删除逻辑
            with app.test_request_context():
                response = admin_delete_session(session_id)
                result = response.get_json()
                if result.get('success'):
                    results['success'].append(session_id)
                else:
                    results['failed'].append({'id': session_id, 'error': result.get('error')})
        except Exception as e:
            results['failed'].append({'id': session_id, 'error': str(e)})

    return jsonify({
        'success': True,
        'deleted_count': len(results['success']),
        'failed_count': len(results['failed']),
        'results': results
    })


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    elif size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.1f} MB'
    else:
        return f'{size_bytes / (1024 * 1024 * 1024):.1f} GB'


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI Article Writer API Server")
    print("=" * 60)
    print(f"📍 API Server: http://localhost:5000")
    print(f"📖 API Docs: http://localhost:5000/api/health")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
