# AI Article Writer Skill - 需求收集对话记录

> 记录时间：2026-02-26
> 项目：CC_AI_WRITER

---

## 第一轮问答

### Q1: 文章类型
**问题**：你希望这个Skill专注写作什么类型的文章？

**用户选择**：**AI的科普文章**

---

### Q2: 写作环节
**问题**：这个Skill需要覆盖哪些写作环节？

**用户选择**：**全流程自动化 (推荐)**
- 调研→大纲→写作→排版，一步到位

---

### Q3: 输入方式
**问题**：用户调用这个Skill时，你期望用户提供什么输入信息？

**用户选择**：**灵活组合**
- 支持多种输入模式，由用户自行选择

---

### Q4: 输出格式
**问题**：输出格式有什么特殊要求？

**用户选择**：
- ✅ 微信公众号格式
- ✅ HTML富文本
- ✅ 多格式支持
- ✅ **增加交互模式：关键节点确认（大纲、初稿等关键阶段需要用户审核确认**

---

## 第二轮问答

### Q5: 调研深度
**问题**：AI科普文章需要什么程度的调研深度？

**用户选择**：**深度调研 (推荐)**
- 全面搜集10+信息源，包括官方文档、技术博客、研究论文等

---

### Q6: 确认节点
**问题**：在哪些关键节点需要用户确认？

**用户选择**：
- ✅ 大纲确认
- ✅ 调研报告确认
- ✅ 初稿审核
- ✅ 排版前确认

**4个确认节点全覆盖**

---

### Q7: 文章规格
**问题**：AI科普文章的典型长度是多少？

**用户补充**：
> "我希望你每次询问我是短、中、长文输出格式，另外再次强调我希望输出格式是富文本，并且带配图用Gemini API生成，我之后会在项目里配置好API和调用说明。"

---

### Q8: 写作风格
**问题**：AI科普文章的写作风格是什么？

**用户选择**：**灵活适配**
- 根据目标读者自动调整风格

---

## 第三轮问答

### Q9: 配图策略
**问题**：配图的数量和位置策略是什么？

**用户选择**：**章节配图 (推荐)**
- 封面图 + 每个章节一张配图，AI生成

---

### Q10: 图片风格
**问题**：AI生成配图的风格偏好？

**用户选择**：**主题适配**
- 根据文章主题自动选择合适风格

---

### Q11: Skill命名
**问题**：你希望这个Skill的命令名称是什么？

**用户选择**：**`/ai-article-writer`**

---

### Q12: 调研来源
**问题**：深度调研的信息来源渠道？

**用户选择**：**网络搜索**
- 使用WebSearch和WebFetch进行网络调研

---

## 第四轮问答

### Q13: Gemini API配置
**问题**：关于Gemini API的配置，你希望如何处理？

**用户选择**：**稍后配置 (推荐)**
- 先创建Skill，预留API配置位置，之后用户告知API调用方式

---

## 用户补充要求

### 1. 增加scripts目录
**用户反馈**：
> 是否需要在一级子目录下增加 "scripts"文件夹，并且在此文件夹下增加 `generate_image.py`

**处理**：已采纳，目录结构中增加 `scripts/generate_image.py`

---

### 2. 配图风格统一
**用户反馈**：
> Phase 4 配图生成中强调一条，所有配图的风格必须统一

**处理**：已采纳，在Phase 4中增加风格统一机制：
- 生成第一张图前先确定整体风格基调
- 记录风格关键词，所有配图复用
- 生成后进行风格一致性检查

---

## 最终需求汇总

| 维度 | 规格 |
|------|------|
| Skill名称 | `/ai-article-writer` |
| 文章类型 | AI科普文章 |
| 写作流程 | 全流程自动化（4个确认节点） |
| 调研深度 | 深度调研（网络搜索） |
| 确认节点 | 调研报告→大纲→初稿→排版前 |
| 文章长度 | 每次询问（短/中/长） |
| 配图策略 | 封面+每章节配图（Gemini API） |
| 图片风格 | 主题适配 + **风格统一** |
| 输出格式 | 微信公众号 + HTML富文本 |
| 写作风格 | 灵活适配 |
| API配置 | 稍后配置（预留接口） |

---

## Skill 目录结构

```
/Users/www.macpe.cn/.claude/skills/ai-article-writer/
├── SKILL.md                    # 主技能文件（核心工作流+SOP）
├── scripts/
│   └── generate_image.py       # Gemini图片生成脚本
├── references/
│   ├── workflow.md             # 详细工作流程SOP
│   ├── research-guide.md       # 深度调研指南
│   ├── writing-standards.md    # AI科普写作规范
│   ├── image-generation.md     # Gemini API配图指南
│   └── output-formats.md       # 输出格式模板（微信/HTML）
└── assets/
    └── templates/
        ├── wechat.html         # 微信公众号排版模板
        └── article.html        # 通用HTML富文本模板
```

---

## API配置

### Gemini API信息

| 项目 | 值 |
|------|-----|
| API端点 | `https://api.apicore.ai/v1/chat/completions` |
| 模型 | `gemini-3-pro-image-preview-4k` |
| API Key | `sk-3Qgr...dtoe` |
| 文档地址 | https://doc.apicore.ai/api-314031054 |

### 配置文件位置

```
/Users/www.macpe.cn/CC_AI_WRITER/
├── gemini_config.json              # 项目根目录配置
└── ai-article-writer/
    └── gemini_config.json          # Skill目录配置
```

---

## VSCode配置

### 刷新VSCode窗口

当修改配置文件后，需要刷新VSCode：

1. **重新加载窗口**：
   - 按 `Cmd + Shift + P` 打开命令面板
   - 输入 `Reload Window`
   - 回车执行

2. **或者直接关闭再打开项目文件夹**

### Markdownlint配置

项目根目录已创建 `.markdownlint.json` 禁用以下规则：

```json
{
  "MD013": false,  // 行长度限制
  "MD033": false,  // 内联HTML
  "MD040": false,  // 代码块语言标识
  "MD041": false,  // 首行标题
  "MD045": false   // 图片alt文本
}
```

---

## 使用方式

### 调用Skill

```bash
/ai-article-writer 什么是大语言模型？
```

### 单独生成配图

```bash
python3 ai-article-writer/scripts/generate_image.py \
  --prompt "AI概念图, 神经网络" \
  --style "科技感, 蓝色调, 几何图形, high quality" \
  --output "./output/test/images/cover.png" \
  --verbose
```

---

## 文件修复记录

### 2026-02-26 修复内容

1. **移动Skill到项目目录**
   - 从 `.claude/skills/` 移动到 `CC_AI_WRITER/ai-article-writer/`

2. **修复HTML模板图片路径**
   - `wechat.html`: 图片路径改为占位符 `{{COVER_IMAGE}}`
   - `article.html`: 图片路径改为占位符 `{{CHAPTER_IMAGE}}`

3. **修复Markdown链接**
   - `output-formats.md`: 占位符链接 `(URL)` → `(#)`
   - `workflow.md`: 目录链接改为普通文本

4. **添加配置文件**
   - `.markdownlint.json`: 禁用markdownlint警告
   - `gemini_config.json`: API配置

