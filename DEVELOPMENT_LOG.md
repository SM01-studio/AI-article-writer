# CC_AI_WRITER 开发日志

> 项目：AI Article Writer - AI科普文章自动化写作助手

---

## 2026-03-19 (周四)

### 完成的工作

#### 1. 修复 Chrome 浏览器卡顿问题

**问题**：从主门户跳转到 AI Writer 子页面后，Chrome 浏览器严重卡顿，粒子效果迟缓

**排查过程**：
1. 怀疑粒子效果优化导致 → 回滚代码后问题依旧
2. Safari 浏览器正常 → 排除代码问题
3. 最终确认：Chrome 缓存了线上错误的代码

**解决**：清除 Chrome 浏览器缓存（`Cmd+Shift+R` 强制刷新）

---

#### 2. 修复 Phase 4 字数统计问题

**问题**：Phase 4 完成正文环节，字数统计显示不正确

**原因**：`len(content)` 计算的是字符数，不是字数

**修复**：添加 `count_words()` 函数，准确计算中英文字数
```python
def count_words(text: str) -> int:
    """统计文本字数（中英文混合）"""
    import re
    if not text:
        return 0
    # 移除 Markdown 标记
    text = re.sub(r'[#*_`~\[\]()>-]', '', text)
    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计英文单词
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words
```

**修改文件**：`api_server.py`

---

#### 3. 修复 Phase 5 下载路径问题

**问题**：Phase 5 下载按钮无响应，下载路径不正确

**原因**：`API_BASE_URL.replace('/api', '')` 在生产环境下错误
- 生产环境 `API_BASE_URL` = `https://api.siliang.cfd/api/writer`
- `.replace('/api', '')` = `https://api.siliang.cfd/writer`（错误）

**修复**：使用正则表达式正确提取基础 URL
```javascript
const apiBaseForDownload = API_BASE_URL.replace(/\/api\/writer$/, '').replace(/\/api$/, '');
```

**修改文件**：`app.js`

---

#### 4. 优化页面跳转速度（认证缓存）

**问题**：从主门户跳转到子页面等待时间过长

**原因**：每次访问都需等待认证 API 验证（约 1.1 秒）

**优化方案**：
- 添加 5 分钟缓存，避免重复验证
- 添加 3 秒超时保护
- 网络错误时使用缓存结果继续

**修改文件**：`app.js` - `verifyAuth()` 函数

---

#### 5. 增加 SSE 超时时间

**问题**：Phase 4 配图生成超过 5 分钟后前端超时

**修复**：SSE 超时从 5 分钟增加到 15 分钟

**修改文件**：`app.js`

---

### 待解决问题

#### Phase 4 配图生成失败

**现象**：配图生成 2 分钟后连接断开，显示"配图生成服务暂时不可用"

**排查结果**：
- 前端 SSE 超时：已增加到 15 分钟 ✅
- Nginx 超时：600s 配置正确 ✅
- Gemini API 密钥：有效 ✅
- **根本原因**：第三方 API `api.apicore.ai` 返回 524 超时错误（Cloudflare 超时）

**状态**：⏸️ 等待第三方 API 服务恢复

---

### 已推送的 Git 提交

| 提交 | 说明 |
|------|------|
| `6350eda` | fix: Phase 4 word count and Phase 5 download URL |
| `a202ed5` | perf: Add auth cache and timeout to speed up page load |
| `4de7a2c` | fix: Increase SSE timeout to 15min for image generation |

---

### 测试结果汇总

| 阶段 | 功能 | 状态 |
|------|------|------|
| 首页 | 页面加载 | ✅ 正常 |
| 跳转 | 主门户 → 子页面 | ✅ 优化后快速 |
| Phase 1 | 深度调研 | ✅ 通过 |
| Phase 2 | 大纲设计 | ✅ 通过 |
| Phase 3 | 内容撰写 | ✅ 通过 |
| Phase 4 | AI 配图 | ⏸️ 第三方 API 超时 |
| Phase 5 | 排版输出 | 待测试 |
| Phase 6 | 完成导出 | 待测试 |

---

## 2026-03-17 (周一)

### 完成的工作

#### 1. 修复 Phase 2 字数设置不同步问题

**问题**：首页选择 short ~1500字，但 Phase 2 大纲确认显示 ~3000字

**原因**：`phase_handler.py` 中的 `generate_outline_template` 函数字数定义与前端不一致

**字数映射对比**：
| 长度 | 前端/app.js | glm_service.py | phase_handler.py (修复前) |
|------|-------------|----------------|---------------------------|
| short | ~1500 | 1500 | **2000** ❌ |
| medium | ~3000 | 3000 | **4000** ❌ |
| long | ~8000 | 8000 | 8000 ✅ |

**修复**：统一 `phase_handler.py` 中的字数定义
- short: 2000 → 1500
- medium: 4000 → 3000

**修改文件**：`phase_handler.py:255, 265`

**部署**：已同步到生产服务器，服务已重启

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
  - Phase 3 初稿撰写:显示 `⏱️ Xs` 计时
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

---

#### 1. 修复 Phase 4 配图相关问题

**问题1: 配图数量没有按锁定内容生成**
- **原因**：`generate_images_stream` 函数没有根据 `image_plan.chapters` 的长度来确定章节配图数量
- **修复**：修改 `api_server.py` 中的 `generate_images_stream` 函数,根据 `image_plan.chapters` 长度生成配图
- **修改文件**：`api_server.py:925-956`

---

## 2026-03-12 (周四) 🎉 项目上线成功！

### 完成的工作

#### 1. 完成部署上线

**最终部署架构**:
| 组件 | 地址 | 状态 |
|------|------|------|
| **前端** | https://siliang.cfd/ | ✅ 运行中 |
| **后端 API** | https://api.siliang.cfd/ | ✅ 运行中 |
| **GitHub** | https://github.com/SM01-studio/AI-article-writer | ✅ 已发布 |

**服务器配置**:
| 服务 | 状态 | 说明 |
|------|------|------|
| `ai-article-api` | ✅ | Flask API 服务器 |
| `ai-article-task-processor` | ✅ | 后台任务处理器 |
| `nginx` | ✅ | 反向代理 + SSL |

#### 2. 修复的问题

**问题1: DNS 配置**
- 为 `api.siliang.cfd` 添加 A 记录指向 `47.79.0.228`

**问题2: SSL 证书申请**
- 使用 Certbot 申请 Let's Encrypt SSL 证书
- 配置 HTTPS (443端口)

**问题3: CORS 配置**
- 更新 `ALLOWED_ORIGINS` 环境变量
- 添加 `https://siliang.cfd` 到允许列表

**问题4: 任务处理器未运行**
- 创建 `ai-article-task-processor.service` systemd 服务
- 启动后台任务处理（处理 Phase 1 搜索任务）

**问题5: SSE 超时配置**
- 更新 Nginx SSE 专用配置
- 超时时间增加到 10 分钟
- 禁用缓冲确保实时推送

**问题6: SSL 配置丢失**
- 更新 Nginx 配置时意外覆盖 SSL 配置
- 恢复完整的 HTTPS 配置

#### 3. 功能验证

| 阶段 | 功能 | 状态 |
|------|------|------|
| Phase 1 | 深度调研 | ✅ 通过 |
| Phase 2 | 大纲设计 | ✅ 通过 |
| Phase 3 | 内容撰写 | ✅ 通过 |
| Phase 4 | AI 配图 | ✅ 通过 |
| Phase 5 | 多格式排版 | ✅ 通过 |
| Phase 6 | 完成导出 | ✅ 通过 |

#### 4. 演示视频添加到 GitHub

**视频压缩**:
- 原始视频: 127MB（超过 GitHub 100MB 限制）
- 压缩命令: `ffmpeg -i demo.mp4 -vcodec h264 -crf 28 -preset fast CC-AI-Writer-compressed.mp4`
- 压缩后: 6.8MB
- 上传到 GitHub README

**修改文件**:
- `README.md` - 添加演示视频部分

#### 5. 本地开发启动脚本

创建 `start-local.sh` 脚本，方便本地开发时同时启动前端和后端：
```bash
#!/bin/bash
# 启动后端
cd ai-article-writer/backend && source venv/bin/activate && python api_server.py &
# 启动前端
cd ../web && python -m http.server 8080 &
```

**修改文件**:
- `ai-article-writer/web/start-local.sh`

### 里程碑 🏆

**2026-03-12** - AI Article Writer 项目成功上线！

- 从本地开发项目到真正可在线访问的产品
- 前后端分离部署（Vercel + 阿里云）
- HTTPS 安全连接
- 完整的 6 阶段写作流程验证通过
- 演示视频成功上传到 GitHub

---

## 2026-03-12 (周四) 下午 - 新项目启动

### Siliang AI LAB 主门户项目

**项目概述**:
创建一个统一的主门户系统，用于管理多个 AI Web 应用。

**项目位置**: `/Users/www.macpe.cn/siliang-ai-lab/`

**功能规划**:
| 功能模块 | 说明 |
|----------|------|
| 登录/注册 | 用户身份验证 |
| 用户管理 | 管理员 + 普通用户角色 |
| 应用仪表板 | 展示所有可用应用（缩略图卡片） |
| 应用集成 | 集成现有 AI Article Writer |

**技术栈**:
| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS + Vanilla JavaScript |
| 后端 | Python + Flask |
| 数据库 | SQLite |
| 认证 | JWT Token |

**目录结构**:
```
siliang-ai-lab/
├── web/                 # 前端
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── login.html       # 登录/注册页
│   └── dashboard.html   # 应用仪表板
├── backend/             # Flask API
│   ├── app.py           # 主程序
│   ├── auth.py          # 认证模块
│   └── models.py        # 数据模型
├── data/                # SQLite 数据库
└── README.md
```

**状态**: 🚧 项目初始化中

---

## 2026-03-11 (周三)

### 完成的工作

#### 1. 项目部署上线（第一阶段）

**部署架构**:
- **前端**: Vercel (https://ai-article-writer-eta.vercel.app/, https://siliang.cfd/)
- **后端**: 阿里云服务器 Ubuntu 22.04 (http://47.79.0.228/api)
- **GitHub**: https://github.com/SM01-studio/AI-article-writer

**部署步骤**:

1. **代码改造**（本地）
   - API Key 改为环境变量读取 (`glm_service.py`, `gemini_service.py`)
   - 前端 API 地址配置化 (`api.js`, `config.js`)
   - CORS 生产环境配置 (`api_server.py`)
   - 创建 `.gitignore`, `.env.example`, `vercel.json`

2. **GitHub 仓库**
   - 初始化 Git 仓库
   - 推送代码到 https://github.com/SM01-studio/AI-article-writer
   - 创建 README.md 项目文档

3. **前端 Vercel 部署**
   - 导入 GitHub 项目
   - Root Directory: `ai-article-writer/web`
   - 部署地址: https://ai-article-writer-eta.vercel.app/
   - 自定义域名: https://siliang.cfd/

4. **后端云服务器部署**
   - 服务器: 阿里云 2核2G ¥39/月
   - IP: 47.79.0.228
   - 安装: Python 3.10, Nginx, Git
   - 克隆代码并安装 Python 依赖
   - 配置 .env 环境变量 (GLM_API_KEY, GEMINI_API_KEY)
   - 配置 Systemd 服务: `ai-article-api.service`
   - 配置 Nginx 反向代理

**当天状态**:
- ✅ 前端已部署 (Vercel)
- ✅ 后端已部署 (阿里云)
- ⚠️ 待解决: HTTPS/SSL 配置 (Mixed Content 问题)

---

#### 2. 新建部署相关文件

| 文件 | 说明 |
|------|------|
| `.gitignore` | Git 忽略配置，排除敏感文件 |
| `.env.example` | 环境变量模板 |
| `config.js` | 前端配置文件（设置 API 地址） |
| `vercel.json` | Vercel 部署配置 |
| `deploy/` | 部署配置目录 |
| `deploy/api-server.service` | Systemd 服务配置 |
| `deploy/nginx.conf` | Nginx 反向代理配置 |
| `deploy/README.md` | 部署指南文档 |
| `README.md` | 项目文档 |

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
