# 页模板与编号


## 目录

- `Cover Slide Template`
- `Slide 1 of N`
- `Content Slide Template`
- `Slide X of N`
- `Back Cover Slide Template`
- `Slide N of N`
- `Preset → Dimensions Reference`
- `Section Dividers`
- `Slide Numbering`
- `Filename Slugs`

## Cover Slide Template

```markdown
## Slide 1 of N

**Type**: Cover
**Filename**: 01-slide-cover.png

// NARRATIVE GOAL
[What this slide achieves in the story arc]

// KEY CONTENT
Headline: [main title]
Sub-headline: [supporting tagline]

// VISUAL
[Detailed visual description - specific elements, composition, mood]

// LAYOUT
Layout: [optional: A 出口构图名，取自 references/layouts.md 的词表，e.g., title-hero]
[Composition, hierarchy, spatial arrangement]
```

## Content Slide Template

```markdown
## Slide X of N

**Type**: Content
**Filename**: {NN}-slide-{slug}.png

// NARRATIVE GOAL
[What this slide achieves in the story arc]

// KEY CONTENT
Headline: [main message - narrative, not label]
Sub-headline: [supporting context]
Body:
- [point 1 with specific detail]
- [point 2 with specific detail]
- [point 3 with specific detail]

// VISUAL
[Detailed visual description]

// LAYOUT
Layout: [optional: A 出口构图名，取自 references/layouts.md 的词表]
[Composition, hierarchy, spatial arrangement]
```

## Back Cover Slide Template

```markdown
## Slide N of N

**Type**: Back Cover
**Filename**: {NN}-slide-back-cover.png

// NARRATIVE GOAL
[Meaningful closing - not just "thank you"]

// KEY CONTENT
Headline: [memorable closing statement or call-to-action]
Body: [optional summary points or next steps]

// VISUAL
[Visual that reinforces the core message]

// LAYOUT
Layout: [optional: A 出口构图名，取自 references/layouts.md 的词表]
[Clean, impactful composition]
```

## Preset → Dimensions Reference

When using a preset, look up dimensions in `references/dimensions-presets.md`:

| Preset | Dimensions |
|--------|------------|
| blueprint | grid + cool + technical + balanced |
| sketch-notes | organic + warm + handwritten + balanced |
| corporate | clean + professional + geometric + balanced |
| minimal | clean + neutral + geometric + minimal |
| ... | See `dimensions-presets.md` for the full 17-preset mapping |

## Section Dividers

Use `---` (horizontal rule) between:
- Header metadata and STYLE_INSTRUCTIONS
- STYLE_INSTRUCTIONS and first slide
- Each slide entry

## Slide Numbering

- Cover is always Slide 1
- Content slides use sequential numbers
- Back Cover is always final slide (N)
- Filename prefix matches slide position: `01-`, `02-`, etc.

## Filename Slugs

Generate meaningful slugs from slide content:

| Slide Type | Slug Pattern | Example |
|------------|--------------|---------|
| Cover | `cover` | `01-slide-cover.png` |
| Content | `{topic-slug}` | `02-slide-problem-statement.png` |
| Back Cover | `back-cover` | `10-slide-back-cover.png` |

Slug rules:
- Kebab-case (lowercase, hyphens)
- Derived from headline or main topic
- Maximum 30 characters
- Unique within deck
