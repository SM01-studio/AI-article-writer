# Gemini API 配图指南

> AI Article Writer 的AI配图生成指南

## 目录

1. [配置说明](#配置说明)
2. [API信息](#api信息)
3. [风格统一机制](#风格统一机制)
4. [Prompt模板](#prompt模板)
5. [风格关键词库](#风格关键词库)
6. [生成脚本使用](#生成脚本使用)
7. [常见问题](#常见问题)

---

## 配置说明

### ✅ 已配置完成

API配置已保存在项目根目录 `gemini_config.json`：

```json
{
  "api_key": "sk-3QgrJaeHnxNei4C37WEULwaSed2loJmGbJ79Cug3bpYrdtoe",
  "endpoint": "https://api.apicore.ai/v1/chat/completions",
  "model": "gemini-3-pro-image-preview-4k"
}
```

### 配置文件位置

脚本会按以下顺序查找配置文件：
1. 项目根目录: `/CC_AI_WRITER/gemini_config.json`
2. Skill目录: `/skills/ai-article-writer/gemini_config.json`
3. 用户目录: `~/.gemini/config.json`

---

## API信息

### 基本信息

| 项目 | 值 |
|------|-----|
| API端点 | `https://api.apicore.ai/v1/chat/completions` |
| 模型名称 | `gemini-3-pro-image-preview-4k` |
| 请求格式 | OpenAI兼容格式 |
| 文档地址 | https://doc.apicore.ai/api-314031054 |

### 请求示例

```bash
curl --location --request POST 'https://api.apicore.ai/v1/chat/completions' \
--header 'Authorization: Bearer sk-xxxx' \
--header 'Content-Type: application/json' \
--data-raw '{
    "model": "gemini-3-pro-image-preview-4k",
    "stream": false,
    "messages": [
        {
            "role": "user",
            "content": "A beautiful sunset over mountains"
        }
    ]
}'
```

### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| model | string | 是 | 固定值 `gemini-3-pro-image-preview-4k` |
| stream | boolean | 否 | 是否流式返回，建议 `false` |
| messages | array | 是 | OpenAI格式的消息数组 |
| messages[].role | string | 是 | 固定值 `user` |
| messages[].content | string | 是 | 图片描述prompt |

---

## 风格统一机制

### 核心原则

⚠️ **同一篇文章的所有配图必须使用统一的视觉风格**

### 实现方式

#### Step 1: 确定风格基调

在生成第一张图前，确定以下风格维度：

```
风格基调 = {
  "色调": "冷色调（蓝/紫）",
  "风格": "科技感",
  "元素": "几何图形 + 渐变",
  "氛围": "未来感",
  "质量": "high quality, detailed, 4K"
}
```

#### Step 2: 生成风格关键词

将风格基调转换为Prompt关键词：

```
风格关键词 = "科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"
```

#### Step 3: 复用风格关键词

**所有配图使用相同的风格关键词**：

```
封面prompt = "AI大语言模型概念图, [风格关键词]"
章节1 prompt = "Transformer架构可视化, [风格关键词]"
章节2 prompt = "神经网络连接图, [风格关键词]"
章节3 prompt = "AI应用场景, [风格关键词]"
```

#### Step 4: 风格一致性检查

生成后检查：
- [ ] 所有图片色调是否一致
- [ ] 所有图片风格是否一致
- [ ] 图片与内容是否契合

如发现偏差，使用相同风格关键词重新生成。

---

## Prompt模板

### 封面图模板

```
模板：
"[主题核心概念] visualization, [主题关键元素], [风格关键词]"

示例：
"Large Language Model concept visualization, neural network, data flow, 科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"
```

### 章节图模板

```
模板：
"[章节核心概念] illustration, [章节关键元素], [风格关键词]"

示例：
"Transformer architecture illustration, attention mechanism, self-attention layers, 科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"
```

### 概念解释图模板

```
模板：
"[概念名称] explanation diagram, [概念要素], [风格关键词]"

示例：
"Embedding vector space explanation diagram, word vectors, semantic similarity, 科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"
```

### 应用场景图模板

```
模板：
"[应用场景] scene, [场景元素], [风格关键词]"

示例：
"AI assistant helping with writing scene, human and AI collaboration, modern office, 科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"
```

---

## 风格关键词库

### 按色调分类

| 色调 | 关键词 |
|------|--------|
| 冷色调 | 蓝色调, 紫色调, 青色, 深蓝, 渐变蓝 |
| 暖色调 | 橙色调, 红色调, 金色, 暖黄 |
| 中性色 | 黑白灰, 银色, 白色背景 |
| 多彩 | 彩虹色, 渐变彩虹, 霓虹 |

### 按风格分类

| 风格 | 关键词 |
|------|--------|
| 科技感 | 科技感, 未来感, 赛博朋克, 数字化, 数据可视化 |
| 简约 | 简约, 极简主义, 扁平化, 清晰 |
| 写实 | 写实, 照片级, 真实感, 3D渲染 |
| 插画 | 插画风格, 手绘感, 卡通, 可爱 |
| 抽象 | 抽象, 艺术感, 创意, 概念艺术 |

### 按元素分类

| 元素 | 关键词 |
|------|--------|
| 几何 | 几何图形, 六边形, 球体, 线条, 网格 |
| 自然 | 自然元素, 有机形态, 流动, 波浪 |
| 科技元素 | 电路板, 神经网络, 节点连接, 粒子 |
| 人物 | 人物剪影, 团队协作, 商务场景 |

### 按氛围分类

| 氛围 | 关键词 |
|------|--------|
| 专业 | 专业, 商务, 企业级, 严肃 |
| 活泼 | 活泼, 轻松, 有趣, 友好 |
| 神秘 | 神秘, 深邃, 未知, 探索 |
| 未来 | 未来感, 前沿, 创新, 突破 |

### 推荐风格组合

**AI科普文章推荐组合**：

```
组合1：科技未来风（推荐）
"科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K"

组合2：简约专业风
"简约, 极简主义, 白色背景, 清晰, 专业, high quality, clean"

组合3：数据可视化风
"数据可视化, 深蓝背景, 发光线条, 网格, 科技感, high quality, detailed"

组合4：友好插画风
"插画风格, 柔和色调, 友好, 清晰, 现代, high quality, cute"
```

---

## 生成脚本使用

### 基本用法

```bash
# 生成封面图
python scripts/generate_image.py \
  --prompt "AI大语言模型概念图, 神经网络, 数据流" \
  --style "科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K" \
  --output "output/[文章标题]/images/cover.png"

# 生成章节图
python scripts/generate_image.py \
  --prompt "Transformer架构, 注意力机制, 自注意力层" \
  --style "科技感, 蓝色调, 几何图形, 渐变, 未来感, high quality, detailed, 4K" \
  --output "output/[文章标题]/images/chapter-1.png"
```

### 详细模式

```bash
python scripts/generate_image.py \
  --prompt "..." \
  --style "..." \
  --output "..." \
  --verbose
```

### 批量生成

```bash
# 在workflow中批量生成所有配图
for i in {1..5}; do
  python scripts/generate_image.py \
    --prompt "[章节$i核心概念]" \
    --style "[统一风格关键词]" \
    --output "output/[文章标题]/images/chapter-$i.png"
done
```

---

## 常见问题

### Q1: API调用失败

```
可能原因：
1. API Key无效或过期
2. 网络连接问题
3. API配额用尽

解决方案：
1. 检查 gemini_config.json 中的 API Key
2. 检查网络连接
3. 访问 https://apicore.ai 查看用量
```

### Q2: 生成的图片风格不一致

```
原因：风格关键词不统一

解决方案：
1. 确保所有图片使用完全相同的风格关键词
2. 风格关键词放在prompt末尾
3. 使用"推荐风格组合"中的预设
```

### Q3: 图片质量不佳

```
优化方案：
1. 添加质量关键词："high quality, detailed, 4K"
2. 简化prompt，聚焦核心概念
3. 尝试不同的风格组合
```

### Q4: 图片与内容不匹配

```
优化方案：
1. 确保prompt准确描述章节核心概念
2. 避免过于抽象的描述
3. 参考章节内容提炼关键词
```

### Q5: 生成速度慢

```
优化方案：
1. 简化prompt，减少复杂描述
2. 使用并发请求（注意API限制）
3. 预生成配图，缓存复用
```

### Q6: 响应格式问题

```
如果遇到响应解析错误：
1. 使用 --verbose 参数查看完整响应
2. 检查API返回的图片格式（URL或base64）
3. 根据实际响应格式调整脚本
```
