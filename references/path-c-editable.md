# C 出口 · 可编辑 PPTX

客户要自己改字、要套品牌母版、要加原生动画——只有这一类需求才走 C。**C 出口不在本 skill 内实现渲染**：它把统一计划交给外部引擎，本 skill 负责"输入成型 + 交付核验"。

## C0 · 先看引擎是否可用（必做，硬门）

外部引擎：`ppt-master`（MIT，© Hugo He），正本目录 `<skills-root>/ppt-master`。

它自带授权完整性闸门，进任何路线之前必须先跑：

```bash
python3 <skills-root>/ppt-master/scripts/attribution_guard.py
```

**判据只认当次退出码，⛔ 不认本文里的任何历史读数。**（2026-11-10 真事故：本文曾写着「返回 78 ⇒ C 出口当前不可用」，而当天引擎已修好、闸门早已 `exit 0`；文档没跟着改，出口路由照旧降级成 A 的位图合图，用户拿到一份「打不开字」的 pptx。文档里的旧读数是**历史**，不是当前状态。）

**实测记录（2026-11-10 复测，当天修复后）**：`attribution_guard.py` → **exit 0**（连跑两次均 0）；`LICENSE` 归一化 sha256 = `80cefc23…0921`，与闸门内置摘要一致 ⇒ **C 出口可用**。

按上游规则：当次非 0 才**停止**，不许检查、修补或绕过这个闸门。遇到红灯只有两条路：

1. 告诉用户：C 出口引擎校验不过，需要从官方完整分发重装 ppt-master（或把缺失的 attribution 文件补回原样），再重试。
2. 经用户同意后降级（降级必须在交付摘要里写明）：
   - 降 A：出图片式 `.pptx`，**明确说"文字不可编辑"**；
   - 降 B：出单文件 HTML + `qa/` 截图 + `outline.md`，让用户自己在 PowerPoint/WPS 里照着改。

⛔ 不许装作 C 出口成功，也不许把 A 的图片 pptx 说成"可编辑"。

## C1 · 输入准备（引擎可用时）

ppt-master 认它自己的 plan 规格，不认我们的自由格式。转换口径：

| 我们的 | 交给引擎 |
|---|---|
| `outline.md` 头部（topic/audience/language/slide count） | 顶层元信息 |
| `outline.md` 的 `<STYLE_INSTRUCTIONS>` | 色彩/字重/密度锚点（它不认四维命名，转成具体 hex 与字重描述） |
| `pages/NN.md` 的 `title` / `points` / `type` | 该页的 page job 与内容块 |
| `pages/NN.md` 的 `notes` | 备注页 |
| `layout` 字段 | 不直接映射；只作为"这页要有几个块、什么关系"的提示 |
| 主题底纹（`.cp-marble` 等材质） | 取 `assets/textures/<theme>/mat-*.png` 或 `tex-*.png`，作为**版式背景或局部装饰**交给引擎；⛔ 整页铺底图片会撞 `verify-pptx-editable.py` 的 `FULLBLEED_RATIO=0.9`，可编辑判据当场红 |

**主题底纹的用法**：`mat-*.png` 是材质样片（不平铺）、`tex-*.png` 才按 `manifest.json` 的 `tile_w/tile_h` 平铺；底纹只做低面积装饰，或要求引擎设为版式背景。细则见 `references/theme-to-export.md`。

**动笔前先读** `ppt-master/SKILL.md` 的 Mandatory Load Order（它要求先读 routing.md 再选路线），不要跳步。常见路线：`generate-pptx`（默认）、`edit-native-pptx`（改已有 pptx）、`beautify`（美化既有件）。

## C2 · 什么时候值得走 C

| 场景 | 值不值 |
|---|---|
| 甲方明确说"我要能改字" | 值 |
| 必须套公司母版/法务模板 | 值 |
| 要原生动画或转成视频 | 值（引擎有 animation/video 路线） |
| 只是自己看/发群 | 不值，走 A 或 B 更快 |
| 只有一页要改 | 不值，回 A/B 单页重出 |

## C3 · 交付核验（回来必查）

| # | 查什么 | 判据 |
|---|---|---|
| 1 | 文本真可编辑 | 跑 `scripts/verify-pptx-editable.py <出件>`（exit 0 才算）；判据是每页 ≥1 个文本形状且无整页位图，⛔ 不是「PowerPoint 能打开」 |
| 2 | 页数与大纲一致 | 与 `outline.md` 的 N 相等 |
| 3 | 字体与母版 | 母版/占位符生效；**字体判「版式没走形」，不判「零替换」**——引擎会把 CJK 面统一钉成 `Microsoft YaHei`、拉丁面钉成 `Arial`（2026-11-10 实测），macOS 打开时必然提示替换成苹方，属预期，只要行宽/换行没变就不算失败 |
| 4 | 备注有讲稿 | 备注栏能读到 `pages/NN.md` 的 `notes` |
| 5 | 风格没走形 | 配色/字重/留白三类页上一致，没有一页像另一份 deck |

任一条不过，先回引擎重跑该页（它的规则是"在哪层坏就在哪层修"），不要在我们这层硬补。

## C3.5 · 出件后回读形状层（别靠「能打开」）

```bash
python3 scripts/verify-pptx-editable.py "<出件.pptx>" --json
```

它读的是**形状层**，不是后缀：每页文本形状数 + 整页位图占比（图片占页 ≥90% 且无文本 ⇒ 判为 A 出口的合图件）。exit 0 才叫可编辑。

**出件会带编辑级警告，别当失败**：手写 SVG 若把 `font-family` 写到每个 `<text>`、又没给根 `data-pptx-page-role`，末检查器会给 `Noncanonical compact authoring` / `ungrouped top-level element` 之类**advisory**（实测 3 页 19 条），POSTFLIGHT 仍是 `passed-with-warnings`。要清就按它提示跑 `compact_svg_styles.py` 归一化，不清也能导出。

两侧都实测过（2026-11-10）：C 出口的原生件 → 每页 `TEXT_BOX`、图片 0、exit 0；`merge-to-pptx.py` 的合图件 → 每页 1 张 picture、文本 0、exit 1。

⛔ 不许把 `merge-to-pptx.py` 的产物当 C 出口交付——它是 A 出口，文件名和页数都对，只有形状层能看出区别。

## C4 · 本 skill 与 C 出口的边界

- **不打包** ppt-master 的资产（78MB、13,019 文件、自带授权闸门），只作指针引用：本机实例在本地云盘的 Kroma 目录（`<云盘>/Ob/Kroma/ppt-master`），仓库内 `skills/ppt-master` 是指向它的软链。所以 来雪亭Lesciotia 在没有 ppt-master 的机器上仍然能用 A/B 两出口。
- **不接管** ppt-master 的执行纪律（它自己的 blocking gate 优先）。
- **只提供**：分析、archetype 页序、大纲、逐页记录、质检口径。
- 换到 C 出口后，`pages/NN.md` 仍是正本；ppt-master 的中间产物归它自己的 artifact ownership 规则管，不要再复制一份到 `pages/`。
