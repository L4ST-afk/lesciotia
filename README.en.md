[中文](README.md) · English

# 来雪亭 Lesciotia

One script, two artefacts: a **single-file HTML** deck you page through in any browser, offline; and a **native PPTX** whose text and shapes stay editable. When the output must look exactly right and will not be touched again, there is a third road: per-page images.

17 layout families (38 styles), 9 themes, 5 complete decks — all offline. Each theme carries the name of a Shanghai Metro station: one station's first step out of the gates, one palette and one surface. The HTML target needs only Python 3's standard library; the PPTX target adds `python-pptx`.

The name comes from Laixue Pavilion on Jiangxin Island, Wenzhou — north-east corner of the islet, facing Mount Luofu. The allusion, the pronunciation and what was given up for it: [`references/naming.md`](references/naming.md).

Provenance, pronunciation and the costs accepted are recorded in [`references/naming.md`](references/naming.md).

## Three layers

| Word | What it governs | Directory | Count |
|---|---|---|---|
| **Frame** | Skeleton: how information is ordered, how many columns, in what sequence | `assets/layouts/` | 17 families / 38 styles |
| **Tilework** | Surface: palette, type, material | `assets/themes/` | 9 |
| **Snow** | The raw material the user brings in | none (input side) | — |

Snow falls on the tiles, not on the beams — so "snow" belongs to the tilework layer, while what you bring is called **falling snow**. These three words are names only; directory names do not change. See [`SKILL.md`](SKILL.md) §three layers.

## The approach: tilework decided a priori, not scraped from one render

Comparable HTML-to-PPTX tools walk the same road — render the page in a headless browser, then scrape the DOM and computed styles into native shapes (`slidesmith`, `GX-Alex/html2pptx`, `dom-to-pptx`, `html-native-pptx`, `mmoollee101-lab/HTMLtoPPTX`). That road gets true numbers, at the price of **making the render the sole source of truth**: a theme change forces a full re-layout, two exports of the same HTML need not agree, and whatever the scrape cannot see (complex gradients, boolean shapes, motion) falls back to a page screenshot.

Lesciotia inverts it: tilework is **a priori**. `--hex` tokens and a 1600×900 grid live in files; Targets B and C read the same `:root` and emit separately, measuring with the same bundled fonts and writing line breaks ahead of time. The goal: swap the tilework once and both targets move together. Screenshot-level similarity is not the aim.

Three things anyone can re-check:

- Change the theme in `:root` only; HTML and PPTX move together. There is no second palette table in any script.
- Margins, column widths and type sizes come from one set of numbers: page margins, `--radius` 18px, `.h2` at 54/68px are read from CSS, not eyeballed twice. (Title size is now decided by the `h2` rule in `--deck-css` / the theme CSS.)
- If the recipient's machine lacks the font, lines do not reflow: breaks are locked to hard segments computed from real advance widths; only glyph shapes differ.

## Two optional pieces (the deck builds without them)

- **Page skeleton `.sk12`**: a 12-column grid (`l1`–`l12` plus `full`), giving "how the blocks on one page sit" a countable cell. The family page decides *what* a page is; the skeleton only decides *where* things go. ⛔ Never use it as a substitute for the family page.
- **Glass lens `assets/effects/lens.js`**: rounded-rect SDF → sine profile → Snell refraction → RGB channel dispersion; bending only in the rim band, zero displacement at the centre. When pixels are unreadable (opened via `file://`) it falls back to SVG turbulence and marks a corner badge. Mechanism, parameters and measurements: [`references/effects-lens.md`](references/effects-lens.md).

## Wash fields: `fill` and `boolean`

Gradients and booleans are not in PPT's shape library — they are **evaluated at export time**. The tilework writes a CSS declaration, `wash_bridge.py` translates it once, and the browser interprets the same declaration elsewhere. In a spec:

```json
{"type":"wash","title":["渐变与布尔"],"color":"#FFFFFF",
 "shapes":[
  {"shape":"rect","box":[0,0,1600,900],"fill":{"gradient":"linear-gradient(135deg, #0E1622 0%, var(--line-2) 45%, rgba(214,166,58,.75) 100%)"}},
  {"shape":"circle","center":[1360,760],"r":420,"fill":{"gradient":"radial-gradient(circle at 30% 30%, rgba(255,255,255,.55) 0%, rgba(255,255,255,0) 70%)"}}
 ]}
```

- `fill`: `{"gradient": "…"}` (multi-stop, angle or `to side`, rgba alpha) or `{"solid": "--token" | "#RRGGBB", "alpha": 0.4}`.
- `boolean`: `{"op":"subtract"|"intersect","a":…,"b":…}` → emits `a:custGeom`. Operands in three forms: `{"center":[x,y],"r":n}` (two circles solved analytically, cleanest boundary), `{"path":"M…A…Z"}`, `{"points":[[x,y],…]}`. The last two are flattened to polylines and go through `poly_bool`'s "split, classify, hand over" — **multiple contours are allowed** (holes, bitten-off pieces). Self-intersecting polylines are refused outright: their "inside" is undefined. **Union is not offered** — overlap two shapes of the same colour instead.
- When two shapes **share an edge**, classification is by "is the interior on the same side or the opposite side of that edge": same side → intersection keeps it, difference drops it; opposite side → the reverse. Same-side is probed by testing both sides along the normal. Of the two overlapping segments only A's is kept — keeping both makes a double line and the hand-over breaks. When the two boundaries coincide exactly, intersection returns A and difference reports empty.
- `path`: the `d` string inside `clip-path: path()` goes in as-is and **is emitted as curves by default** — every `A` is split at ≤90° and converted to cubic Béziers (`k = 4/3·tan(θ/4)`), `Q` is degree-elevated, `C` written straight as `a:cubicBezTo`; only `"curve":"polyline"` falls back to sampling. Boolean results stay polylines: a **true** curve-vs-curve cut needs `skia-pathops`, which conflicts with this library's zero-heavy-dependency line. It is not pulled in.
- Any page may carry a `wash` layer: it lands first inside `slide()`, content sits on top.

Three pits hit along the way are recorded in code comments: `p:style` hangs a theme shadow on shapes (in the tilework they are flat, so it must be stripped); `#RRGGBB` must be written as a colour (otherwise white type on a dark ground silently becomes black); `:root` token substitution must report "undefined" rather than pasting the whole string back.

## Dual-target drift: `--html`

Emitting one source through two targets, the likeliest failure is not a rendering difference — it is **somebody editing only one side**. `check-wash.py spec.json --html deck.html` takes the declarations written in the spec (raw gradient text, `--token`) and looks for them in the HTML: after normalising whitespace the same string must be found. Not found → red, naming the page and the shape.

It proves "both sides write the same tilework", not "both renderers draw the same picture" — the latter only a per-renderer comparison can show.

## Page transitions: read the tilework, don't guess the speed

Target B's transition lives in `assets/base.css`: `.slide{opacity:0; transform:translateX(30px); transition:opacity .5s …}` — a fade plus a short lateral shift. Target C does not guess "about half a second"; it **reads the same declaration block**: duration from the first time value in `transition`, direction from the sign of `translateX()`.

The default maps to `fade`, not `push`, and the reason is magnitude: 30px on a 1600-wide canvas is 1.9%, while PowerPoint's push shoves the whole page width — that turns a "slight slide" into "a different feel". Prefer a small difference over an amplified one. If you want the push, ask for it: `--transition push`, direction taken as `from-right` (in CSS it is +30px coming in).

A single page can override or disable it: `{"type":"push","direction":"from-right"}` / `{"type":"none"}`.
`morph` goes through `mc:AlternateContent` wrapping `p159:morph`, with older PowerPoints falling back to `fade`.

The per-page PNGs from `--render-check` are **byte-identical** to those produced with no transition at all (all 8 md5s equal across v9 and v7) — the transition is purely additive and never touches the static layout.

## How gradients and booleans get in

Gradients are taken **per layer**: `linear-gradient` (angle and `to <side>`, multi-stop, rgba) becomes `a:gradFill`, and CSS multi-layer `background` becomes several shapes at the same position — layers, z-order and per-layer alpha must match.

Booleans are **evaluated at export**: PPTX has no boolean instruction, so the result is written as one `a:custGeom` path. Either the tilework writes `clip-path: path()` directly (B and C each interpret the same `d`, curves intact), or an op plus shape parameters are computed by `wash_bridge.py` (currently covering two-circle difference and intersection).

Written off, not converted: `conic-gradient`, `repeating-*`, `background-blend-mode`, `filter`. Motion is not converted — HTML keeps it, PPT gets a still.

The remaining cost: motion is lost, complex shadows and blend modes are lost, gradient interpolation is approximate (premultiplied sRGB and sRGB+alpha differ). When you need those, take Target A (per-page images, 100% likeness, not editable) or call `ppt-master` as an external engine — neither is built in.

## Optional backends: use them if installed, say so if degraded

Default dependencies are unchanged: python3 + python-pptx + lxml (Pillow / officecli optional). Two things cannot be done with zero dependencies but every comparable tool does them, so they are **optional**:

| Backend | What it buys | Installed | Not installed |
|---|---|---|---|
| `skia-pathops` | **true** curve boolean (cut along the curve, result carries `cubicBezTo`) | when both operands are `path`, used automatically; `curves:"require"` forces it | falls back to polyline evaluation and prints "degraded: N booleans to polyline"; `require` errors out |
| `uharfbuzz` | Target C measures via full **shaping** (kerning and ligatures) | effective once `--hb-measure` is on | falls back to per-glyph accumulation and prints "wanted --hb-measure but it is not installed" |

`pip install skia-pathops uharfbuzz` is all it takes. The capability table appears in the emitted `--json` under `wash.backend` (`{"pathops": true, "uharfbuzz": false}`) — **that line tells you whether the same spec is the same precision on two machines**. `--hb-measure` is off by default because full shaping differs from the existing metric by 1–3% on long sentences, enough to move a break point: changing the backend means changing the line breaking, and a human has to decide that.

## Reverse flow: PPTX → HTML

Forward is "content → Targets B and C". In practice there is also the other direction: someone hands you a pptx and you need it on the web, or as HTML you can keep editing.

```bash
python3 scripts/pptx-to-html.py deck.pptx -o deck.html          # single file, keyboard paging
python3 scripts/pptx-to-html.py deck.pptx -o deck.html --notes  # notes toggled with the n key
```

This road **reads shapes**, it does not scrape a render: position, size, weight, colour and paragraph alignment come from XML and land as absolutely positioned HTML. Three details worth noting:

- **`a:gradFill` reversed**: stops plus `lin ang` → CSS `linear-gradient`; `<a:path path="circle"/>` → `radial-gradient`.
- **`custGeom` → inline SVG**: compound shapes from boolean or path output (crescents, lenses, chamfered hexagons) have no native HTML counterpart, so every `a:path`'s `moveTo/lnTo/cubicBezTo` is read into an SVG `d`, one `<path>` per shape.
- **Tables → `<table>`**, images → base64 inline, notes → a hidden `<aside>`.

It is an **approximate** reconstruction, and says so in three places: charts and SmartArt keep a placeholder frame and are counted; the theme-colour inheritance chain is resolved only to the layer written in the file (unresolved ones fall to neutral grey and are counted); shadows, 3D and WordArt are not restored (same trade-off as Target C: in the tilework they are flat).

The reverse direction (HTML → PPTX) remains "write a spec first, then emit", **no general scraping** — the reason is the approach at the top of this file: numbers obtained by scraping a render are a snapshot of that instant, and a theme change forces a full re-layout. The reverse flow reads the PPT's own structure, which is why it is actually steadier than a scrape.

## Round trip: change words only, leave the layout alone

Given someone else's finished pptx, the common request is "change a few sentences"; re-layout is rare. Re-layout means reinterpreting the layout, which necessarily drifts; so this road **replaces text nodes in the original file and nothing else**.

```bash
python3 scripts/retext-pptx.py deck.pptx --dump texts.json          # inventory: every non-empty text box, per page
python3 scripts/retext-pptx.py deck.pptx --edits edits.json -o new.pptx   # words and notes only
python3 scripts/retext-pptx.py new.pptx --verify                     # validate via officecli
```

Each inventory row carries `slide / id / name / text / paras / runs / geom`, where `geom` is the fingerprint of "position + type size + autofit". `edits.json` addresses shapes by `id` (or `name`):

```json
{"edits": [
  {"slide": 1, "id": 4, "text": "新标题\n第二行"},
  {"slide": 3, "name": "verdict", "text": "换一句结论"},
  {"slide": 1, "notes": "只改备注：不必点名形状"}
]}
```

Writing back keeps the first paragraph's `pPr` and the first run's `rPr` (size, colour, weight, family untouched), and copies line breaks from the original paragraph style. After the edit every shape's `spPr/style/bodyPr` sha is compared: **if the geometry changed, something went wrong** — it is named, never silently "successful"; shapes that cannot be addressed land in `skipped` rather than being hit by mistake.

Chained with the reverse flow it is a closed loop: `pptx → pptx-to-html.py` (see the result; every shape in the HTML carries `data-slide/data-id/data-name`) → fill `edits.json` by id → `retext-pptx.py` back to pptx. **Geometry is inherited from the original; only the words change.**

Three things it does not do, stated plainly: it does not change font family (go back to Target B, edit the template, re-emit); it does not re-break lines (text far beyond the box overflows — currently only the geometry fingerprint is compared, overflow is not checked); it does not touch images or charts.

## Frame: 36 styles merged into 17 families

The old version laid out 36 single pages, one file each, so picking a layout meant scanning a 36-row table. Most were one skeleton with a different column count or drawing: two-column / three-column / bullets are the same card grid, chart-bar/line/pie/radar are the same canvas. They are now 17 families / 38 styles, **one file per family, one style per section** (`charts` shows bar, line, pie and radar in a single page, plus a countable dot matrix, waterfall and dumbbell):

`cover` `section` `end` `text` `quote` `code` `compare` `charts` `image` `image-set` `process` `diagram` `data` `toc` `ring` `split` `quiz`

- There is exactly one source of truth for family and style: `assets/layouts/_families.json`; documents no longer use the old names.
- The `layout` field takes the family name; switching style within a family changes one class (`g2`/`g3`, or the style marked on the family page). Skeleton styles live in `assets/layouts.css` — never inline them in the family page.
- One old defect fixed on the way: `charts` used to pull Chart.js from a CDN, so opening it offline gave a **blank page**. It now ships `assets/vendor/chart.umd.min.js` (MIT, see `ATTRIBUTION.md`) and renders offline. `code` used to link highlight.js without a theme, producing not one colour; that is dropped and it renders as plain text.

The gate is `scripts/check-layouts.py` (L1–L7): family↔file mismatch, **`data-style` on the section disagreeing with `styles`**, an old name revived, documents using old names, a family page pointing at the network, a missing vendor file, **a class used with no style behind it** — any one red blocks delivery.

## Two layers of frame: family pages give the style, `layouts.css` gives the structure

Family pages only say "which style this section is and what it contains"; the skeleton styles all live in `assets/layouts.css` (18 sections, one per family). Previously structural classes like `flow` / `arch` / `steps` / `gal` / `cmp` were **defined in neither base.css nor the themes**, so the `diagram` family rendered as "one vertical column of text" — that is why L7 exists: a class name written with no style behind it must go red.

## The type scale: nine steps, not one set per theme

Measured against 200 pages of layout libraries and 50 template decks (1011 pages): real decks use only 7 sizes (32pt page titles most often, 14pt body as the workhorse, 12pt captions), and hierarchy comes from **few steps with big jumps**, not from inflating line height; the modal page margin is 6%, and 4/3/2-column cards are each about a third.

On that reading, `base.css` defines nine token steps (px@1920, 1pt = 2px):

| token | px | pt | Use |
|---|---|---|---|
| `--t-hero` | 200 | 100 | one number to a page |
| `--t-display` | 144 | 72 | closing statement |
| `--t-h1` | 80 | 40 | chapter name |
| `--t-h2` | 64 | 32 | page title (most used) |
| `--t-h3` | 48 | 24 | subhead |
| `--t-h4` | 40 | 20 | card title |
| `--t-body` | 32 | 16 | body |
| `--t-body-sm` | 28 | 14 | dense body / code |
| `--t-cap` | 24 | 12 | caption, footer (projection floor) |

204 hard-coded `font-size` values across the 9 themes and 5 full decks were mechanically snapped to the scale; themes no longer invent their own sizes. Full measurements and trade-offs: `references/style-audit.md`.

## The fit gate: raise the type, and overflow must be judged by a machine

Going from 24px to 32px makes overflow inevitable, and eyeballing 17 families × dozens of sections is not realistic:

```bash
python3 scripts/check-fit.py                 # all 17 families
python3 scripts/check-fit.py --theme qiu-r   # re-measure under a theme
python3 scripts/check-fit.py path/to/page.html
```

F1 beyond the canvas / F2 clipped by itself / F3 horizontal overflow / F4 clipped by a parent. `.notes`, `.overview`, `.deck-header` and decorative layers are not measured; elements with a scrollable ancestor (such as `pre.card`) are let through in place. The implementation "starts a read-only HTTP server and injects a probe when `.html` is requested", **writing no temporary files** — the early version that copied to a temp dir and symlinked assets had the probe write through the symlink and dirty 14 family-page sources.

## Prose: lift a spoken transcript to a density that can ship

What users hand over often reads like this: "We do equipment data collection, we can save factories labour, three factories use it, results are okay, there are still a few problems…"

Put straight into a layout, every page has words and no page has a point. So there is a **prose gate**, and it **does not generate text** — writing happens in the conversation (only when a human genuinely cannot write is a model called); the gate only refuses to sign:

```bash
python3 scripts/check-prose.py deck.json            # red → exit 1
python3 scripts/check-prose.py deck.json --strict   # warnings count as red too
```

Nine criteria, each countable: a cliché hit is red (赋能/闭环/抓手/一站式…); a title made only of abstractions with neither object nor action; `lede` sharing ≥50% of two characters with the title (restating eats a line); a single bullet ≥27 characters (does not fit one line at 24px); a number with no stated source; an abbreviation's first use with no gloss; two conclusion sentences on one page; body under 36 characters (an empty page) or over 300 (mush); more question and exclamation marks than pages.

The three steps for lifting density (`references/prose-gate.md`): **split** (one fact, one judgement, one number per bullet), **stand** (one claim per page, title gives object plus action, lede gives the cost, bullets give the evidence), **verify** (run the gate).

`export-pptx.py` runs the same gate before emitting: **red refuses**, only `--allow-prose` lets it through, and the summary keeps a record. The sample is a set of contrasts: `examples/prose/rough-input.md` (the raw draft untouched), `good-spec.json` (lifted, 3 pages that ship), `bad-spec.json` (the cliché version, 26 reds, blocked — and `bad.pptx` does not exist afterwards, which is what a gate should look like).

## Typing: first decide which kind this is, then whether it reads right

Nine criteria govern "dense enough", but dense is not correct: a thing that should be a proposal, written in briefing form, is dense on every page and wrong as a whole. So typing comes first — five fixed recipes, not free-form prompting:

| Type | When | Skeleton |
|---|---|---|
| Briefing `briefing` | Upward: weekly, progress, review | conclusion first → claim + evidence + one number → next step is exactly one thing |
| Proposal `proposal` | Asking for resources: charter, budget, partnership | problem and cost → at most 3 steps → evidence → what is wanted (money/people/time) |
| Teaching `teaching` | Training, explainers, mechanism walkthroughs | slot → prerequisite → typicality ladder (typical/edge/counter-example) → boundary |
| Retro `retro` | Close-out, incident, post-launch | facts → root cause down to the changeable layer → what changes (who/when verified) → what is not changing this time |
| Launch `launch` | Outward: release, version, product page | one claim → three checkable pieces of evidence → one limitation → one action |

```bash
python3 scripts/pick-recipe.py --detect draft.md    # typing: trigger words plus structural signals; if two fit, say so
python3 scripts/pick-recipe.py --show teaching     # print that type's prompt so the gate is satisfied while writing
python3 scripts/check-prose.py deck.json --suggest  # type after the gate
```

Typing **reads all three languages, Chinese first**: a Chinese trigger scores 2, English/Japanese 1 (English matched on word boundaries, so `report` does not hit `reporter`). In mixed text the author's language wins — measured on "这周汇报一下进展……我讲 budget 与 proposal 那部分", typed as briefing (7 vs 2), not dragged off by the embedded English words.

Five things are compiled into the prompt: the output form (a deck spec, not prose); hard requirements a number can check (≤26 characters, one clause per bullet, numbers carry `source`, the closing gives exactly one thing); the same banned-word table as the gate; the **four closing questions** (borrowed from the same library's prose-register criteria and turned into questions: would it hold under another theme? who is speaking? would deleting it lose information? is there a source?); and that type's skeleton (the four teaching segments are the shape a framework-semantics piece reduces to on a page).

When two types both fit, follow this library's old rule and **write in segments, never mix them** — "incident retro plus budget request" means four retro pages then two proposal pages, with the type change stated in the kicker, rather than one page both assigning blame and asking for money.

## Real-render verification on the cheap: take officecli's contract, not its binary

The officecli binary is 32 MB and 90% of its time is the renderer itself — bundling it neither speeds anything up nor keeps the "pure python3" line intact. What can be taken is the **call contract**, already wired into `export-pptx.py`:

| Call | One run | Use | When |
|---|---|---|---|
| `view issues --json` | 0.2 s | judgeable problem types (low contrast, squashed image, rejected preset adjustment…) | every deck, before validate |
| `validate` | 0.9 s cold / 0.3 s warm | whether the schema holds | every deck |
| `--grid auto --page 1-N` | about 5 s for a thumbnail sheet of the whole deck | "did anything explode" | on by default via `--render-grid` |
| Single page at full resolution | 5–7 s / page | evidence, for a human | `--render-pages 1,3` renders only the named pages |

`view issues` runs first, meaning "what looks wrong" before "is the structure right" — the former answers in 0.2 seconds, the latter waits for the renderer; the other order just waits twice. This is the same reasoning as `ppt-builder`'s `visual.geom_check`.

Not done: no bulk PDF export (the path returns "No exporter plugin"), and its headless browser is not internalized (multi-page `-o` directories report "No headless browser available").

## Install

1. Unzip and put the whole `来雪亭Lesciotia/` directory **into** your skills root (as a peer of the other skills) — or
   `git clone https://github.com/L4ST-afk/lesciotia.git 来雪亭Lesciotia`. The **repo is `lesciotia`; the installed
   directory is still `来雪亭Lesciotia`**. The two are not interchangeable: the scripts locate their root by directory name.
2. Target B (HTML) needs no installation: the scripts use only the Python 3 standard library, and fonts and styles are internalised.
3. Target C (native PPTX) needs exactly one thing: `pip install python-pptx`. Without it `export-pptx.py` exits with code 2 — it does **not** fall back to "screenshot every page into a pptx", because that is not an editable artifact.
4. Optional: `officecli` (single binary, at `~/.local/bin/officecli`). It does two things — OpenXML sequence validation and true page rendering (`view screenshot` / `view pdf`). `export-pptx.py --render-check` runs both; without it the step is skipped and says so, never passing a hand-drawn approximation off as a render.
5. The `ppt-master` engine is **no longer the only road to Target C**: its 2.3 MB SVG→PPTX pipeline depends on skia-pathops / uharfbuzz and is "another authoring layer", in conflict with "one tilework, two targets". Call it as an external engine only for complex gradients, boolean merges or motion, and it stays outside the package.

## Self-check

After installing, run the self-test to confirm the package is complete on your machine:

```bash
cd 来雪亭Lesciotia
python3 scripts/selftest.py; echo "EXIT=$?"
```

`EXIT=0` means pass. Per-item detail and how to run each gate separately: `SELFTEST.md`.

**Each target has a real renderer**: on the C side officecli (`validate` plus page screenshots), on the B side Chrome/Chromium `--headless --screenshot` (which is what `scripts/render-png.sh` uses). Both actually draw pixels, so "is the same declaration the same direction under two renderers" can be cross-checked — the arc `sweep` direction was verified this way (a `M 100 100 A 150 150 0 0 1 250 250` with a dashed `sweep=0` arc over it bulges up-right in Chrome's screenshot and in our own point order, and both go down-left for `sweep=0`). **Only geometric direction and pixel visibility can be cross-checked**; motion playback remains blind.

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | Main entry: routing, command surface, size budget |
| `references/` | Per-topic volumes (layouts, themes, naming, paths, QA) |
| `assets/themes/` | 9 tileworks (theme CSS), such as `qiu-r.css` |
| `assets/layouts/` | 17 frame families (38 styles, one style per section) |
| `assets/full-decks/` | 5 complete decks |
| `assets/textures/` | material images exported from the 9 tileworks (derived, `board.png` plus `mat-*.png`/`tex-*.png`) |
| `assets/textures-src/` | source bitmaps and registry (`registry.json`); derived tiles land in `assets/textures/<theme>/` and are guarded by `scripts/check-bitmap-assets.py` |
| `examples/previews/` | theme preview boards (single HTML files, open directly) |
| `scripts/export-pptx.py` | Primary generator: one spec → native PPTX; `--html` emits Target B from the same source |
| `scripts/pptx-to-html.py` | Reverse flow: someone else's `.pptx` → single-file HTML (reads shapes, not a render) |
| `scripts/retext-pptx.py` | Round trip: text nodes only; unchanged geometry fingerprint lets it through |
| `scripts/check-*.py` | 12 offline gates: `check-wash` (B and C writing the same declarations), `check-theme-colors` / `check-theme-textures` (tilework and material images), `check-fit` (F1–F4), `check-layouts` (family/style/old names/offline/vendor), `check-prose` (density), `check-morph` (transition pairing), `check-deck-sync` / `check-preview-sync` (deck and preview board in step), `check-bitmap-assets` (bitmap sources and derived files), `check-fonts` / `check-installed-fonts` (bundled and installed fonts) |
| `scripts/check_doc_claims.py` | Document reconciliation: every number and name written in md is checked back against disk (a vanished anchor is red too) |
| `scripts/selftest.py` | Self-test suite: run it after installing; `EXIT=0` means complete |
| `SELFTEST.md` | Per-item criteria and how to run each gate alone |
| `docs/封面.md` | Cover registration, the inscription, print notes |
| `scripts/` (others) | Remaining generators and material tools (`build-deck.py`, `md2deck.py`, `merge-to-pptx.py`, `export-theme-textures.py`, …) |

## Licence and third-party assets

**This skill's own text and specs ship under MIT** (`Copyright (c) 2026 L4ST-afk`) — see [`LICENSE`](LICENSE).
**Bundled third-party assets** (including two internalised font families and html-ppt's MIT assets) are registered one by one in [`ATTRIBUTION.md`](ATTRIBUTION.md); the licence texts themselves live in `LICENSE-html-ppt.txt`, `assets/fonts/OFL-素材集市智造黑1.02.txt` and `assets/fonts/cheesefoam/OFL.txt`.

These three licence texts must ship with any redistribution.

Bundled fonts (the P9 declaration):

- `素材集市智造黑1.02.ttf` — SIL OFL 1.1, full character set, one weight
- `CheeseFoamOolongSong-Subset-Bold.woff2` — SIL OFL 1.1, GB2312 subset
- `assets/fonts/latin/` — Playfair Display, Inter, Space Grotesk, JetBrains Mono, each Regular and Bold (Latin subsets, SIL OFL 1.1, licences in the matching `OFL-*.txt`).
  ⚠ Space Grotesk's 400 instance carries an internal family name written upstream as "Space Grotesk Light" while CSS still calls it `Space Grotesk`; the PPT side declares the internal name, and the scripts align both.

## morph and role names (why shapes get renamed)

morph tweens by "same-named object across pages", and python-pptx counts names **independently per page**: `TextBox 3` on page 1 and `TextBox 3` on page 2 are two different roles entirely.
So on emit the automatic names are rewritten to `family-sN` (content) and `family-bgN` (wash layer), so two pages of the same family actually line up.

Two preconditions, stated plainly: ① only **same-family** adjacent pages can pair (cross-family never pairs, deliberately); ② optional blocks that appear and vanish shift the numbering (a kicker on one page and not the next moves everything after it by one). For strict pairing, give the shape a `name` in the spec — neither the gate nor the renderer looks at names, pairing uses it alone.

`scripts/check-morph.py` verifies three things: `p159:morph` sits inside `mc:AlternateContent/p159:Choice` with `p159` in `Ignorable` (omitting it makes it silently dropped), `p14:dur` is within the schema range, and **whether anything pairs** (zero same-named shapes on the next page → this page's morph equals fade, red; a morph declared on the last page is only idle, noted but not red).

**Playback cannot be verified, and that is written into the gate's output.** No tool currently available plays it back and reports: officecli's screenshots are stills and `validate` only proves the schema. The deepest comparable, `jsamuel1/PptxGenJS`'s fork, also only ticked "schema passes" in its own acceptance list — the line `Verified to animate in PowerPoint` is empty.
