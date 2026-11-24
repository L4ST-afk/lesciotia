# curio-cabinet

Wunderkammer material-display aesthetic: warm paper ground, generous rounded corners, deep-one-step outlines, sticker white borders, flattened hierarchy, physical-thumbnail icons.

## Design Aesthetic

A cabinet of curiosities: different materials arranged under one strict order. Soft, rounded, thick-outlined, sticker-like, with hierarchy deliberately flattened. Warm and approachable, but every element sits on a shared grid order. The feel is a curated display of tactile objects, not a flat digital dashboard.

## Background

- Color: Warm off-white `#fbf8f2` (never pure white); cream highlight `#fffdf6`; surface card `#ffffff`.
- Texture: Quiet paper grain; dividers and grids in light warm gray `#e6dfd2`.
- Shadows carry a warm tint `rgba(120,100,70,.14)`; ⛔ neutral gray shadows.

## Typography

### Primary Font (Headlines)

Rounded, friendly humanist sans-serif; medium weight (500, not bold); zero letter-spacing on titles. Warm, approachable letterforms.

### Secondary Font (Body)

Clean rounded sans-serif, regular weight (400), relaxed line height. Readable at small sizes; emphasis comes from size and whitespace, not heavy weight contrast.

## Color Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Background | Warm Off-White | `#fbf8f2` | Primary ground |
| Cream Highlight | Cream | `#fffdf6` | Highlight panels, never pure white |
| Primary Text | Warm Charcoal | `#2b2620` | Headlines, body |
| Soft Text | Warm Gray | `#6b6257` | Secondary copy |
| Grid / Divider | Warm Sand | `#e6dfd2` | Borders, separators |
| Accent · Rose | `#d4697f` / deep `#8e3a52` / wash `#fde8ef` | — | Primary warm accent |
| Accent · Teal | `#2f9e8f` / deep `#14544e` / wash `#d9f2e8` | — | Growth, calm |
| Accent · Amber | `#c47a1e` / deep `#6b3f0a` / wash `#fbe6c8` | — | Warm emphasis |
| Accent · Slate Blue | `#6b8aa8` / deep `#2f4a63` / wash `#e8eef5` | — | Calm secondary |
| Accent · Cinnabar | `#c8322b` / deep `#8a1a16` | — | Seal / closing stamp, sparing use |

Pick one accent family per deck; do not mix several solid accents on one page.

## Visual Elements

- Rounded corners in three values only: large card `32px`, capsule/pill `999px`, circle `50%`; small square chips ≤16px may use `6px`. ⛔ no fourth corner family.
- Boundaries come from an outline one step deeper than the fill (`2px`; `1.5px` in dense tables/grids), not from a fill-color contrast against the background.
- Sticker white edge lets any shape sit on any background; keep the white border around cut-out shapes.
- Icons read as physical thumbnails of real objects; ⛔ wireframe symbol icons.
- Hierarchy flattened: no alert-red emphasis; emphasis through size and whitespace, not weight contrast or z-axis lift.
- State feedback by shape and offset (hover −2px / active +2px), not color change alone.

## Style Rules

### Do

- Keep one corner-radius family across the deck
- Use warm-tinted shadows and cream highlights
- Match outlines to the deep-one-step rule
- Reserve cinnabar red for a closing seal or single key mark
- Keep grid symmetry and generous padding

### Don't

- Introduce a fourth corner value or a new radius scale
- Use neutral gray shadows or pure white grounds
- Lift panels along the z-axis to compete for attention
- Rely on bold weight contrast or alert-red for emphasis
- Mix multiple accent solids on the same page
- Add slide numbers, footers, or logos baked into the image

## Best For

Teaching cards, lifestyle and parenting content, friendly brand decks, social-content cards, illustrated explainers. ⛔ Hard data-heavy reports, formal compliance materials, dark atmospheric keynotes.
