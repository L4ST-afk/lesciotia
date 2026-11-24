# Confirmation Questions

Concrete option copy for the confirmation steps. SKILL.md lists which questions to ask — this file gives the verbatim options. Adapt copy to the runtime's native user-input tool; the intent matters more than the exact wording.


> 本文件只放 Round 1 的六个问题（Q0–Q5）。自定义四维、大纲/逐页评审、既有内容取舍见 `confirmation-more.md`。

## Round 1 (Always)

Batch all six questions in a single call（`interaction.ask` 支持一次传多个 question；没有批量能力就按序逐个问）。

### Q0: Exit mode（先问，决定走哪条路径）

```yaml
header: 交付形态
question: 这份 deck 最终要长成什么？
options:
  - label: A · 影像 deck（推荐）
    description: 逐页 AI 生图再合成 pptx/pdf；视觉强、适合读和传播，但文字不可编辑
  - label: B · 网页 deck
    description: 单文件 HTML，键盘翻页 + 演讲者模式 + 逐字稿；适合上台讲，离线可开
  - label: C · 可编辑 PPTX
    description: 原生文本/形状，客户能自己改字；需外部引擎 ppt-master，可用性以 `path-c-editable.md` C0 闸门**当次**退出码为准
  - label: A + B 都要
    description: 先定 HTML 结构，再按同一份逐页记录出图；页序必须一一对应
```

### Q1: Style

```yaml
header: Style
question: Which visual style for this deck?
options:
  - label: "{recommended_preset} (Recommended)"
    description: Best match based on content analysis
  - label: "{alternative_preset}"
    description: "{alternative style description}"
  - label: Custom dimensions
    description: Choose texture, mood, typography, density separately
```

### Q2: Audience

```yaml
header: Audience
question: Who is the primary reader?
options:
  - label: General readers (Recommended)
    description: Broad appeal, accessible content
  - label: Beginners/learners
    description: Educational focus, clear explanations
  - label: Experts/professionals
    description: Technical depth, domain knowledge
  - label: Executives
    description: High-level insights, minimal detail
```

### Q3: Slide Count

```yaml
header: Slides
question: How many slides?
options:
  - label: "{N} slides (Recommended)"
    description: Based on content length
  - label: "Fewer ({N-3} slides)"
    description: More condensed, less detail
  - label: "More ({N+3} slides)"
    description: More detailed breakdown
```

### Q4: Review Outline

```yaml
header: Outline
question: Review outline before generating prompts?
options:
  - label: Yes, review outline (Recommended)
    description: Review slide titles and structure
  - label: No, skip outline review
    description: Proceed directly to prompt generation
```

### Q5: Review Page Records

```yaml
header: 逐页记录
question: 出产物前，要不要先审逐页记录（pages/NN.md）？
options:
  - label: 要，先审记录（推荐）
    description: 逐页核对标题、要点、画面、讲稿，最省返工
  - label: 不用，直接出
    description: 直接进入渲染
```

> 口径说明：审 `pages/` 等价于审 prompts——A 出口的 prompts 由 pages 派生，改记录会同步回去。

