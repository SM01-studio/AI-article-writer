# 输出格式规范

> AI Article Writer 的输出格式和排版指南

## 目录

1. [输出格式概览](#输出格式概览)
2. [微信公众号格式](#微信公众号格式)
3. [HTML富文本格式](#html富文本格式)
4. [Markdown格式](#markdown格式)
5. [文件命名规范](#文件命名规范)

---

## 输出格式概览

### 支持的格式

| 格式 | 文件 | 使用场景 |
|------|------|----------|
| Markdown | content.md | 原始文档、版本管理 |
| 微信公众号 | wechat.html | 微信公众号发布 |
| HTML富文本 | article.html | 网站、博客发布 |

### 输出目录结构

```
output/[文章标题]/
├── content.md          # Markdown原文
├── wechat.html         # 微信公众号格式
├── article.html        # HTML富文本格式
└── images/
    ├── cover.png       # 封面图
    ├── chapter-1.png   # 第一章配图
    ├── chapter-2.png   # 第二章配图
    └── ...
```

---

## 微信公众号格式

### 特点

- 使用**内联CSS样式**（微信不支持外部样式）
- 限制最大宽度
- 图片居中对齐
- 适配微信阅读体验

### 样式规范

```html
<!-- 段落样式 -->
<p style="margin: 0 0 16px 0; line-height: 1.8; color: #333; font-size: 16px;">
  段落内容
</p>

<!-- 标题样式 -->
<h1 style="margin: 24px 0 16px 0; font-size: 24px; font-weight: bold; color: #000;">
  一级标题
</h1>

<h2 style="margin: 20px 0 12px 0; font-size: 20px; font-weight: bold; color: #000;">
  二级标题
</h2>

<h3 style="margin: 16px 0 10px 0; font-size: 18px; font-weight: bold; color: #333;">
  三级标题
</h3>

<!-- 图片样式 -->
<div style="text-align: center; margin: 20px 0;">
  <img src="images/cover.png" style="max-width: 100%; height: auto;" alt="图片描述">
</div>

<!-- 引用样式 -->
<blockquote style="margin: 16px 0; padding: 12px 16px; background: #f5f5f5; border-left: 4px solid #007AFF; color: #666;">
  引用内容
</blockquote>

<!-- 列表样式 -->
<ul style="margin: 12px 0; padding-left: 24px; line-height: 1.8;">
  <li style="margin: 8px 0;">列表项</li>
</ul>

<!-- 强调样式 -->
<strong style="color: #007AFF; font-weight: bold;">重点内容</strong>

<!-- 分割线 -->
<hr style="margin: 24px 0; border: none; border-top: 1px solid #eee;">
```

### 完整模板

见 [assets/templates/wechat.html](../assets/templates/wechat.html)（模板文件）

### 微信格式注意事项

1. **不支持的元素**：
   - `<script>` 标签
   - 外部CSS链接
   - 部分HTML5标签
   - JavaScript交互

2. **图片处理**：
   - 本地图片需上传到微信服务器
   - 建议图片宽度不超过900px
   - 使用WebP或JPEG格式压缩

3. **字数限制**：
   - 单篇建议不超过20000字
   - 超长文章建议分篇

---

## HTML富文本格式

### 特点

- 完整HTML文档
- 响应式设计
- 优雅的排版样式
- 代码高亮支持

### 样式规范

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>文章标题</title>
  <style>
    /* 基础样式 */
    * {
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.8;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      background: #fff;
    }

    /* 标题样式 */
    h1 {
      font-size: 32px;
      font-weight: 700;
      margin: 40px 0 20px 0;
      color: #000;
      line-height: 1.3;
    }

    h2 {
      font-size: 24px;
      font-weight: 600;
      margin: 32px 0 16px 0;
      color: #111;
      border-bottom: 2px solid #007AFF;
      padding-bottom: 8px;
    }

    h3 {
      font-size: 20px;
      font-weight: 600;
      margin: 24px 0 12px 0;
      color: #222;
    }

    /* 段落样式 */
    p {
      margin: 0 0 16px 0;
      text-align: justify;
    }

    /* 图片样式 */
    img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 24px auto;
      border-radius: 8px;
    }

    /* 引用样式 */
    blockquote {
      margin: 20px 0;
      padding: 16px 20px;
      background: #f8f9fa;
      border-left: 4px solid #007AFF;
      color: #555;
      font-style: italic;
    }

    /* 代码样式 */
    code {
      background: #f4f4f4;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: "SF Mono", Consolas, monospace;
      font-size: 0.9em;
    }

    pre {
      background: #2d2d2d;
      color: #f8f8f2;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 20px 0;
    }

    pre code {
      background: none;
      padding: 0;
      color: inherit;
    }

    /* 列表样式 */
    ul, ol {
      margin: 16px 0;
      padding-left: 24px;
    }

    li {
      margin: 8px 0;
    }

    /* 表格样式 */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }

    th, td {
      padding: 12px;
      border: 1px solid #ddd;
      text-align: left;
    }

    th {
      background: #f5f5f5;
      font-weight: 600;
    }

    /* 分割线 */
    hr {
      margin: 32px 0;
      border: none;
      border-top: 1px solid #eee;
    }

    /* 响应式 */
    @media (max-width: 600px) {
      body {
        padding: 20px 16px;
      }

      h1 {
        font-size: 24px;
      }

      h2 {
        font-size: 20px;
      }
    }
  </style>
</head>
<body>
  <!-- 文章内容 -->
</body>
</html>
```

### 完整模板

见 [assets/templates/article.html](../assets/templates/article.html)（模板文件）

---

## Markdown格式

### 规范

使用标准GitHub Flavored Markdown (GFM)

### 模板

```markdown
# [文章标题]

> 作者：[作者名]
> 日期：[发布日期]
> 阅读时间：约[X]分钟

![封面图](images/cover.png)

## 引言

[引言内容...]

## 第一章：[标题]

[章节内容...]

![章节配图](images/chapter-1.png)

### 1.1 [小节标题]

[小节内容...]

> 引用内容示例

**重点强调**

- 列表项1
- 列表项2

## 第二章：[标题]

[章节内容...]

## 结语

[结语内容...]

---

*参考资料：*
1. [来源1](#)  <!-- 替换为实际URL -->
2. [来源2](#)  <!-- 替换为实际URL -->
```

---

## 文件命名规范

### 目录命名

```
output/
├── 什么是大语言模型-20240315/     # 主题-日期
├── AI Agent工作原理-20240320/
└── RAG技术详解-20240325/
```

### 文件命名

```
content.md          # 固定名称
wechat.html         # 固定名称
article.html        # 固定名称
images/
├── cover.png       # 封面图
├── chapter-1.png   # 按章节编号
├── chapter-2.png
└── ...
```

### 图片格式

| 用途 | 格式 | 说明 |
|------|------|------|
| 封面图 | PNG/JPEG | 建议PNG保持质量 |
| 章节图 | PNG/JPEG | 建议PNG保持质量 |
| 微信发布 | WebP/JPEG | 压缩后上传 |
