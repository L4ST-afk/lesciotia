---
name: 来雪亭Lesciotia
version: 1.2.73
description: "把内容做成一份 deck：一份大纲、一套风格系统、三种交付形态（影像件／网页件／可改件）——A 影像 deck（逐页 AI 生图 → pptx/pdf，不能改字）、B 网页 deck（单文件 HTML，键盘翻页 + 演讲者模式 + 逐字稿）、C 可改件（原生 PPTX，文本与形状都能改）。当用户要做 PPT、slides、slide deck、presentation、keynote、幻灯片、演示文稿、教学演示、培训材料、pitch deck、发布会 deck、技术分享 slides、周报/复盘 deck、科普长图或小红书图文，或要求「把这份文档/文章/笔记做成 X 页」、「逐页改某一页」、「加演讲者视图/讲稿」、「要可编辑的 pptx」时使用；用户要求给某个主题做预览页、theme preview、风格总览板、看某主题长什么样时也使用。Keywords: ppt, pptx, slides, slide deck, deck, presentation, keynote, slideshow, 幻灯片, 演示文稿, 教学演示, 讲稿, 演讲者模式, theme preview, 主题预览, style board, 风格板。"
metadata:
  vaccineOrigin: local
  vaccineVersion: e8d93bf0731f
  version: "1.2.73"
  created: "2026-11-10"
  sources:
    - "html-ppt (MIT, © lewis)（历史来源：2026-11-23 起本库代码件与整册已全部自写，无复制件）"
    - "ppt-master（C 出口外部引擎，指针引用）"
    - "三个 deck-* 模板件（只取场景→页序的事实结构）"
---

# 来雪亭Lesciotia · 结论成页

## 名称与读音

**中文槽：来雪亭**（主用——目录名、正文自称、对外表述都用它）｜**拉丁槽：Lesciotia**（仅作检索锚，必须跟在中名后，不单独出现）｜**合写：来雪亭Lesciotia**（无空格、无连字符、无下划线、无分隔符）。

**读音钉死**：意大利式 /leʃˈʃɔtja/，汉语「莱晓提亚」。`sci`＝/ʃ/，`-tia`＝/tja/。
⛔ 不读「莱西奥蒂亚」（英语式）；⛔ 不读「莱斯基奥提亚」（古典拉丁式）。
⛔ 汉字固定用「提亚」，不用「提娅」——「娅」是女名用字，本名标的是地方。

**双槽分工**：中文槽承载意象——雪从外来、落进亭中＝接料成景；拉丁槽只承载「可念、可搜、不撞名」，不拆字义解释。

**名字溯源**：亭在江心屿东北角，一九六四年郭沫若引文天祥《北归宿中川寺》「罗浮山下雪来未」诗意题「来雪亭」横额。拉丁槽 `Lesciotia` 是音骨架（`Le`／`sci`／`tia` 三段对三字，中段 `o` 承「雪」的圆唇韵），只作检索锚，⛔ 不拆字义解释；读音以本页 §读音钉死 为准。

### 三层词汇（2026-11-21 定）

名字里的「亭」和「雪」各管一层，别混用：

| 词 | 管什么 | 对应目录 | 数量 |
|---|---|---|---|
| **梁架** | 骨架：信息怎么排、几栏、什么顺序 | `assets/layouts/` + `assets/layouts.css` | 17 族 / 39 式（族页给式，`layouts.css` 给结构；每段 `data-style` 与 `_families.json` 的 `styles` 对账） |

梁架闸 `scripts/check-layouts.py`：族↔文件、段落数↔式数、旧名不得复活、文档不得再用旧名、族页不许指外网。
| **瓦作** | 表面：配色、字体、材质 | `assets/themes/` | 9 |
| **落雪** | 用户投进来的原始素材 | 无（输入侧） | — |

**梁架**取木构承重骨架义，且能拆出具体式样（三架梁、五架梁），对上 17 族、39 式：一族一文件，族页里一段一式；**同骨架的变体不再单列成段，而是同段的一个参数**（`g2/g3`、`mark=pc/diff`、`chrome`、`media`…），注记写在段的 `.params` 行。
**瓦作**取屋面工艺义（瓦、脊、滴水），是覆盖全部 17 个梁架的表面层——雪落在瓦上，不落在梁架上。
**落雪**取「雪从外来、落进亭中才成景」这一层：素材是别人的，本 skill 负责把料落成一页页。

⛔ 三个词只是**称呼**，目录名一律不改（`assets/layouts/`、`assets/themes/` 保持原样）。
改路径会打断全部引用与四道闸门，收益不抵成本。文档里写「14 个梁架（`assets/layouts/`）」这种带路径的形式。
⛔ 「檐」不可用作分层词：已占 40 处，龙华寺主题的核心母题就叫「塔檐 · 香灰 · 白墙」。

把内容炼成一份 deck。**一份 plan，三条渲染路径**：大纲、逐页记录、风格映射共享；出口只决定「最后长成什么文件」。

**主题预览（2026-11-20 内化，2026-11-24 补齐九份）**：九个主题各有一份预览页在 `examples/previews/<slug>-theme-preview.html`（`century-sq` 世纪广场、`century-ave` 世纪大道、`guanglan-rd` 广兰路、`friendship-bldg` 友好大厦、`qiu-r` 虬江、`panyu-rd` 番禺路、`fuzhou-rd` 福州路、`wanhang-fy` 万航渡、`longhua-si` 龙华寺），均为自包含单文件（字体 data URI，可直接发人）。生成脚本 `scripts/gen-theme-preview.py` + 模板 `scripts/preview-template.html` 已放进 skill，自定位、不依赖工作区：

```bash
python3 scripts/gen-theme-preview.py <主题名> <中文名> <英文名> [--dark|--aero]
# 世纪广场不加标志；世纪大道 --dark；广兰路 --aero；⛔ 两者互斥
```

完整制作方法与验收判据见 `references/theme-preview.md`（三种 flavor 判据、生成链路、新主题接入 checklist、踩坑）。改完预览必跑 `scripts/check_doc_claims.py` 与 `scripts/selftest.py`。
主题预览还能截成「风格切片」放主页：`python3 scripts/gen-theme-slices.py` 读九份预览板、隐藏字体授权提示条（`.fb/.lh/.py-fontnote`）、按固定框 380,8–1520,700 裁出板头＋色板＋材质，缩到 900 宽写进 `docs/themes/<slug>.png`；⛔ 预览板版面一变就得同步改裁切框，否则切片会带进下一节。

## 反例优先：踩坑在前，规则在后

**踩坑（2026-11-10，本地实测）**：融合后第一版把一份 5 页 deck 截成了 6 张图。不是渲染坏了，是数页数错了——`grep` 把内联进 HTML 的 `runtime.js` 注释里那行 `<section class="slide" data-no-logo>` 也算成一页。当时我先信的是脚本退出码 0 和「✔」日志，直到打开目录才看见多出的空页。同一类错在 C 出口差点重演：把「指针指向的引擎目录还在」当成「引擎可用」，跑出 `exit 78` 才发现那份 ppt-master 是被删过文件的残本。（同日晚已按官方 v6.7.2 补齐，闸门 `exit 0`；所以「C 能不能用」的判据改成**每次现场跑闸门**，不再看文档里的读数。）

**踩坑（2026-11-20，四主题预览页）**：改了主题 `:root` 的 token，预览页却还在写旧色值——12 个色值里 8 个对不上。同一轮还叠着三处同类：友好大厦 CSS 定义了 10 个 `.fb-*` 真材质，预览页一个没用、全走世纪广场的通用 `.d-*`（于是「鎏金塔身」显示拉丝不锈钢、「红玻璃星」显示瓷砖格）；广兰路主题 CSS 里 0 个 `.cp-*`，预览页靠生成器内联兜底补、兜底还写死旧色；世纪大道的导览面板整段还是上游的公园语汇（地铁站台写着「植被与休憩」）。**四处全是静默的**：退出码 0、日志全 OK、页面照常渲染，只是内容在说谎。根因是「生成器里硬编码替换表」这个结构——它把主题真值抄了一份，抄本必然漂移。

**踩坑（2026-11-20 第二轮，模板源）**：上一条修完，产物全绿了，但 `scripts/preview-template.html` **本身**还是错的——`--primary` 写着 `#f9d328`、`--line-6` 写着 `#d62768`（主题早已压到 `#721538`）。产物对是因为 `sync_palette` 按位置覆盖了；模板错是因为没人查模板。**闸门只查产物，就永远查不到「产物对、源错」这一层**——而任何绕过 `sync_palette` 的路径（手工改模板、新增分支忘了覆盖）都会把旧色直接漏进交付件。这是同类漂移的第三次复发，前两次修的都是下游。

**规则（预览页）**：预览页里任何与主题有关的**色值、材质类、组件类、语汇**，一律从主题 CSS 读，⛔ 不许在生成器里硬编码第二份。`gen-theme-preview.py` 的 `read_tokens()` + `sync_palette()` 就是这条的落地：色板 hex 全部取自 `:root`，改 token 预览页自动跟上。判据由 `scripts/check-preview-sync.py` 守——**六类**漂移任一条不成立就红：① 色板 hex 与 `:root` 不符 ② 材质样片退回 `.d-*` ③ 用了未定义的 `.cp-*` ④ 导览面板残留上游语汇 ⑤ `.g-modal` 压卡正文 ⑥ **模板源 `--token:#hex` 与主题真值不符**。已接进 `selftest.py`。**改完任何主题或模板，必须跑它，⛔ 不许只看「生成成功」。**

**踩坑（2026-11-21，字体子集与 token 死引用）**：龙华寺换法华文楷，要求「汉字用楷书、标点回落系统宋体」。第一版子集把 `，。；：！“”‘’《》〈〉「」` 一起打了进去——页面看着完全正常、六闸全绿，但标点根本没回落。根因：**CSS 字体回退是按字形走的**，字体里有这个字形，浏览器就不回退；光改 `font-family` 回退链无效，必须从子集里删掉字形。同一轮还挖出第二个静默错：万航渡的 `.g-card h3` 写着 `font-family:var(--font-body)`，而**九个主题都没定义 `--font-body`**（只有 `--font-sans`），浏览器直接丢弃整条声明、字体走继承——既不报错也不回落，看着「有点像但不是」，错了很久没人发现。两个错都属同一类：**声明写下了，但没生效，而没有任何闸门会问「它到底生效了吗」。**

**规则（字体）**：内化字体的子集内容与 token 引用由 `scripts/check-fonts.py` 守，六条判据任一不成立就红：① 子集里必须有汉字（**文件不存在时改查 `assets/fonts/FONTS.md`：登记为「自备」→ WARN 放行，未登记 → 红**）② `@font-face` 指向的文件必须存在且含汉字 ③ `@font-face` 声明了却无人引用＝白加载（实测抓到过 1.04 MB 死声明）④ 引用了内化字体却没有对应 `@font-face` ⑤ 标点回落策略（主题写 `@font-policy han-only` 声明）下，回退链里第一个含全角标点的字体必须就是宋体，中间插霞鹜文楷/楷体会截走标点 ⑥ `font-family:var(--font-X)` 里的 token 必须在本主题定义过。已接进 `selftest.py`。**换字体、改子集、动回退链之后必须跑它，⛔ 不许只看「页面看着对」。**

**规则（字体分发，2026-11-21）**：字体有**两条路**——A 装到系统（`@font-face` 的 `local()` 优先匹配，浏览器直接用系统字体，不加载子集）；B 放进 `assets/fonts/` 随包走。两条可混用。检测用 `scripts/check-installed-fonts.py`（`--html` 出浏览器实测页）。**han-only 主题（龙华寺）的 `local()` 必须配 `unicode-range`**：该主题标点必须回落宋体，而完整版 ttf 含标点，只写 `local()` 会让标点被楷书截走。`unicode-range:U+0020-007E,U+4E00-9FFF` 让浏览器**按码位**决定用不用这款字体，30 个常用全角标点全部落在区间外 → 回落宋体；子集 3818 个码位也全在区间内，随包行为不变。⛔ 回退链里也不许出现裸族名 `'法华文楷'`，否则绕过 `unicode-range` 直接命中。判据 F7 守 `local()` 族名：写错时浏览器**静默跳过**，页面看着正常但承诺失效，所以族名必须能在子集 name 表或本机系统字体里找到依据；判据 F8 守 han-only 主题的标题字体：用了 `local()` 却没 `unicode-range` 直接红。本库**不随包分发第三方字体**，只有万航渡喜脉体随包（本库派生件，OFL 允许再分发）。其余 7 款登记在 `assets/fonts/FONTS.md`，用户自备。判据是「**文件要么存在且含汉字，要么在 FONTS.md 登记为自备**」——两者都不是才红。理由：字体是文件不是风格，把 woff2 放进公开仓库属于再分发，7 款里只有 3 款带 OFL 原文允许再分发，2 款只有「免费商用」的使用授权，2 款连随包许可文本都没有。⛔ 别为了「开箱即用」把字体塞回仓库，那会把授权问题变成法律问题。缺字体时页面照常渲染（回退链写全在 `--ff-title`/`--ff-body`），只是标题笔意不同。**判断一款字体能否内化，分三步，缺一步就会误判**：
① 查 `name` 表（nameID 13/14）——作者自己写没写许可；
② 查 zfont.cn 字体页的「免费商用—许可范围」七项标签——**必须读 DOM 的 `class="can"/"not"`**，页面文本看不出区别。重点是**嵌入**（本库核心用法：woff2 当网页字体）和**衍生**（裁子集算不算）；
③ 查作者原文——**zfont 是二手登记，作者原文才是一手证据**，冲突时以原文为准。
⛔ **「name 表没写 OFL」≠「没有 OFL」**：南西油墨宋就是反例，`nameID 13` 空、作者公众号只写「免费商用」，但 zfont 登记为 SIL OFL 且七项全允许。「基于思源宋体」也不等于「可以再分发」，且同源判断不能靠 upem/点数（位图化重矢量化会全变），要做像素骨架比对并**带对照组**——方法见 `assets/fonts/FONTS.md`。
⚠️ **嵌入被标 `not` 的字体不能当网页字体用**：摇醒青年黑即属此类（zfont 标嵌入禁止、衍生禁止）。2026-11-21 已处置：`friendship-bldg.css` 的 `@font-face` **只留 `local()`、删掉 `url()`**，子集不随包分发；用户装了就用他自己的，没装则标题回落**宋骨黑体**（内化 OFL），预览页顶部有静态提示条。
⛔ 回退链里 `'SongguHei','宋骨黑体'` 必须排在 `'PingFang SC'` 之前，否则没装摇醒的用户掉到系统黑体，丢掉「标题偏宋意」的设计意图——闸门 F4 盯这个。
⛔ **`local()` 的可用名字每款字体都不一样，必须单独实测**：摇醒青年黑只有全名 `摇醒青年黑1.0 Regular` 能命中（族名与 PostScript 名都失败）；爱点风雅黑相反，英文族名 `Aidian FengYaHei` 与 PostScript 名 `AidianFengYaHei-Regular` 都能命中，中文族名「爱点风雅黑」失败。而 CoreText 层面这些名字全都正常，所以系统字体册查不出问题——只能在浏览器里实测 `new FontFace(n,'local("...")').load()`。验证看 `document.fonts` 里该族 `status` 是否 `loaded`，且回退字体是否变 `unloaded`。
⛔ **嵌入被标 `not` 的字体一律不随包**：摇醒青年黑（zfont font_799）、爱点风雅黑（zfont font_657）、法华文楷（zfont font_777）都是嵌入/衍生禁止，处置都是「`@font-face` 只留 `local()` + 子集 woff2 从仓库删除 + 预览页静态提示条 + 回退到随包 OFL 字体」。只删 `url()` 而留着文件等于风险还在。回退要挑**同类骨架**的随包 OFL 字体：黑体回宋骨黑体，楷体回霞鹜文楷，别一律掉到系统字体。
⛔ **注释里不许写 `@font-policy han-only` 字面量**：`check-fonts.py` 的 F5/F8 用正则扫全文，会把注释当真策略，触发假红。要提这条策略就写「han-only 标点策略」。
⛔ **别在 CSS 注释里写出 `@font-policy han-only` 的字面量**：`check-fonts.py` 用正则扫全文，会把注释当真策略，F5 立刻按 han-only 判红（2026-11-21 踩过）。

**方法坑（字体验证）**：① **全角标点宽度恒等于字号**，字宽法区分不出字体（`，。、？！（）` 在哪个字体里都是 40px），只能用 `·` `×` `—` 这类有区分度的字符判定；② **canvas 像素比对在这里失效**——缺字形时所有候选字体都回退到同一个默认字体，渲染结果全等，会误判成「都匹配」（第一遍就是这么被误导的）；③ macOS 上**族名与文件名经常对不上**（`STKaiti` → `simkai.ttf`、`STSong` → `songti.ttc`），查系统字体必须先做名字映射，否则「查不到」会被当成「没问题」。

**规则（模板源）**：`scripts/preview-template.html` 是生成器的唯一输入，它的 `--token` 默认值必须**等于某个主题的真值**（通常是世纪广场），⛔ 不许写一个「历史上曾经对过」的值。第 ⑥ 类检查就是这条的判据：它只对账「承载品牌色的 token」，材质固有色（大理石/草坪/玻璃渐变端色）不在此列——那些是材质本身的颜色，不跟主题走。

**规则**：页数只认「剥掉 `<script>`/`<style>` 块之后的 `<section>` 里 class 含 `slide` 的计数」（按词边界匹配，`class="slide full"` 也算），并与 `pages/` 份数、产物张数三方对账；任何「跑成功了」都以产物本身为证，不信退出码、不信日志。落地在 `scripts/render-png.sh` 的 `count_slides` 与 `scripts/build-deck.py` 的写后自检（两处同源）——都得能让这一条**红**。

## 为什么会有这个 skill（生成背景）

1. **出生背景**：库里那份四维风格系统的 slide-deck 效果不错（下载量最高），但它缺场景页序、演讲者视图、可编辑交付、交付前质检四块；库里另有五个 skill 各补一块——于是收敛成一个入口。改写与许可说明见 `ATTRIBUTION.md`，正文不再逐个点名来源。
2. **样本来源**：B 出口资产 9 主题——**9 件自建实体**（`century-sq` / `century-ave` / `guanglan-rd` / `friendship-bldg` / `qiu-r` / `panyu-rd` / `fuzhou-rd` / `longhua-si` / `wanhang-fy`），本库是唯一正本；**2026-11-23 起上游主题全数删除**（36 → 28 → 0）；要临时换气质，从 `references/palette-atlas.md` 的六组起手式抄 token，不落成文件；17 族版式（39 式）、三类场景页序、C 出口的外部引擎与三套硬纪律。取自与维护的边界见 `assets/themes/README.md`。
3. **未言明的偏好**：要的不是「再来一个模板库」，而是「一次 plan、按需长成三种文件」——所以收敛成一份 `pages/NN.md` 作正本，三个出口都从它派生。
4. **失败样本**：见下条。
5. **压缩损失**：上游的 WebGL 背景、37 份规则卷、FX 特效模块（`fx-runtime.js` 及其依赖的 `fx/`，2026-11-14 已连同空壳一并删除）、外部引擎的几何库都没并进来；要这些能力按下方分流表转走上游。

**失败样本**（v1.0.0，2026-11-10）：第一次自测，`render-png.sh` 把 5 页报成 6 页。缺的上下文是「内联后的 HTML 里，`runtime.js` 自己的注释也含 `<section class="slide">` 字样」——我照搬了上游的 grep 判据，没意识到 HTML 已被我们内联成单文件。重来会这么改：先剥 `<script>` 再数，并把页数与 `pages/` 份数对账后再继续。

| 拿到手的东西 | 文件形态 | 强在哪 | 做不到的（失效边界） | 什么时候选 |
|---|---|---|---|---|
| **影像件（A · 影像 deck）** | `NN-slide-*.png` → `.pptx` / `.pdf` | 视觉密度高、逐页可控、社媒好传播 | 文字不可编辑；改字要重出图 | 阅读型/分享型 deck，或没有模板约束的创意稿 |
| **网页件（B · 网页 deck）** | 单个 `.html`（双击可开，离线可用） | 键盘翻页、动效、S 键演讲者模式（当前/下一页 + 逐字稿 + 计时）、真字体 | 静态页，不能多人协同编辑；导 pptx 只是图片 | 要**讲**：分享、内训、发布会、demo day |
| **可改件（C · 可编辑 PPTX）** | 原生 `.pptx`（文本/形状/图片可改） | 甲方能自己改字、和 HTML 侧共用一套瓦作 token | `export-pptx.py` 覆盖 12 个页型（含 `figure` 一图一页、`figures` 多图一页；图与图组按 `--radius` 同值裁成圆角，圆角是图片形状本身，不是贴角遮罩）；渐变与布尔经 `wash_bridge.py` 换算成 `a:gradFill` / `a:custGeom`；页切换按瓦作 `.slide` 的时长出 `p:transition`（含 morph）；spec 里 `wash`/`shapes` 的 `fill`（渐变）与 `boolean`（两圆差/交）由 `wash_bridge.py` 在导出时求值；加 `--animate` 才写 `p:timing`——每页内容形状按阅读顺序切 ≤4 组，放映时一次回车淡入一组（`animate:false` 单页关、`animate_groups` 改组数）；导出时顺手删掉母版里残留的日期/页脚/页码占位 | 客户明确要改字，或要「HTML 与 PPT 同风格」 |

**册级导航条**（长册才知道讲到第几节）：首部写 `<!-- nav: 序 > 现状 > 判断 > 出册 -->`，每页写 `<!-- sec: 现状 -->`，B 侧生成 `.deck-nav`、C 侧按同数据画；`nav-block:` 出色块型（通栏底 + 当前节实块）。只放顶部、只此两式——⛔ 不放左侧（竖排要重排版心）、⛔ 不放底部（与页脚抢行）、⛔ 不做图标型（库里没有图标体系）。条高上限 44px，页面上内边距 72px，再高就压标题。
**十式与 md 指令**：图带压卡写 `<!-- layout: ride -->`（一图当带、首段压带内、列表项当白卡，字段用全角「｜」切：`标题｜副标｜段一｜段二`）；底线三段卡写 `<!-- layout: cols3 -->`（`标题｜段一｜段二`，可再加 `<!-- chips: A｜B｜C -->` 出标签行）；左文右图出血写 `<!-- layout: bleed -->`（两段正文 + 一张图，图推到页边）。C 出口没有这三种结构，分别降级成列表页/列表页/单图页，导出时逐页打印「降级」——⛔ 不是静默丢弃。

甘特写 `<!-- layout: gantt -->`＋一张表（`任务 | 模块 | 起 | 止 | 完成`，日期 `2026-07` 或 `2026-07-15` 都认）：月份刻度按最早与最晚自动算，跨年自动分带，条内实色段＝完成度，模块变更处加一道虚线；表后一段是底部结论带。C 侧降级为表格，日期与完成度留下，条与分带不保留。模块格写 `<!-- layout: modules -->`＋最多四张卡（`标题｜段一｜段二`），再配一张图，图独占末格、其余格装载文字；C 侧降级为列表页。

弧形分割写 `<!-- layout: arc -->`＋两段正文＋一张图：一条 S 弧当分界，图在右、通到页顶与页右，文在左。弧线是 `objectBoundingBox` 的 clipPath（0–1 坐标），换画布尺寸不跑形；⛔ 别用 `border-radius` 的椭圆角假造，它只能弯一次。C 侧出单图页。
弧线时间轴写 `<!-- layout: timeline-arc -->`＋至多六条 `日期｜标题｜说明`：曲线与圆点在 SVG 里按贝塞尔算，卡片跟着圆点的 y 交替上下，日期竖杆连回曲线。C 侧降级为列表页。
底部口号带写 `<!-- band: 一句话 -->`，可挂任意页：通栏一条压在页底，字距 .22em；挂带的页会自动隐藏页脚、把内容区收进 150px。
横条比例写 `<!-- layout: bars -->`＋至多七条 `标签｜数值`：标签独立成左列，圆角轨道只留色段，实色段按比例拉长，数值钉在右端，表后一段当注脚。⛔ 别把标签放进轨道——深字压在深色段上，短条的标签会跨在实色段与浅轨道两侧，对比度必有一侧不够（1.2.70 首版就是这个毛病）。
条身可换「皮肤」，只认七个 token，**基座默认声明、九瓦作逐个声明**，不写死在组件里：`--bar-track`（轨道底）、`--bar-rim` / `--bar-rim-bottom`（上下内亮边）、`--bar-well`（凹槽内影）、`--bar-fill`（条身渐变）、`--bar-fill-gloss`（条身高光层）、`--bar-fill-ring`（条身内圈与落影）。基座 `base.css` 有一组中性兜底（tint 轨道、纯 accent 条身），任何新瓦作不声明也不会崩；但 `check-theme-colors.py` 要求九个瓦作各自显式声明这七件（缺一记 `BAR` FAIL），兜底不算交付。数值列一律用 `--text-1`，⛔ 不用 `--accent`——世纪广场的标线黄压浅底只有 1.79:1，数字必须跟正文同色。广兰路已按 Aqua 口径声明：轨道是水槽玻璃、条身是果冻凝胶，高光走 `--aero-gloss` 同族但更薄，⛔ 别直接整条套 `--aero-gloss`（它按 18/21px 的硬水线取值，44px 的条上会糊成一片白）。数值带 `%` 直接当百分比，超过 100 的大数按最大值归一。这是「排名＋占比」的清单读法，⛔ 不与 charts 族的坐标轴图表混用。C 侧降级为两列表格。
团队卡写 `<!-- layout: team -->`＋二至四条 `姓名｜职务｜一句简介`，再按同序列图：人像切进有机形状（四组 `border-radius` 百分比拧出来，不用 SVG），形状在后方错位探出一角；无图时同形退成 accent 淡色块。⛔ 人像要用抠好的透明底 PNG 或纯色底，白底棚拍会在有机形里留一圈白。C 侧降级为列表页，人像与有机形不保留。
**实心块上的字只有一种写法**：品牌色（`--accent`/`--accent-2`/`--accent-3`/`--primary`）做底时，字色一律 `var(--accent-ink)`，逐主题按 WCAG 算过（白字压 accent-2 常见只有 2–3:1）。⛔ 不硬写 `#fff`、⛔ 不放 `--text-1/2/3`；浅色 tint（`color-mix(accent 10–26%, surface)`）才是深字的合法底。闸门 `check-theme-colors.py` 会逐块扫这条。

**质感三件**：`.soft-cast` 用光影替边框（⛔ 别再给形状叠描边）、`.glass-pane` 玻璃面（走 `--glass-bg`/`--glass-blur`，缺省退回中性 Aqua 参数，C 侧只能降成半透明填＋内高光）、`.bubble` 气泡（径向透明渐变＋错位叠两层）。三者是装饰件，⛔ 不覆盖九瓦作各自的玻璃语言。

**三个名字怎么用**：给用户说功能名（网页件 / 可改件 / 影像件），A/B/C 只留在命令、脚本与 `check-wash` 这类工具名里。
**常见错误**：把网页件当可改件发出去（对方改不了字）；以为两件像素全同（同一套瓦作、两个渲染器：圆角按同值裁形，裁切取景与动效仍有差）；拿影像件应急后又改内容（只能整页重出）。

**不适用**：飞书幻灯片（走 `ppt` skill）；纯数据看板/图表页（走 `lieflat-charts`）；PDF 打印适配（走 `print-safe`）；没有内容只要空模板（走 `assets/full-decks/` 自取）。

**不做什么（non-goals）**：不做像素级精修（那是设计软件）；不做多人协同编辑（B 出口是静态件）；不从零发明版式（只组合 `assets/layouts/` 的 17 族）；不接管「改已有 pptx / 填品牌模板 / 加动画」（那是外部引擎的路）；不替用户编数据（缺数字一律留占位并在摘要里列出来）。

## 与库里近邻 skill 的分流

本 skill 与库里几个同类 skill 能力重叠：`html-ppt-skill`、`ppt-master` 仍在库中——命中以下情况时**明确转走**，不要两边都跑。三个 `deck-*` 模板件已于 2026-11-10 移入 `_archive/20261110-模板副本并入html-anything/`（正本在 `html-anything/…/<同名>/TEMPLATE.md`），它们的页序层已并入 `references/archetypes.md` 的 `course` / `pitch`。

| 请求长什么样 | 去哪 | 为什么 |
|---|---|---|
| 要做一份 deck / PPT / slides（含"讲"和"发"） | **本 skill** | 有统一 plan + 三出口 + 质检门 |
| 只要"某套现成模板/主题的效果"、只想换皮 | `html-ppt-skill`（`assets/` 同源） | 纯模板检索，不需要 plan 流程 |
| 要观众屏同步 / 分段计时 / 讲稿 | **本 skill** | `assets/runtime.js` 原生提供（`S` 键），不需要外部引擎 |
| 要激光笔 / 排练记录（每页停留时长） | 没有 | 本 skill 不提供，也不建议为此引入外部依赖；直说没有 |
| 已有 `.pptx` 要美化 / 填模板 / 加动画或转视频 | `ppt-master` | 它管"改已有件"，本 skill 管"从内容出件" |
| 要飞书幻灯片（在线协作、URL 交付） | `ppt` | 交付渠道不同 |
| 要做**落地页／作品集／营销站**（不是 deck） | `design-taste-frontend` | 反 AI 腔的网页设计品味在那边，本 skill 只管 deck |
| 一次做完但要能改字 | 本 skill C 出口；只有当次 `attribution_guard.py` 非 0 才按 `path-c-editable.md` 降级并明说 | ⛔ 不许用 A 出口的位图 pptx 冒充可编辑件 |

## 腐化信号（什么时候该回源重读）

- B 出口的 `assets/` 更新（主题数、runtime 键盘映射变了）→ 重拷 `assets/`，跑一遍 `build-deck.py` + `render-png.sh` 自检（两个脚本的判据都是产物本身）。
- 底板（四维风格规格或 `base-prompt.md`）被上游更新 → 逐份 diff，只合入本 skill 没改造过的部分。
- 主题 CSS 改了、deck 也交付了 → 跑 `scripts/build-deck.py examples/decks/<deck>/index.html -o "<交付路径>" --force`，再跑 `scripts/check-deck-sync.py`（按 `data-sha256` 判，旧产物必红）。登记表在 `assets/decks.json`。
- 主题 CSS 改了却没重出材质图 → 跑 `scripts/export-theme-textures.py` 再跑 `scripts/check-theme-textures.py`（闸按 `source_sha256` 判，旧图必红）。
- 位图 tile 被重出过（换了源图、改了 `--band`/`--base`）→ 跑 `scripts/make-material-tile.py` 重出，再改 `registry.json` 的 `derived_sha256` 并重跑 `scripts/check-bitmap-assets.py`；⛔ 别只换图不改登记（B2 必红）。
- 改完主题 CSS 出现「闸全绿但页面没变化」→ 先 `check-bitmap-assets.py`（B11 查括号配平与「声明紧接选择器」接缝），再 `probe-texture-visibility.py`（量像素）。⛔ 少一个 `}` 会让整段位图规则被浏览器当无效声明丢弃，而选择器/blend/opacity 全都还在文件里。
- 同一材质在两个主题里各存一张图（哪怕只是重出一遍）→ 家族制里这算退化：一张 tile 只能一条登记，多处消费写 `used_by`（B9 会红）。
- 外部引擎版本号变了 → 先跑 `<ppt-master>/scripts/attribution_guard.py`，非 0 就停用 C 出口，不许跳过闸门。引擎版本以它自己 `SKILL.md` 的 frontmatter 为准（2026-11-10 补齐时是 6.7.2，2026-11-14 实测已是 6.9.0）；⛔ 别把本文里的版本号当当前值。
- 本 skill 自己的 `references/` 出现 >200 行、或改了内容却没更新顶部目录 → 当场拆。
- 某条 path 文档半年没被用过，而上游已补了同等能力 → 删掉它，改用指针。

## 用户输入与图片来源

- **提问**：优先用当前 runtime 的用户输入工具（`interaction.ask` / `AskUserQuestion` / `ask_user` 等）；没有就发编号纯文本。能批量就一次问完。
- **生图后端（A 出口）**：当前请求点名 > `EXTEND.md` 的 `preferred_image_backend` > 自动选（runtime 原生生图工具优先；只有一个外部后端就用它；多个就问一次）。
- **硬要求**：生图前每页 prompt 必须落成独立文件（`prompts/NN-slide-{slug}.md`），它是可复现记录，换后端不用重写提示词。

## 确认政策

默认**先确认再出件**。点名 skill、给了文件、匹配到 archetype、`EXTEND.md` 默认值——都只是**推荐输入**，不代表可以跳过确认。
本请求里明确说「直接生成 / 不用确认 / 按默认出」才可跳过；跳过后在**下一步**先声明假定的出口/风格/受众/页数/语言。

## 脚本

`{baseDir}` = 本 SKILL.md 所在目录。全部是 python3 / bash，**不需要 bun、不需要 npm**。

二十四支脚本按用途分五组（建件／出图／七道判据闸／维护闸／字体），**完整清单、依赖、退出码语义**只在
[`references/scripts-inventory.md`](references/scripts-inventory.md)（唯一清单；⛔ 别在这里抄第二份）。

两个可选后端（都**装了才用、没装就报降级**，不写进依赖）：`skia-pathops` 让曲线布尔沿曲线真裁（`curves: require` 时缺它就报错），
`uharfbuzz` 让 C 出口量宽改走整段 shaping（`--hb-measure`，默认关——它会改断行点）。能力表在 `wash_bridge.backend_report()`，出件 `--json` 里带。

**Markdown 入口**是 `scripts/md2deck.py`（`#` 成封面、`##` 切页，按正文自动配 cover/text/process/image-set/image-single/quote/code/split 族，`### 分节` 各自成页，默认给列表加 `data-build` 逐条揭示；`--inline` 直接出单文件，`--no-build` 关揭示；加 `--pptx 出件.pptx` 同一份 md 再出一件原生 PPTX，单图页会落成 `figure`（一图一页、不裁），图组与代码页在 C 出口没有等价页型，会逐条列出跳过）；逆流出口是 `scripts/pptx-to-html.py`（PPTX → 单文件 HTML，读形状不抓渲染）；正向仍是 B/C 两个出口。
逆流之后再回来改字，不重排：`scripts/retext-pptx.py` 在**原 pptx** 上只换文字节点（`--dump` 抽清单 → `--edits` 改 → `--verify`），
几何沿用原件、逐形状比指纹，改到版式就报错。C 出口做完必跑真渲染核验：`--render-check`（`view issues` 0.2 s → `validate` →
`--render-grid` 一次出整册缩略，约 5 s 管炸版；`--render-pages 1,3` 只重渲点名页，别逐页渲）。
三条合并类脚本（`build-deck.py` / `merge-to-pptx.py` / `merge-to-pdf.py`）都认 `--force` 与 `--json`；
判据是**产物本身**，⛔ 别靠退出码或 grep 日志判成败。
**新增或改完 B 主题，先取色、再体检，最后才谈好不好看**：

```bash
python3 scripts/pick-brand-colors.py --colors '#主色,#次色,#强调' --bg '#底'   # 先把手定的明度拉到等距档
python3 scripts/check-theme-colors.py assets/themes --md theme-colors.md      # 再验这组色过不过
```

- 取色器只管明度：色相是你定的品牌关系（谁深谁浅也照原顺序），⛔ 别让它顺手改色相——改色相是重新设计。
- 体检 ⚠️ 里「两强调色 ΔL*<10」「三线色挤在一起」「`--grad` 中段彩度掉 ≥25%」三类，**先回去跑取色器**再手调；眼睛判不出 ΔL*，手调只会又调出 0.7 级。

- ❌ 级（`--text-1` 压底 <4.5:1）**不许交付**，压深文字或换底，别改主色迁就。
- ⚠️ 级（主色对底 <3:1、两强调色 ΔL*<10、ΔH 落在 15–40°、主色与底同明度）可以先上，但**必须在该主题 css 头部注释里写明取舍**——否则下一个主题 fork 它时会把这处缺陷当默认继承下去。
- 带状态色（信息／警示／成功）的主题，ΔH 落 15–40° 常常无解（警示红橙与暖主色天生 20–40°）。此时**换轴登记**，别硬调色相：在 css 注释写 `/* amb-ok: accent-2/accent-3 | 面积 12% vs 2% + 图标冗余 + 永不同框 */`，依据须 ≥20 字且盖住面积／形状／位置三轴中至少两轴。登记后报告里单列「换轴放行」，⛔ 不静默消失；依据不合格仍按 ⚠️ 算，登记的对照不上任何暧昧对则报「失效豁免」——该删。
- 新增主题的接完判据：只改 `:root` 与组件，让体检数字不坏；数字变坏而说不清理由，就是没接完。

## 选项（口头或命令行都认）

| 选项 | 说明 |
|---|---|
| `--exit image|html|editable|image+html` | 出口形态；省略则按确认门 Q0 |
| `--style <key>` | 风格键（21 个之一）或 `custom` |
| `--audience <type>` | beginners / intermediate / experts / executives / general |
| `--lang <code>` | 输出语言（en / zh / ja …） |
| `--slides <N>` | 目标页数（archetype 区间内，8-25 常用，上限 30） |
| `--ref <files...>` | 参考图（A 出口：style / palette / direct） |
| `--outline-only` | 只到大纲就停 |
| `--pages-only` | 只到逐页记录就停（不渲染） |
| `--regenerate <N>` | 只重出指定页：`3` 或 `2,5,8` |
| `--allow-prose` | 成稿闸报红也照样出片（默认拒；用时摘要里留记录） |
| `--hb-measure` | C 出口量宽改走 uharfbuzz 整段 shaping（装了才有；会改断行结果，默认关） |
| `--animate` | C 出口逐组揭示：写 `p:timing`，每页 ≤4 组，`--animate-ms` 改淡入时长（默认 400ms） |
| `--from-pptx <file>` | **逆流**：手上已有 pptx，先转成网页 deck（`scripts/pptx-to-html.py`），再按需改内容 |
| 往返改字（不成选项） | 用 `scripts/retext-pptx.py` 单独走：`--dump` 抽清单 → 按 `id`/`name` 填 `edits.json` → `--edits` 回写原 pptx → `--verify` |

## 工作流（清单在眼前，判据在卷里）

复制这份清单，逐项打勾；每步的出口条件与细节**只在** `references/workflow.md`：

```
- [ ] Step 0: 读配置（EXTEND.md）
- [ ] Step 1: 分析内容（类型 / 受众 / 语言 / 页数 / archetype / slug）
- [ ] Step 2: 确认门 ⚠️ 必须（出口 + 风格 + 受众 + 页数 + 两个评审开关）
- [ ] Step 3: 出大纲 outline.md（含 STYLE_INSTRUCTIONS）
- [ ] Step 4: 评审大纲（条件）
- [ ] Step 5: 出逐页记录 pages/NN.md（A 出口再派生 prompts/）
- [ ] Step 5.5: 成稿闸 check-prose.py（红一条不出片）
- [ ] Step 6: 评审逐页记录（条件）
- [ ] Step 7: 渲染（按出口走 A / B / C 的 path 文档）
- [ ] Step 8: 质检门（13 条，逐页过，每条要留证据）
- [ ] Step 9: 交付摘要（把没验到的写出来）
```

四句路由判据：**Step 2 没闭合不进 Step 3**；`pages/NN.md` 是唯一正本；页序按 `NN-` 数字不按 mtime；Step 8 每条都要证据，没有证据只许写「证据不足」。

## 什么算做完

三种答法写在 `references/qa-checklist.md` 开头：**能交**（13 条全过且各有据）／**不能交**（哪页哪条、重做还是降级）／**没验到**（哪几条、怎么验）。
一句判据：截图看过只算目检（抓溢出、错字），页数三方对齐、单文件无残留链接、文本真能双击改，这类**结构事实**才算过。结论带范围——B 过 ≠ A/C 过，本机过 ≠ 换环境也过。

**C 出口的「可编辑」只认形状层**：交付前跑 `scripts/verify-pptx-editable.py <出件>`，exit 0 才算。A 出口的合图件在这里必红（每页 1 张 picture、0 文本），⛔ 它的文件名和页数都是对的，别靠「能打开」判。

**文档里的旧读数不是当前状态**：引擎闸门、脚本成功日志、上一轮的 exit code 都属于**当次可复跑**的东西，判据必须现场重跑一次（2026-11-10 就因为信了文档里一句「闸门返回 78」，把可编辑请求降级成了位图件）。

## 风格系统

21 个风格键跨出口通用；A 出去读 `styles-<key>.md`，B 出去用 `assets/themes/<theme>.css`。选法三句：按内容类型选键（架构→`blueprint`、融资→`corporate`、发布→`bold-editorial`、数据→`swiss-grid`）；B 出口没有手绘/粉笔皮，遇 `sketch-notes` / `hand-drawn-edu` / `chalkboard` 要么换 `soft-pastel`/`academic-paper` 并明说降级，要么整份转 A；选 `custom` 时四维组合，B 出口只有 texture/density 能精确落地，mood/typography 只算近似，**别假装四维都落地**。

完整映射、四维取值、降级规则、加新风格的 checklist 见 `references/styles-unified.md`。

**B 出口主题 fork 样例**：`assets/themes/century-sq.css`（世纪广场 Century Sq，亮色版，2026-11-19 由 `guanglan-rd.css` fork）——保留全部 token 名 / 组件选择器 / 六档字号，只换材质与色板；视觉规范为柯布西耶模度 + 清水混凝土/大理石/拉丝钢/磨砂玻璃 + 交通标线黄（`--primary`，2026-11-20 由 `#F6CB07` 压暗到 `#DAB406`）与 2/4/6 号线次色。⛔ 正文不复述色值——真值只在 `assets/themes/century-sq.css` 的 `:root`，这里写死一个 hex 就是第三份副本。其暗色姐妹版 `assets/themes/century-ave.css`（世纪大道 Century Ave，同日由亮色版 fork）保留同一套结构，只把天光/混凝土换成高压钠灯暖光 + 米白/绿/蓝/玫红/黄酚醛树脂，约 3000K 暖调、⛔ 无赛博朋克。两者共用 `assets/fonts.css` 的内化字体语义 token（标题/按钮智造黑、正文思源宋体），主题里只映射不重复声明。加 B 主题不算加风格键，⛔ 不要为此动「21 个风格键」表。

**暗色 fork 不得整体降字重（2026-11-22）**：暗色版只换色与材质，字重按角色保持与亮色版一致——标题、正文、说明各自一条档位，⛔ 一句「切深色字重统一下调」把正文一起改瘦（实测 `century-ave` 与 `century-sq` 字重分布一致：700 共 10/9 处、500 各 2 处、600 各 1 处，新 fork 照此守）。要压暗色标题的「厚」，先看是不是色温与底色的对比错觉，再单动标题那一类；⛔ 靠整体减档换「轻盈」。

**满版模板吃主题（2026-11-23 改写后）**：`assets/full-decks/` 五套只剩 `index.html`（各带一份本库风格 README），按 `base.css` → `layouts.css` → `theme-link` 三行接线，没有私有 `style.css`、也没有模板调色块——配色只有主题一个来源。换主题＝改 `theme-link` 的 href 与 `assets/decks.json` 的 `theme`，改源后 `built` 件必须重打包，否则 `scripts/check-deck-sync.py` 报"源比产物新"。考古判据：自定义属性按「元素自身声明 > 继承」解析，层序不参与，所以旧模板把调色块挂在 `.tpl-*` 上必然压过主题（实测封面色不变）；做法与负例见 [theme-full-decks.md](references/theme-full-decks.md)。

**瓦作 → A/C 的桥（2026-11-21）**：主题原先只服务 B 出口——A 出口是逐页生图、C 出口交外部引擎，两侧都不读 CSS。`scripts/export-theme-textures.py` 把主题里的材质类与内联 SVG 纹理渲染成 PNG（9 主题 / 74 张，落在 `assets/textures/<theme>/`），A 用 `board.png` 当 style 参考图、C 用 `mat-*.png`/`tex-*.png` 当局部底纹；⛔ PNG 是派生件，色值真源仍在 `:root`，主题一改必须重出。完整用法与验收见 [theme-to-export.md](references/theme-to-export.md)。

**位图材质：CSS 补不出的那一层（2026-11-22，v2 家族制）**：瓦作出图截出的只是 CSS 能画出的东西——大理石的层理与巨脉、颗粒、纸纤维，`radial-gradient` 画到极限也只是「白底 + 两道极淡斜光」。真位图只补这一层，且**按材质家族分件**：一条登记 = 一张图，多处消费走 `used_by`，⛔ 不按主题复制。两个角色：
① **细层理 / 颗粒 / 纸纤维 / 石灰华**——灰度**无缝 tile**，`repeat` + `background-size` 取固有尺寸（换整数倍＝换粒径，同一张 `grain` 在 512/384/256 三种粒径服务水磨石/碑石/香灰）；② **大脉络（hero）**——`no-repeat` + `cover` + `background-position` 换裁切（一张 1024 脉络图让三块面看似三种石料）。颜色仍取 `:root`，位图只给灰阶疏密。七条登记 ≈1.5 MB 覆盖 8 主题 11 处消费（按主题各出一套要 ≈4.4 MB）。做法、容量账、踩坑见 [theme-bitmap.md](references/theme-bitmap.md)；A/B 样 `examples/marble-bitmap-ab.html`。⛔ 不该换位图的材质：磨砂玻璃、拉丝钢、几何标线、印章边框。

**反 AI 腔禁型（deck 适用版）**见 [taste-deck.md](references/taste-deck.md)：16 条照用、7 条换说法、6 条不适用（附理由），并裁定 density 只用本 skill 四维。

## 场景 archetype

8 类页序（`course` / `pitch` / `tech-talk` / `weekly` / `launch` / `research` / `explainer` / `review`）决定"第几页该说什么"，**只定页序与页型，不定视觉**；必须页型、页数区间、默认风格、常见坑见 `references/archetypes.md`。

## 逐页改版

先改 `pages/NN.md`，再按出口同步产物；`NN` 会变、`slug` 不变。改/加/删/换风格的完整分支见 `references/modification-guide.md`。

## 执行纪律

1. **先备份再改长文件**：动任何 >200 行的既有文件前 `cp x x.bak-$(date +%Y%m%d-%H%M%S)`；用行列表操作而不是字符串偏移；改完核对标题数/frontmatter 闭合。
2. **门就是门**：Step 2 未闭合不进 Step 3；每个确认门等到用户明说再往下。
3. **不在门内打包多阶段**：一个门没关，不提前准备下一阶段的产物。
4. **在哪层坏就在哪层修**：单页问题改单页；大纲问题回大纲；工具问题修工具——不许靠降级要求蒙混。
5. **页序按 `NN-` 数字**，不按 mtime/文件名排序；merge 前先核对页数与大纲一致。
6. **不虚构数据**：没有的数字留占位标记并在交付摘要里列出来，不许编；没有实测的数字**给方法不给数**。
7. **降级要明说**：B 出口做不出手绘皮、C 出口缺外部引擎、A 出口后端不可用——都要在正文里说清楚，不许静默换方案。
8. **体量谁改超谁重构，同一轮内下沉**：本文件逼近软限就当场把细节推去新卷，⛔ 不留待办。

## 文件布局

```
slide-deck/{slug}/
├── source-{slug}.{ext}          原始内容
├── analysis.md                  分析结论（含最终确认）
├── outline.md                   大纲 + STYLE_INSTRUCTIONS（风格唯一真源）
├── pages/NN-{slug}.md           逐页记录（唯一正本）
├── prompts/NN-slide-{slug}.md   A 出口生图提示词（由 pages 派生）
├── index.html                   B 出口源（引用 ../assets/*）
├── {slug}-single.html           B 出口交付（单文件）
├── NN-slide-{slug}.png          A 出口逐页图
├── qa/*.png                     逐页截图（质检用）
├── notes.json                   可选：{文件名: 讲稿}
└── {slug}.pptx / {slug}.pdf     A 出口合并件
```

**slug**：2-4 个 kebab-case 词，从主题提取（"Introduction to Machine Learning" → `intro-machine-learning`）。

**回滚基线**：要写的文件已存在 → 先复制为**同目录**的 `<name>.bak-YYYYMMDD-HHMMSS.<ext>`（持久留在产物目录，不落临时目录），再写新件；脚本层由 `--force` 触发同一动作。

## 成稿闸（Prose Gate）

用户给的常是一段口语；本库不生成文字，但要一个不签字的判官。九条判据（套话/标题空转/首句复述/单条超长/
数字无出处/术语无注/一页多主张/太空或太糊/问叹滥用）见 `references/prose-gate.md`：

```bash
python3 scripts/check-prose.py pages/                 # 直接吃正本（目录或单个 NN-*.md）
python3 scripts/check-prose.py pages/ --strict        # 警告也当红
python3 scripts/check-prose.py deck.json              # 也认 spec.json（派生件）
python3 scripts/check-prose.py pages/ --emit-spec deck.json   # 派生 spec 给 export-pptx
```

**闸门吃正本，不要求手抄 spec**：`pages/NN-{slug}.md` 是唯一正本，`spec.json` 由 `--emit-spec`
机器生成（字段别名 `points→items`、`refs→source` 见 `references/page-record.md`）。⛔ 手写 spec ＝ 第二份正本。

`export-pptx.py` 出件前自动跑同一份闸，红即拒（`--allow-prose` 才放行）。⛔ 别把它放进渲染后——文字不对，
渲得再准也没用。

**先判型，再写**：五型配方（汇报/提案/讲解/复盘/发布）在 `scripts/pick-recipe.py`，由触发词＋结构信号判（中/英/日都认，中文命中计 2、外文计 1），
两型都对就分段写、不混段。判据管「够不够密」，配方管「像不像这一型」：

```bash
python3 scripts/pick-recipe.py --detect 草稿.md     # 判型（也可直接喂 spec）
python3 scripts/pick-recipe.py --show briefing      # 出该型提示词，写时就把闸满足掉
python3 scripts/check-prose.py deck.json --suggest   # 闸后顺手判型（pages/ 也认）
```

细则见 `references/prose-recipes.md`。⛔ 配方不替代闸：写完仍要过九条。

## 体量预算（Budget Gate）

| 对象 | 软限 | 硬限 | 超了怎么办 |
|---|---|---|---|
| `SKILL.md` | 400 行 | 500 行 | 流程细节下沉到 reference，主文件只留判据与路由 |
| `references/*.md` | 100 行 | 200 行 | >100 行顶部必须有目录；>200 行必须拆成两份 |
| 单份 reference 字节 | 60KB | — | 只定点读（grep / sed 行段），不整读 |

改完跑这三条（前两条是库里的现成尺，第三条是本 skill 自己的文档对账闸——那两支都不读「43 个主题」这句话是不是真的）：

```bash
python3 <judgement-skill>/scripts/check_limits.py <本目录>   # 体量：谁超了
python3 <judgement-skill>/scripts/vaccinate.py <本目录>      # 结构免疫 14 支
python3 scripts/check_doc_claims.py                                    # 文档断言对账，exit 0 才算过
```

`<judgement-skill>` ＝ 本机另行安装的体量与判据体检件，⛔ 不在本仓内；没装则跳过前两条，第三条始终可跑。

第三条查七类：数字与磁盘事实不符、**断言锚点消失**（文档被改写＝失去覆盖，同样算不过）、本地引用悬空（全目录扫，含 `assets/` 里的 md/html）、html 破图破链、字段名过期与幽灵路径、把历史读数当当前状态、SKILL.md 清单与 `references/` 目录双向不齐。**它必须能红**：13 支注入反例 + 1 支正例基线的实测见 `SELFTEST.md` 第 16 节。

较真的理由：模型打开长文件时的实际行为近似 `head 100`，第 100 行之后的规则等于不存在。

## 还没验的

只在一处登记：`SELFTEST.md` 第 10 节（2026-11-10 起为**空表**，原五条已验完并删；新发现的没验项写进去，验过即删）。⛔ 别留「大概能用」。

## References

全部 59 份，文件名即 `references/` 下的路径，按用途分组：

- **流程**：`references/workflow.md` / `references/prose-gate.md`（成稿闸九条）/ `references/prose-recipes.md`（五型配方）/ `references/analysis-framework.md` / `references/archetypes.md` / `references/confirmation.md` / `references/confirmation-more.md` / `references/outline-template.md` / `references/outline-slide-templates.md` / `references/page-record.md`
- **出口**：`references/path-a-image.md` / `references/path-b-html.md` / `references/path-c-editable.md` / `references/effects-lens.md`（可选：玻璃透镜位移场）
- **风格与四维**：`references/styles-unified.md` / `references/styles-blueprint.md` / `references/styles-corporate.md` / `references/styles-minimal.md` / `references/styles-notion.md` / `references/styles-bold-editorial.md` / `references/styles-editorial-infographic.md` / `references/styles-intuition-machine.md` / `references/styles-scientific.md` / `references/styles-dark-atmospheric.md` / `references/styles-pixel-art.md` / `references/styles-vintage.md` / `references/styles-watercolor.md` / `references/styles-sketch-notes.md` / `references/styles-hand-drawn-edu.md` / `references/styles-chalkboard.md` / `references/styles-vector-illustration.md` / `references/styles-fantasy-animation.md` / `references/styles-curio-cabinet.md` / `references/dimensions-texture.md` / `references/dimensions-mood.md` / `references/dimensions-typography.md` / `references/dimensions-density.md` / `references/dimensions-presets.md`
- **设计与文案**：`references/design-guidelines.md` / `references/design-visual.md` / `references/layouts.md` / `references/style-audit.md`（外面真件的字号与几何实测）/ `references/chart-grammar.md`（数据形状→图型判据） / `references/palette-atlas.md`（备选配色起手式） / `references/content-rules.md` / `references/base-prompt.md`
- **交付与维护**：`references/taste-deck.md` / `references/qa-checklist.md` / `references/presenter.md` / `references/modification-guide.md` / `references/preferences-schema.md` / `references/theme-preview.md` / `references/palette-check.md` / `references/theme-to-export.md` / `references/theme-bitmap.md` / `references/theme-bitmap-mask.md` / `references/theme-marble-veins.md` / `references/theme-full-decks.md` / `references/scripts-inventory.md`

常用几份的用途：

| 文件 | 内容 |
|---|---|
| `references/workflow.md` | Step 0–9 的判据正文与摘要模板 |
| `references/analysis-framework.md` | 内容分析框架 + archetype/出口判定 |
| `references/archetypes.md` | 8 类场景页序、必备页型、默认风格、常见坑 |
| `references/styles-unified.md` | 21 风格 × 三出口映射 + 降级规则 + 加新风格 checklist |
| `references/page-record.md` | `pages/NN.md` 字段规范（三出口共用） |
| `references/path-b-html.md` | 主题/版式路由、单文件打包、演讲者模式 |
| `references/path-c-editable.md` | 交外部引擎、回读核验、引擎门与降级 |
| `references/taste-deck.md` | deck 适用版反 AI 腔禁型（16 照用／7 换说法／6 不适用） |
| `references/qa-checklist.md` | 交付前 13 条（通用 11 + 出口 2） |
| `references/theme-bitmap-mask.md` | 第三角色掩膜的规格：一图两用（金脉 `::after` / 白脉 `::before` 转 180°）、`file://` 必内联 |
| `references/theme-marble-veins.md` | 脉的排列组合：`--alt` 四旋钮（裁切/旋转/缩放/对比）、三主题配对表、两条做不通的路 |

## 偏好文件

`EXTEND.md` 放在 Step 0 第一个命中的路径（`.来雪亭Lesciotia/`，详情见 `references/workflow.md`）。常用一行改法：

- `default_exit: image`（默认 A；可改 `html` / `editable`）
- `style: blueprint`、`audience: experts`、`language: zh`
- `preferred_image_backend: auto`（默认：runtime 原生优先，只有一个外部后端就用它，多个才问）
- `preferred_image_backend: ask`（每次出图前都确认后端）

## 自检（离线）

```bash
python3 scripts/selftest.py          # 期望打印 PASS、退出码 0
```

冒烟级：编译全部脚本 ＋ 入口 `--help` 能起来；⛔ 不联网、不读凭据。
另含七道**判据级**闸（直接读产物/字体文件对账，不是「脚本能起来」）：`check-preview-sync.py`（预览页漂移）、`check-fonts.py`（字体子集与 token）、`check-theme-textures.py`（材质图与主题源对账）、`check-bitmap-assets.py`（位图登记与磁盘/主题对账，B1–B11）、`probe-texture-visibility.py`（位图是否真的可见）、`check-deck-sync.py`（交付 deck 与主题是否同步）、`check-wash.py`（瓦作翻译闸：spec 里翻不动的染层报红）、符号链接检查。只有 `check-theme-textures`（3 条）与 `check-bitmap-assets`（5 条）在自检里带**负例**（改 sha／删图／撤 manifest／删派生件／塞未登记源图／同图重复登记／CSS 少一个右括号必须红），其余各闸的负例见 `SELFTEST.md`；⛔ 别把「自检 PASS」当「七道都验过」。
