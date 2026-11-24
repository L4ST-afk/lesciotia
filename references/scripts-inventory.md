# 脚本清单（30 支：29 支 .py ＋ render-png.sh）

> 从 `SKILL.md` 的「## 脚本」下沉（2026-11-23，评审#09：主文件承载了整张表且计数与磁盘不符）。
> 本卷是脚本的唯一清单；⛔ 新增/删除脚本必须同步本卷，`scripts/check_doc_claims.py` 的
> `[脚本漏登]/[脚本悬空]` 双向判据会红。

## 目录

- 全表
- 共同约定
- 七道判据闸与必跑链

## 全表

| 脚本 | 用途 | 依赖 |
|---|---|---|
| `scripts/md2deck.py` | **Markdown 入口**：`.md` → 单册 HTML（`#` 封面 / `##` 切页；≥2 图→image-set 族（窄图过半→image-phone；4-5 张→band bento 主图 2×2；≤3 张→gal three），代码块→code，表→split，列表→text 卡列、编号≥3→process、单图→image-single、纯引用→quote、`###` 分节各自成页；首部 `<!-- nav: 序 > 现状 -->` + 每页 `<!-- sec: 现状 -->` 长出册级导航条（`nav-block:` 出色块型）；`--inline` 走 `build-deck.py` 出单文件；`--pptx` 把同一份 md 映射成 C 出口 spec 并调 `export-pptx.py`（cover/bullets/quote/table/end/figure 有对应，图组与代码页跳过并列出；长句自动拆「主句+小注」）。只认这几条映射，装不下仍要跑 `check-fit.py` | 无 |
| `scripts/build-deck.py` | 把 B 出口的 deck 内联成**单文件 HTML**（css/js/本地图全内联，主题收敛）；打包前先扫**中文半角标点**（罗蛇 T03，`--allow-punct` 降级为警告） | 无 |
| `scripts/render-png.sh` | headless Chrome 逐页截图（QA 与 A 出口的图片核验） | Google Chrome / Chromium |
| `scripts/selftest.py` | **冒烟自检**：编译全部脚本＋入口 `--help` 探测，并对瓦作/位图/染层三道闸跑负例（3＋5＋4 条），另加布尔数值、双出口漂移、morph 配对（正例必须配、跨页型零同名必须红）、曲线布尔（装了 pathops 就与解析 lens 对账；`curves=require` 在屏蔽 pathops 的环境里必须红）与 PPTX→HTML（页数与文字必须过来）、往返闭环（改字后几何指纹必须一模一样）；⛔ 只证「脚本没坏到语法都过不去」，不证业务口径 | 无 |
| `scripts/check-installed-fonts.py` | **系统字体分发检查**：`local()` 族名与 `unicode-range` 是否撑得住（han-only 主题的标点回落），`--html` 出浏览器实测页 | 无 |
| `scripts/make-ximai-bold.py` | **标题字生成**（可复现）：喜脉喜欢体裁字 → 沿轮廓机械外扩加粗 → 按 OFL 改名写 `WanhangXimaiBold-Subset.woff2`；重跑需自备原 ttf | fontTools / pyftsubset |
| `scripts/merge-to-pptx.py` | 逐页 PNG → PPTX（**A 出口**，每页一张全幅图；页序按 `NN-` 前缀，不按 mtime） | python-pptx, Pillow |
| `scripts/export-pptx.py` | **C 出口·原生**：读主题 `:root` 与一套 1600×900 栅格，用 python-pptx 直出可编辑 PPTX（12 页型：cover/bullets/kpi/end/comparison/timeline/table/quote/**chart**/**figure**（一图一页，位图原比例缩进版心、图注在下；SVG 点名拒绝）；`figure`/`figures` 的图片与图组按 `--radius` 同值写 `a:prstGeom roundRect`（图仍是原图，形状即裁切），图注条只圆底角——原生 chart part，可改数据；`kind=bar/bar-h/line/pie/doughnut/radar`，瀑布/哑铃/点阵无原生等价，**点名拒绝**）；字体按「声明栈→本机→同类骨架」降级并写入三槽（latin/ea/cs）；写完回读逐页数形状与字符，整页贴图必红；`--deck-css` 读整册模板标题、`--bundle-fonts` 拷随包 ttf、`--preview` 自绘近似、出件前自动跑成稿闸 `check-prose.py`（红即拒，`--allow-prose` 放行）；`--render-check` 调 officecli 出结构问题清单+校验+真渲染（`--render-grid` 只出整册缩略拼图，约 5 秒；`--render-pages 1,3` 只重渲点名页）；`--transition`/`--transition-ms` 出页切换（默认按瓦作 `.slide` 推时长与方向）；`--animate` 写 `p:timing` 逐组淡入（每页内容形状切 ≤4 组、`clickEffect`+`withEffect` 挂同 grpId，`--animate-ms` 改时长，页面 `animate:false`/`animate_groups` 可覆盖）；页面/形状可带 `wash`（`fill` 渐变、`boolean` 差交、`path` 直译且默认按三次贝塞尔出件（`wash_bezier`，`"curve":"polyline"` 才回折线），导出时求值；`boolean` 两边都是 `path` 且装了 `skia-pathops` 时走真曲线裁剪（`wash_curves`/`curve_bool`），`"curves":"require"` 强制该档；`--hb-measure` 把量宽换成 uharfbuzz 整段 shaping） | python-pptx；可选 Pillow / officecli |
| `scripts/check-layouts.py` | **梁架闸**：L1 族↔文件一一对应、L2 族页每段 `<section data-style>` 的集合＝`_families.json` 的 `styles`（段数与式数同时对数）、L3 旧名不得复活成文件、L4 文档里不再把旧名当版式名、L5 族页不许指外网脚本、L6 引用的 vendor 文件必须在、**L7 族页用到的 class 必须在 base.css / layouts.css / 主题里真有样式**；`--json` 出摘要 | 标准库 |
| `scripts/check-fit.py` | **装得下闸**：起只读 HTTP 服务、请求 `.html` 时注入探针，用 headless Chrome 逐段量 F1 越出画布 / F2 自身被裁 / F3 横向溢出 / F4 被父盒裁；`.notes`/`.overview`/`.deck-header`/装饰层不量，有可滚动祖先的元素就地放过；`--theme` 换主题复量；⛔ 不许改回「复制到临时目录 + 软链 assets」那一版（探针写穿 symlink 会脏族页源码） | Google Chrome / Chromium |
| `scripts/pick-recipe.py` | **体裁判型与提示词配方**：五型（汇报/提案/讲解/复盘/发布），中/英/日三语触发词（中文×2、外文×1，词边界匹配）＋结构信号打分，头名与次名差 ≤2 判「两型都对」（分段写不混段）；`--detect` 判草稿或 spec、`--show <key>` 出该型提示词（角色+硬要求+禁词+四问+骨架）、`--list`、`--json` | 标准库 |
| `scripts/check-prose.py` | **成稿闸**：九条判据查文字密度——套话词表、标题空转、lede 复述标题、单条 ≥20 字或多句读、数字无 `source`、缩写首现无括注、一页多主张、正文 <30 或 >260 字（阈值随正文字号 32px 重算）、问叹超页数；`--strict` 警告也算红，`--suggest` 闸后判型，`--json` 出摘要 | 标准库 |
| `scripts/check-wash.py` | **瓦作翻译闸**：验 spec 的 `fill` / `boolean` / `path` 能不能翻——`conic-gradient`、`repeating-*`、`union`、`polygon()`、未定义 token、自交折线一律红；`--html` 再加一道「两处声明是否同一串」的漂移比对；不给 spec 时只报瓦作里的「已知不换算」清单（INFO，不红） | 标准库 + wash_bridge |
| `scripts/check-morph.py` | **morph 结构闸**：`p159:morph` 是否在 `mc:AlternateContent/p159:Choice` 内、`Ignorable` 是否带 `p159`、`p14:dur` 是否在 schema 范围、**与下一页的同名形状数**（0 个 ⇒ 实际退化成 fade，红）；末页声明 morph 只出注记。⛔ 播放效果不判（本机无播放器，闸里明写「未核验」） | 标准库 + python-pptx |
| `scripts/retext-pptx.py` | **往返改字**（已有 pptx → 只改文字/备注 → 还是那份 pptx）：`--dump` 抽非空文本框清单（`slide/id/name/text/paras/runs/geom` 指纹）、`--edits` 照清单改、`--verify` 调 officecli；改完逐形状比 `spPr/style/bodyPr` 的 sha（`_sp_hash`），几何一变就报错 | python-pptx；可选 officecli |
| `scripts/pptx-to-html.py` | **逆流出口**：已有 PPTX → 单文件 HTML（读形状不抓渲染）：位置/字号/字重/颜色/对齐从 XML 读，`a:gradFill` 反解成 CSS 渐变（含 radial），`custGeom` 读成内联 SVG，表格 → `<table>`、图片 → base64、备注 → 隐藏 aside；图表/SmartArt 占位并计数。**近似还原**，不还阴影/3D/艺术字 | python-pptx |
| `scripts/wash_bridge.py` | **染层与墨线**：CSS `linear-gradient`/`radial-gradient`（多色标、角度、alpha）→ `a:gradFill`，布尔结果（两圆走解析解；其余多边形对多边形走 `poly_bool` 折线求值，可出多轮廓/挖洞，共享边按同侧/异侧分类——`collinear_overlap`）与 `clip-path: path()`（M/L/C/Q/A/Z，`svg_segments`/`custgeom_segments` 把 A/Q/C 换成 `a:cubicBezTo`）→ `a:custGeom`；带 proofer CLI，出一份样张核对换算；另含**可选后端**封装 `curve_bool`（skia-pathops，缺则 RuntimeError）/ `hb_width`（uharfbuzz，缺则 RuntimeError）与能力表 `backend_report()` | python-pptx + lxml |
| `scripts/verify-pptx-editable.py` | 判一份 pptx 是否**真可编辑**（形状层：每页文本形状数 + 整页位图占比） | python-pptx |
| `scripts/merge-to-pdf.py` | 逐页 PNG → PDF | Pillow |
| `scripts/check_doc_claims.py` | **维护闸**：文档里写的数字/名字/路径逐条对回磁盘事实；另含**罗蛇字符级红线 T07/T08**（中文容器的负字距与假斜体，含内联 `style` 与代码注释豁免）（改完文档必跑，见下方体量段） | 无 |
| `scripts/gen-theme-slices.py` | 从九份预览板截「风格切片」写 `docs/themes/<slug>.png`（隐藏字体提示条、固定裁切框 380,8–1520,700、缩到 900 宽），给 README 主页九宫格用 | Pillow + Chrome（走 `render-png.sh`） |
| `scripts/gen-theme-preview.py` | 生成 B 出口主题预览 HTML（自包含单文件；三种 flavor 见 `references/theme-preview.md`，配色判据见 `references/palette-check.md`） | 无 |
| `scripts/check-theme-colors.py` | **配色体检闸**：读 `:root` 的 hex token，算 WCAG 对比度 / CIE L* 间距 / 色相暧昧带（含 `amb-ok` 换轴放行与 `blk-ok` 描边放行，后者会把合成描边对主色的对比度一并算出）/ 主色-底明度差；`--md` 出人读报告、`--json` 出明细；**有 FAIL 即非零退出** | 无 |
| `scripts/check-preview-sync.py` | **预览页一致性闸（判据级）**：应查集合＝主题 CSS 全集（**缺预览页即红**）；读产物 HTML 对回主题 CSS，查色板 hex / 材质类 / 组件类 / 导览语汇 / 浮层压卡 / 模板源真值六类静默漂移；`--only` 限定主题、`--json` 出明细 | 无 |
| `scripts/check-deck-sync.py` | **deck 一致性闸**：交付单文件 deck 里内联的 `<style data-from data-sha256>` 指纹必须等于主题源文件当前指纹（主题改了没重打包 ⇒ 红）、源 deck 必须在库里、残留本地 link/script 不许有、页数与 `assets/decks.json` 登记一致；交付文件不在本机时降为 WARN | 无 |
| `scripts/check-fonts.py` | **字体闸（判据级）**：读 woff2 的 cmap 与主题 CSS 对账，查子集内容 / `@font-face` 死声明 / 字体 token 死引用 / 标点回落策略；`--only` 限定主题、`--json` 出明细 | fontTools（**硬依赖**，缺则 FAIL 并 exit 2） |
| `scripts/pick-brand-colors.py` | **配色取色器**：给定已定的色相，把明度按 `--gap`（默认 10 级）等距拉开、只改明度不改色相，吐出逐对 ΔL* 与对底对比；`--json` 出机器摘要 | 无 |
| `scripts/export-theme-textures.py` | **瓦作出图**：把主题 CSS 的材质类与内联 SVG 纹理渲染成 PNG（`assets/textures/<theme>/`，含材质板 `board.png` 与 manifest），供 A 出口当 style 参考图、C 出口当底纹贴图；幂等，源未变则跳过 | Google Chrome / Chromium |
| `scripts/make-material-tile.py` | **材质位图出图**：`--profile marble/grain/fiber/travertine` 出灰度**无缝 tile**（抽大块明暗 → 位移 + 余弦交叉淡化 → 压到极窄区间），供主题 `repeat` 叠在 token 上；`vein/vein-dark` 两档**不做无缝**，出 Calacatta 式大脉络（200..255 / 反相 0..58）；`mask` 出 RGBA **脉络掩膜**（alpha=形状，配 token 色走 mask-image，⛔ 必须 data URI 内联，Chromium 拦 file:// mask）。颜色不进图，⛔ 位图必须灰度 | Pillow / numpy |
| `scripts/check-bitmap-assets.py` | **位图资产闸**：`registry.json` 对回磁盘与主题 CSS，查字段/sha/尺寸/色彩类型、体积预算、blend 白名单、许可落点、**每个 `used_by` 逐处接线**、源目录孤儿、**同图重复登记必红（B9）**、**分档预算不许写松（B10）**、**接线主题 CSS 必须能解析（B11）**（B1–B11）；判据见 `references/theme-bitmap.md` | 无 |
| `scripts/probe-texture-visibility.py` | **可见性实测**：对每个 `used_by` 渲 A/B（`<sel>--flat` / 默认），headless Chrome 截图后量「高频增益」与「低通差」，**判的是像素不是 CSS 文本**。⚠️ 闸只能证明四要素写在文件里，证明不了它真的画出来（见`references/theme-bitmap.md` 的两次假绿）；接完线必跑一遍，约 3–6 秒/处 | Pillow / numpy / 本机 Chrome |
| `scripts/check-theme-textures.py` | **瓦作出图闸**：manifest 的 `source_sha256` 对回当前 CSS（改主题不出图 ⇒ 红）、逐张 PNG 宽高、palette 仍在 `:root`、9 主题覆盖、孤儿文件；判据见 `references/theme-to-export.md` | 无 |

## 共同约定

三个合并类脚本都认 `--force`（覆盖前先在同目录留 `.bak-<时间戳>` 基线）和 `--json`（末行输出一行**机器可读**摘要，含页数/体积/内联数）；`render-png.sh` 用 `FORCE=1` 覆盖。所有脚本的判据都是**产物本身**（回读页数/内联数/文件非空），不是退出码——外层读 `--json` 末行的 `ok`（`build-deck.py` 的 ✓ 只在写后回读全过时才打印），⛔ 别靠 grep 日志里的 ✓。

- `render-png.sh` 用 `FORCE=1` 覆盖。
- 判据一律是**产物本身**（回读页数/内联数/文件非空），不是退出码；外层读 `--json` 末行的 `ok`。
- 退出码语义：`check-theme-colors.py` 有 FAIL 即 1；`check-fonts.py` 缺 fontTools 即 2；`check-deck-sync.py` 未登记源/缺产物/指纹不符即 1；`check-preview-sync.py` 缺预览页即 1。

## 七道判据闸与必跑链

判据级闸（直接读产物/字体文件对账，不是「脚本能起来」）：`check-preview-sync.py`（预览页漂移）、`check-fonts.py`（字体子集与 token）、`check-theme-textures.py`（材质图与主题源对账）、`check-bitmap-assets.py`（位图登记与磁盘/主题对账，B1–B11）、`probe-texture-visibility.py`（位图是否真的可见）、`check-deck-sync.py`（交付 deck 与主题是否同步）、外加符号链接检查与 `check-morph.py`（morph 结构，不当判据闸——播放验不了）。

改主题必跑：`check-theme-textures` → `check-bitmap-assets` → `probe-texture-visibility` → `selftest` → `check_doc_claims` → `check-theme-colors` → `check-preview-sync` → `check-deck-sync`（另有 `check_limits` / `vaccinate` 两支体量与体检闸，按库规矩另加）。

⛔ 只有 `check-theme-textures`（3 条）、`check-bitmap-assets`（5 条）与 `check-wash`（4 条，conic／union／未定义 token／未知 shape）在 `selftest.py` 里带负例，另加「布尔数值（解析 lens 作标尺 + 自交必拒）」「双出口漂移」与「morph 配对（跨页型零同名必红）」三组，其余各闸的负例见 `SELFTEST.md`——别把「自检 PASS」当「七道都验过」。
