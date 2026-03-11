# AI Article Writer

<p align="center">
  <strong>超级 AI 公众号文章自动化写作助手</strong>
</p>

<p align="center">
  支持从深度调研、大纲设计、内容撰写到多格式排版的全流程自动化
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#部署指南">部署指南</a> •
  <a href="#技术架构">技术架构</a>
</p>

---

## 功能特性

### 📝 6 阶段自动化写作流程

| 阶段 | 功能 | 说明 |
|------|------|------|
| **Phase 1** | 深度调研 | WebSearch + 微信公众号 + 小红书多源调研，10+ 信息源 |
| **Phase 2** | 大纲设计 | AI 智能生成结构化大纲，支持迭代优化 |
| **Phase 3** | 内容撰写 | 逐章节撰写，支持实时反馈修改 |
| **Phase 4** | 配图生成 | Gemini AI 生成封面 + 章节配图，风格统一 |
| **Phase 5** | 智能排版 | 自动排版，适配微信公众号格式 |
| **Phase 6** | 完成导出 | 多格式输出：HTML / DOCX / 微信公众号格式 |

### ✨ 核心亮点

- 🔍 **深度调研** - 整合搜狗搜索、微信公众号、小红书多平台信息
- 🤖 **AI 驱动** - GLM-4 智能内容生成，Gemini 高质量配图
- 💬 **对话式交互** - 每个阶段支持反馈修改，精准控制输出
- 📊 **多格式输出** - 一键导出微信公众号、HTML 富文本、Word 文档
- 🖼️ **自动配图** - AI 生成风格统一的封面和章节配图
- 🚀 **前后端分离** - 支持 Vercel + 云服务器灵活部署

---

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+ (可选，用于本地前端开发)

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/SM01-studio/AI-article-writer.git
cd AI-article-writer

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
cd ai-article-writer
pip install -r requirements.txt

# 4. 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 文件，填入 API Keys

# 5. 启动后端服务
cd web
python api_server.py

# 6. 访问前端页面
# 打开浏览器访问 http://localhost:8080
```

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```env
# API Keys (必填)
GLM_API_KEY=your_glm_api_key          # 智谱 AI API Key
GEMINI_API_KEY=your_gemini_api_key    # Gemini API Key

# 服务器配置
FLASK_ENV=development
SECRET_KEY=your_random_secret_key

# CORS 配置 (生产环境填写前端域名)
ALLOWED_ORIGINS=*
```

---

## 部署指南

### 架构说明

```
┌─────────────────┐     ┌─────────────────┐
│   Vercel        │     │   云服务器       │
│   (前端静态)     │────▶│   (后端 API)    │
│                 │     │                 │
│  HTML/CSS/JS    │     │  Flask + Task   │
└─────────────────┘     └─────────────────┘
```

### 前端部署 (Vercel)

1. 访问 [Vercel](https://vercel.com) 并登录
2. 点击 **Import Project** 导入 GitHub 仓库
3. 配置项目：
   - **Root Directory**: `ai-article-writer/web`
   - **Framework Preset**: Other
4. 点击 **Deploy** 部署

### 后端部署 (云服务器)

详细部署指南请查看 [deploy/README.md](deploy/README.md)

快速部署步骤：

```bash
# 1. 服务器安装依赖
sudo apt update && sudo apt install python3-pip nginx -y

# 2. 克隆代码
git clone https://github.com/SM01-studio/AI-article-writer.git
cd AI-article-writer

# 3. 配置环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r ai-article-writer/requirements.txt

# 4. 配置 .env 文件
cp .env.example .env
nano .env  # 填入 API Keys

# 5. 启动服务
sudo cp deploy/api-server.service /etc/systemd/system/
sudo systemctl start api-server
sudo systemctl enable api-server

# 6. 配置 Nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/api-server
sudo ln -s /etc/nginx/sites-available/api-server /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 技术架构

### 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | HTML5 + Tailwind CSS + Vanilla JavaScript |
| **后端** | Python + Flask + Flask-CORS |
| **AI 服务** | GLM-4 (智谱 AI) + Gemini (图片生成) |
| **搜索服务** | 搜狗搜索 + 微信公众号 + 小红书 |
| **部署** | Vercel (前端) + Nginx + Systemd (后端) |

### 项目结构

```
AI-article-writer/
├── ai-article-writer/           # 核心应用
│   ├── web/                     # Web 应用
│   │   ├── index.html           # 前端页面
│   │   ├── css/                 # 样式文件
│   │   ├── js/                  # JavaScript
│   │   ├── api_server.py        # 后端 API
│   │   ├── phase_handler.py     # 阶段处理器
│   │   ├── glm_service.py       # GLM 服务
│   │   ├── gemini_service.py    # Gemini 服务
│   │   └── vercel.json          # Vercel 配置
│   ├── scripts/                 # 工具脚本
│   ├── references/              # 参考文档
│   └── requirements.txt         # Python 依赖
├── deploy/                      # 部署配置
│   ├── api-server.service       # Systemd 服务
│   ├── nginx.conf               # Nginx 配置
│   └── README.md                # 部署指南
├── .env.example                 # 环境变量模板
└── README.md                    # 本文件
```

---

## API 服务

### 外部 API 依赖

| 服务 | 用途 | 获取方式 |
|------|------|----------|
| [智谱 AI](https://open.bigmodel.cn/) | 内容生成 | 注册获取 API Key |
| [Gemini](https://aistudio.google.com/) | 图片生成 | 注册获取 API Key |

### 主要 API 端点

```
POST /api/session/create          # 创建会话
POST /api/research/start          # 开始调研
POST /api/outline/generate        # 生成大纲
POST /api/draft/generate          # 撰写初稿
POST /api/images/generate         # 生成配图
POST /api/layout/generate         # 生成排版
GET  /api/export/complete         # 完成导出
```

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，欢迎提交 [Issue](https://github.com/SM01-studio/AI-article-writer/issues)
