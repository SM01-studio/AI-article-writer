/**
 * AI Article Writer - API Service
 * 后端API调用服务
 */

// API 基础配置 - 支持环境变量配置
// 在生产环境中，可以通过 window.API_BASE_URL 设置后端地址
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:5000/api';

// API 调用封装
const api = {
    // 健康检查
    async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', message: error.message };
        }
    },

    // ==================== 任务队列 API ====================

    // 创建任务
    async createTask(taskType, sessionId, params = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}/task/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_type: taskType,
                    session_id: sessionId,
                    params: params
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Create task failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 获取任务状态
    async getTask(taskId) {
        try {
            const response = await fetch(`${API_BASE_URL}/task/${taskId}`);
            return await response.json();
        } catch (error) {
            console.error('Get task failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 获取最近任务
    async getRecentTasks(limit = 10) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/recent?limit=${limit}`);
            return await response.json();
        } catch (error) {
            console.error('Get recent tasks failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 轮询任务直到完成
    async pollTaskUntilComplete(taskId, onProgress, interval = 2000, maxAttempts = 60) {
        let attempts = 0;
        while (attempts < maxAttempts) {
            const result = await this.getTask(taskId);
            if (!result.success) {
                throw new Error(result.error || '获取任务状态失败');
            }

            const task = result.task;

            // 回调进度
            if (onProgress) {
                onProgress(task);
            }

            // 检查是否完成
            if (task.status === 'completed') {
                return task;
            }

            if (task.status === 'failed') {
                throw new Error(task.error || '任务失败');
            }

            // 等待后继续轮询
            await new Promise(resolve => setTimeout(resolve, interval));
            attempts++;
        }

        throw new Error('任务超时');
    },

    // ==================== 会话 API ====================

    // 创建会话
    async createSession(topic, length, audience) {
        try {
            const response = await fetch(`${API_BASE_URL}/session/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, length, audience })
            });
            return await response.json();
        } catch (error) {
            console.error('Create session failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 获取会话
    async getSession(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/session/${sessionId}`);
            return await response.json();
        } catch (error) {
            console.error('Get session failed:', error);
            return { success: false, error: error.message };
        }
    },

    // ==================== 调研 API ====================

    // 开始调研
    async startResearch(sessionId, topic, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}/research/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, topic, options })
            });
            return await response.json();
        } catch (error) {
            console.error('Start research failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交调研反馈
    async submitResearchFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/research/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit research feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // ==================== 大纲 API ====================

    // 生成大纲
    async generateOutline(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/outline/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Generate outline failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交大纲反馈
    async submitOutlineFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/outline/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit outline feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 确认大纲项目（勾选确认）
    async confirmOutlineItems(sessionId, confirmedItems) {
        try {
            const response = await fetch(`${API_BASE_URL}/outline/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    type: 'confirmation',
                    confirmed_items: confirmedItems
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Confirm outline items failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 生成初稿
    async generateDraft(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/draft/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Generate draft failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交初稿反馈
    async submitDraftFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/draft/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit draft feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 生成配图
    async generateImages(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/images/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Generate images failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 生成排版
    async generateLayout(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/layout/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Generate layout failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交排版反馈
    async submitLayoutFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/layout/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit layout feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 完成导出
    async completeExport(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/export/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Complete export failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交调研反馈
    async submitResearchFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/research/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit research feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交大纲反馈
    async submitOutlineFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/outline/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit outline feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交初稿反馈
    async submitDraftFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/draft/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit draft feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 提交排版反馈
    async submitLayoutFeedback(sessionId, feedback) {
        try {
            const response = await fetch(`${API_BASE_URL}/layout/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, feedback })
            });
            return await response.json();
        } catch (error) {
            console.error('Submit layout feedback failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 小红书搜索
    async searchXiaoHongShu(keywords, limit = 5) {
        try {
            const response = await fetch(`${API_BASE_URL}/research/xiaohongshu`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords, limit, session_id: state?.sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('XiaoHongShu search failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 微信公众号搜索
    async searchWeixin(keywords, limit = 5) {
        try {
            const response = await fetch(`${API_BASE_URL}/research/weixin`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords, limit, session_id: state?.sessionId })
            });
            return await response.json();
        } catch (error) {
            console.error('Weixin search failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 获取会话状态
    async getSession(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/session/${sessionId}`);
            return await response.json();
        } catch (error) {
            console.error('Get session failed:', error);
            return { success: false, error: error.message };
        }
    },

    // 删除会话
    async deleteSession(sessionId) {
        try {
            const response = await fetch(`${API_BASE_URL}/session/${sessionId}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (error) {
            console.error('Delete session failed:', error);
            return { success: false, error: error.message };
        }
    }
};

// 导出 API 对象
window.api = api;
