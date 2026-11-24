# Outline Template

Standard structure for slide deck outlines with style instructions.


> 本文件只管大纲头部与 STYLE_INSTRUCTIONS。封面/正文/封底页模板、页序编号、文件命名见 `outline-slide-templates.md`。

## 目录

- `Outline Format`
- `Building STYLE_INSTRUCTIONS from Dimensions`
- `STYLE_INSTRUCTIONS Block`

## Outline Format

```markdown
# Slide Deck Outline

**Topic**: [topic description]
**Exit**: [image / html / editable / image+html]
**Archetype**: [course / pitch / tech-talk / weekly / launch / research / explainer / review]
**Style**: [style key OR "custom"]
**Dimensions**: [texture] + [mood] + [typography] + [density]
**Audience**: [target audience]
**Language**: [output language]
**Slide Count**: N slides
**Generated**: YYYY-MM-DD HH:mm

---

<STYLE_INSTRUCTIONS>
Design Aesthetic: [2-3 sentence description combining dimension characteristics]

Background:
  Texture: [from texture dimension]
  Base Color: [from mood dimension palette]

Typography:
  Headlines: [from typography dimension - describe visual appearance]
  Body: [from typography dimension - describe visual appearance]

Color Palette:
  Primary Text: [Name] ([Hex]) - [usage]
  Background: [Name] ([Hex]) - [usage]
  Accent 1: [Name] ([Hex]) - [usage]
  Accent 2: [Name] ([Hex]) - [usage]

Visual Elements:
  - [element 1 from texture + mood combination]
  - [element 2 with rendering guidance]
  - ...

Density Guidelines:
  - Content per slide: [from density dimension]
  - Whitespace: [from density dimension]

Style Rules:
  Do: [guidelines from dimension combinations]
  Don't: [anti-patterns from dimension combinations]
</STYLE_INSTRUCTIONS>

---

[Slide entries follow...]
```

## Building STYLE_INSTRUCTIONS from Dimensions

When using custom dimensions or presets, build STYLE_INSTRUCTIONS by combining:

### 1. Design Aesthetic

Combine characteristics from all four dimensions into 2-3 sentences:

| Texture | Contribution |
|---------|--------------|
| clean | "Clean, digital precision with crisp edges" |
| grid | "Technical grid overlay with engineering precision" |
| organic | "Hand-drawn feel with soft textures" |
| pixel | "Chunky pixel aesthetic with 8-bit charm" |
| paper | "Aged paper texture with vintage character" |

| Mood | Contribution |
|------|--------------|
| professional | "Professional navy and gold palette" |
| warm | "Warm earth tones creating approachable atmosphere" |
| cool | "Cool analytical blues and grays" |
| vibrant | "Bold, high-saturation colors with energy" |
| dark | "Deep cinematic backgrounds with glowing accents" |
| neutral | "Minimal grayscale sophistication" |

### 2. Background

From `references/dimensions-texture.md`:
- Texture description
- Base color from mood palette

### 3. Typography

From `references/dimensions-typography.md`:
- Headline visual description (NOT font names)
- Body text visual description (NOT font names)

**Important**: Describe appearance for image generation: "bold geometric sans-serif with perfect circular O shapes" NOT "Inter font".

### 4. Color Palette

From `references/dimensions-mood.md`:
- Copy the palette specifications for the selected mood
- Include hex codes and usage notes

### 5. Visual Elements

Combine texture and mood characteristics:

| Combination | Visual Elements |
|-------------|-----------------|
| clean + professional | Clean charts, outlined icons, structured grids |
| grid + cool | Technical schematics, dimension lines, blueprints |
| organic + warm | Hand-drawn icons, brush strokes, doodles |
| pixel + vibrant | Pixel art icons, retro game elements |
| paper + warm | Vintage stamps, aged elements, sepia overlays |

### 6. Density Guidelines

From `references/dimensions-density.md`:
- Content per slide limits
- Whitespace requirements
- Element count guidelines

### 7. Style Rules

Combine dimension-specific rules:

**Do rules by texture**:
- clean: Maintain sharp edges, use grid alignment
- grid: Show precise measurements, use technical diagrams
- organic: Allow imperfection, layer with subtle overlaps
- pixel: Keep aliased edges, use chunky elements
- paper: Add subtle aging effects, use warm tones

**Don't rules by texture**:
- clean: Don't use hand-drawn elements
- grid: Don't use organic curves
- organic: Don't use perfect geometry
- pixel: Don't smooth edges
- paper: Don't use bright digital colors

## STYLE_INSTRUCTIONS Block

The `<STYLE_INSTRUCTIONS>` block is the SINGLE SOURCE OF TRUTH for style information in this outline.

| Section | Content | Source |
|---------|---------|--------|
| Design Aesthetic | Overall visual direction | Combined from all dimensions |
| Background | Base color and texture details | texture + mood dimensions |
| Typography | Font descriptions (visual, not names) | typography dimension |
| Color Palette | Named colors with hex codes and usage | mood dimension |
| Visual Elements | Graphic elements with rendering instructions | texture + mood dimensions |
| Density Guidelines | Content limits and whitespace | density dimension |
| Style Rules | Do/Don't guidelines | Combined from dimensions |

**Important**:
- Typography descriptions must describe visual appearance (e.g., "rounded sans-serif", "bold geometric") since image generators cannot use font names
- Prompts should extract STYLE_INSTRUCTIONS from this outline, NOT re-read style files

