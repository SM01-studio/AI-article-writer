# CC_AI_WRITER 开发日志

> 项目：AI Article Writer - AI科普文章自动化写作助手

---

## 2026-03-10 (周二)

### 完成的工作

#### 0. 前端网页优化

**1. 星空背景增加星云效果**
- **需求**：让页面背景更好看
- **实现**：在 `initParticles` 函数中添加 2-3 个随机星云
- **效果**：蓝色、紫色、粉色、青色星云，带呼吸动画
- **修改文件**：`app.js:1871-1950`

**2. 大纲/初稿生成页面增加计时器**
- **需求**：生成长时间等待，需要显示计时
- **实现**：
  - Phase 2 大纲生成：显示 `⏱️ Xs` 计时
  - Phase 3 初稿撰写：显示 `⏱️ Xs` 计时
  - 任务完成后自动停止计时器
- **修改文件**：`app.js:524-570, 658-711`

**3. 移除首页测试面板**
- **需求**：前端测试基本完成，移除开发用测试面板
- **修改文件**：`index.html:133-153`

**4. 移除 Phase 4 输出路径显示**
- **需求**：输出路径不需要在页面显示
- **修改文件**：`app.js:2800-2813`

**5. 移除 Phase 5 输出路径显示**
- **需求**：输出路径不需要在页面显示
- **修改文件**：`app.js:3049-3066`

**6. 修复 Complete 页面下载按钮冲突**
- **问题**：页面底部 "Download Files 下载文件" 按钮与上方下载按钮功能冲突
- **修复**：移除底部按钮，保留 `renderCompleteFromApi` 中的 wechat.docx 下载按钮
- **修改文件**：`index.html:430-437`

#### 1. 修复 Phase 4 配图相关问题

**问题1：配图数量没有按锁定内容生成**
- **原因**：`generate_images_stream` 函数没有根据 `image_plan.chapters` 的长度来确定章节配图数量
- **修复**：修改 `api_server.py` 中的 `generate_images_stream` 函数，根据 `image_plan.chapters` 长度生成配图
- **修改文件**：`api_server.py:925-956`

**问题2：配图预览显示 `'" />` 乱码**
- **原因**：图片 URL 使用相对路径 `/api/images/...`，前端静态服务器无法代理到后端
- **修复**：修改 `app.js`，使用 `API_BASE_URL` 指向后端服务器
- **修改文件**：`app.js:2657, 2887`

**问题3：添加生图计时器**
- **需求**：生图等待时间长，需要显示计时
- **修复**：在 Phase 4 进度区域添加 `⏱️ 0s` 计时器，每秒更新
- **修改文件**：`app.js:753, 806-896`

**问题4：SSE 完成后 session 未同步**
- **原因**：Phase 4 SSE 完成后只更新内存中的 session，未同步到共享文件
- **修复**：添加 `shared_update_session` 调用
- **修改文件**：`api_server.py:1044-1046`

#### 2. 修复 Phase 5 排版输出问题

**问题1：文件下载失败**
- **原因**：下载 URL 使用相对路径，前端静态服务器无法代理
- **修复**：修改 `renderLayoutFromApi` 函数，使用 `API_BASE_URL`
- **修改文件**：`app.js:2948-2996`

**问题2：docx 文件无内容**
- **原因**：`generate_wechat_html` 函数将所有内容包裹在 `<p>` 标签内，导致无效 HTML 结构
- **修复**：重写 `generate_wechat_html` 函数，正确处理块级元素
- **修改文件**：`api_server.py:1404-1467`

**问题3：images/ 配图目录行显示**
- **需求**：不需要单独下载图片，去除该行
- **修复**：在 `renderLayoutFromApi` 中过滤掉目录项
- **修改文件**：`app.js:2945-2946`

**问题4：Phase 5 获取不到 session**
- **原因**：`generate_layout` 只检查内存中的 session，不检查共享文件
- **修复**：添加从共享文件获取 session 的逻辑
- **修改文件**：`api_server.py:1168-1177`

#### 3. 修复配图数量显示说明

**问题**：配图数量显示不清晰，用户不确定是否包含封面
- **修复**：
  - 前端显示改为 `X张（1封面 + N章节图）` 格式
  - 后端 AI 助手 prompt 中也使用相同格式
- **修改文件**：
  - `app.js:2315`
  - `api_server.py:2154, 2193`

### 修改文件汇总

| 文件 | 修改内容 |
|------|----------|
| `api_server.py` | 配图数量计算、session 同步、HTML 结构修复、配图数量显示 |
| `app.js` | 图片 URL、下载 URL、计时器、配图数量显示、过滤目录项 |

### 服务地址
- Frontend: http://localhost:8080
- API: http://localhost:5000

---

## 2026-03-09 (周一)

### 完成的工作

#### 1. 公众号文章生成任务
- **主题**：普通打工人如何用 Nano Banana 2 让自己减负
- **完成流程**：
  - 深度调研（WebSearch + 微信公众号 + 小红书三源搜索）
  - 大纲设计（7章节 + 4张配图，单线手绘极简风格）
  - 内容撰写
  - 配图生成
  - DOCX 输出与压缩
- **输出文件**：`wechat02.docx`

#### 2. 修复 Phase 2 导入 JSON 后确认窗口不显示的问题
- **问题**：用户导入 Phase1.json 文件并确认后，跳转到 Phase 2 时确认窗口不显示
- **根本原因**：
  1. `syncImportedDataToBackend()` 函数没有同步 `confirmed_outline` 字段
  2. 后端 `/api/sync/2` 路由没有保存 `confirmed_outline` 到共享文件
- **修复**：
  1. `app.js` - `syncImportedDataToBackend()` 添加 Phase 2 的 `confirmed_outline` 同步
  2. `api_server.py` - `/api/sync/2` 路由添加 `confirmed_outline` 保存到共享文件
- **修改文件**：
  - `app.js:3247-3273` - 修改同步函数，添加 confirmed_outline 支持
  - `api_server.py:267-277` - 修改 Phase 2 同步逻辑，保存 confirmed_outline

#### 3. 修复前端搜索使用 GLM API
- **问题**：前端网页搜索使用搜狗爬虫返回假数据
- **修复**：`/api/research/start` 路由改用 GLM API 搜索
- **修改文件**：`api_server.py:343-357`

#### 4. 修复 Phase 2 AI 助手 500 错误
- **问题**：`update_session` 函数名未定义
- **修复**：将所有 `update_session` 改为 `shared_update_session`
- **修改文件**：`api_server.py:610, 653, 1883, 1886`

#### 5. 修复 Phase 4 图片重新生成和缩略图显示问题
- **问题**：
  1. `regenerateImage` 函数没有从服务器获取更新后的数据
  2. 缩略图 `onerror` 和 `onclick` 中变量转义问题
- **修复**：
  1. `regenerateImage` 添加从服务器获取最新图片数据的逻辑
  2. 使用 `data-*` 属性传递参数，避免特殊字符转义问题
- **修改文件**：`app.js:2773-2801, 2607-2626`

### 待测试
- [ ] Phase 2 完整流程测试：导入 Phase1.json → 硟认 → 跳转 Phase 2 → 验证确认窗口显示
- [ ] Phase 4 图片重新生成功能测试

### 服务地址
- Frontend: http://localhost:8080
- API: http://localhost:5000

---

## 2026-03-08 (周日)

### 完成的工作

#### 7. Phase 2 勾选确认流程开发
- **问题**：大纲阶段需要类似 Phase 1 的勾选确认机制
- **解决方案**：
  1. 添加 5 个可确认项目：章节结构、配图规划、写作风格、配图风格、预计字数
  2. 每项显示勾选框，用户勾选后点击"更新确认"按钮锁定
  3. 已锁定的项目显示🔒，禁用勾选框
  4. AI 助手根据 confirmed_outline 状态，只处理未确认的项目
- **新增/修改文件**：
  - `api_server.py`:
    - `outline_feedback()` - 添加 type='confirmation' 处理
    - `handle_outline_chat()` - 添加 confirmed_outline 状态到 prompt
    - `/api/chat` - 返回 confirmed_outline
    - `generate_outline()` - 初始化 confirmed_outline
  - `app.js`:
    - `renderOutlineFromApi()` - 添加勾选确认 UI
    - `updateOutlineConfirmation()` - 更新勾选状态
    - `confirmOutlineAndContinue()` - 确认并锁定项目
    - `refreshPhaseContent()` - 传递 confirmed_outline
  - `api.js`:
    - `confirmOutlineItems()` - 新增 API 方法

#### 8. 修复配图数量计算（包括封面）
- **问题**：配图数量计算不正确，没有包括封面
- **修复**：修改 `handle_outline_chat()` 中的数量计算逻辑
- **修改文件**：`api_server.py`
  - 配图数量 = 1（封面）+ 章节图数量
  - 用户修改配图数时，章节图 = 总数 - 1

#### 9. 修复封面尺寸为 16:9
- **问题**：封面尺寸是 1024x1024（方形），不符合公众号文章习惯
- **修复**：将封面尺寸改为 1024x576（16:9）
- **修改文件**：
  - `api_server.py` - 所有封面尺寸改为 1024x576
  - `phase_handler.py` - 大纲生成时封面尺寸
  - `glm_service.py` - GLM 服务生成时封面尺寸
  - `gemini_service.py` - Gemini 配图生成时封面尺寸
  - `app.js` - 前端显示默认尺寸

#### 1. Phase 4 配图生成实时进度显示
- **问题**：配图生成页面是静态等待，用户不知道进度
- **修复**：修复后端 SSE 路由方法（POST → GET），实现实时进度显示
- **文件**：`api_server.py`

#### 2. Phase 1/2 AI 助手对话刷新主界面
- **问题**：用户反馈后，AI助手窗口有回复，但主界面没有刷新
- **修复**：修改 `handle_research_chat` 和 `handle_outline_chat`，使用与 Phase 3 相同的处理逻辑
- **文件**：`api_server.py`

#### 3. 修复多次修改数据丢失问题
- **问题**：用户第二次修改时，第一次的修改内容会丢失
- **修复**：在每次更新前先获取最新的 session 数据，只更新 AI 返回的字段
- **涉及**：Phase 1、2、3 的 Chat 处理函数

#### 4. 优化大纲修改逻辑
- **问题**：AI 每次都会重新生成章节，覆盖之前的修改
- **修复**：优化 prompt，明确告诉 AI 只返回用户要求修改的字段
- **文件**：`api_server.py` - `handle_outline_chat`

#### 5. Phase 1 新流程：勾选确认 + 锁定机制
- **问题**：AI 大模型处理搜索结果不准确，用户无法精确控制保留哪些来源
- **解决方案**：
  1. 每条搜索结果显示勾选框
  2. 用户勾选后点击"更新"确认
  3. 已确认的来源显示🔒锁定状态
  4. 新搜索的内容追加到待确认区域
- **新增文件**：
  - `references/outline-generation.md` - 大纲生成标准文档
- **修改文件**：
  - `app.js` - `renderResearchFromApi()` 添加勾选框和更新按钮
  - `api_server.py` - 添加 confirmed_sources 和 pending_sources 字段

#### 6. 创建大纲生成标准文档
- **文件**：`references/outline-generation.md`
- **内容**：
  - 大纲 JSON 格式规范
  - 章节结构规范（章节数量、顺序）
  - 标题规范（必须具体化、禁止泛泛标题）
  - 描述规范（80-150字，包含4个要素）
  - Key Points 规范（3-5个要点）
  - 修改流程规范（只修改用户要求的字段）
- **更新**：`SKILL.md` 添加大纲标准文档引用

### 技术细节

#### 后端修改
- `api_server.py`:
  - `handle_research_chat()` - Phase 1 对话处理
  - `handle_outline_chat()` - Phase 2 大纲对话处理
  - `handle_draft_chat()` - Phase 3 初稿对话处理
  - `/api/images/generate/stream` - SSE 路由 GET 方法
  - `start_research()` - 添加 pending_sources 和 confirmed_sources 字段
  - `research_feedback()` - 处理搜索结果确认

#### 前端修改
- `app.js`:
  - `renderResearchFromApi()` - 重写，添加勾选确认功能
  - `updateResearchConfirmation()` - 新增，更新确认状态
  - `confirmResearchAndContinue()` - 新增，确认并继续

### 待测试/待优化
- [x] Phase 1 勾选确认流程（基本可用，有小问题后续优化）
- [x] Phase 2 勾选确认流程（已完成）
- [ ] Phase 3 多次修改数据保留

### 服务地址
- Frontend: http://localhost:8080
- API: http://localhost:5000

---

## 历史记录

### 2026-02-26 (需求收集)
- 完成需求调研对话
- 确定全流程自动化（4个确认节点）
- 确定配图策略（Gemini API，风格统一）
- 创建目录结构和配置文件
