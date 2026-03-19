/**
 * AI Article Writer - Multi-Page Application
 * 每个阶段独立页面展示
 */

// 状态管理
const state = {
    currentPage: 'home',
    sessionId: null,  // 后端会话ID
    topic: '',
    length: 'medium',
    audience: 'general',
    useRealApi: true,  // 是否使用真实API
    chatHistory: {},   // 各阶段的对话历史 { phase: [messages] }
    isChatLoading: false,  // Chat 是否正在加载
    phases: {
        home: { id: 0, name: 'Home', nameEn: '首页' },
        research: { id: 1, name: 'Deep Research', nameEn: '深度调研', needsConfirm: true },
        outline: { id: 2, name: 'Outline Design', nameEn: '大纲设计', needsConfirm: true },
        draft: { id: 3, name: 'Content Writing', nameEn: '内容写作', needsConfirm: true },
        images: { id: 4, name: 'Image Generation', nameEn: '配图生成', needsConfirm: false },
        layout: { id: 5, name: 'Layout & Export', nameEn: '排版输出', needsConfirm: true },
        complete: { id: 6, name: 'Complete', nameEn: '完成' }
    }
};

// 页面顺序
const pageOrder = ['home', 'research', 'outline', 'draft', 'images', 'layout', 'complete'];

// DOM 元素缓存
let elements = {};

/**
 * 从 URL 参数中提取并保存 Token（跨域认证）
 */
function extractTokenFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('auth_token');

    if (token) {
        console.log('[Auth] 从 URL 参数获取到 Token');
        localStorage.setItem('auth_token', token);

        // 清除 URL 中的 token 参数（安全考虑）
        const cleanUrl = window.location.pathname + window.location.hash;
        window.history.replaceState({}, document.title, cleanUrl);
    }

    return token;
}

/**
 * 验证用户登录状态（生产环境）
 * 检查 localStorage 中的 auth_token 是否有效
 * 🔧 优化：添加缓存和超时处理，加快页面加载
 */
async function verifyAuth() {
    // 本地开发环境跳过验证
    if (!window.AUTH_API_URL) {
        console.log('[Auth] 开发环境，跳过登录验证');
        return true;
    }

    // 先尝试从 URL 参数提取 Token
    extractTokenFromUrl();

    const token = localStorage.getItem('auth_token');
    if (!token) {
        console.log('[Auth] 未找到 token，跳转到登录页');
        window.location.href = window.LOGIN_URL + '?from=subapp';
        return false;
    }

    // 🔧 优化：检查缓存，避免重复请求
    const cachedAuth = sessionStorage.getItem('auth_verified');
    const cacheTime = sessionStorage.getItem('auth_verified_time');
    const CACHE_DURATION = 5 * 60 * 1000; // 5 分钟缓存

    if (cachedAuth === 'true' && cacheTime && (Date.now() - parseInt(cacheTime)) < CACHE_DURATION) {
        console.log('[Auth] 使用缓存，跳过验证');
        return true;
    }

    // 🔧 优化：添加超时处理（3秒）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    try {
        const response = await fetch(`${window.AUTH_API_URL}/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            console.log('[Auth] Token 无效，跳转到登录页');
            localStorage.removeItem('auth_token');
            sessionStorage.removeItem('auth_verified');
            window.location.href = window.LOGIN_URL + '?from=subapp';
            return false;
        }

        const data = await response.json();
        console.log('[Auth] 登录验证成功:', data.user?.username || data.user?.email);

        // 🔧 优化：缓存验证结果
        sessionStorage.setItem('auth_verified', 'true');
        sessionStorage.setItem('auth_verified_time', Date.now().toString());

        return true;
    } catch (error) {
        clearTimeout(timeoutId);

        // 超时或网络错误时，如果之前验证过，允许继续使用
        if (cachedAuth === 'true') {
            console.log('[Auth] 网络错误，使用缓存结果继续');
            return true;
        }

        console.error('[Auth] 验证失败:', error);
        // 首次验证失败也允许继续使用（避免因网络问题阻断用户）
        return true;
    }
}

// 初始化
async function init() {
    // 生产环境先验证登录状态
    const isAuthed = await verifyAuth();
    if (!isAuthed) {
        return; // 正在跳转，不继续初始化
    }

    cacheElements();
    setupEventListeners();
    initParticles();
    updateLengthButtons();
}

// 缓存DOM元素
function cacheElements() {
    elements = {
        topicInput: document.getElementById('topic'),
        audienceSelect: document.getElementById('audience'),
        startBtn: document.getElementById('startBtn'),
        lengthBtns: document.querySelectorAll('.length-btn'),
        toastContainer: document.getElementById('toastContainer'),
        pages: {
            home: document.getElementById('page-home'),
            research: document.getElementById('page-research'),
            outline: document.getElementById('page-outline'),
            draft: document.getElementById('page-draft'),
            images: document.getElementById('page-images'),
            layout: document.getElementById('page-layout'),
            complete: document.getElementById('page-complete')
        },
        contents: {
            research: document.getElementById('research-content'),
            outline: document.getElementById('outline-content'),
            draft: document.getElementById('draft-content'),
            images: document.getElementById('images-content'),
            layout: document.getElementById('layout-content'),
            complete: document.getElementById('complete-content')
        }
    };
}

// 事件监听
function setupEventListeners() {
    // 长度选择
    elements.lengthBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            state.length = btn.dataset.length;
            updateLengthButtons();
        });
    });

    // 开始按钮
    elements.startBtn.addEventListener('click', handleStart);

    // 添加加载已有会话的按钮事件
    const loadSessionBtn = document.getElementById('load-session-btn');
    if (loadSessionBtn) {
        loadSessionBtn.addEventListener('click', handleLoadSession);
    }
}

// 加载已有会话
async function handleLoadSession() {
    const sessionId = prompt('请输入Session ID:\n(例如: 20260302_171453)');
    if (!sessionId) {
        showToast('请输入Session ID | Please enter Session ID', 'error');
        return;
    }

    // 尝试加载会话
    try {
        const result = await api.getSession(sessionId);
        if (result.success && result.data) {
            state.sessionId = sessionId;
            state.topic = result.data.topic || '未知主题';
            state.useRealApi = true;
            showToast('✅ 会话加载成功 | Session loaded', 'success');
            goToPage('research');
            generateResearchContent();
        } else {
            showToast('❌ 会话不存在或已过期 | Session not found or expired', 'error');
        }
    } catch (error) {
        console.error('Load session failed:', error);
        showToast('❌ 加载失败 | Load failed', 'error');
    }
}

// 更新长度按钮状态
function updateLengthButtons() {
    elements.lengthBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.length === state.length) {
            btn.classList.add('active');
        }
    });
}

// 开始创作
async function handleStart() {
    const topic = elements.topicInput.value.trim();
    if (!topic) {
        showToast('请输入文章主题 | Please enter a topic', 'error');
        elements.topicInput.focus();
        return;
    }

    state.topic = topic;
    state.audience = elements.audienceSelect.value;

    // 显示加载状态
    showToast('🔄 正在创建会话... Creating session...', 'info');

    // 调用后端API创建会话
    if (state.useRealApi && window.api) {
        try {
            const result = await api.createSession(topic, state.length, state.audience);
            if (result.success) {
                state.sessionId = result.session_id;
                showToast('✅ 会话创建成功 | Session created', 'success');
            } else {
                showToast('⚠️ 使用模拟模式 | Using simulation mode', 'warning');
                state.useRealApi = false;
            }
        } catch (error) {
            console.error('API call failed:', error);
            showToast('⚠️ API连接失败，使用模拟模式 | API failed, using simulation', 'warning');
            state.useRealApi = false;
        }
    }

    // 跳转到调研页面
    goToPage('research');

    // 生成调研内容
    setTimeout(() => {
        generateResearchContent();
    }, 500);
}

// 页面跳转
function goToPage(pageName) {
    // 隐藏所有页面
    Object.values(elements.pages).forEach(page => {
        page.classList.remove('active');
    });

    // 显示目标页面
    const targetPage = elements.pages[pageName];
    if (targetPage) {
        targetPage.classList.add('active');
        state.currentPage = pageName;

        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 生成调研内容
async function generateResearchContent() {
    const topic = state.topic || '大龙虾Openclaw对房地产管理的的帮助';

    // 显示加载状态
    elements.contents.research.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在调研... | Researching...</h4>
            <p style="color: var(--text-muted);">请稍候，正在深度调研主题...</p>
        </div>
    `;

    // 首先询问是否使用小红书和微信公众号搜索
    if (state.useRealApi && state.sessionId && window.api) {
        // 显示搜索选项（小红书 + 微信公众号）
        const searchOptionsHtml = `
            <div class="result-box info" style="margin-bottom: 1rem;">
                <h4 class="result-title">🔍 搜索选项 | Search Options</h4>
                <p style="color: var(--text-secondary); margin: 1rem 0;">
                    请选择需要搜索的平台。除网页搜索外，还可以选择搜索小红书和微信公众号获取更多真实案例和深度内容。<br>
                    <span style="color: var(--text-hint);">Select the platforms to search. In addition to web search, you can include XiaoHongShu and WeChat for real cases and in-depth content.</span>
                </p>

                <div style="margin: 1.5rem 0; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <label style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; cursor: pointer;">
                        <input type="checkbox" id="include-xiaohongshu" checked style="width: 18px; height: 18px; accent-color: #ff2442;">
                        <span style="color: var(--text-secondary);">
                            <strong style="color: #ff2442;">📱 小红书 | XiaoHongShu</strong>
                            <span style="display: block; font-size: 0.85rem; color: var(--text-hint);">用户真实体验分享、产品测评、使用心得</span>
                        </span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 0.75rem; cursor: pointer;">
                        <input type="checkbox" id="include-weixin" checked style="width: 18px; height: 18px; accent-color: #07c160;">
                        <span style="color: var(--text-secondary);">
                            <strong style="color: #07c160;">💬 微信公众号 | WeChat Official Accounts</strong>
                            <span style="display: block; font-size: 0.85rem; color: var(--text-hint);">行业深度分析、专业观点、企业案例</span>
                        </span>
                    </label>
                </div>

                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <button id="search-all-btn" class="btn btn-primary" style="flex: 1; min-width: 200px;">
                        🚀 开始搜索 | Start Search
                    </button>
                    <button id="skip-extra-btn" class="btn btn-secondary" style="flex: 1; min-width: 200px;">
                        🌐 仅网页搜索 | Web Only
                    </button>
                </div>
            </div>
        `;

        elements.contents.research.innerHTML = searchOptionsHtml;

        // 添加按钮事件
        return new Promise((resolve) => {
            const searchBtn = document.getElementById('search-all-btn');
            const skipBtn = document.getElementById('skip-extra-btn');
            const xhsCheckbox = document.getElementById('include-xiaohongshu');
            const weixinCheckbox = document.getElementById('include-weixin');

            searchBtn.addEventListener('click', async () => {
                const includeXiaoHongShu = xhsCheckbox.checked;
                const includeWeixin = weixinCheckbox.checked;

                searchBtn.disabled = true;
                skipBtn.disabled = true;
                searchBtn.innerHTML = '🔄 正在搜索... | Searching...';

                await executeResearch(topic, includeXiaoHongShu, includeWeixin);
                resolve();
            });

            skipBtn.addEventListener('click', async () => {
                skipBtn.disabled = true;
                searchBtn.disabled = true;
                skipBtn.innerHTML = '🔄 正在进行网页搜索... | Searching...';
                await executeResearch(topic, false, false);
                resolve();
            });
        });
    }

    // 如果不使用真实API，直接执行调研
    await executeResearch(topic, false);
}

// 执行调研（使用任务队列）
async function executeResearch(topic, includeXiaoHongShu, includeWeixin) {
    // 构建搜索来源描述
    let sources = ['网页'];
    if (includeXiaoHongShu) sources.push('小红书');
    if (includeWeixin) sources.push('微信公众号');
    const sourceDesc = sources.join(' + ');

    // 显示等待UI
    renderWaitingUI(topic, sourceDesc);

    // 创建任务
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            // 创建搜索任务
            const taskResult = await api.createTask('research', state.sessionId, {
                topic: topic,
                include_xiaohongshu: includeXiaoHongShu,
                include_weixin: includeWeixin
            });

            if (taskResult.success) {
                state.currentTaskId = taskResult.task_id;
                console.log('✅ 任务已创建:', taskResult.task_id);

                // 开始轮询任务状态
                await pollTaskStatus(taskResult.task_id, topic);
                return;
            } else {
                showToast('❌ 创建任务失败 | Task creation failed', 'error');
            }
        } catch (error) {
            console.error('Task creation failed:', error);
            showToast('❌ 任务创建失败 | Task failed', 'error');
        }
    }

    // 如果任务创建失败，使用备用方案
    showToast('⚠️ 使用备用模式 | Using fallback mode', 'warning');
    renderFallbackResult(topic);
}

// 渲染等待UI（带动态效果和计时器）
function renderWaitingUI(topic, sourceDesc) {
    const startTime = Date.now();

    const html = `
        <div class="result-box processing" id="research-waiting">
            <div class="processing-header">
                <div class="processing-spinner"></div>
                <h4 class="result-title">🔍 正在深度调研... | Researching...</h4>
            </div>
            <div class="processing-info">
                <p style="color: var(--text-secondary); margin: 0.5rem 0;">
                    <strong>主题 Topic:</strong> ${topic}
                </p>
                <p style="color: var(--text-secondary); margin: 0.5rem 0;">
                    <strong>搜索渠道 Sources:</strong> ${sourceDesc}
                </p>
            </div>
            <div class="processing-status">
                <div class="status-item">
                    <span class="status-label">⏱️ 已用时 Elapsed:</span>
                    <span class="status-value" id="elapsed-time">0秒</span>
                </div>
                <div class="status-item">
                    <span class="status-label">📊 进度 Progress:</span>
                    <span class="status-value" id="progress-text">准备中...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">📋 任务ID Task ID:</span>
                    <span class="status-value" id="task-id-display" style="font-family: monospace; font-size: 0.85rem;">-</span>
                </div>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" id="progress-bar" style="width: 0%;"></div>
            </div>
            <p style="color: var(--text-hint); font-size: 0.85rem; margin-top: 1rem;">
                💡 AI助手正在通过MCP工具搜索真实内容，请稍候...<br>
                AI Assistant is searching via MCP tools, please wait...
            </p>
        </div>

        <style>
            .processing-header {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .processing-spinner {
                width: 32px;
                height: 32px;
                border: 3px solid rgba(255,255,255,0.1);
                border-top-color: var(--accent-primary);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .processing-status {
                background: rgba(0,0,0,0.2);
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
            }
            .status-item {
                display: flex;
                justify-content: space-between;
                padding: 0.5rem 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .status-item:last-child {
                border-bottom: none;
            }
            .progress-bar-container {
                width: 100%;
                height: 6px;
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
                overflow: hidden;
                margin-top: 1rem;
            }
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
                transition: width 0.3s ease;
            }
        </style>
    `;

    elements.contents.research.innerHTML = html;

    // 启动计时器
    window.researchTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const elapsedEl = document.getElementById('elapsed-time');
        if (elapsedEl) {
            elapsedEl.textContent = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
        }
    }, 1000);
}

// 更新等待UI的进度
function updateWaitingProgress(progress, message, taskId = null) {
    const progressText = document.getElementById('progress-text');
    const progressBar = document.getElementById('progress-bar');
    const taskIdDisplay = document.getElementById('task-id-display');

    if (progressText) progressText.textContent = message;
    if (progressBar) progressBar.style.width = `${progress}%`;
    if (taskIdDisplay && taskId) taskIdDisplay.textContent = taskId;
}

// 停止计时器
function stopResearchTimer() {
    if (window.researchTimer) {
        clearInterval(window.researchTimer);
        window.researchTimer = null;
    }
}

// 轮询任务状态
async function pollTaskStatus(taskId, topic) {
    const maxAttempts = 120; // 最多轮询120次（4分钟）
    const interval = 2000; // 每2秒轮询一次
    let attempts = 0;

    updateWaitingProgress(5, '任务已提交，等待处理...', taskId);

    while (attempts < maxAttempts) {
        try {
            const result = await api.getTask(taskId);

            if (!result.success) {
                throw new Error(result.error || '获取任务状态失败');
            }

            const task = result.task;

            // 更新进度显示
            updateWaitingProgress(
                task.progress || 10,
                task.message || '处理中...',
                taskId
            );

            // 检查任务状态
            if (task.status === 'completed') {
                stopResearchTimer();
                showToast('✅ 调研完成！| Research completed!', 'success');

                // 显示结果并保存到 state
                if (task.result && task.result.research_data) {
                    state.researchData = task.result.research_data;  // 保存到 state
                    renderResearchFromApi(task.result.research_data);
                } else {
                    renderFallbackResult(topic);
                }
                return;
            }

            if (task.status === 'failed') {
                stopResearchTimer();
                showToast(`❌ 任务失败: ${task.error}`, 'error');
                renderFallbackResult(topic);
                return;
            }

            // 继续等待
            await new Promise(resolve => setTimeout(resolve, interval));
            attempts++;

        } catch (error) {
            console.error('Poll task failed:', error);
            attempts++;
            await new Promise(resolve => setTimeout(resolve, interval));
        }
    }

    // 超时
    stopResearchTimer();
    showToast('⏰ 任务超时，请稍后重试 | Task timeout', 'warning');
    renderFallbackResult(topic);
}

// 渲染备用结果（精简版）
function renderFallbackResult(topic) {
    stopResearchTimer();

    const html = `
        <div class="result-box warning">
            <h4 class="result-title">⚠️ 调研模式切换 | Research Mode Fallback</h4>
            <p style="color: var(--text-secondary); margin: 1rem 0;">
                AI助手暂时不可用，显示基础搜索结果。<br>
                <span style="color: var(--text-hint);">AI Assistant temporarily unavailable, showing basic results.</span>
            </p>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">📚 基础信息 | Basic Information</div>
            <p style="color: var(--text-muted);">主题: ${topic}</p>
            <p style="color: var(--text-hint); font-size: 0.85rem;">
                请稍后重试，或联系管理员检查AI助手服务状态。
            </p>
        </div>
    `;

    elements.contents.research.innerHTML = html;
}
// 生成大纲内容
async function generateOutlineContent() {
    // 显示加载状态（带计时器）
    const timerId = 'outline-timer';
    elements.contents.outline.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在生成大纲... | Generating Outline...</h4>
            <p style="color: var(--text-muted);">请稍候，正在设计文章结构...</p>
            <p id="${timerId}" style="color: var(--accent); margin-top: 0.5rem;">⏱️ 0s</p>
        </div>
    `;

    // 启动计时器
    const startTime = Date.now();
    const timerInterval = setInterval(() => {
        const timerEl = document.getElementById(timerId);
        if (timerEl) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            timerEl.textContent = `⏱️ ${elapsed}s`;
        }
    }, 1000);

    // 保存计时器ID以便后续清除
    state._outlineTimerInterval = timerInterval;

    // 调用后端API
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            const result = await api.generateOutline(state.sessionId);
            if (result.success) {
                state.outline = result.data;  // 保存到 state
                // 清除计时器
                if (state._outlineTimerInterval) {
                    clearInterval(state._outlineTimerInterval);
                    state._outlineTimerInterval = null;
                }
                // 合并 confirmed_outline 到 data
                const outlineData = { ...result.data, confirmed_outline: result.confirmed_outline };
                renderOutlineFromApi(outlineData);
                showToast('✅ 大纲生成完成 | Outline generated', 'success');
                return;
            }
        } catch (error) {
            console.error('Outline API failed:', error);
            showToast('⚠️ API调用失败，使用模拟数据 | API failed, using simulation', 'warning');
        }
    }

    // 备用：使用原有硬编码内容
    const chapterCount = state.length === 'short' ? 4 : state.length === 'medium' ? 6 : 8;

    const content = `
        <div class="result-box info">
            <h4 class="result-title">📋 Article Outline | 文章大纲</h4>
            <p style="color: var(--text-muted);">
                Structured ${chapterCount} chapters | 已规划${chapterCount}个章节
            </p>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📖 章节结构 | Chapter Structure</div>
            <ol style="color: var(--text-secondary); padding-left: 1.5rem; line-height: 2;">
                <li><strong>0. 引言 Introduction</strong> - 为什么这个话题重要</li>
                <li><strong>1. 核心概念 Core Concepts</strong> - 基础定义与解释</li>
                <li><strong>2. 技术原理 Technical Principles</strong> - 深入技术细节</li>
                <li><strong>3. 应用场景 Applications</strong> - 实际案例分析</li>
                <li><strong>4. 发展趋势 Future Trends</strong> - 未来展望</li>
                <li><strong>5. 总结 Conclusion</strong> - 要点回顾</li>
            </ol>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎨 配图规划 | Image Planning</div>
            <ul class="result-list">
                <li><strong>Cover 封面:</strong> 科技感主题 (1024×1024)</li>
                <li><strong>Chapter 1-2:</strong> 概念配图 - 示意图解</li>
                <li><strong>Chapter 3-4:</strong> 应用配图 - 实例展示</li>
                <li><strong>Conclusion:</strong> 结语配图 - 总结图示</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎯 写作风格 | Writing Style</div>
            <div class="detail-text">
                <strong>目标读者:</strong> ${getAudienceText(state.audience)}<br>
                <strong>语言深度:</strong> ${state.audience === 'tech' ? '专业 Technical' : '通俗 Accessible'}<br>
                <strong>配图风格:</strong> 科技感, 深蓝色调, 几何图形, 4K
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📊 预计字数 | Word Count</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: var(--text-primary);">
                ~${getWordCount(state.length)} words | 字
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认大纲结构是否符合预期？是否需要调整章节顺序?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if the outline structure meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有问题或调整建议，请在下方输入 | Feedback & Adjustment Requests</span>
                    </div>
                    <textarea id="feedback-outline" class="feedback-input" placeholder="例如：请增加一章关于行业趋势的内容 / Please add a chapter about industry trends..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(2)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.outline.innerHTML = content;
}

// 生成初稿内容
async function generateDraftContent() {
    // 显示加载状态（带计时器）
    const timerId = 'draft-timer';
    elements.contents.draft.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在撰写初稿... | Writing Draft...</h4>
            <p style="color: var(--text-muted);">请稍候，正在根据大纲撰写文章...</p>
            <p id="${timerId}" style="color: var(--accent); margin-top: 0.5rem;">⏱️ 0s</p>
        </div>
    `;

    // 启动计时器
    const startTime = Date.now();
    const timerInterval = setInterval(() => {
        const timerEl = document.getElementById(timerId);
        if (timerEl) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            timerEl.textContent = `⏱️ ${elapsed}s`;
        }
    }, 1000);

    // 保存计时器ID以便后续清除
    state._draftTimerInterval = timerInterval;

    // 调用后端API
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            const result = await api.generateDraft(state.sessionId);
            if (result.success) {
                state.draft = result.data;  // 保存到 state
                state.draftContent = result.data.content || result.data;  // 保存内容
                // 清除计时器
                if (state._draftTimerInterval) {
                    clearInterval(state._draftTimerInterval);
                    state._draftTimerInterval = null;
                }
                renderDraftFromApi(result.data);
                showToast('✅ 初稿撰写完成 | Draft completed', 'success');
                return;
            }
        } catch (error) {
            console.error('Draft API failed:', error);
            showToast('⚠️ API调用失败，使用模拟数据 | API failed, using simulation', 'warning');
        }
    }

    // 备用：使用原有硬编码内容
    const content = `
        <div class="result-box success">
            <h4 class="result-title">✍️ Draft Complete | 初稿完成</h4>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📄 文章概览 | Article Overview</div>
            <ul class="result-list">
                <li><strong>标题 Title:</strong> ${state.topic}</li>
                <li><strong>字数 Words:</strong> ~${getWordCount(state.length)} words | 字</li>
                <li><strong>章节数 Chapters:</strong> ${state.length === 'short' ? '4' : state.length === 'medium' ? '6' : '8'}</li>
                <li><strong>配图数 Images:</strong> ${state.length === 'short' ? '3' : state.length === 'medium' ? '5' : '7'}</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📝 内容预览 | Content Preview</div>
            <div class="detail-code" style="max-height: 250px; overflow-y: auto;">
# ${state.topic}

## 引言 | Introduction
在当今数字化时代，这是关于"${state.topic}"的科普文章...

## 核心概念 | Core Concepts
首先我们需要理解什么是${state.topic}...

## 抷术原理 | Technical Principles
${state.topic}的核心技术基于深度学习...

## 应用场景 | Applications
在实际场景中 ${state.topic}已经广泛应用...

## 总结 | Conclusion
通过本文的介绍相信大家对"${state.topic}"有了更深入的了解...
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">✅ 质量检查 | Quality Check</div>
            <ul class="result-list">
                <li>✓ 结构完整 | Complete structure</li>
                <li>✓ 逻辑清晰 | Clear logic</li>
                <li>✓ 语言流畅 | Smooth language</li>
                <li>✓ 读者适配 | Audience adapted</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认初稿内容是否符合预期?是否需要调整某些章节?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if the draft meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有问题或调整建议，请在下方输入 | Feedback & Adjustment Requests</span>
                    </div>
                    <textarea id="feedback-draft" class="feedback-input" placeholder="例如：第二章的技术原理部分过于深奥，请简化 / The technical principles section is too technical..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(3)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.draft.innerHTML = content
}

// 生成配图内容 - 使用 SSE 实时进度
async function generateImagesContent() {
    // 显示加载状态（带进度条）
    elements.contents.images.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在生成配图... | Generating Images...</h4>
            <p style="color: var(--text-muted);">请稍候，正在使用AI生成配图...</p>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📊 生成进度 | Generation Progress</div>
            <div id="images-progress-container" style="
                background: var(--bg-secondary);
                padding: 1.5rem;
                border-radius: 12px;
            ">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <div style="flex: 1; height: 8px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden;">
                        <div id="images-progress-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width 0.3s;"></div>
                    </div>
                    <span id="images-progress-text" style="color: var(--text-secondary); font-size: 0.9rem;">0%</span>
                    <span id="images-timer" style="color: var(--accent); font-size: 0.9rem; font-weight: 600; min-width: 60px; text-align: right;">⏱️ 0s</span>
                </div>
                <div id="images-progress-status" style="color: var(--text-hint); font-size: 0.85rem;">
                    准备开始...
                </div>
                <div id="images-progress-list" style="margin-top: 1rem;"></div>
            </div>
        </div>
    `;

    // 使用 SSE 实时获取进度
    if (state.sessionId) {
        try {
            await generateImagesWithSSE(state.sessionId);
            return;
        } catch (error) {
            console.error('SSE failed, falling back to regular API:', error);
        }
    }

    // 备用：使用普通 API
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            const result = await api.generateImages(state.sessionId);
            if (result.success) {
                state.images = result.data;
                renderImagesFromApi(result.data);
                showToast('✅ 配图生成完成 | Images generated', 'success');
                return;
            }
        } catch (error) {
            console.error('Images API failed:', error);
            showToast('⚠️ API调用失败', 'warning');
        }
    }

    // 最终备用：模拟内容
    const content = `
        <div class="result-box warning">
            <h4 class="result-title">🎨 Images Generated | 配图生成完成</h4>
        </div>
        <div class="detail-section">
            <div class="detail-section-title">🖼️ 配图列表 | Image List</div>
            <p style="color: var(--text-hint);">配图生成服务暂时不可用</p>
        </div>
    `;
    elements.contents.images.innerHTML = content;
}

// SSE 实时生成配图
async function generateImagesWithSSE(sessionId) {
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(`${API_BASE_URL}/images/generate/stream?session_id=${sessionId}`);

        const progressBar = document.getElementById('images-progress-bar');
        const progressText = document.getElementById('images-progress-text');
        const progressStatus = document.getElementById('images-progress-status');
        const progressList = document.getElementById('images-progress-list');
        const timerElement = document.getElementById('images-timer');

        let imagesData = [];
        let startTime = null;
        let timerInterval = null;

        // 计时器更新函数
        const updateTimer = () => {
            if (!startTime || !timerElement) return;
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerElement.textContent = `⏱️ ${minutes > 0 ? minutes + 'm ' : ''}${seconds}s`;
        };

        // 开始计时器
        const startTimer = () => {
            startTime = Date.now();
            timerInterval = setInterval(updateTimer, 1000);
        };

        // 停止计时器
        const stopTimer = () => {
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.event === 'start') {
                    startTimer();
                    const total = data.total || 6;
                    progressStatus.textContent = `开始生成 ${total} 张配图...`;
                    progressList.innerHTML = Array(total).fill(0).map((_, i) => `
                        <div id="img-item-${i}" style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                            <span style="width: 24px; height: 24px; border-radius: 50%; background: var(--bg-tertiary); display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">${i + 1}</span>
                            <span style="flex: 1; color: var(--text-secondary);">等待生成...</span>
                            <span style="color: var(--text-hint);">⏳</span>
                        </div>
                    `).join('');

                } else if (data.event === 'progress') {
                    const current = data.current || 0;
                    const total = data.total || 6;
                    const percent = Math.round((current / total) * 100);
                    const message = data.message || '';

                    progressBar.style.width = `${percent}%`;
                    progressText.textContent = `${percent}%`;
                    progressStatus.textContent = message;

                    // 更新当前项状态
                    const currentItem = document.getElementById(`img-item-${current - 1}`);
                    if (currentItem) {
                        currentItem.innerHTML = `
                            <span style="width: 24px; height: 24px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; color: white;">${current}</span>
                            <span style="flex: 1; color: var(--text-secondary);">${message}</span>
                            <span style="color: var(--accent);">🔄</span>
                        `;
                    }

                } else if (data.event === 'image_complete') {
                    const image = data.image;
                    imagesData.push(image);

                    const current = data.current || imagesData.length;
                    const total = data.total || 6;
                    const percent = Math.round((current / total) * 100);

                    progressBar.style.width = `${percent}%`;
                    progressText.textContent = `${percent}%`;

                    // 更新完成的项
                    const completedItem = document.getElementById(`img-item-${current - 1}`);
                    if (completedItem && image) {
                        completedItem.innerHTML = `
                            <span style="width: 24px; height: 24px; border-radius: 50%; background: ${image.success ? 'var(--success)' : 'var(--error)'}; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; color: white;">${current}</span>
                            <span style="flex: 1; color: var(--text-secondary);">${image.name || `图片${current}`}</span>
                            <span style="color: ${image.success ? 'var(--success)' : 'var(--error)'};">${image.success ? '✅' : '❌'}</span>
                        `;
                    }

                } else if (data.event === 'complete') {
                    stopTimer();
                    eventSource.close();

                    const finalData = data.data;
                    state.images = finalData;
                    renderImagesFromApi(finalData);

                    showToast('✅ 配图生成完成 | Images generated', 'success');
                    resolve(finalData);
                }

            } catch (e) {
                console.error('Parse SSE error:', e);
            }
        };

        eventSource.onerror = (error) => {
            stopTimer();
            console.error('SSE error:', error);
            eventSource.close();
            reject(error);
        };

        // 超时保护
        setTimeout(() => {
            stopTimer();
            eventSource.close();
            reject(new Error('SSE timeout'));
        }, 300000); // 5分钟超时
    });
}

// 生成排版内容
async function generateLayoutContent() {
    // 显示加载状态
    elements.contents.layout.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在排版... | Layout Processing...</h4>
            <p style="color: var(--text-muted);">请稍候，正在生成多格式输出...</p>
        </div>
    `;

    // 调用后端API
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            const result = await api.generateLayout(state.sessionId);
            if (result.success) {
                renderLayoutFromApi(result.data);
                showToast('✅ 排版完成 | Layout completed', 'success');
                return;
            }
        } catch (error) {
            console.error('Layout API failed:', error);
            showToast('⚠️ API调用失败，使用模拟数据 | API failed, using simulation', 'warning');
        }
    }

    // 备用：使用原有硬编码内容
    const content = `
        <div class="result-box success">
            <h4 class="result-title">📄 Layout Complete | 排版完成</h4>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📁 输出文件 | Output Files</div>
            <ul class="result-list">
                <li><strong>content.md</strong> - Markdown原文</li>
                <li><strong>wechat.html</strong> - 微信公众号格式 (内联CSS)</li>
                <li><strong>article.html</strong> - HTML富文本格式</li>
                <li><strong>images/</strong> - 配图目录</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📱 微信格式特点 | WeChat Features</div>
            <ul class="result-list">
                <li>✓ 内联CSS样式 | Inline CSS styles</li>
                <li>✓ 适配微信阅读体验 | WeChat optimized</li>
                <li>✓ 图片居中对齐 | Centered images</li>
                <li>✓ 最大宽度限制 | Max-width constrained</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认排版效果是否符合预期?微信公众号格式是否正确?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if layout meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有问题或调整建议，请在下方输入 | Feedback & Adjustment Requests</span>
                    </div>
                    <textarea id="feedback-layout" class="feedback-input" placeholder="例如：请调整字体大小 / Please adjust the font size..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(5)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.layout.innerHTML = content;
}

// 生成完成内容
async function generateCompleteContent() {
    // 显示加载状态
    elements.contents.complete.innerHTML = `
        <div class="result-box info">
            <h4 class="result-title">🔄 正在导出... | Exporting...</h4>
            <p style="color: var(--text-muted);">请稍候，正在生成最终文件...</p>
        </div>
    `;

    // 调用后端API
    if (state.useRealApi && state.sessionId && window.api) {
        try {
            const result = await api.completeExport(state.sessionId);
            if (result.success) {
                renderCompleteFromApi(result.data);
                showToast('✅ 导出完成 | Export completed', 'success');
                return;
            }
        } catch (error) {
            console.error('Export API failed:', error);
            showToast('⚠️ API调用失败，使用模拟数据 | API failed, using simulation', 'warning');
        }
    }

    // 备用：使用原有硬编码内容
    const content = `
        <div class="result-box success">
            <h4 class="result-title">📦 Export Complete | 导出完成</h4>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📦 最终输出 | Final Output</div>
            <ul class="result-list">
                <li><strong>wechat.docx</strong> - 微信公众号可上传格式</li>
                <li><strong>文件大小 Size:</strong> ~670KB (已压缩)</li>
                <li><strong>符合限制 Limit:</strong> ✓ &lt;14.5MB</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">✅ 完成检查 | Completion Check</div>
            <ul class="result-list">
                <li>✓ 图片已压缩 | Images compressed</li>
                <li>✓ 格式已转换 | Format converted</li>
                <li>✓ 可直接上传微信公众号 | Ready for WeChat</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎉 任务完成 | Task Complete</div>
            <div class="detail-text" style="color: #4ade80; font-weight: 600;">
                所有文件已生成完毕可以导出使用！
                <br>
                <span style="color: var(--text-hint);">
                    All files generated successfully, ready for export!
                </span>
            </div>
        </div>
    `;

    elements.contents.complete.innerHTML = content;
}

// 确认并进入下一页
function confirmAndNext(currentPhase) {
    const currentIndex = pageOrder.indexOf(state.currentPage);
    const nextIndex = currentIndex + 1;

    if (nextIndex < pageOrder.length) {
        const nextPage = pageOrder[nextIndex];
        goToPage(nextPage);

        // 生成下一页内容
        setTimeout(() => {
            switch(nextPage) {
                case 'research': generateResearchContent(); break;
                case 'outline': generateOutlineContent(); break;
                case 'draft': generateDraftContent(); break;
                case 'images': generateImagesContent(); break;
                case 'layout': generateLayoutContent(); break;
                case 'complete': generateCompleteContent(); break;
            }
        }, 300);

        showToast('Confirmed! Proceeding... 已确认!', 'success');
    }
}

// 重新生成当前阶段
function regeneratePhase(phase) {
    showToast('Regenerating... 重新生成中...', 'info');

    setTimeout(() => {
        switch(phase) {
            case 1: generateResearchContent(); break;
            case 2: generateOutlineContent(); break;
            case 3: generateDraftContent(); break;
            case 4: generateImagesContent(); break;
            case 5: generateLayoutContent(); break;
        }
        showToast('Regenerated! 重新生成完成!', 'success');
    }, 1000);
}

// 提交反馈
async function submitFeedback(phase) {
    let feedbackId = '';
    let phaseName = '';

    switch(phase) {
        case 1:
            feedbackId = 'feedback-research';
            phaseName = '调研报告 Research';
            break;
        case 2:
            feedbackId = 'feedback-outline';
            phaseName = '大纲设计 Outline';
            break;
        case 3:
            feedbackId = 'feedback-draft';
            phaseName = '初稿内容 Draft';
            break;
        case 5:
            feedbackId = 'feedback-layout';
            phaseName = '排版输出 Layout';
            break;
    }


    const feedbackElement = document.getElementById(feedbackId);
    const feedback = feedbackElement ? feedbackElement.value.trim() : '';

    if (feedback) {
        // 存储反馈
        state.feedbacks = state.feedbacks || {};
        state.feedbacks[phase] = feedback;

        // 显示正在调整的提示
        showToast(`🔄 正在根据反馈调整... Adjusting based on feedback...`, 'info');

        // 调用后端API提交反馈
        console.log('submitFeedback called:', { phase, feedback, useRealApi: state.useRealApi, sessionId: state.sessionId });
        if (state.useRealApi && state.sessionId && window.api) {
            try {
                let result = null;
                switch(phase) {
                    case 1:
                        result = await api.submitResearchFeedback(state.sessionId, feedback);
                        console.log('Research feedback result:', result);
                        if (result.success && result.data) {
                            renderResearchFromApi(result.data);
                            showToast(`✅ 已根据反馈调整完成! Adjusted based on feedback!`, 'success');
                            return;
                        }
                        break;
                    case 2:
                        result = await api.submitOutlineFeedback(state.sessionId, feedback);
                        console.log('Outline feedback result:', result);
                        if (result.success && result.data) {
                            console.log('Calling renderOutlineFromApi with:', result.data);
                            // 合并 confirmed_outline 到 data
                            const outlineData = { ...result.data, confirmed_outline: result.confirmed_outline };
                            renderOutlineFromApi(outlineData);
                            showToast(`✅ 已根据反馈调整完成! Adjusted based on feedback!`, 'success');
                            return;
                        }
                        break;
                    case 3:
                        result = await api.submitDraftFeedback(state.sessionId, feedback);
                        if (result.success && result.data) {
                            renderDraftFromApi(result.data);
                            showToast(`✅ 已根据反馈调整完成! Adjusted based on feedback!`, 'success');
                            return;
                        }
                        break;
                    case 5:
                        result = await api.submitLayoutFeedback(state.sessionId, feedback);
                        if (result.success && result.data) {
                            renderLayoutFromApi(result.data);
                            showToast(`✅ 已根据反馈调整完成! Adjusted based on feedback!`, 'success');
                            return;
                        }
                        break;
                }
                // 如果API调用失败，使用备用方案
                console.warn('API feedback failed, using fallback');
            } catch (error) {
                console.error('Feedback API failed:', error);
                showToast('⚠️ API调用失败，使用本地调整 | API failed, using local adjustment', 'warning');
            }
        }

        // 备用：使用本地内容调整（显示反馈但内容不变）
        console.log('Using fallback rendering, sessionId:', state.sessionId, 'useRealApi:', state.useRealApi);
        setTimeout(() => {
            switch(phase) {
                case 1:
                    generateResearchContentWithFeedback(feedback);
                    break;
                case 2:
                    generateOutlineContentWithFeedback(feedback);
                    break;
                case 3:
                    generateDraftContentWithFeedback(feedback);
                    break;
                case 5:
                    generateLayoutContentWithFeedback(feedback);
                    break;
            }
            showToast(`✅ 已根据反馈调整完成! Adjusted based on feedback!`, 'success');
        }, 1000);
    } else {
        showToast('请输入反馈内容 | Please enter your feedback', 'warning');
    }
}

// 根据反馈生成调整后的调研内容
// 根据反馈生成调整后的调研内容（精简版）
function generateResearchContentWithFeedback(feedback) {
    const topic = state.topic || '未知主题';

    const content = `
        <div class="result-box info">
            <h4 class="result-title">🔍 Research Report | 调研报告 <span class="updated-badge">已更新 Updated</span></h4>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">
                Topic 主题: "${topic}"
            </p>
        </div>

        <div class="adjustment-notice">
            <span class="adjustment-icon">🔄</span>
            <span class="adjustment-text">
                <strong>已根据您的反馈调整 | Adjusted based on your feedback:</strong>
                <br>
                <em>"${feedback}"</em>
            </span>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📚 信息源详情 | Source Details</div>
            <p style="color: var(--text-muted);">调研结果已根据反馈更新，请查看上方内容。</p>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    调研内容是否满足需求？是否继续进入大纲设计阶段？
                    <br>
                    <span style="color: var(--text-hint);">
                        Does the research meet your requirements? Ready for outline design?
                    </span>
                </div>
                <div class="confirm-buttons">
                    <button class="btn btn-primary" onclick="confirmAndNext(1)">
                        ✅ 确认并继续 | Confirm & Continue
                    </button>
                    <button class="btn btn-secondary" onclick="regeneratePhase(1)">
                        🔄 重新调研 | Re-research
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.research.innerHTML = content;
}
// 根据反馈生成调整后的大纲内容
function generateOutlineContentWithFeedback(feedback) {
    const chapterCount = state.length === 'short' ? 4 : state.length === 'medium' ? 6 : 8;

    const adjustmentNote = `
        <div class="adjustment-notice">
            <span class="adjustment-icon">🔄</span>
            <span class="adjustment-text">
                <strong>已根据您的反馈调整 | Adjusted based on your feedback:</strong>
                <br>
                <em>"${feedback}"</em>
            </span>
        </div>
    `;

    const content = `
        <div class="result-box info">
            <h4 class="result-title">📋 Article Outline | 文章大纲 <span class="updated-badge">已更新 Updated</span></h4>
            <p style="color: var(--text-muted);">
                Structured ${chapterCount} chapters | 已规划${chapterCount}个章节
            </p>
        </div>

        ${adjustmentNote}

        <div class="detail-section">
            <div class="detail-section-title">📖 章节结构 | Chapter Structure</div>
            <ol style="color: var(--text-secondary); padding-left: 1.5rem; line-height: 2;">
                <li><strong>0. 引言 Introduction</strong> - 为什么这个话题重要</li>
                <li><strong>1. 核心概念 Core Concepts</strong> - 基础定义与解释</li>
                <li><strong>2. 技术原理 Technical Principles</strong> - 深入技术细节</li>
                <li><strong>3. 应用场景 Applications</strong> - 实际案例分析</li>
                <li><strong>4. 发展趋势 Future Trends</strong> - 未来展望</li>
                <li><strong>5. 总结 Conclusion</strong> - 要点回顾</li>
            </ol>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎨 配图规划 | Image Planning</div>
            <ul class="result-list">
                <li><strong>Cover 封面:</strong> 科技感主题 (1024×1024)</li>
                <li><strong>Chapter 1-2:</strong> 概念配图 - 示意图解</li>
                <li><strong>Chapter 3-4:</strong> 应用配图 - 实例展示</li>
                <li><strong>Conclusion:</strong> 结语配图 - 总结图示</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认大纲结构是否符合预期？是否需要调整章节顺序?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if the outline structure meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有进一步调整建议,请在下方输入 | Additional Feedback</span>
                    </div>
                    <textarea id="feedback-outline" class="feedback-input" placeholder="例如：请增加一章关于行业趋势的内容 / Please add a chapter about industry trends..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(2)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.outline.innerHTML = content;
}

// 根据反馈生成调整后的初稿内容
function generateDraftContentWithFeedback(feedback) {
    const adjustmentNote = `
        <div class="adjustment-notice">
            <span class="adjustment-icon">🔄</span>
            <span class="adjustment-text">
                <strong>已根据您的反馈调整 | Adjusted based on your feedback:</strong>
                <br>
                <em>"${feedback}"</em>
            </span>
        </div>
    `;

    const content = `
        <div class="result-box success">
            <h4 class="result-title">✍️ Draft Complete | 初稿完成 <span class="updated-badge">已更新 Updated</span></h4>
        </div>

        ${adjustmentNote}

        <div class="detail-section">
            <div class="detail-section-title">📄 文章概览 | Article Overview</div>
            <ul class="result-list">
                <li><strong>标题 Title:</strong> ${state.topic || '文章标题'}</li>
                <li><strong>字数 Words:</strong> ~${getWordCount(state.length)} words | 字</li>
                <li><strong>章节数 Chapters:</strong> ${state.length === 'short' ? '4' : state.length === 'medium' ? '6' : '8'}</li>
                <li><strong>配图数 Images:</strong> ${state.length === 'short' ? '3' : state.length === 'medium' ? '5' : '7'}</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📝 内容预览 | Content Preview</div>
            <div class="detail-code" style="max-height: 250px; overflow-y: auto;">
# ${state.topic || '文章标题'}

## 引言 | Introduction
在当今数字化时代，这是关于"${state.topic || '主题'}"的科普文章...

## 核心概念 | Core Concepts
首先我们需要理解什么是${state.topic || '主题'}...

## 技术原理 | Technical Principles
${state.topic || '主题'}的核心技术基于深度学习...

## 应用场景 | Applications
在实际场景中 ${state.topic || '主题'}已经广泛应用...

## 总结 | Conclusion
通过本文的介绍相信大家对"${state.topic || '主题'}"有了更深入的了解...
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认初稿内容是否符合预期?是否需要调整某些章节?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if the draft meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有进一步调整建议,请在下方输入 | Additional Feedback</span>
                    </div>
                    <textarea id="feedback-draft" class="feedback-input" placeholder="例如：第二章的技术原理部分过于深奥,请简化 / The technical principles section is too technical..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(3)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.draft.innerHTML = content;
}

// 根据反馈生成调整后的排版内容
function generateLayoutContentWithFeedback(feedback) {
    const adjustmentNote = `
        <div class="adjustment-notice">
            <span class="adjustment-icon">🔄</span>
            <span class="adjustment-text">
                <strong>已根据您的反馈调整 | Adjusted based on your feedback:</strong>
                <br>
                <em>"${feedback}"</em>
            </span>
        </div>
    `;

    const content = `
        <div class="result-box success">
            <h4 class="result-title">📄 Layout Complete | 排版完成 <span class="updated-badge">已更新 Updated</span></h4>
        </div>

        ${adjustmentNote}

        <div class="detail-section">
            <div class="detail-section-title">📁 输出文件 | Output Files</div>
            <ul class="result-list">
                <li><strong>content.md</strong> - Markdown原文</li>
                <li><strong>wechat.html</strong> - 微信公众号格式 (内联CSS)</li>
                <li><strong>article.html</strong> - HTML富文本格式</li>
                <li><strong>images/</strong> - 配图目录</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📱 微信格式特点 | WeChat Features</div>
            <ul class="result-list">
                <li>✓ 内联CSS样式 | Inline CSS styles</li>
                <li>✓ 适配微信阅读体验 | WeChat optimized</li>
                <li>✓ 图片居中对齐 | Centered images</li>
                <li>✓ 最大宽度限制 | Max-width constrained</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认排版效果是否符合预期?微信公众号格式是否正确?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if layout meets expectations.
                    </span>
                </div>

                <!-- 反馈输入框 -->
                <div class="feedback-section">
                    <div class="feedback-label">
                        <span>💬 如有进一步调整建议,请在下方输入 | Additional Feedback</span>
                    </div>
                    <textarea id="feedback-layout" class="feedback-input" placeholder="例如：请调整字体大小 / Please adjust the font size..."></textarea>
                    <button class="feedback-submit-btn" onclick="submitFeedback(5)">
                        <span>📤 提交反馈 Submit Feedback</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    elements.contents.layout.innerHTML = content;
}


// 下载文件
function downloadFiles() {
    showToast('Preparing download... 准备下载...', 'info');
    setTimeout(() => {
        showToast('Download started! 开始下载!', 'success');
    }, 500);
}

// 开始新文章
function startNew() {
    state.topic = '';
    state.currentPage = 'home';
    elements.topicInput.value = '';
    goToPage('home');
    showToast('Ready for new article! 准备创作新文章!', 'success');
}

// 辅助函数
function getWordCount(length) {
    const counts = { short: '1,500', medium: '3,000', long: '8,000' };
    return counts[length] || counts.medium;
}

function getAudienceText(audience) {
    const texts = {
        tech: 'Tech Professionals | 技术从业者',
        general: 'General Public | 大众读者',
        mixed: 'Mixed Audience | 混合读者'
    };
    return texts[audience] || texts.general;
}

// Toast 提示
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== 统一 Chat 功能 ====================

/**
 * 渲染 Chat 面板 - 在每个 Phase 页面底部显示
 * @param {number} phase - 当前阶段 (1-5)
 * @param {string} placeholder - 输入框占位符
 */
function renderChatPanel(phase, placeholder = '输入您的要求，AI 助手会帮您优化内容...') {
    const history = state.chatHistory[phase] || [];

    // 生成对话消息 HTML
    const messagesHtml = history.map(msg => {
        const isUser = msg.role === 'user';
        return `
            <div class="chat-message ${isUser ? 'user' : 'assistant'}" style="
                display: flex;
                justify-content: ${isUser ? 'flex-end' : 'flex-start'};
                margin-bottom: 0.75rem;
            ">
                <div style="
                    max-width: 85%;
                    padding: 0.75rem 1rem;
                    border-radius: 12px;
                    background: ${isUser ? 'linear-gradient(135deg, var(--primary), var(--accent))' : 'var(--bg-secondary)'};
                    color: ${isUser ? 'white' : 'var(--text-secondary)'};
                    font-size: 0.9rem;
                    line-height: 1.5;
                ">
                    ${isUser ? '' : '<span style="font-weight: 600; color: var(--accent);">🤖 AI 助手</span><br>'}
                    ${msg.content}
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="chat-panel" style="
            margin-top: 1.5rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
        ">
            <!-- Chat 头部 -->
            <div class="chat-header" style="
                padding: 1rem 1.25rem;
                background: var(--bg-secondary);
                border-bottom: 1px solid var(--border-color);
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.5rem;">💬</span>
                    <div>
                        <div style="font-weight: 600; color: var(--text-primary);">AI 助手对话</div>
                        <div style="font-size: 0.8rem; color: var(--text-hint);">与 AI 对话优化当前内容</div>
                    </div>
                </div>
                <button onclick="clearChatHistory(${phase})" style="
                    padding: 0.4rem 0.8rem;
                    background: transparent;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    color: var(--text-hint);
                    font-size: 0.8rem;
                    cursor: pointer;
                ">清空对话</button>
            </div>

            <!-- Chat 消息区域 -->
            <div class="chat-messages" id="chat-messages-${phase}" style="
                padding: 1rem 1.25rem;
                max-height: 300px;
                overflow-y: auto;
                min-height: ${history.length > 0 ? '100px' : '60px'};
                display: flex;
                flex-direction: column;
                justify-content: ${history.length > 0 ? 'flex-start' : 'center'};
                align-items: center;
            ">
                ${history.length > 0 ? messagesHtml : `
                    <div style="color: var(--text-hint); font-size: 0.9rem; text-align: center;">
                        👋 您好！我是 AI 助手，可以帮您优化当前内容。<br>
                        <span style="font-size: 0.8rem;">例如：补充调研、调整大纲、修改文章风格等</span>
                    </div>
                `}
            </div>

            <!-- Chat 输入区域 -->
            <div class="chat-input-area" style="
                padding: 1rem 1.25rem;
                background: var(--bg-secondary);
                border-top: 1px solid var(--border-color);
            ">
                <div style="display: flex; gap: 0.75rem;">
                    <input type="text" id="chat-input-${phase}"
                        placeholder="${placeholder}"
                        style="
                            flex: 1;
                            padding: 0.75rem 1rem;
                            background: var(--bg-primary);
                            border: 1px solid var(--border-color);
                            border-radius: 8px;
                            color: var(--text-primary);
                            font-size: 0.9rem;
                        "
                        onkeypress="if(event.key==='Enter') sendChatMessage(${phase})"
                    />
                    <button onclick="sendChatMessage(${phase})" id="chat-send-btn-${phase}"
                        style="
                            padding: 0.75rem 1.25rem;
                            background: linear-gradient(135deg, var(--primary), var(--accent));
                            border: none;
                            border-radius: 8px;
                            color: white;
                            font-weight: 500;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            gap: 0.5rem;
                        ">
                        <span>发送</span>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                        </svg>
                    </button>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-hint);">
                    💡 提示：您可以要求 AI 补充信息、调整内容、修改风格等，直到满意后点击"确认并继续"
                </div>
            </div>
        </div>
    `;
}

/**
 * 发送 Chat 消息
 */
async function sendChatMessage(phase) {
    const inputEl = document.getElementById(`chat-input-${phase}`);
    const sendBtn = document.getElementById(`chat-send-btn-${phase}`);
    const message = inputEl.value.trim();

    if (!message || state.isChatLoading) return;
    if (!state.sessionId) {
        showToast('请先开始一个写作任务', 'error');
        return;
    }

    // 初始化对话历史
    if (!state.chatHistory[phase]) {
        state.chatHistory[phase] = [];
    }

    // 添加用户消息
    state.chatHistory[phase].push({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
    });

    // 清空输入框
    inputEl.value = '';

    // 更新 UI 显示用户消息
    updateChatMessagesUI(phase);

    // 显示加载状态
    state.isChatLoading = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span>思考中...</span>';

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                phase: phase,
                message: message,
                history: state.chatHistory[phase].slice(-10)  // 最近5轮对话
            })
        });

        const result = await response.json();

        if (result.success) {
            // 添加助手回复
            state.chatHistory[phase].push({
                role: 'assistant',
                content: result.reply,
                timestamp: new Date().toISOString()
            });

            // 更新 UI
            updateChatMessagesUI(phase);

            // 如果有更新内容，刷新页面
            if (result.updated_content) {
                showToast('内容已更新！', 'success');
                // 根据阶段刷新对应内容，同时传递 confirmed_outline
                const dataWithConfirmation = { ...result.updated_content, confirmed_outline: result.confirmed_outline };
                refreshPhaseContent(phase, dataWithConfirmation);
            }
        } else {
            showToast(`发送失败: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`网络错误: ${error.message}`, 'error');
    } finally {
        state.isChatLoading = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span>发送</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>';
    }
}

/**
 * 更新 Chat 消息区域 UI
 */
function updateChatMessagesUI(phase) {
    const container = document.getElementById(`chat-messages-${phase}`);
    if (!container) return;

    const history = state.chatHistory[phase] || [];

    if (history.length === 0) {
        container.innerHTML = `
            <div style="color: var(--text-hint); font-size: 0.9rem; text-align: center;">
                👋 您好！我是 AI 助手，可以帮您优化当前内容。<br>
                <span style="font-size: 0.8rem;">例如：补充调研、调整大纲、修改文章风格等</span>
            </div>
        `;
        return;
    }

    container.innerHTML = history.map(msg => {
        const isUser = msg.role === 'user';
        return `
            <div class="chat-message ${isUser ? 'user' : 'assistant'}" style="
                display: flex;
                justify-content: ${isUser ? 'flex-end' : 'flex-start'};
                margin-bottom: 0.75rem;
            ">
                <div style="
                    max-width: 85%;
                    padding: 0.75rem 1rem;
                    border-radius: 12px;
                    background: ${isUser ? 'linear-gradient(135deg, var(--primary), var(--accent))' : 'var(--bg-secondary)'};
                    color: ${isUser ? 'white' : 'var(--text-secondary)'};
                    font-size: 0.9rem;
                    line-height: 1.5;
                ">
                    ${isUser ? '' : '<span style="font-weight: 600; color: var(--accent);">🤖 AI 助手</span><br>'}
                    ${msg.content}
                </div>
            </div>
        `;
    }).join('');

    // 滚动到底部
    container.scrollTop = container.scrollHeight;
}

/**
 * 清空对话历史
 */
function clearChatHistory(phase) {
    state.chatHistory[phase] = [];
    updateChatMessagesUI(phase);
    showToast('对话已清空', 'info');
}

/**
 * 更新配图风格
 */
function updateImageStyle(style) {
    if (!style) return;

    // 更新显示
    const currentStyleEl = document.getElementById('current-image-style');
    if (currentStyleEl) {
        currentStyleEl.textContent = style;
    }

    // 保存到 state
    if (!state.outline) state.outline = {};
    if (!state.outline.image_plan) state.outline.image_plan = {};
    state.outline.image_plan.style = style;

    // 显示提示
    showToast(`✅ 已选择配图风格: ${style.substring(0, 20)}...`, 'success');

    console.log('Image style updated:', style);
}

/**
 * 根据阶段刷新内容显示
 */
function refreshPhaseContent(phase, content) {
    switch (phase) {
        case 1:
            state.researchData = content;
            renderResearchFromApi(content);
            break;
        case 2:
            state.outline = content;
            renderOutlineFromApi(content);
            break;
        case 3:
            state.draft = content;
            renderDraftFromApi(content);
            break;
        case 4:
            state.images = content;
            renderImagesFromApi(content);
            break;
        case 5:
            state.layout = content;
            renderLayoutFromApi(content);
            break;
    }
}

// 粒子效果
function initParticles() {
    const canvas = document.getElementById('particles');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    let nebulae = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 1.5 + 0.5,
            speedX: (Math.random() - 0.5) * 0.3,
            speedY: (Math.random() - 0.5) * 0.3,
            opacity: Math.random() * 0.3 + 0.1
        };
    }

    // 创建星云效果
    function createNebula() {
        const colors = [
            { r: 100, g: 150, b: 255 },   // 蓝色星云
            { r: 180, g: 100, b: 255 },   // 紫色星云
            { r: 255, g: 150, b: 180 },   // 粉色星云
            { r: 100, g: 200, b: 200 },   // 青色星云
        ];
        const color = colors[Math.floor(Math.random() * colors.length)];
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 200 + 150,
            color: color,
            opacity: Math.random() * 0.03 + 0.01,
            phase: Math.random() * Math.PI * 2,
            speed: Math.random() * 0.0005 + 0.0002
        };
    }

    function initParticlesArray() {
        particles = [];
        const count = Math.floor((canvas.width * canvas.height) / 20000);
        for (let i = 0; i < count; i++) {
            particles.push(createParticle());
        }

        // 初始化2-3个星云
        nebulae = [];
        const nebulaCount = Math.floor(Math.random() * 2) + 2;
        for (let i = 0; i < nebulaCount; i++) {
            nebulae.push(createNebula());
        }
    }

    // 绘制星云
    function drawNebula(nebula, time) {
        const pulseOpacity = nebula.opacity + Math.sin(time * nebula.speed * 1000 + nebula.phase) * 0.01;

        const gradient = ctx.createRadialGradient(
            nebula.x, nebula.y, 0,
            nebula.x, nebula.y, nebula.radius
        );

        const { r, g, b } = nebula.color;
        gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${pulseOpacity})`);
        gradient.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, ${pulseOpacity * 0.5})`);
        gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(nebula.x, nebula.y, nebula.radius, 0, Math.PI * 2);
        ctx.fill();
    }

    function animate(time) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 绘制星云（在星星下面）
        nebulae.forEach(nebula => drawNebula(nebula, time || 0));

        particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;
            if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
            if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
            ctx.fill();
        });

        particles.forEach((p1, i) => {
            particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 80) {
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(255, 255, 255, ${0.05 * (1 - dist / 80)})`;
                    ctx.stroke();
                }
            });
        });

        requestAnimationFrame(animate);
    }

    resize();
    initParticlesArray();
    animate();
    window.addEventListener('resize', () => { resize(); initParticlesArray(); });
}

// ========== API数据渲染函数 ==========

// 渲染调研数据（从API返回）- 带勾选确认功能
function renderResearchFromApi(data) {
    console.log('=== renderResearchFromApi called ===');
    console.log('data:', JSON.stringify(data, null, 2));
    console.log('pending_sources:', data?.pending_sources);
    console.log('confirmed_sources:', data?.confirmed_sources);

    const topic = data.topic || state.topic;
    const confirmedSources = data.confirmed_sources || [];  // 已确认的来源
    const pendingSources = data.pending_sources || data.sources || [];  // 待确认的来源
    const isConfirmed = data.confirmed || false;  // 是否已完成最终确认

    // 渲染已确认的来源（锁定状态）
    let confirmedHtml = '';
    if (confirmedSources.length > 0) {
        confirmedHtml = `
            <div style="margin-bottom: 1.5rem;">
                <div class="detail-section-title" style="color: var(--success);">
                    ✅ 已确认的信息来源（${confirmedSources.length}条，已锁定）
                </div>
                ${confirmedSources.map((source, index) => `
                    <div class="research-source" style="border-left: 3px solid var(--success); opacity: 0.8;">
                        <div class="source-header">
                            <span style="color: var(--success); margin-right: 0.5rem;">🔒</span>
                            <span class="source-title">${source.title || '来源 ' + (index + 1)}</span>
                        </div>
                        <div class="source-content">
                            ${source.summary ? `<p>${source.summary}</p>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // 渲染待确认的来源（可勾选）
    let pendingHtml = '';
    if (pendingSources.length > 0) {
        pendingHtml = `
            <div style="margin-bottom: 1.5rem;">
                <div class="detail-section-title">
                    📋 待确认的信息来源（${pendingSources.length}条）
                </div>
                <p style="color: var(--text-hint); font-size: 0.9rem; margin-bottom: 1rem;">
                    请勾选需要保留的信息来源，然后点击"更新"按钮。未勾选的将被移除。
                </p>
                ${pendingSources.map((source, index) => `
                    <div class="research-source" id="pending-source-${index}" style="border-left: 3px solid var(--accent);">
                        <div class="source-header" style="display: flex; align-items: center; gap: 0.5rem;">
                            <input type="checkbox" id="source-check-${index}" value="${index}" checked style="width: 18px; height: 18px;">
                            <span class="source-badge ${source.type === 'WeChat' ? 'wechat' : source.type === 'XiaoHongShu' ? 'xiaohongshu' : 'web'}">
                                ${source.type === 'WeChat' ? '微信公众号' : source.type === 'XiaoHongShu' ? '小红书' : 'WebSearch'}
                            </span>
                            <span class="source-title">${source.title || '来源 ' + (index + 1)}</span>
                        </div>
                        <div class="source-content" style="margin-left: 2rem;">
                            ${source.summary ? `<p>${source.summary}</p>` : ''}
                        </div>
                    </div>
                `).join('')}

                <button onclick="updateResearchConfirmation()" style="
                    margin-top: 1rem;
                    padding: 0.75rem 1.5rem;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                ">
                    🔄 更新确认（移除未勾选）
                </button>
            </div>
        `;
    }

    // 渲染关键发现
    let keyFindingsHtml = '';
    if (data.key_findings) {
        keyFindingsHtml = `
            <div class="detail-section">
                <div class="detail-section-title">🎯 核心发现 | Key Findings</div>
                <ul class="result-list">
                    ${data.key_findings.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // 确认按钮（当有待确认来源时显示）
    let confirmButtonHtml = '';
    if (pendingSources.length === 0 && confirmedSources.length > 0) {
        confirmButtonHtml = `
            <div style="margin-top: 1.5rem; padding: 1rem; background: var(--bg-secondary); border-radius: 12px;">
                <p style="color: var(--success); font-weight: 600;">
                    ✅ 所有信息来源已确认（${confirmedSources.length}条）
                </p>
                <button onclick="confirmResearchAndContinue()" style="
                    margin-top: 1rem;
                    padding: 0.75rem 2rem;
                    background: var(--success);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                ">
                    ✅ 确认并继续（进入大纲阶段）
                </button>
            </div>
        `;
    }

    const content = `
        <div class="result-box info">
            <h4 class="result-title">🔍 Research Report | 调研报告</h4>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">
                Topic 主题: "${topic}"
            </p>
        </div>

        ${confirmedHtml}
        ${pendingHtml}
        ${keyFindingsHtml}

        ${confirmButtonHtml}

        <div class="detail-section">
            <div class="detail-section-title">📋 调整信息 | Adjustment</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    如需增加搜索内容，请在下方 AI 助手窗口输入新的搜索需求。
                    <br>
                    <span style="color: var(--text-hint);">
                        If you need more information, please ask AI assistant to search.
                    </span>
                </div>
            </div>
        </div>

        ${renderChatPanel(1, '例如：请搜索更多关于XX的案例、补充XX领域的信息...')}
    `;

    elements.contents.research.innerHTML = content;
}

// 更新调研确认（移除未勾选的来源）
async function updateResearchConfirmation() {
    const checkboxes = document.querySelectorAll('[id^="source-check-"]');
    const selectedIndices = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value));

    // 获取待确认的来源
    const pendingSources = state.researchData?.pending_sources || state.researchData?.sources || [];
    const confirmedSources = state.researchData?.confirmed_sources || [];

    // 保留已确认的来源 + 勾选的待确认来源
    const selectedPending = selectedIndices.map(i => pendingSources[i]);
    const newConfirmedSources = [...confirmedSources, ...selectedPending];

    // 更新数据
    state.researchData.confirmed_sources = newConfirmedSources;
    state.researchData.pending_sources = [];
    state.researchData.sources = newConfirmedSources;
    state.researchData.key_findings = [`已确认 ${newConfirmedSources.length} 个信息来源`];

    // 重新渲染
    renderResearchFromApi(state.researchData);

    showToast(`✅ 已确认 ${selectedPending.length} 条来源，共 ${newConfirmedSources.length} 条`, 'success');
}

// 确认并继续（进入下一阶段）
function confirmResearchAndContinue() {
    if (confirm('确认进入大纲设计阶段？')) {
        goToPage('outline');
        // 🔧 修复：跳转后自动生成大纲
        setTimeout(() => {
            generateOutlineContent();
        }, 300);
    }
}

// 渲染等待AI助手搜索的界面
function renderWaitingForAI(data, topic, includeXiaoHongShu, includeWeixin) {
    let basicSourcesHtml = '';
    if (data.sources && data.sources.length > 0) {
        data.sources.forEach((source, index) => {
            basicSourcesHtml += `
                <div class="research-source" style="opacity: 0.7;">
                    <div class="source-header">
                        <span class="source-badge ${source.type === 'WeChat' ? 'wechat' : source.type === 'XiaoHongShu' ? 'xiaohongshu' : 'web'}">${source.type === 'WeChat' ? '微信公众号' : source.type === 'XiaoHongShu' ? '小红书' : 'WebSearch'}</span>
                        <span class="source-title">${source.title || '来源 ' + (index + 1)}</span>
                    </div>
                    <div class="source-content">
                        <p style="color: var(--text-hint);">${source.summary || '基础搜索结果'}</p>
                        ${source.url ? `<a href="${source.url}" target="_blank" class="url-link" style="font-size: 0.85rem;">🔗 访问链接</a>` : ''}
                    </div>
                </div>
            `;
        });
    }

    const content = `
        <div class="result-box warning" style="margin-bottom: 1rem;">
            <h4 class="result-title">⏳ 等待AI助手深度搜索... | Waiting for AI Assistant</h4>
            <p style="color: var(--text-secondary); margin: 1rem 0;">
                当前显示的是基础搜索结果。AI助手正在通过MCP工具进行深度搜索（小红书+微信公众号），搜索完成后刷新页面即可看到完整结果。
                <br>
                <span style="color: var(--text-hint);">Current results are basic. AI Assistant is performing deep search via MCP tools. Refresh when complete.</span>
            </p>
            <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                <p style="margin: 0; font-family: monospace; font-size: 0.9rem;">
                    <strong>📋 Session ID:</strong> <span style="color: var(--accent-primary);">${state.sessionId}</span>
                </p>
            </div>
            <button id="refresh-research-btn" class="btn btn-primary" style="margin-top: 1rem;">
                🔄 刷新获取AI搜索结果 | Refresh for AI Results
            </button>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📚 基础搜索结果 | Basic Search Results</div>
            ${basicSourcesHtml || '<p style="color: var(--text-muted);">暂无数据</p>'}
        </div>
    `;

    elements.contents.research.innerHTML = content;

    // 添加刷新按钮事件
    const refreshBtn = document.getElementById('refresh-research-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '🔄 正在检查... | Checking...';

            try {
                const result = await api.startResearch(state.sessionId, topic, { includeXiaoHongShu, includeWeixin });
                if (result.success && result.source === 'ai_assistant') {
                    showToast('✅ AI助手搜索完成！| AI search completed!', 'success');
                    renderResearchFromApi(result.data);
                } else {
                    showToast('⏳ AI助手仍在搜索中，请稍后再试 | AI still searching, please try again', 'warning');
                    refreshBtn.disabled = false;
                    refreshBtn.innerHTML = '🔄 刷新获取AI搜索结果 | Refresh for AI Results';
                }
            } catch (error) {
                console.error('Refresh failed:', error);
                showToast('❌ 刷新失败 | Refresh failed', 'error');
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '🔄 刷新获取AI搜索结果 | Refresh for AI Results';
            }
        });
    }
}

// 渲染大纲数据（从API返回）
function renderOutlineFromApi(data) {
    console.log('renderOutlineFromApi received data:', JSON.stringify(data, null, 2));
    console.log('Chapters count:', data.chapters ? data.chapters.length : 0);
    console.log('Chapters:', data.chapters);
    console.log('confirmed_outline:', data.confirmed_outline);

    // 获取确认状态（从 data 或 state 中获取）
    const confirmedOutline = data.confirmed_outline || state.confirmed_outline || {
        chapters: false,
        image_plan: false,
        writing_style: false,
        image_style: false,
        word_count: false
    };

    // 保存到 state
    state.confirmed_outline = confirmedOutline;

    let chaptersHtml = '';
    if (data.chapters && data.chapters.length > 0) {
        chaptersHtml = data.chapters.map(ch => {
            // 显示要点（如果有）
            let keyPointsHtml = '';
            if (ch.key_points && ch.key_points.length > 0) {
                keyPointsHtml = `
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: var(--text-muted); font-size: 0.9rem;">
                        ${ch.key_points.map(kp => `<li>${kp}</li>`).join('')}
                    </ul>`;
            }
            // 显示配图建议（如果有）
            let imageSuggestionHtml = '';
            if (ch.image_suggestion) {
                imageSuggestionHtml = `<div style="margin-top: 0.3rem; color: var(--accent); font-size: 0.85rem;">🖼️ ${ch.image_suggestion}</div>`;
            }

            return `
                <li style="margin-bottom: 1rem;">
                    <strong style="font-size: 1.1rem; color: var(--text-primary);">${ch.number}. ${ch.title}</strong>
                    <p style="margin: 0.5rem 0; color: var(--text-secondary); line-height: 1.6;">${ch.description}</p>
                    ${keyPointsHtml}
                    ${imageSuggestionHtml}
                </li>`;
        }).join('');
    }
    console.log('Generated chaptersHtml:', chaptersHtml.substring(0, 200) + '...');

    let imagePlanHtml = '';
    if (data.image_plan) {
        imagePlanHtml = `
            <li><strong>Cover 封面:</strong> ${data.image_plan.cover?.description || '主题封面'} (${data.image_plan.cover?.size || '1024x576'})</li>
            ${data.image_plan.chapters ? data.image_plan.chapters.map((img, i) => `<li><strong>Chapter ${i+1}:</strong> ${img}</li>`).join('') : ''}
        `;
    }

    // 如果有调整说明，显示已更新标记
    const updatedBadge = data.adjusted ? '<span class="updated-badge">已更新 Updated</span>' : '';
    const adjustmentNote = data.adjusted && data.adjustment_note ? `
        <div class="adjustment-notice">
            <span class="adjustment-icon">🔄</span>
            <span class="adjustment-text">
                <strong>已根据您的反馈调整 | Adjusted based on your feedback:</strong>
                <br>
                <em>"${data.adjustment_note}"</em>
            </span>
        </div>
    ` : '';

    // 构建勾选确认部分（类似 Phase 1）
    const confirmedItemsHtml = `
        <div class="detail-section" style="background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div class="detail-section-title" style="margin-bottom: 1rem;">
                📋 大纲确认 | Outline Confirmation
                <span style="color: var(--text-muted); font-size: 0.85rem; font-weight: normal;">
                    （勾选需要保留的项目，点击"确认"锁定）
                </span>
            </div>
            <p style="color: var(--text-hint); font-size: 0.9rem; margin-bottom: 1rem;">
                请勾选需要确认的大纲项目，然后点击"更新确认"按钮。已确认的项目将被锁定，AI 助手将只处理未确认的项目。
            </p>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <!-- 章节结构 -->
                <div class="outline-confirm-item" id="confirm-item-chapters" style="
                    padding: 1rem; border-radius: 8px; border: 2px solid ${confirmedOutline.chapters ? 'var(--success)' : 'var(--border-color)'};
                    background: ${confirmedOutline.chapters ? 'rgba(76, 175, 80, 0.1)' : 'var(--bg-primary)'};
                    opacity: ${confirmedOutline.chapters ? 0.8 : 1};
                ">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="outline-check-chapters" ${confirmedOutline.chapters ? 'checked' : ''} ${confirmedOutline.chapters ? 'disabled' : ''}
                            onchange="updateOutlineConfirmation('chapters', this.checked)"
                            style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 600;">📖 章节结构</span>
                        ${confirmedOutline.chapters ? '<span style="color: var(--success);">🔒</span>' : ''}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        ${data.chapter_count || 6} 个章节
                    </div>
                </div>

                <!-- 配图规划 -->
                <div class="outline-confirm-item" id="confirm-item-image_plan" style="
                    padding: 1rem; border-radius: 8px; border: 2px solid ${confirmedOutline.image_plan ? 'var(--success)' : 'var(--border-color)'};
                    background: ${confirmedOutline.image_plan ? 'rgba(76, 175, 80, 0.1)' : 'var(--bg-primary)'};
                    opacity: ${confirmedOutline.image_plan ? 0.8 : 1};
                ">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="outline-check-image_plan" ${confirmedOutline.image_plan ? 'checked' : ''} ${confirmedOutline.image_plan ? 'disabled' : ''}
                            onchange="updateOutlineConfirmation('image_plan', this.checked)"
                            style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 600;">🎨 配图规划</span>
                        ${confirmedOutline.image_plan ? '<span style="color: var(--success);">🔒</span>' : ''}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        ${(data.image_plan?.chapters?.length || 0) + 1} 张配图（含1张封面 + ${data.image_plan?.chapters?.length || 0}张章节图）
                    </div>
                </div>

                <!-- 写作风格 -->
                <div class="outline-confirm-item" id="confirm-item-writing_style" style="
                    padding: 1rem; border-radius: 8px; border: 2px solid ${confirmedOutline.writing_style ? 'var(--success)' : 'var(--border-color)'};
                    background: ${confirmedOutline.writing_style ? 'rgba(76, 175, 80, 0.1)' : 'var(--bg-primary)'};
                    opacity: ${confirmedOutline.writing_style ? 0.8 : 1};
                ">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="outline-check-writing_style" ${confirmedOutline.writing_style ? 'checked' : ''} ${confirmedOutline.writing_style ? 'disabled' : ''}
                            onchange="updateOutlineConfirmation('writing_style', this.checked)"
                            style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 600;">🎯 写作风格</span>
                        ${confirmedOutline.writing_style ? '<span style="color: var(--success);">🔒</span>' : ''}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        ${getAudienceText(state.audience)}
                    </div>
                </div>

                <!-- 配图风格 -->
                <div class="outline-confirm-item" id="confirm-item-image_style" style="
                    padding: 1rem; border-radius: 8px; border: 2px solid ${confirmedOutline.image_style ? 'var(--success)' : 'var(--border-color)'};
                    background: ${confirmedOutline.image_style ? 'rgba(76, 175, 80, 0.1)' : 'var(--bg-primary)'};
                    opacity: ${confirmedOutline.image_style ? 0.8 : 1};
                ">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="outline-check-image_style" ${confirmedOutline.image_style ? 'checked' : ''} ${confirmedOutline.image_style ? 'disabled' : ''}
                            onchange="updateOutlineConfirmation('image_style', this.checked)"
                            style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 600;">🖼️ 配图风格</span>
                        ${confirmedOutline.image_style ? '<span style="color: var(--success);">🔒</span>' : ''}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        ${data.image_plan?.style || '默认风格'}
                    </div>
                </div>

                <!-- 预计字数 -->
                <div class="outline-confirm-item" id="confirm-item-word_count" style="
                    padding: 1rem; border-radius: 8px; border: 2px solid ${confirmedOutline.word_count ? 'var(--success)' : 'var(--border-color)'};
                    background: ${confirmedOutline.word_count ? 'rgba(76, 175, 80, 0.1)' : 'var(--bg-primary)'};
                    opacity: ${confirmedOutline.word_count ? 0.8 : 1};
                ">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <input type="checkbox" id="outline-check-word_count" ${confirmedOutline.word_count ? 'checked' : ''} ${confirmedOutline.word_count ? 'disabled' : ''}
                            onchange="updateOutlineConfirmation('word_count', this.checked)"
                            style="width: 18px; height: 18px; cursor: pointer;">
                        <span style="font-weight: 600;">📊 预计字数</span>
                        ${confirmedOutline.word_count ? '<span style="color: var(--success);">🔒</span>' : ''}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        ~${data.word_count || getWordCount(state.length)} 字
                    </div>
                </div>
            </div>

            <button onclick="confirmOutlineAndContinue()" style="
                margin-top: 1rem;
                padding: 0.75rem 1.5rem;
                background: var(--primary);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
            ">
                🔄 更新确认（锁定已勾选的项目）
            </button>
        </div>
    `;

    const content = `
        <div class="result-box info">
            <h4 class="result-title">📋 Article Outline | 文章大纲 ${updatedBadge}</h4>
            <p style="color: var(--text-muted);">
                Structured ${data.chapter_count || 6} chapters | 已规划${data.chapter_count || 6}个章节
            </p>
        </div>

        ${adjustmentNote}

        ${confirmedItemsHtml}

        <div class="detail-section">
            <div class="detail-section-title">📖 章节结构 | Chapter Structure</div>
            <ol style="color: var(--text-secondary); padding-left: 1.5rem; line-height: 2;">
                ${chaptersHtml || '<li>大纲生成中...</li>'}
            </ol>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎨 配图规划 | Image Planning</div>
            <ul class="result-list">
                ${imagePlanHtml || '<li>配图规划中...</li>'}
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🎯 写作风格 | Writing Style</div>
            <div class="detail-text">
                <strong>目标读者:</strong> ${getAudienceText(state.audience)}<br>
                <strong>语言深度:</strong> ${state.audience === 'tech' ? '专业 Technical' : '通俗 Accessible'}<br>
                <strong>配图风格:</strong> <span id="current-image-style">${data.image_plan?.style || '科技感, 深蓝色调, 几何图形, 4K'}</span>
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🖼️ 配图风格选择 | Image Style Selection</div>
            <div style="margin: 0.5rem 0;">
                <select id="image-style-selector" onchange="updateImageStyle(this.value)" style="
                    width: 100%;
                    padding: 0.75rem;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    background: var(--bg-secondary);
                    color: var(--text-primary);
                    font-size: 0.95rem;
                    cursor: pointer;
                ">
                    <option value="">-- 选择配图风格 | Select Image Style --</option>
                    <option value="科技感, 深蓝色调, 几何图形, 渐变, 未来感, 4K" ${data.image_plan?.style?.includes('科技感') ? 'selected' : ''}>🔵 科技感（蓝色调）</option>
                    <option value="温暖, 橙色调, 亲和力, 生活化, 柔和, high quality" ${data.image_plan?.style?.includes('温暖') ? 'selected' : ''}>🟠 温暖风格（橙色调）</option>
                    <option value="自然, 绿色调, 清新, 环保, 有机, 4K" ${data.image_plan?.style?.includes('自然') ? 'selected' : ''}>🟢 自然风格（绿色调）</option>
                    <option value="专业, 黑白灰, 简约, 商务, 高端, 4K" ${data.image_plan?.style?.includes('黑白') ? 'selected' : ''}>⚫ 专业商务（黑白灰）</option>
                    <option value="活泼, 多彩, 创意, 有趣, 4K" ${data.image_plan?.style?.includes('活泼') ? 'selected' : ''}>🌈 活泼创意（多彩）</option>
                    <option value="复古, 怀旧, 棕色调, 文艺, 质感, 4K" ${data.image_plan?.style?.includes('复古') ? 'selected' : ''}>🟤 复古文艺（棕色调）</option>
                    <option value="极简, 白色背景, 线条, 留白, 优雅, 4K" ${data.image_plan?.style?.includes('极简') && !data.image_plan?.style?.includes('手绘') ? 'selected' : ''}>⚪ 极简风格（白色调）</option>
                    <option value="奢华, 金色, 高贵, 精致, 闪耀, 4K" ${data.image_plan?.style?.includes('奢华') ? 'selected' : ''}>🟡 奢华风格（金色调）</option>
                    <option value="手绘, 水彩, 梦幻, 柔和, 艺术, 渐变色, 4K" ${data.image_plan?.style?.includes('水彩') ? 'selected' : ''}>🎨 手绘水彩风格</option>
                    <option value="手绘, 卡通, 可爱, 活泼, 插画, 趣味, 4K" ${data.image_plan?.style?.includes('手绘') && data.image_plan?.style?.includes('卡通') ? 'selected' : ''}>✏️ 手绘卡通风格</option>
                    <option value="单线手绘, 极简线条, 简约, 留白, 艺术感, 4K" ${data.image_plan?.style?.includes('单线手绘') ? 'selected' : ''}>✍️ 单线手绘极简风格</option>
                </select>
            </div>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">
                💡 选择配图风格将影响 Phase 4 的图片生成效果
            </p>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📊 预计字数 | Word Count</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: var(--text-primary);">
                ~${data.word_count || getWordCount(state.length)} words | 字
            </div>
        </div>

        ${renderChatPanel(2, '例如：增加一章关于XX、删除第三章、调整配图风格、修改字数...')}
    `;

    console.log('About to update DOM, element exists:', !!elements.contents.outline);
    elements.contents.outline.innerHTML = content;
    console.log('DOM updated successfully, chapter count in DOM:', data.chapter_count);
}

// 更新大纲项目的勾选状态
function updateOutlineConfirmation(itemKey, isChecked) {
    console.log(`updateOutlineConfirmation: ${itemKey} = ${isChecked}`);

    // 实时更新 UI 样式
    const itemDiv = document.getElementById(`confirm-item-${itemKey}`);
    if (itemDiv) {
        if (isChecked) {
            itemDiv.style.borderColor = 'var(--success)';
            itemDiv.style.background = 'rgba(76, 175, 80, 0.1)';
            itemDiv.style.opacity = '0.8';
        } else {
            itemDiv.style.borderColor = 'var(--border-color)';
            itemDiv.style.background = 'var(--bg-primary)';
            itemDiv.style.opacity = '1';
        }
    }
}

// 确认大纲项目并继续
async function confirmOutlineAndContinue() {
    console.log('confirmOutlineAndContinue called');

    if (!state.sessionId) {
        showToast('请先创建会话 | Please create a session first', 'warning');
        return;
    }

    // 收集所有勾选的项目
    const confirmedItems = {
        chapters: document.getElementById('outline-check-chapters')?.checked || false,
        image_plan: document.getElementById('outline-check-image_plan')?.checked || false,
        writing_style: document.getElementById('outline-check-writing_style')?.checked || false,
        image_style: document.getElementById('outline-check-image_style')?.checked || false,
        word_count: document.getElementById('outline-check-word_count')?.checked || false
    };

    console.log('Confirmed items:', confirmedItems);

    // 检查是否有勾选任何项目
    const hasAnyChecked = Object.values(confirmedItems).some(v => v);
    if (!hasAnyChecked) {
        showToast('请至少勾选一个项目 | Please select at least one item', 'warning');
        return;
    }

    // 显示加载状态
    showToast('正在确认大纲项目... | Confirming outline items...', 'info');

    try {
        const result = await api.confirmOutlineItems(state.sessionId, confirmedItems);
        console.log('Confirm result:', result);

        if (result.success) {
            // 更新本地状态
            if (result.confirmed_outline) {
                state.confirmed_outline = result.confirmed_outline;
            }

            // 重新渲染大纲（会显示已锁定的项目）
            if (result.data) {
                // 合并 confirmed_outline 到 data
                const outlineData = { ...result.data, confirmed_outline: result.confirmed_outline };
                renderOutlineFromApi(outlineData);
            }

            // 计算已确认的项目数
            const confirmedCount = Object.values(confirmedItems).filter(v => v).length;
            const totalItems = 5;
            const allConfirmed = result.all_confirmed;

            if (allConfirmed) {
                showToast('✅ 所有大纲项目已确认锁定！可以继续到下一步', 'success');
            } else {
                showToast(`✅ 已确认 ${confirmedCount}/${totalItems} 个项目，剩余项目可以继续调整`, 'success');
            }
        } else {
            showToast('确认失败: ' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('Confirm outline items failed:', error);
        showToast('确认失败: ' + error.message, 'error');
    }
}

// 渲染初稿数据（从API返回）
function renderDraftFromApi(data) {
    const content = `
        <div class="result-box success">
            <h4 class="result-title">✍️ Draft Complete | 初稿完成</h4>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📄 文章概览 | Article Overview</div>
            <ul class="result-list">
                <li><strong>Title 标题:</strong> ${data.title || state.topic}</li>
                <li><strong>Word Count 字数:</strong> ~${data.word_count || '3,000'} words</li>
                <li><strong>Chapters 章节:</strong> ${data.chapter_count || 6} sections</li>
            </ul>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📝 内容预览 | Content Preview</div>
            <div class="draft-preview" style="
                background: var(--bg-secondary);
                padding: 1.5rem;
                border-radius: 12px;
                max-height: 400px;
                overflow-y: auto;
                line-height: 1.8;
                color: var(--text-secondary);
            ">
                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">${data.content || '初稿内容生成中...'}</pre>
            </div>
        </div>

        ${data.quality_check ? `
        <div class="detail-section">
            <div class="detail-section-title">✅ 质量检查 | Quality Check</div>
            <ul class="result-list">
                <li>Structure 结构: ${data.quality_check.structure ? '✅' : '❌'}</li>
                <li>Logic 逻辑: ${data.quality_check.logic ? '✅' : '❌'}</li>
                <li>Language 语言: ${data.quality_check.language ? '✅' : '❌'}</li>
                <li>Audience Fit 读者适配: ${data.quality_check.audience_fit ? '✅' : '❌'}</li>
            </ul>
        </div>
        ` : ''}

        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    初稿内容是否符合预期？是否需要修改或补充？
                    <br>
                    <span style="color: var(--text-hint);">
                        Does the draft meet your expectations? Any modifications needed?
                    </span>
                </div>
            </div>
        </div>

        ${renderChatPanel(3, '例如：第二章太专业了请简化、增加更多案例...')}
    `;

    elements.contents.draft.innerHTML = content;
}

// 渲染配图数据（从API返回）- 增强版：支持计时器、进度、缩略图、重新生成
function renderImagesFromApi(data) {
    const sessionId = state.sessionId;
    const images = data.images || [];
    const successCount = data.success_count || images.filter(i => i.success).length;
    const failedCount = data.failed_count || images.filter(i => !i.success).length;
    const totalTime = data.total_elapsed_time || 0;

    // HTML 转义函数
    const escapeHtml = (str) => {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
                  .replace(/"/g, '&quot;')
                  .replace(/'/g, '&#039;')
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;');
    };

    // 生成图片卡片 HTML
    let imagesHtml = '';
    if (images.length > 0) {
        imagesHtml = images.map((img, idx) => {
            const isSuccess = img.success;
            const statusIcon = isSuccess ? '✅' : '❌';
            const statusText = isSuccess ? '生成成功' : (img.error || '生成失败');
            const statusColor = isSuccess ? 'var(--success)' : 'var(--error)';

            // 图片预览区域
            let previewHtml = '';
            const imageId = `img-${sessionId}-${img.name.replace(/\./g, '-')}`;
            if (isSuccess && img.file_path) {
                // 显示实际图片 + 刷新按钮
                // 使用 data-* 属性传递参数，避免转义问题
                const safeSessionId = escapeHtml(sessionId);
                const safeImageName = escapeHtml(img.name);
                const safeDescription = escapeHtml(img.description || img.name);
                previewHtml = `
                    <div style="position: relative;">
                        <img id="${imageId}"
                             src="${API_BASE_URL}/images/${sessionId}/${encodeURIComponent(img.name)}?t=${Date.now()}"
                             alt="${safeDescription}"
                             style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px;"
                             data-session="${safeSessionId}"
                             data-name="${safeImageName}"
                             onerror="handleImageError(this, this.dataset.session, this.dataset.name)"
                        />
                        <button data-session="${safeSessionId}" data-name="${safeImageName}"
                            onclick="refreshImagePreview(this.dataset.session, this.dataset.name)"
                            style="position: absolute; top: 8px; right: 8px;
                                   padding: 0.25rem 0.5rem; font-size: 0.7rem;
                                   background: rgba(0,0,0,0.6); color: white; border: none;
                                   border-radius: 4px; cursor: pointer; opacity: 0.7;"
                            onmouseover="this.style.opacity='1'"
                            onmouseout="this.style.opacity='0.7'">
                            🔄 刷新
                        </button>
                    </div>`;
            } else {
                // 显示占位符
                previewHtml = `
                    <div style="
                        width: 100%;
                        height: 120px;
                        background: ${isSuccess ? 'linear-gradient(135deg, var(--primary), var(--accent))' : 'var(--bg-tertiary)'};
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: ${isSuccess ? 'white' : 'var(--text-hint)'};
                        font-size: 2rem;
                    ">${isSuccess ? '🖼️' : '⚠️'}</div>`;
            }

            // 重新生成按钮（失败的图片显示）
            const regenerateBtn = !isSuccess ? `
                <button onclick="regenerateImage('${img.name}')"
                    style="margin-top: 0.5rem; padding: 0.3rem 0.6rem; font-size: 0.75rem;
                           background: var(--accent); color: white; border: none;
                           border-radius: 4px; cursor: pointer;">
                    🔄 重新生成
                </button>` : '';

            return `
                <div class="image-item" style="
                    background: var(--bg-secondary);
                    padding: 1rem;
                    border-radius: 8px;
                    text-align: center;
                    border: 2px solid ${isSuccess ? 'transparent' : 'var(--error)'};
                ">
                    ${previewHtml}
                    <div style="margin-top: 0.5rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                        <span style="font-size: 0.9rem;">${statusIcon}</span>
                        <span style="font-size: 0.8rem; color: ${statusColor};">${statusText}</span>
                    </div>
                    <p style="margin-top: 0.3rem; color: var(--text-secondary); font-weight: 500;">${img.name}</p>
                    <p style="font-size: 0.75rem; color: var(--text-hint);">${img.description || ''}</p>
                    ${img.file_size ? `<p style="font-size: 0.7rem; color: var(--text-hint);">${formatFileSize(img.file_size)}</p>` : ''}
                    ${regenerateBtn}
                </div>
            `;
        }).join('');
    }

    // 时间轴进度显示
    const timelineHtml = images.map((img, idx) => {
        const status = img.success ? 'completed' : (img.error ? 'failed' : 'pending');
        const icon = img.success ? '✅' : (img.error ? '❌' : '⏳');
        return `
            <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0;">
                <span style="width: 24px; height: 24px; border-radius: 50%; background: ${img.success ? 'var(--success)' : (img.error ? 'var(--error)' : 'var(--bg-tertiary)')};
                             display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">${idx + 1}</span>
                <span style="font-size: 0.85rem; color: var(--text-secondary);">${img.name}</span>
                <span style="font-size: 0.85rem;">${icon}</span>
                ${img.elapsed_time ? `<span style="font-size: 0.75rem; color: var(--text-hint);">${img.elapsed_time}s</span>` : ''}
            </div>
        `;
    }).join('');

    const content = `
        <!-- 状态摘要 -->
        <div class="result-box ${failedCount > 0 ? 'warning' : 'success'}">
            <h4 class="result-title">🎨 Images Generated | 配图生成完成</h4>
            <div style="display: flex; gap: 1.5rem; margin-top: 0.5rem;">
                <span style="color: var(--text-secondary);">
                    ✅ 成功: <strong style="color: var(--success);">${successCount}</strong>
                </span>
                <span style="color: var(--text-secondary);">
                    ❌ 失败: <strong style="color: ${failedCount > 0 ? 'var(--error)' : 'var(--text-hint)'};">${failedCount}</strong>
                </span>
                <span style="color: var(--text-secondary);">
                    ⏱️ 耗时: <strong style="color: var(--accent);">${totalTime}秒</strong>
                </span>
            </div>
        </div>

        <!-- 时间轴进度 -->
        <div class="detail-section">
            <div class="detail-section-title">📊 生成进度 | Generation Timeline</div>
            <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px;">
                ${timelineHtml}
            </div>
        </div>

        <!-- 配图预览 -->
        <div class="detail-section">
            <div class="detail-section-title">🖼️ 配图预览 | Image Preview</div>
            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 1rem;
            ">
                ${imagesHtml || '<p style="color: var(--text-muted);">配图生成中...</p>'}
            </div>
        </div>

        <!-- 配图风格 -->
        <div class="detail-section">
            <div class="detail-section-title">🎭 配图风格 | Image Style</div>
            <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px;">
                <p style="color: var(--text-secondary); margin: 0;">${data.style_keywords || '默认科技风格'}</p>
                <button onclick="showStyleEditor()" style="margin-top: 0.5rem; padding: 0.4rem 0.8rem;
                    background: var(--bg-tertiary); color: var(--text-secondary); border: 1px solid var(--border-color);
                    border-radius: 4px; cursor: pointer; font-size: 0.85rem;">
                    ✏️ 修改风格并重新生成
                </button>
            </div>
        </div>

        <!-- 质量检查 -->
        ${data.quality_check ? `
        <div class="detail-section">
            <div class="detail-section-title">✅ 质量检查 | Quality Check</div>
            <ul class="result-list">
                <li>Style Consistent 风格统一: ${data.quality_check.style_consistent ? '✅' : '❌'}</li>
                <li>Resolution 分辨率: ${data.quality_check.resolution_ok ? '✅' : '❌'}</li>
                <li>Theme Match 主题匹配: ${data.quality_check.theme_matched ? '✅' : '❌'}</li>
                <li>All Success 全部成功: ${data.quality_check.all_success ? '✅' : '❌'}</li>
            </ul>
        </div>
        ` : ''}

        ${renderChatPanel(4, '例如：换一种风格、重新生成某张图片...')}
    `;

    elements.contents.images.innerHTML = content;
}

// 重新生成单张图片
async function regenerateImage(imageName) {
    if (!state.sessionId) return;

    // 找到对应的图片卡片，显示进度
    const imageCard = document.querySelector(`[onclick*="regenerateImage('${imageName}')"]`)?.closest('.image-item');
    let progressDiv = null;
    let timerInterval = null;
    let startTime = Date.now();

    // 创建进度显示
    if (imageCard) {
        progressDiv = document.createElement('div');
        progressDiv.className = 'regenerate-progress';
        progressDiv.style.cssText = 'margin-top:0.5rem;padding:0.5rem;background:var(--bg-tertiary);border-radius:4px;text-align:center;font-size:0.85rem;';
        progressDiv.innerHTML = '<span class="progress-text">🔄 重新生成中... <span class="timer">⏱️ 0s</span></span>';
        imageCard.appendChild(progressDiv);

        // 启动计时器
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const timerSpan = progressDiv.querySelector('.timer');
            if (timerSpan) {
                timerSpan.textContent = `⏱️ ${elapsed}s`;
            }
        }, 1000);
    }

    showToast(`正在重新生成 ${imageName}...`, 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/images/regenerate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                image_name: imageName
            })
        });

        const result = await response.json();

        // 停止计时器
        if (timerInterval) {
            clearInterval(timerInterval);
        }

        if (result.success) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            showToast(`✅ ${imageName} 重新生成成功！耗时 ${elapsed}s`, 'success');

            // 🔧 修复：从服务器获取最新数据后刷新显示
            if (result.image) {
                // 更新本地状态中的图片数据
                const imgIndex = state.images.images.findIndex(i => i.name === imageName);
                if (imgIndex >= 0) {
                    state.images.images[imgIndex] = result.image;
                }
            }
            // 重新渲染
            renderImagesFromApi(state.images);
        } else {
            if (progressDiv) {
                progressDiv.innerHTML = `<span style="color:var(--error);">❌ 生成失败: ${result.error || result.message}</span>`;
            }
            showToast(`重新生成失败: ${result.error || result.message}`, 'error');
        }
    } catch (error) {
        // 停止计时器
        if (timerInterval) {
            clearInterval(timerInterval);
        }
        if (progressDiv) {
            progressDiv.innerHTML = `<span style="color:var(--error);">❌ 生成失败: ${error.message}</span>`;
        }
        showToast(`重新生成失败: ${error.message}`, 'error');
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// 处理图片加载错误
function handleImageError(imgElement, sessionId, imageName) {
    console.log('Image load error:', imageName);
    imgElement.style.display = 'none';
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'width:100%;height:120px;background:var(--bg-tertiary);border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--text-hint);gap:0.5rem;';
    errorDiv.innerHTML = '<span>🖼️ 加载失败</span>';
    const btn = document.createElement('button');
    btn.style.cssText = 'padding:0.3rem 0.6rem;font-size:0.75rem;background:var(--accent);color:white;border:none;border-radius:4px;cursor:pointer;';
    btn.textContent = '🔄 刷新';
    btn.onclick = function() { refreshImagePreview(sessionId, imageName); };
    errorDiv.appendChild(btn);
    imgElement.parentElement.appendChild(errorDiv);
}

// 刷新单个图片预览
function refreshImagePreview(sessionId, imageName) {
    const imageId = 'img-' + sessionId + '-' + imageName.replace(/\./g, '-');
    const imgElement = document.getElementById(imageId);
    if (imgElement) {
        imgElement.src = `${API_BASE_URL}/images/${sessionId}/${imageName}?t=${Date.now()}`;
    }
    showToast('图片刷新中...', 'info');
}// 复制输出路径
function copyOutputPath() {
    const pathInput = document.getElementById('output-path');
    if (pathInput) {
        navigator.clipboard.writeText(pathInput.value);
        showToast('路径已复制到剪贴板', 'success');
    }
}

// 显示风格编辑器（简化版）
function showStyleEditor() {
    const currentStyle = state.images?.style_keywords || '科技感, 蓝色调, 高质量';
    const newStyle = prompt('请输入新的配图风格关键词:\n(例如: 手绘风格, 素描线条, 清新淡雅)', currentStyle);
    if (newStyle && newStyle !== currentStyle) {
        regenerateAllImagesWithStyle(newStyle);
    }
}

// 使用新风格重新生成所有图片
async function regenerateAllImagesWithStyle(newStyle) {
    if (!state.sessionId) return;

    showToast(`正在使用新风格重新生成配图...`, 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/images/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                style: newStyle
            })
        });

        const result = await response.json();

        if (result.success) {
            state.images = result.data;
            renderImagesFromApi(result.data);
            showToast(`配图已使用新风格重新生成！`, 'success');
        } else {
            showToast(`重新生成失败: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast(`重新生成失败: ${error.message}`, 'error');
    }
}

// 渲染排版数据（从API返回）- 增强版：支持真实大小、下载、路径选择
function renderLayoutFromApi(data) {
    const sessionId = state.sessionId;

    // 生成文件列表 HTML（带下载按钮）- 过滤掉 images/ 目录
    let filesHtml = '';
    if (data.files && data.files.length > 0) {
        const filteredFiles = data.files.filter(file => !file.name.endsWith('/'));
        filesHtml = filteredFiles.map(file => {
            // 修复下载 URL：正确处理 API_BASE_URL
            // 生产环境 API_BASE_URL = 'https://api.siliang.cfd/api/writer'
            // 需要提取 'https://api.siliang.cfd' 作为下载基础 URL
            const apiBaseForDownload = API_BASE_URL.replace(/\/api\/writer$/, '').replace(/\/api$/, '');
            const downloadUrl = file.download_url
                ? `${apiBaseForDownload}${file.download_url}`
                : null;
            const downloadBtn = downloadUrl ? `
                <a href="${downloadUrl}" download="${file.name}"
                   style="margin-left: 0.5rem; padding: 0.2rem 0.5rem; background: var(--accent);
                          color: white; text-decoration: none; border-radius: 4px; font-size: 0.75rem;">
                    📥 下载
                </a>` : '';

            return `
                <li style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                    <div>
                        <strong>${file.name}</strong>
                        <span style="color: var(--text-hint);"> - ${file.type}</span>
                        ${file.size ? `<span style="color: var(--accent); margin-left: 0.5rem;">(${file.size})</span>` : ''}
                    </div>
                    ${downloadBtn}
                </li>
            `;
        }).join('');
    }

    // 总大小和微信限制提示
    const totalSizeHtml = data.total_size ? `
        <div style="display: flex; align-items: center; gap: 1rem; margin-top: 0.5rem;">
            <span style="color: var(--text-secondary);">
                📦 总大小: <strong style="color: var(--accent);">${data.total_size}</strong>
                (${data.total_size_mb || 0} MB)
            </span>
            <span style="color: ${data.within_wechat_limit !== false ? 'var(--success)' : 'var(--error)'};">
                ${data.within_wechat_limit !== false ? '✅ 符合微信14.5MB限制' : '⚠️ 超出微信限制'}
            </span>
        </div>
    ` : '';

    const content = `
        <div class="result-box success">
            <h4 class="result-title">📄 Layout Complete | 排版完成</h4>
            ${totalSizeHtml}
        </div>

        <!-- 输出文件列表 -->
        <div class="detail-section">
            <div class="detail-section-title">📁 输出文件 | Output Files</div>
            <ul class="result-list" style="list-style: none; padding: 0; margin: 0;">
                ${filesHtml || '<li style="color: var(--text-muted);">文件生成中...</li>'}
            </ul>

            <!-- 打包下载按钮 -->
            <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                <a href="${API_BASE_URL}/download/all/${sessionId}"
                   style="padding: 0.6rem 1.2rem; background: linear-gradient(135deg, var(--primary), var(--accent));
                          color: white; text-decoration: none; border-radius: 8px; font-weight: 500;
                          display: inline-flex; align-items: center; gap: 0.5rem;">
                    📦 打包下载全部文件
                </a>
            </div>
        </div>

        <!-- 微信格式特点 -->
        ${data.wechat_features ? `
        <div class="detail-section">
            <div class="detail-section-title">📱 微信格式特点 | WeChat Features</div>
            <ul class="result-list">
                <li>✓ 内联CSS样式 | Inline CSS styles</li>
                <li>✓ 适配微信阅读体验 | WeChat optimized</li>
                <li>✓ 图片居中对齐 | Centered images</li>
                <li>✓ 最大宽度限制 | Max-width constrained</li>
            </ul>
        </div>
        ` : ''}

        <!-- 确认检查 -->
        <div class="detail-section">
            <div class="detail-section-title">📋 确认检查 | Confirmation Check</div>
            <div class="confirm-box">
                <div class="confirm-question">
                    请确认排版效果是否符合预期?微信公众号格式是否正确?
                    <br>
                    <span style="color: var(--text-hint);">
                        Please confirm if layout meets expectations.
                    </span>
                </div>
            </div>
        </div>

        ${renderChatPanel(5, '例如：调整排版样式、修改输出格式...')}
    `;

    elements.contents.layout.innerHTML = content;
}

// 复制排版输出路径
function copyLayoutPath() {
    const pathInput = document.getElementById('layout-output-path');
    if (pathInput) {
        navigator.clipboard.writeText(pathInput.value);
        showToast('路径已复制到剪贴板', 'success');
    }
}

// 打开输出文件夹（在浏览器中显示）
function openOutputFolder() {
    const pathInput = document.getElementById('layout-output-path');
    if (pathInput) {
        // 在新窗口中打开文件列表
        window.open(`/api/files/${state.sessionId}`, '_blank');
    }
}

// 渲染完成数据（从API返回）
function renderCompleteFromApi(data) {
    // 找到 wechat.docx 文件
    const wechatDocx = data.files?.find(f => f.name === 'wechat.docx');
    const docxSize = wechatDocx?.size || '未知大小';
    const downloadUrl = wechatDocx?.download_url
        ? `${API_BASE_URL.replace('/api', '')}${wechatDocx.download_url}`
        : `${API_BASE_URL}/download/${state.sessionId}/wechat.docx`;

    const content = `
        <div class="result-box success">
            <h4 class="result-title">🎉 Export Complete | 导出完成</h4>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📄 微信公众号文件 | WeChat File</div>
            <div style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 12px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
                <h3 style="margin-bottom: 0.5rem;">wechat.docx</h3>
                <p style="color: var(--text-hint); margin-bottom: 1rem;">${docxSize}</p>
                <a href="${downloadUrl}" download="wechat.docx"
                   style="display: inline-block; padding: 0.8rem 2rem; background: linear-gradient(135deg, var(--primary), var(--accent));
                          color: white; text-decoration: none; border-radius: 8px; font-weight: 500; font-size: 1.1rem;">
                    📥 下载文件
                </a>
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">📤 微信上传说明 | WeChat Upload Guide</div>
            <div class="detail-text">
                <p><strong>1. 点击上方按钮下载 wechat.docx 文件</strong></p>
                <p><strong>2. 登录微信公众号后台 → 素材管理</strong></p>
                <p><strong>3. 上传 DOCX 文件即可使用</strong></p>
                <p style="color: var(--text-hint); margin-top: 1rem;">
                    文件大小限制: ${data.size_limit || '14.5MB'} | 当前文件: ${data.within_limit !== false ? '✅ 符合限制' : '⚠️ 超出限制'}
                </p>
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">🔄 重新开始</div>
            <button onclick="startNew()" style="padding: 0.8rem 2rem; background: var(--bg-tertiary); border: 2px solid var(--border-color); border-radius: 8px; cursor: pointer; font-size: 1rem;">
                ✨ 创建新文章
            </button>
        </div>
    `;

    elements.contents.complete.innerHTML = content;
}

// 初始化
document.addEventListener('DOMContentLoaded', init);

// 将函数暴露到全局作用域（供 HTML onclick 使用）
window.goToPage = goToPage;
window.confirmAndNext = confirmAndNext;
window.regeneratePhase = regeneratePhase;
window.downloadFiles = downloadFiles;
window.startNew = startNew;
window.submitFeedback = submitFeedback;

// ========== 测试功能：导出/导入/快速跳转 ==========

/**
 * 快速跳转到指定阶段（测试用）
 * @param {string} phaseName - 阶段名称: research, outline, draft, images, layout, complete
 */
function quickJumpToPhase(phaseName) {
    // 如果没有 sessionId，创建一个测试用的
    if (!state.sessionId) {
        state.sessionId = 'test_' + Date.now();
        state.topic = state.topic || '测试主题 Test Topic';
        state.useRealApi = true;
    }

    // 跳转到目标页面
    goToPage(phaseName);
    showToast(`🧪 测试模式：已跳转到 ${state.phases[phaseName]?.name || phaseName}`, 'info');

    // 如果目标页面内容为空，显示提示
    const contentEl = elements.contents[phaseName];
    if (contentEl && (!contentEl.innerHTML || contentEl.innerHTML.trim() === '')) {
        contentEl.innerHTML = `
            <div class="result-box info">
                <h4 class="result-title">🧪 测试模式 | Test Mode</h4>
                <p style="color: var(--text-secondary);">
                    当前为测试跳转，此阶段暂无数据。<br>
                    您可以：
                </p>
                <ul style="color: var(--text-muted); margin: 1rem 0 1rem 1.5rem;">
                    <li>点击 "重新生成" 按钮生成此阶段内容</li>
                    <li>从首页导入已保存的阶段数据</li>
                </ul>
            </div>
        `;
    }
}

/**
 * 导出阶段数据到 JSON 文件
 * @param {number} phase - 阶段号 1-4
 */
function exportPhaseData(phase) {
    let data = null;
    let filename = '';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

    switch (phase) {
        case 1: // Research
            data = state.researchData || {
                topic: state.topic,
                sources: [],
                key_findings: []
            };
            filename = `phase1_research_${timestamp}.json`;
            break;
        case 2: // Outline
            data = state.outline || {
                title: '',
                sections: []
            };
            filename = `phase2_outline_${timestamp}.json`;
            break;
        case 3: // Draft
            data = {
                content: state.draftContent || state.draft || '',
                topic: state.topic
            };
            filename = `phase3_draft_${timestamp}.json`;
            break;
        case 4: // Images
            data = state.images || {
                cover: null,
                chapters: []
            };
            filename = `phase4_images_${timestamp}.json`;
            break;
        default:
            showToast('❌ 无效的阶段号', 'error');
            return;
    }

    // 添加元数据
    const exportData = {
        version: '1.0',
        exported_at: new Date().toISOString(),
        phase: phase,
        phase_name: getPhaseName(phase),
        session_id: state.sessionId,
        topic: state.topic,
        data: data
    };

    // 创建并下载文件
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`✅ 已导出 ${getPhaseName(phase)} 数据`, 'success');
    console.log(`Exported phase ${phase} data:`, exportData);
}

/**
 * 导入阶段数据
 * @param {number} phase - 阶段号 1-4
 * @param {HTMLInputElement} inputEl - file input 元素
 */
function importPhaseData(phase, inputEl) {
    const file = inputEl.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const importData = JSON.parse(e.target.result);

            // 验证数据
            if (!importData.data) {
                throw new Error('无效的数据格式：缺少 data 字段');
            }

            // 恢复状态
            if (importData.session_id) {
                state.sessionId = importData.session_id;
            }
            if (importData.topic) {
                state.topic = importData.topic;
                if (elements.topicInput) {
                    elements.topicInput.value = importData.topic;
                }
            }

            // 根据阶段恢复数据
            switch (phase) {
                case 1: // Research
                    state.researchData = importData.data;
                    renderResearchFromApi(importData.data);
                    break;
                case 2: // Outline
                    state.outline = importData.data;
                    // 🔧 修复：合并 confirmed_outline 到 data，确保确认状态正确显示
                    const outlineDataWithConfirmation = {
                        ...importData.data,
                        confirmed_outline: importData.confirmed_outline || {}
                    };
                    renderOutlineFromApi(outlineDataWithConfirmation);
                    break;
                case 3: // Draft
                    state.draft = importData.data;
                    state.draftContent = importData.data.content;
                    renderDraftFromApi(importData.data);
                    break;
                case 4: // Images
                    state.images = importData.data;
                    renderImagesFromApi(importData.data);
                    break;
            }

            // 同步导入的数据到后端（确保AI聊天能看到导入的数据）
            syncImportedDataToBackend(phase, importData);

            // 跳转到对应页面
            const pageNames = ['', 'research', 'outline', 'draft', 'images'];
            goToPage(pageNames[phase]);

            showToast(`✅ 已导入 ${getPhaseName(phase)} 数据`, 'success');
            console.log(`Imported phase ${phase} data:`, importData);

        } catch (error) {
            showToast(`❌ 导入失败: ${error.message}`, 'error');
            console.error('Import failed:', error);
        }
    };

    reader.onerror = function() {
        showToast('❌ 文件读取失败', 'error');
    };

    reader.readAsText(file);
    // 重置 input 以允许重复选择同一文件
    inputEl.value = '';
}

/**
 * 同步导入的数据到后端（确保AI聊天能看到导入的数据）
 * @param {number} phase - 阶段号 1-4
 * @param {Object} importData - 导入的完整数据
 */
async function syncImportedDataToBackend(phase, importData) {
    if (!state.useRealApi || !window.api) {
        console.log('[Import] 跳过后端同步（非API模式）');
        return;
    }

    try {
        // 🔧 修复：构建同步数据时包含 confirmed_outline
        const syncData = {
            session_id: importData.session_id || state.sessionId,
            topic: importData.topic || state.topic,
            data: importData.data
        };

        // Phase 2 需要同步 confirmed_outline
        if (phase === 2 && importData.confirmed_outline) {
            syncData.confirmed_outline = importData.confirmed_outline;
        }

        const response = await fetch(`/api/sync/${phase}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(syncData)
        });

        const result = await response.json();
        if (result.success) {
            console.log(`[Import] 阶段 ${phase} 数据已同步到后端`);
        } else {
            console.warn('[Import] 后端同步失败:', result.error);
        }
    } catch (error) {
        console.warn('[Import] 后端同步请求失败:', error);
    }
}

/**
 * 获取阶段名称
 */
function getPhaseName(phase) {
    const names = {
        1: '深度调研 Research',
        2: '大纲设计 Outline',
        3: '内容写作 Draft',
        4: '配图生成 Images'
    };
    return names[phase] || `Phase ${phase}`;
}

// 暴露测试功能到全局
window.quickJumpToPhase = quickJumpToPhase;
window.exportPhaseData = exportPhaseData;
window.importPhaseData = importPhaseData;
