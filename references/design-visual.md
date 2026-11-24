# Design — 颜色、字体与视觉元素


## 目录

- `Color Selection`
- `Typography Principles`
- `Font Recommendations`
- `Visual Elements Reference`
- `Dimension Combination Guide`

## Color Selection

See `references/dimensions-mood.md` for full mood dimension specs.

**Content-First Approach**:
1. Analyze content topic, mood, and industry
2. Consider target audience expectations
3. Match palette to subject matter
4. Ensure strong contrast for readability

**角色色走主题槽，品牌固定色留 hex（2026-11-16 实测）**：

- **反例**：初稿正文 / 标题 / 背景 / 强调等角色色全部硬编码 hex，散落在各页；警示红铺满 40 余处。换主题或改母版时要逐块找色。
- **规则**：
  - 角色色（正文、次要文字、标题、背景、强调）引用主题槽——B 出口走 CSS 变量，C 出口走母版主题色；同角色全篇同槽。
  - 品牌固定色（logo 色、主视觉色、金 / 米 / 湖等品牌色）可留 hex。
  - 警示色只标真风险点，不逐块铺；一页多处飘红等于没有重点。
- 对比度与 `--accent-ink` 口径仍按 `qa-checklist.md` #5，本条只管色值挂在哪一层。

**Quick Palette Guide**:
| Content Type | Recommended Mood |
|--------------|-----------------|
| Technical/Architecture | cool |
| Educational/Friendly | warm |
| Corporate/Professional | professional |
| Creative/Artistic | vibrant |
| Scientific/Medical | cool or neutral |
| Entertainment/Gaming | dark or vibrant |

## Typography Principles

See `references/dimensions-typography.md` for full typography dimension specs.

| Element | Treatment |
|---------|-----------|
| Headlines | Bold, 2-3x body size, narrative style |
| Body Text | Regular weight, readable size |
| Captions | Smaller, lighter weight |
| Data Labels | Monospace for technical content |
| Emphasis | Use bold or color, not underlines |

## Font Recommendations

**English Fonts**:
| Font | Style | Best For |
|------|-------|----------|
| Liter | Sans-serif, geometric | Modern, clean, technical |
| HedvigLettersSans | Sans-serif, distinctive | Brand-forward, creative |
| Oranienbaum | High-contrast serif | Elegant, classical |
| SortsMillGoudy | Classical serif | Traditional, readable |
| Coda | Round sans-serif | Friendly, approachable |

**Chinese Fonts**:
| Font | Style | Best For |
|------|-------|----------|
| MiSans | Modern sans-serif | Clean, versatile, screen-optimized |
| Noto Sans SC | Neutral sans-serif | Standard, multilingual |
| siyuanSongti | Refined Song typeface | Elegant, editorial |
| alimamashuheiti | Geometric sans-serif | Commercial, structured |
| LXGW Bright | Song-Kai hybrid | Warm, readable |

**Multilingual Pairing**:
| Use Case | English | Chinese |
|----------|---------|---------|
| Technical | Liter | MiSans |
| Editorial | Oranienbaum | siyuanSongti |
| Friendly | Coda | LXGW Bright |
| Corporate | HedvigLettersSans | alimamashuheiti |

## Visual Elements Reference

See `references/dimensions-texture.md` for full texture dimension specs.

### Background Treatments

| Treatment | Description | Best For |
|-----------|-------------|----------|
| Solid color | Single background color | Clean, minimal |
| Split background | Two colors, diagonal or vertical | Contrast, sections |
| Gradient | Subtle vertical or diagonal fade | Modern, dynamic |
| Textured | Pattern or texture overlay | Character, style |

### Typography Treatments

| Treatment | Description | Best For |
|-----------|-------------|----------|
| Size contrast | 3-4x difference headline vs body | Impact, hierarchy |
| All-caps headers | Uppercase with letter spacing | Authority, structure |
| Monospace data | Fixed-width for numbers/code | Technical, precision |
| Hand-drawn | Organic, imperfect letterforms | Friendly, approachable |

### Geometric Accents

| Element | Description | Best For |
|---------|-------------|----------|
| Diagonal dividers | Angled section separators | Energy, movement |
| Corner brackets | L-shaped frames | Focus, framing |
| Circles/hexagons | Shape frames for images | Modern, tech |
| Underline accents | Thick lines under headers | Emphasis, hierarchy |

## Dimension Combination Guide

When combining dimensions, consider compatibility:

| Audience | Recommended Dimensions |
|----------|----------------------|
| Executives | clean + neutral + geometric + minimal |
| Beginners | organic + warm + humanist + minimal |
| General | any texture + any mood + humanist/geometric + balanced |
| Experts | grid/clean + cool + technical + balanced/dense |

| Content Type | Recommended Dimensions |
|--------------|----------------------|
| Tutorial | organic + warm + handwritten + balanced |
| Technical | grid + cool + technical + balanced |
| Business | clean + professional + geometric + balanced |
| Creative | organic + vibrant + humanist + balanced |
| Data-heavy | clean + cool + technical + dense |
