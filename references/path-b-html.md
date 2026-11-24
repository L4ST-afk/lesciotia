# B 出口 · 网页 deck（单文件 HTML）

要"讲"就用这个：键盘翻页、动效、`S` 演讲者模式（当前/下一页 + 逐字稿 + 计时）、离线可开、一个文件发出去。

## 目录

- `B0 · 手上有什么`
- `B1 · 定主题与版式`
- `B2 · 搭 deck`
- `B3 · 写每一页的六条规矩`
- `B4 · 打包成单文件`
- `B5 · 逐页核验`
- `B6 · 演讲者模式`
- `B7 · 现场级能力：本库到哪为止`
- `B8 · 交付`

## B0 · 手上有什么

| 路径 | 内容 |
|---|---|
| `{baseDir}/assets/base.css` | token + 版式原语 + 1920×1080 固定画布（不要按 deck 改它） |
| `{baseDir}/assets/themes/*.css` | 9 个主题（全部自建实体），各是一组 `:root` 变量覆盖（含 2026-11-19 fork 的 `century-sq` 亮色版与 `century-ave` 暗色版）；备选配色只在 `references/palette-atlas.md` 记 token，不落成主题文件 |
| `{baseDir}/assets/layouts/*.html` | 17 族版式（族页内一段一式），带真实示例数据 |
| `{baseDir}/assets/full-decks/*/` | 5 套成套模板（course-module / pitch-deck / tech-sharing / weekly-report / presenter-mode-reveal） |
| `{baseDir}/assets/animations/` | 26 个 CSS 动效类（`data-anim`）＋1 个 JS 计数器（`counter-up`），runtime `ANIMS` 共 27 项 |
| `{baseDir}/assets/runtime.js` | 键盘、演讲者窗、总览、深链、进度条、`?render` 出图态 |
| `{baseDir}/examples/demo-deck.html` | 一份真实的单文件成品（5 页，swiss-grid），可直接双击打开看效果 |

**铁律：不从零写版式。** 先挑现成 `layout`，把示例数据换成真内容；17 族都不合适才考虑新造，并写清为什么。

## B1 · 定主题与版式

1. 主题：按 `styles-unified.md` 的「主题选择速查」挑；拿不准就打开 `assets/themes/<name>.css` 看 `:root` 色板，别凭名字猜。
2. 版式：按页的 `type` 与 `points` 数量挑（见下表）。`pages/NN.md` 的 `layout` 字段写的就是文件名 stem。

| 这页要干什么 | layout（族） | 族内用哪一式 |
|---|---|---|
| 封面 | `cover` | 唯一一式：kicker + 标题 + lede + pills |
| 目录/议程 | `toc` | 3–6 条，多了就拆 |
| 章节过渡 | `section` | 大字 + 一句过渡 |
| 3–5 条并列要点 | `text` | 要点清单式（旧名 bullets）；别超过 5 条 |
| 两组对照 | `compare` | A/B、利弊、旧 vs 新、两图比对都在这一族 |
| 分栏 | `text` | 换 `g2`/`g3` 改栏数，不另挑版式（旧名 two-column/three-column） |
| 3 个数字 / 一个数字撑满 | `data` | 四格 KPI 式或单个大字式（旧名 kpi-grid/stat-highlight） |
| 趋势/对比数据 | `charts` | 柱/线/饼/雷达四式同页可比，Chart.js 已随包（离线可开） |
| 表格 | `data` | 明细表式；行数 >8 就拆页或进附录 |
| 流程/步骤 | `process` | 步骤式；线性流程就用它 |
| 时间线/路线图 | `process` | 时间轴 / 路线图 / 甘特都在这一族 |
| 结构/关系 | `diagram` | 流程图 / 分层架构 / 中心辐射三式 |
| 代码/终端 | `code` | 代码 ≤15 行，超了截断讲重点 |
| 一张图 | `image` | 压标题 / 满幅 / 单图（不裁）/ 图文对半四式 |
| 3–6 张图 | `image-set` | 等分网格或大小错落 |
| 金句 | `quote` | 一句 + 出处 |
| 收束 | `end` | 谢谢式或行动式：给下一步动作，不是「谢谢」 |
| 清单/自测 | `data` | 勾选清单式，讲解 archetype 的 objectives/自测页用它 |

## B2 · 搭 deck

在 `slide-deck/{slug}/index.html` 写。最小骨架（`assets/` 前缀交给打包脚本解析，不要手改成 `../`）：

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="swiss-grid">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{标题}</title>
<link rel="stylesheet" href="assets/fonts.css">
<link rel="stylesheet" href="assets/base.css">
<link rel="stylesheet" id="theme-link" href="assets/themes/guanglan-rd.css">
<link rel="stylesheet" href="assets/animations/animations.css">
</head>
<body data-themes="swiss-grid">
<div class="deck">
  <section class="slide" data-title="Cover">…</section>
  <section class="slide" data-title="…">…</section>
</div>
<script src="assets/runtime.js"></script>
</body></html>
```

**成套模板怎么用**：打开 `assets/full-decks/<name>/index.html`，**抄 `<section>` 块**进自己的 index.html。五套模板都没有私有 `style.css`：版式全走 `assets/layouts.css` 的族页（17 族 38 式），底子走 `assets/base.css`，配色由主题一件决定，所以抄完只需保证自己的 `<link>` 也是这三样。**不要整文件复制**——它的 `../../../assets/` 相对深度是按模板自己的位置算的，复制到别处会全断链。

**可选件（要才引）**：`.sk12` 十二列骨架在 `layouts.css` 里；玻璃透镜另引
`assets/effects/lens.css` + `lens.js`（见 [effects-lens.md](effects-lens.md)）。
⛔ 不必为用一次效果把整册都加脚本——按页引，`data-lens-state` 自己会说明走的是真折射还是湍流兜底。

## B3 · 写每一页的六条规矩

1. **用 token，不写死颜色**：`color: var(--text-1)`，不要 `#111`。贴在 accent 填充上的字必须 `var(--accent-ink)`（主题的 accent 从纯白到纯黑都有，硬写白/黑必有一半主题看不清）。
2. **一页一个 `.slide`**：`runtime.js` 只让 `.is-active` 可见，其余隐藏；别用两层嵌套模拟分页。
3. **图片走 `.img-frame`**：`<figure class="img-frame"><img …></figure>`；截图/图表/logo 加 `contain`（不裁切），照片才让它 `cover`。裸 `<img>` 会撑破版心。主体图要压在色块或版心字上时用带 alpha 的 PNG/WEBP：生成或定制素材时 prompt 写「纯透明底，不烘焙投影」，并在最终背景上核对边缘与残留棋盘格（看像素，不看后缀）；`.img-frame` 不再给它加白底和阴影，满版照片才用不透明。
4. **讲稿进 `<div class="notes">`**：默认隐藏，只在 `S`/`N` 时出现。正页只放观众该看的信息（规则与写法见 `presenter.md`）。
5. **chrome 别手写**：`.deck-header` / `.deck-footer` / `.slide-number` / 进度条由 `base.css` + `runtime.js` 提供；每页只填 `data-current` / `data-total`。
6. **logo 声明一次**：`<body data-logo="logo.svg" data-logo-position="bottom-right">`；封面可用 `data-no-logo` 跳过。不要每页贴一遍。

动效：元素加 `data-anim="fade-up"`；列表/网格用 `anim-stagger-list` + `data-anim-target`。一场分享里动效**只在关键页出现**，每页都动等于没有动效。

页与页之间要有人过界：相邻两页至少留一个存活的元素、看得见地变成下一页的东西（末页的标题缩成页码、图表的柱子长成下一页的坐标轴、色块移到下一分区）。⛔ 停在前一页整体淡出、后一页重新进场——那是替换，不是过渡。这条只在关键页做，普通页直接切；做的时候静止比动作值钱，动作收尾要留得住。

## B4 · 打包成单文件

```bash
python3 {baseDir}/scripts/build-deck.py slide-deck/{slug}/index.html --assets {baseDir}/assets
# → slide-deck/{slug}/index-single.html（默认同名 -single）
```

脚本做的事：本地 css/js 全内联（`@import` 的本地 css 递归展开）、**本地 `<img>` 内联成 data URL**（svg/png/jpg/gif/webp；解析不到的原样保留并判红）、主题收敛成单一 `data-themes`、删掉 `data-theme-base`。写后回读六项不过就非 0 退出：残留本地 `<link>`、残留本地 `<script src>`、剥 `<script>`/`<style>` 后缺 class 含 `slide` 的 `<section>`、残留指向不存在本地文件的 `<img src>`、体积异常（0 或 >8MB）、`data-from=` 计数与内联数不符。读末行 `--json` 的 `ok`，⛔ 别 grep ✓。

**打包后再预览**：作者阶段不用管相对路径能不能直接双击（源文件引的是 `assets/`，只有 skill 目录里才存在），看一眼产物单文件即可。改一次 → 重新打包（约 0.1s），不要试图手工修相对深度。

## B5 · 逐页核验

```bash
bash {baseDir}/scripts/render-png.sh slide-deck/{slug}/index-single.html all slide-deck/{slug}/qa
```

逐页看 `qa/*.png`：文字有没有溢出、图片有没有被切、页码对不对、留白是否被背景吞掉。**看完再交付**——这一步省掉，八成会带着一页糊版交出去。

## B6 · 演讲者模式

按 `S` 开演讲者窗（四张磁性卡），`←/→` 同步，`R` 重置计时，`#/N` 深链。预览是同文件 `?preview=N` 的 iframe，像素级一致。出图走 `?render`：runtime 见到它就掐掉 `.slide` 的过渡与子元素的入场动效（CSS 过渡不吃 `--virtual-time-budget`，不掐会截在 opacity 半路上，整页发灰）。单文件下主题已收敛，`T` 不换主题属预期。详见 `presenter.md`。

**已知限制：`file://` 双击打开时，两块预览是空白**（2026-11-10 三臂实测）。CURRENT/NEXT 是 `iframe(src=本文件?preview=N)`，而 Chrome 把每个 `file://` 页面当不透明源 ⇒ 父窗读不到子窗（实测 `ACCESS-DENIED`），只剩底色。**讲稿、计时、页码、翻页、拖卡片都不受影响**，坏的只有预览。三条出路：

| 办法 | 实测结果 | 场合 |
|---|---|---|
| 起本地服务再开：`python3 -m http.server 8000`，用 `http://127.0.0.1:8000/<slug>-single.html` | iframe `complete`、7 页、封面与指标页文字都对 | **首选**，交付前就该这么验 |
| Chrome 加 `--allow-file-access-from-files` | 同样恢复（`complete`、7 页） | 仅本机自用，别写进交付说明 |
| 双击开、只讲不看预览 | 讲稿与计时可用 | 要**明说**，别让用户在台上才发现 |

两条判据别搞错：
- **别用 DOM 数页数**：`runtime.js` 初始化时会为 `O` 总览克隆整套 slide，7 页的 deck 实测 `document.querySelectorAll('section.slide').length` = **14**。数页只认 HTML 源（剥 `<script>` 后数），或读 `data-total`。
- **预览空 ≠ 键盘坏**：先在 http 下验，再决定是不是真 bug。

## B7 · 现场级能力：本库到哪为止

观众屏同步、当前/下一页预览、讲稿、分段计时都由 `assets/runtime.js` 原生提供（`S` 键），**不需要外部引擎**。

**本库不提供**：激光笔、排练记录（每页停留时长回看）。用户明确要这两样时，直说没有——⛔ 不要含糊承诺，也⛔ 不要为此引入外部引擎把单文件 deck 变成有依赖的工程。

## B8 · 交付

- `{slug}-single.html`（主交付，双击可开、离线可用）
- `qa/NN.png`（逐页预览，方便快速过目/发群）
- `pages/` + `outline.md`（正本，方便下次改）

**不要**把 `assets/` 一起发出去——单文件已内联一切；发目录等于把 500KB 主题库塞给用户。
