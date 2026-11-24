# Content & Style Rules

Guidelines for slide deck content quality and style consistency.

## 目录

- `Content Rules` 1–8（注意力 / 数据追溯 / 自包含 / 占位 / 权属 / 素材标准 / 附件权威 / 图片纪律）
- `Style Rules` 1–4
- `Slide Structure` / `Key Specifications` / `Style Quick Reference`

## Content Rules

### 1. Respect Reader Attention
- Each slide should communicate ONE main idea
- Remove redundant information
- Prioritize clarity over comprehensiveness

### 2. Data Traceability
- All statistics must include source attribution
- Cite sources directly on slides with data
- Use specific numbers over vague claims

### 3. Self-Contained Prompts
- Every detail must be in the image prompt
- No external references (e.g., "like slide 2")
- Include all colors, layouts, and content explicitly

### 4. No Undeclared Placeholders
- Every element must be fully specified
- No "[insert data here]" or "TBD" left silently in a prompt
- Data you cannot obtain: write `TODO(数据)` in `pages/NN.md` and list it in the delivery summary (see `page-record.md` 硬约束 5). ⛔ Never invent a plausible-looking number to fill the hole.
- **证据标记的位置（2026-11-16 实测）**：【估算】【待填】【并列】这类证据等级标记放独立标签行或卡片角标，⛔ 不塞进标题与长句；封面、章节扉页、大标题行不带标记。标记对应的缺口数据仍按上条进交付摘要登记。

### 5. 素材权属与外发边界
- 缺必填的真实素材（图 / 视频 / 文件）时停止并请用户上传；⛔ 不自主生图、改图补齐占位。
- 外发前识别：真实人物姓名、品牌商标、影视 / 动漫 / IP、受保护文案或歌词、可辨认人物、Logo / 水印 / 版权标识、摄影美术作品、影视截图、来源不明素材。
- 首次外发提醒用户确认使用权 / 商业授权；「未发现明显风险 ≠ 权属证明」。
- 发现具体权利风险时点明内容并等确认；用户沉默 ≠ 授权。不去水印、不移除权利标识、不以「复刻」规避肖像 / 著作 / 商标权。

### 6. 素材选用标准
- 分辨率：全屏背景图宽 >1600px、高 >800px（竖向对调）；⛔ 不靠把低清图放大凑门槛。
- 视觉质量：主体清晰，无压缩失真、水印、锯齿、生成畸形或粗糙拼贴；光影、色彩、质感符合选定风格。
- 内容匹配：主体、场景、关键细节对应当页表达，不为填满版面塞无关图。
- 版面适配：比例、主体位置、留白适合目标版面；背景图留出可放文字的低细节区，保证文字对比。

### 7. 附件权威性
- 用户附件是第一手事实来源，优先级高于联网搜索和先验知识；与其他来源冲突时以附件为准。
- 附件内嵌的图 / 表 / 公式信息要读全；附件中的图表只缩放适配，⛔ 裁剪掉信息。

### 8. 图片纪律
- 记下每张图的原始宽高，供裁剪 / 缩放参考。
- 同一张图不多页重复使用（Logo、统一装饰除外）。
- 背景 / 封面图不带文字；生成后检查，出现文字必须重做。

## Style Rules

### 1. Narrative Headlines
Headlines tell the story, not label the content.

| Bad | Good |
|-----|------|
| "Key Statistics" | "Usage doubled in 6 months" |
| "Our Solution" | "One platform replaces five tools" |
| "Benefits" | "Teams save 10 hours weekly" |

### 2. Avoid AI Clichés
Remove these patterns:
- "Dive into", "explore", "journey"
- "Let's look at", "let me show you"
- "Exciting", "amazing", "revolutionary"
- "In conclusion", "to summarize"

### 3. Meaningful Back Cover
Not just "Thank you" or "Questions?"

Include one of:
- Clear call-to-action
- Memorable key takeaway
- Thought-provoking closing statement
- Contact information with purpose

### 4. Consistent Visual Language
Throughout the deck:
- Same icon style
- Same color usage patterns
- Same layout grid system
- Same typography hierarchy

## Slide Structure

| Position | Type | Purpose |
|----------|------|---------|
| 1 | Cover | Title, visual hook, topic introduction |
| 2 to N-1 | Content | Key points, data, explanations |
| N | Back Cover | Summary, call-to-action, memorable close |

## Key Specifications

| Specification | Value |
|---------------|-------|
| Aspect Ratio | 16:9 (landscape) |
| Slide Count | Dynamic based on content |
| Required Slides | Cover + Back Cover minimum |
| Footers | A（生图）: none — no slide numbers, no logos baked into the image. B（网页）: page number comes from runtime's `.slide-number`, don't hand-write it |
| Language Priority | `--lang` → source language → ask user |
| Tone | Direct, confident (avoid AI phrases) |

## Style Quick Reference

| Style | Visual Summary |
|-------|----------------|
| `sketch-notes` | Hand-drawn, warm off-white, conceptual icons |
| `blueprint` | Technical schematics, grid texture, blue tones |
| `bold-editorial` | High contrast, dark backgrounds, magazine impact |
| `vector-illustration` | Flat vector, black outlines, retro colors |
| `minimal` | Maximum whitespace, single accent, zen-like |
| `dark-atmospheric` | Cinematic dark mode, deep purple-black, glowing accents |
| `watercolor` | Hand-painted brush strokes, warm off-white, soft organic edges |
| `notion` | Dashboard aesthetic, clean data viz, SaaS-inspired |
| `corporate` | Navy/gold, structured layouts, business polish |
| `hand-drawn-edu` | Wobbly hand-drawn lines, macaron pastels on warm cream |

This is a 10-row sample. All 17 style specs live at `references/styles-<key>.md`; the
four-dimension index (style → dimensions → A spec → B theme) is `references/styles-unified.md`.
⛔ Don't guess a key from its name — open the file or the index first.
