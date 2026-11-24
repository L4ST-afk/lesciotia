# Confirmation — 第二轮与评审


## 目录

- `Round 2 — Custom Dimensions`
- `Outline Review (Step 4)`
- `Prompt Review (Step 6, 逐页记录版)`
- `Existing Content (Step 1.3)`

## Round 2 — Custom Dimensions

Triggered only when Q1 of Round 1 = "Custom dimensions". Batch all four dimension questions.

### Texture

```yaml
header: Texture
question: Which visual texture?
options:
  - label: clean
    description: Pure solid color, no texture
  - label: grid
    description: Subtle grid overlay, technical
  - label: organic
    description: Soft textures, hand-drawn feel
  - label: pixel
    description: Chunky pixels, 8-bit aesthetic
```

`paper` is also valid — accept via "Other".

### Mood

```yaml
header: Mood
question: Which color mood?
options:
  - label: professional
    description: Cool-neutral, navy/gold
  - label: warm
    description: Earth tones, friendly
  - label: cool
    description: Blues, grays, analytical
  - label: vibrant
    description: High saturation, bold
  - label: macaron
    description: Pastel blocks on cream
```

`dark`, `neutral` valid via "Other".

### Typography

```yaml
header: Typography
question: Which typography style?
options:
  - label: geometric
    description: Modern sans-serif, clean
  - label: humanist
    description: Friendly, readable
  - label: handwritten
    description: Marker/brush, organic
  - label: editorial
    description: Magazine style, dramatic
```

`technical` valid via "Other".

### Density

```yaml
header: Density
question: Information density?
options:
  - label: balanced (Recommended)
    description: 2-3 key points per slide
  - label: minimal
    description: One focus point, maximum whitespace
  - label: dense
    description: Multiple data points, compact
```

## Outline Review (Step 4)

```yaml
header: Confirm
question: 大纲 OK 吗？
options:
  - label: 可以，继续（推荐）
    description: 进入逐页记录
  - label: 先改大纲
    description: 改 outline.md 再继续
  - label: 重出大纲
    description: 换个结构重写
```

## Prompt Review (Step 6, 逐页记录版)

```yaml
header: Confirm
question: 可以开始渲染了吗？
options:
  - label: 可以，开渲（推荐）
    description: 按确认的出口出产物
  - label: 先改逐页记录
    description: 改 pages/NN.md 再继续
  - label: 重出逐页记录
    description: 换一种组织方式重写
```

## Existing Content (Step 1.3)

```yaml
header: Existing
question: Existing content found. How to proceed?
options:
  - label: Regenerate outline
    description: Keep images, regenerate outline only
  - label: Regenerate images
    description: Keep outline, regenerate images only
  - label: Backup and regenerate
    description: Backup to {slug}-backup-{timestamp}, then regenerate all
  - label: Exit
    description: Cancel, keep existing content unchanged
```
