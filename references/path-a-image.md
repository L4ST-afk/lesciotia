# A 出口 · 影像 deck

逐页生图 → 合并成 pptx/pdf。适合阅读型/分享型 deck，或没有模板约束的创意稿。

## A1 · 派生提示词

对 `pages/` 里每一页：

1. 读 `references/base-prompt.md`（骨架）
2. 从 `outline.md` 抽 `<STYLE_INSTRUCTIONS>` 块（**不要回头再读风格文件**，否则同一份 deck 会漂移）
3. 填该页的 `title / kicker / points / visual`
4. 有 `layout` 时加 `references/layouts.md` 的对应构图指引
5. 写到 `prompts/NN-slide-{slug}.md`

提示词文件头部带 frontmatter（可复现记录，换后端不用重写）：

```yaml
---
slide: 3
filename: 03-slide-traction.png
style: corporate
dimensions: clean+professional+geometric+balanced
aspect: "16:9"
references:
  - ref_id: "01"
    filename: 01-ref-brand.png
    usage: direct        # direct | style | palette
---
```

**硬要求**：prompt 文件必须先生成，再调生图后端。没有 prompt 文件就没有可复现性。

## A1.5 · 主题参考（瓦作 → A 出口，2026-11-21）

用户要「和某个瓦作同款视觉」（如「按虬江那套出」）时，主题不能当风格键用，改走这张图：

1. 跑或取 `assets/textures/<theme>/board.png`（没有就 `python3 scripts/export-theme-textures.py --only <theme>`）；
2. 把它作为 `--ref` 的 `style` 参考图传给后端（每页都用同一张）；
3. 从同目录 `manifest.json` 的 `palette` 里挑 3–5 个 hex 写进每页 prompt 的正面描述，
   ⛔ 别在这里另抄一份色值规格——manifest 是派生记录，真源在主题 CSS 的 `:root`；
4. 后端不吃参考图 ⇒ 降级成文字（材质词 + hex 写进 prompt），⛔ 不许静默跳过，交付摘要里写明。

判据：提示词里出现的 hex 必须能在 `manifest.json` 的 `palette` 里找到；主题名必须能对上 `assets/themes/<theme>.css`。

## A2 · 选生图后端

按序：当前请求点名 > `EXTEND.md` 的 `preferred_image_backend` > 自动（runtime 自带的生图工具优先；只有一个外部后端就用它；多个就问一次）。都没有就告诉用户并问怎么办。

会话一致性：后端支持 session 就传 `slides-{slug}-{timestamp}` 复用同一会话；不支持就靠 `STYLE_INSTRUCTIONS` 里的固定配色/元素描述维持一致。

## A3 · 逐页生图

1. 先确认 `prompts/` 里 N 份齐全且与 `pages/` 的 N 一致
2. 逐页顺序生成，每页 10-30s，页间报进度 `Generated X/N`
3. 图落到 deck 根目录，命名 `NN-slide-{slug}.png`
4. 失败先自动重试一次，仍失败就报错停下（不要跳过某页继续，页数一乱后面全错）
5. **别拿 QA 截图当成品图**：`render-png.sh` 产出的是 `{stem}_NN.png`（质检用），merge 脚本只认 `NN-` 前缀；把 B 出口的截图直接喂给它，会以「目录里没有 `NN-*.png`」exit 2 停下。要用就先改名成 `NN-slide-{slug}.png`（2026-11-10 实测踩到）。
6. 素材选用标准与图片纪律（分辨率门槛、视觉质量、内容匹配、版面适配、原始宽高、同图不重复、背景不带字）见 `content-rules.md` §6 / §8。

参考图（`--ref`）：

| usage | 作用 |
|---|---|
| `direct` | 把文件作为参考图传给后端（每页都用） |
| `style` | 只抽线条/质感/氛围写成正面描述，追加进每页提示词 |
| `palette` | 只抽 hex 色板，追加进每页提示词 |

后端不吃参考图时，一律降级成 `style`/`palette` 的文字描述，并在摘要里说明。

## A4 · 合并

```bash
# 逐页 PNG → PPTX（页序按 NN- 前缀；尺寸 auto 时高 7.5in、宽按首图比例，16:9 正好 13.33×7.5）
python3 {baseDir}/scripts/merge-to-pptx.py slide-deck/{slug} --notes slide-deck/{slug}/notes.json

# 逐页 PNG → PDF（150dpi，先转 RGB，避免 alpha 黑底）
python3 {baseDir}/scripts/merge-to-pdf.py slide-deck/{slug} --dpi 150
```

`notes.json` 可选：`{"03-slide-traction.png": "这页只说三件事…"}`，会写进 pptx 备注页。讲稿内容从 `pages/NN.md` 的 `notes` 字段来。

**页数自检**：merge 会打印页数；与 `outline.md` 的 N、`pages/` 份数三方必须相等。不等就停下查，别交付。

## A5 · 单页重出

```bash
# 只重出第 3 页（或 2,5,8）：先改 pages/03，再同步 prompts/03，然后走一遍生图
--regenerate 3
```

顺序永远不变：**先改 pages → 再同步 prompt → 再重出图 → 再 merge**。反过来（直接重出图）会让记录与产物脱节，下次谁改都不知道以谁为准。

## A 出口的边界

- 文字不可编辑。客户要改字就转 C，别承诺"图里字能改"。
- 中文小字在图上容易糊：正文字号按 `design-guidelines.md` 的下限走，宁可拆页不要压字号。
- 敏感人物：用风格化替代形象，不做写实肖像（这是 `content-rules.md` 的既有规则）。
- 不要把大段表格交给模型画——表格页用 B 出口的 `table` 版式，或先出数据图再嵌入。
