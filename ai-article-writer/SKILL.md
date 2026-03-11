---
name: ai-article-writer
description: 超级AI公众号文章自动化写作助手。支持从深度调研、大纲设计、内容撰写到多格式排版的全流程自动化。触发场景：用户调用 /ai-article-writer、请求写作AI公众号文章、需要深度调研+写作。特色功能：4阶段确认机制、深度网络调研、AI生成配图、微信公众号/HTML富文本双格式输出。
---

# AI Article Writer

大师级公众号文章超级自动编写AI写作系统。

## 快速开始

```
/ai-article-writer 什么是大语言模型？
```

系统将引导你完成：
1. 选择文章长度（短/中/长）
2. 确认目标读者
3. 深度调研 → 调研报告确认
4. 生成大纲 → 大纲确认
5. 撰写初稿 → 初稿审核
6. 生成配图（Gemini API）
7. 排版输出 → 最终确认

## 核心工作流程

```
Phase 0: 初始化     → 解析主题 → 询问长度 → 确认读者
Phase 1: 深度调研   → WebSearch + MCP搜索(微信+小红书) → 阅读 → 调研报告 → 🔴确认
Phase 2: 大纲设计   → 结构 → 章节 → 配图规划 → 🔴确认
Phase 3: 内容写作   → 逐章写作 → 初稿 → 🔴确认
Phase 4: 配图生成   → 统一风格 → Gemini API → 风格检查
Phase 5: 排版输出   → 微信/HTML → 🔴确认 → 最终文件
```

## 搜索工具

深度调研阶段使用以下三个搜索工具进行多源信息收集：

| 工具 | 类型 | 功能 | 使用场景 |
|------|------|------|----------|
| **WebSearch** | 内置 | 网页搜索 | 官方文档、学术论文、技术博客 |
| **微信公众号** | MCP | 搜索公众号文章、获取正文 | 中文深度分析、专家观点、行业报告 |
| **小红书** | MCP | 搜索笔记、获取内容和评论 | 用户体验、应用案例、趋势观察 |

详细使用方法请参考 [references/research-guide.md](references/research-guide.md) 中的"MCP搜索工具"章节。

## 详细指南

### 执行各阶段时，阅读对应的参考文档：

| 阶段 | 参考文档 | 说明 |
|------|----------|------|
| Phase 1 | [references/research-guide.md](references/research-guide.md) | 深度调研方法论 |
| Phase 2 | [references/outline-generation.md](references/outline-generation.md) | 大纲生成标准 |
| Phase 2-3 | [references/writing-standards.md](references/writing-standards.md) | AI科普写作规范 |
| Phase 4 | [references/image-generation.md](references/image-generation.md) | Gemini配图指南 |
| Phase 5 | [references/output-formats.md](references/output-formats.md) | 输出格式规范 |
| 全流程 | [references/workflow.md](references/workflow.md) | 详细SOP |

### 配图生成脚本

Phase 4使用 `scripts/generate_image.py` 调用Gemini API：
```bash
python scripts/generate_image.py --prompt "描述" --style "科技感" --output "./images/cover.png"
```

### DOCX转换脚本

Phase 6使用 `scripts/html_to_docx.py` 将wechat.html转换为微信公众号可上传的docx格式：
```bash
# 基本用法（自动输出到同目录）
python scripts/html_to_docx.py --input "./output/文章标题/wechat.html"

# 指定输出路径
python scripts/html_to_docx.py --input "./output/文章标题/wechat.html" --output "./output/文章标题/wechat.docx"

# 自定义文件大小限制（默认14.5MB）
python scripts/html_to_docx.py --input "./output/文章标题/wechat.html" --max-size 10
```

**功能特点**：
- 自动压缩图片，控制文件大小在14.5MB以内
- 保持原有排版样式
- 支持表格、列表、引用等元素
- 自动处理中文字体

## 输出结构

```
output/[文章标题]/
├── content.md          # Markdown原文
├── wechat.html         # 微信公众号格式
├── article.html        # HTML富文本格式
└── images/
    ├── cover.png       # 封面图
    ├── chapter-1.png   # 第一章配图
    └── ...
```

## 关键原则

1. **4个确认节点**：调研报告、大纲、初稿、排版前必须用户确认
2. **配图风格统一**：同一篇文章所有配图使用相同的风格关键词
3. **读者适配**：根据目标读者调整语言深度和表达方式
4. **调研深度**：每篇文章至少10个高质量信息源

---

## 前端页面

### 文件结构

```
web/
├── index.html          # 主页面
├── css/
│   └── styles.css      # 自定义样式
└── js/
    └── app.js          # 交互逻辑
```

### 设计规范

基于 `ui-ux-pro-max` skill 生成的设计系统：

| 元素 | 规范 |
|------|------|
| **风格** | Swiss Modernism 2.0（网格系统、模块化、专业简洁） |
| **主色** | #6366F1 (Indigo) |
| **强调色** | #10B981 (Emerald) |
| **背景色** | #F5F3FF (浅紫) |
| **文字色** | #1E1B4B (深紫) |
| **字体** | Plus Jakarta Sans (Google Fonts) |

### 页面功能模块

1. **Hero 区域**
   - 标题 + 简介
   - 主题输入框（主要输入）
   - 快速开始按钮

2. **配置面板**
   - 文章长度选择：短篇(1500字) / 中篇(3000字) / 长篇(5000字)
   - 目标读者：技术从业者 / 大众 / 混合

3. **工作流进度**
   - 6阶段可视化进度条
   - 当前阶段高亮
   - 确认节点标记

4. **内容预览区**
   - 实时 Markdown 渲染
   - 配图预览

5. **导出选项**
   - 微信公众号格式
   - HTML 富文本格式
   - Markdown 原文

### 技术栈

- **HTML5** + **Tailwind CSS** (CDN)
- **Vanilla JavaScript** (无框架依赖)
- **Marked.js** (Markdown 渲染)

### 使用方式

**方式一：启动本地服务器（推荐）**

```bash
cd ai-article-writer/web
python3 server.py
```

服务启动后自动打开浏览器访问 `http://localhost:8080`

**方式二：直接打开文件**

在浏览器中打开 `web/index.html` 文件（部分功能可能受限）

### 开发步骤

1. 创建 `web/` 文件夹结构
2. 编写 `index.html` 主页面骨架
3. 添加 Tailwind CSS 样式
4. 实现 JavaScript 交互逻辑
5. 集成 Markdown 预览功能
6. 添加响应式适配
