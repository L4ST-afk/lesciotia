# 来源与许可

本 skill 的正文与规格为**内部改写**——按自己的流程需要重写、重组，**出处不逐条登记**；只有带明确许可的第三方**资产**才逐个登记在下面。

## 复制进来的资产（逐个登记）

| 来源 | 版本 | 许可 | 复制了什么 |
|---|---|---|---|
| ~~html-ppt~~（github.com/lewislulu/html-ppt-skill，© 2026 lewis） | 库内快照 2026-09/10 | MIT | **2026-11-23 起 0 件**：`runtime.js` / `base.css` / `fonts.css` / `animations/animations.css` / `render-png.sh` 逐件自写重写；`themes/upstream/`（36→0）；`layouts/` 并成 17 族 / 38 式并逐页重写；`full-decks/` 5 套连各自 `style.css` 一并改写为自有内容（2026-11-23 实测与上游示例 `quick_ratio`≈0.99，故不能只改字体与品牌字样）。⛔ 表中已无任何一件上游资产，`LICENSE-html-ppt.txt` 随之删除；历史比对见 `SELFTEST.md` 第 17 节（留档，不再对应当前文件） |
| **Chart.js** 4.4.3（github.com/chartjs/Chart.js） | 2026-11-23 从 jsDelivr 取回 | **MIT** | `assets/vendor/chart.umd.min.js`（205,637 B）：`layouts/charts` 一族画柱/线/饼/雷达用；此前指 CDN，离线打开是空白 |

## 同类项目勘察（无复制件）

1.2.45 为确认「这些机制在生态里是否已公开」把同赛道项目过了一遍。下表列的是**比对过什么**，
不是归属声明：**一件文件、一行代码、一个滤镜节点都没有复制**；表格之外的许可原文也不必随包分发。

| 项目 | 比对的东西 |
|---|---|
| reveal.js | 嵌套页、演讲者视图、PDF 导出、Auto-Animate 的接口形状 |
| impress.js | 3D 变换翻页的坐标模型 |
| Slidev / Marp | Markdown 出稿与「一份源、多出口」的切分 |
| WebSlides / remark / bespoke.js | 单文件 HTML 分页、插件式翻页、键盘约定 |
| Spectacle | React 页序与过渡的组合 |
| nikdelvin/liquid-glass · clean99/liquid-glass | CSS + SVG `feDisplacementMap` 的折射与色散拆解 |
| archisvaze/liquid-glass | IOR 可调折射，SVG 与 WebGL 双引擎对照 |
| naughtyduk/liquidGL · dashersw/liquid-glass-js | 离屏采样（读不到实时像素时的替代路径）、多层边缘折射 |
| Rethink-JS/rt-liquid-glass | 属性驱动配置 + 不支持的浏览器降级 |
| mmoollee101-lab/HTMLtoPPTX · acaprino/html2pptx | DOM 测量 → 原生文本/形状；行锁与坐标换算 |
| nlj626/html-to-pptx · Design-Arena/html-to-pptx | 截图式导出与测量式导出的取舍 |

判据：这些项目许可各异（多为 MIT，个别为自定义条款），本库**不随包分发它们的任何文件**，故不逐件
登记许可原文；要复核本库实现，直接读 `layouts.css`、`runtime.js`、`assets/effects/lens.js` 与
`references/effects-lens.md`（公式、参数、两条实测都在），不依赖任何外部项目存在。

**1.2.42 起不再声明上游**——判据是「有没有复制资产」，不是「读过没读过」：

- 代码件全部自写（`runtime.js` / `base.css` / `fonts.css` / `animations/animations.css` / `render-png.sh`），
  文件头也不再挂任何上游标记。
- 主题层：`themes/`（9 个）全部自建实体，`themes/upstream/`（36 → 0）；备选配色见 `references/palette-atlas.md`，token 自写。
  现存自有主题 `themes/`（9 个），全部本库自写，无一件上游派生。
- `full-decks/` 5 套在 1.2.42 重写：内容、结构、文案均为本库自有，各自那份 `style.css` 一并删除，
  整册只吃 `base.css` + 主题 —— 这才是「换皮不换骨」该有的接线。
- 因此 `LICENSE-html-ppt.txt` 已删除：没有复制件，就没有要随包分发的许可原文。
  ⛔ 别把它从 git 历史里捡回来——捡回来就等于声明「仍有上游件」，与实际不符。

⚠️ 2026-11-20 中西文排版改动（**上游主题不再是逐字节原样**）：上游这套是英文 PPT 的排版
假设，中文语境下有三处不友好，已在本库就地改掉并逐项登记：

1. **负字距归零**：各主题的 `--letter-tight` 全部由负值改为 `0`（原值 −.01～−.04em，
   逐个留在行内注释里）。中文没有字距收紧的排版传统，负字距会挤掉字怀、让标点贴字。
2. **字体栈插思源黑体**：38 处 `--font-sans` / `--font-display` 在 `'Noto Sans SC'` 前插入
   `'Source Han Sans SC','思源黑体'`。原因是本机有款「（字由心雨）筑紫柔黑」把内部 family
   名伪装成 `Noto Sans SC`，会静默顶替掉 ATTRIBUTION 声明的思源黑体。拉丁字体仍排在最前，
   英文渲染不受影响。
3. **`base.css` 补中文排版默认值**：`--letter-tight` / `--letter-normal` 归零，
   加 `text-autospace:normal`（中西文四分空）、`line-break:strict`、`overflow-wrap:break-word`。

判据已进 `scripts/check_doc_claims.py` 的「中西文」闸（T07 / FONT / AUTO 三条），造错验证过会红。
上游主题已全部删除，主题层不再有反向依赖；备选配色见 `references/palette-atlas.md`（自写 token，非抄本）。

⚠️ 2026-11-20 修正：`themes/upstream/` 原先是**符号链接**指向 `../../../html-ppt-skill/assets/themes`
（即「指针取用」）。实测单独打包后链接即断，36 个版式全部取不到主题，`build-deck.py` 报
`✗ 仍残留 1 个本地 <link>` 直接失败——本机跑得通、一打包就废。已改为实体目录（28 个 css，
35.2 KB）。判据：`find . -type l` 必须为空；有符号链接就等于「只在你这台机器上能用」。

ℹ️ 该件曾于 2026-11-20 补入、2026-11-23 随整册重写删除。判定依据写在上面：「有没有复制件」变了，声明就该跟着变，不是永远挂着更保险。

## 字体：随包 vs 自备

**本库原则上不随包分发第三方字体文件，例外只给「承担品牌字」的四族西文与一款标题体。** 下表 8 款字体里，只有 **万航渡喜脉体** 随包提供
（它是本库自己派生的，按 SIL OFL 1.1 允许再分发）；其余 7 款需用户自行下载，放进
`assets/fonts/<目录>/` 后生效。完整清单、获取方式、子集化步骤见
**`assets/fonts/FONTS.md`**。

**为什么**：字体是**文件**，不是风格。风格（地名、材质、色板）谁都可以用，但把 woff2
放进公开仓库属于**再分发**，需要授权明确允许。下表 7 款里只有 3 款带 OFL 原文（允许
再分发），2 款只有「免费商用」的使用授权（≠ 允许再分发），2 款连随包许可文本都没有。
统一改成「自备」后，不打包就不构成再分发，授权问题消失。

**缺字体会怎样**：不报错、不崩。每款字体的回退链都写全在主题 CSS 的 `--ff-title` /
`--ff-body` 里，缺字时静默落到链上第一个可用的系统字体。版式、色板、间距全部不变，
只是标题从手写体/楷书变成系统宋体或黑体。`scripts/check-fonts.py` 的 F1 判据会检查：
文件**要么存在且含汉字，要么在 `FONTS.md` 里登记为自备**——两者都不是才报错。

## 内化字体

| 字体 | 许可 | 内化范围 | 许可原文 |
|---|---|---|---|
| **素材集市智造黑 1.02**（`assets/fonts/素材集市智造黑1.02.ttf`） | SIL OFL 1.1 | 全字库，单字重 | `assets/fonts/OFL-素材集市智造黑1.02.txt` |
| **芝士奶盖乌龙宋 0.103 · Lite Bold**（`assets/fonts/cheesefoam/CheeseFoamOolongSong-Subset-Bold.woff2`） | SIL OFL 1.1 | **GB2312 子集**（6911 字＋ASCII＋常用标点），woff2 2.6 MB；子集外的繁体/生僻字回落华文中宋、系统宋体 | `assets/fonts/cheesefoam/OFL.txt` |
| **爱点风雅黑 1.00**（⛔ **不随包**，子集已于 2026-11-21 从仓库删除） | **商用免费**，广州爱点视觉文化有限公司（ideavi.cn）；使用须知原文「个人及企业可永久免费使用」。zfont.cn（font_657）2026-11-21 实测：许可协议栏为 `无标准协议 (作者文字声明)`，许可范围**商标/嵌入/衍生三项禁止**，文稿/互联网/视频/印刷允许；字体 `nameID 13/14` 无许可声明，`nameID 0` 写「All Rights Reserved」 | ⛔ **零内化**。`panyu-rd` 只走 `local()`，装了就用自己的爱点风雅黑，没装则标题回落宋骨黑体（OFL 1.1，随包） | 随包 `assets/fonts/aidian/使用须知.txt`（仅声明，无字体文件） |
| **摇醒青年黑 1.0 Regular**（⛔ **不随包**，子集已于 2026-11-21 从仓库删除） | **永久免费商用**，贝塞尔教育科技（重庆）有限公司 / 摇醒实验室；声明原文「摇醒青年黑将永久免费授权所有人免费商用」。zfont.cn 2026-11-21 实测：许可范围**嵌入、衍生两项禁止**（商标/文稿/互联网/视频/印刷允许），推荐指数 43 A 级 | ⛔ **零内化**。`friendship-bldg` 只走 `local()`，装了就用自己的摇醒，没装则标题回落宋骨黑体 | 随包 `assets/fonts/yaoxing/免费商用声明.pdf`（仅声明，无字体文件） |
| **南西油墨宋 1.000**（`assets/fonts/nanxi/NanxiYoumosong-Subset.woff2`） | **SIL OFL 1.1**，松陵南西（nanxiiii.taobao.com）。zfont.cn 2026-11-21 实测：许可协议栏标 `SIL开源字体许可 (OFL)`，许可范围七项**全为允许**（商标/嵌入/文稿/互联网/视频/印刷/**衍生**），推荐指数 50 S 级，无 AI 生成警告。⚠️ 但作者公众号原文**通篇未提 OFL**（只写「免费商用」），OFL 是 zfont 的判定而非作者声明；字体 `name` 表 `nameID 13/14` 仍为空 | **GB2312 一级字子集**（3755 汉字＋ASCII＋常用标点），woff2 5.03 MB | ⚠️ **无随包许可原文**，见下方说明 |
| **万航渡喜脉体 Bold**（`assets/fonts/ximai/WanhangXimaiBold-Subset.woff2`） | 原字 SIL OFL 1.1（字体 `name` 表内附全文），字制区 喜脉喜欢体 FontQu Smile v1.0，© 探火（深圳）品牌策划有限公司；派生件同 OFL 1.1 | **派生件**：原字（upem 2048 / 7787 字形）裁 GB2312 一级字（3997 字形），再沿轮廓机械加粗 +100/2048 em（每边约 2.4%），按 OFL 保留字名条款改名 `Wanhang Ximai`，woff2 2180 KB | `assets/fonts/ximai/OFL.txt`（派生件许可，含原始版权行） |
| **爨八体 1.000**（`assets/fonts/cuanba/CuanBaTi-Subset.woff2`） | **作者声明授权**（非 OFL、非 CC），© 张济海（中国大陆），张济海授权猫啃网发布。猫啃网 2026-11-21 实测原文：「企业与个人均可免费商用，无需取得授权文件」；⛔ **「这款字体不允许修改，任何人不得修改或制作衍生版本」**；⛔ 禁止将字库本身作为商品出售。字体 `nameID 0/13/14` 原为空，子集已补写版权与许可声明 | **GB2312 一级字子集**（3757 汉字，含主题专用字），woff2 3.4 MB。⚠️ **只有汉字**：ASCII 95 个字符、全角标点 27 个全部不在 `cmap` 内，标点数字由回退链上的霞鹜文楷接住 | `assets/fonts/cuanba/授权依据.md`（含猫啃网原文摘录与合规边界） |
| **宋骨黑体 1.310 Medium**（`assets/fonts/songgu/SongguHei-Subset.woff2`） | SIL OFL 1.1，奇文云海设计顾问（chivaltype.com） | **GB2312 一级字子集**（3755 汉字＋ASCII＋常用标点），woff2 542 KB | `assets/fonts/songgu/OFL.txt` |
| **霞鹜文楷 Regular**（`assets/fonts/lxgw/LXGWWenKai-Subset.woff2`） | SIL OFL 1.1，© 2021-2026 LXGW（github.com/lxgw/LxgwWenKai），Reserved Font Name `LXGW WenKai`；字体 `nameID 13` 内附 OFL 全文、`nameID 14` 指向 openfontlicense.org | **GB2312 一级字子集**（3755 汉字＋ASCII 可打印区＋全角标点 27 个，共 3877 码位），woff2 848 KB；未改字形轮廓，仅子集化 | `assets/fonts/lxgw/OFL.txt`（含版权行与子集说明） |
| **Playfair Display / Inter / Space Grotesk / JetBrains Mono**（`assets/fonts/latin/*.ttf`，各 Regular + Bold） | 均 SIL OFL 1.1。Playfair Display © The Playfair Display Project Authors；Inter © The Inter Project Authors；Space Grotesk © 2020 The Space Grotesk Project Authors；JetBrains Mono © 2020 The JetBrains Mono Project Authors | **Latin 子集**，woff2→ttf 解包后未改字形；四族共 8 个面（RIBBI）。⚠ Space Grotesk 400 实例内部族名被上游写作「Space Grotesk Light」，PPT 侧按内部名匹配 | `assets/fonts/latin/OFL.txt`（四族合并） |

**万航渡喜脉体（2026-11-21 派生并内化）**：只被 `assets/themes/wanhang-fy.css` 引用（标题、引语）。这是本库第一款**自己加工过**的字体：
原字是坚果云 `字体/字制区喜脉喜欢体1.00/字制区喜脉喜欢体.ttf`（9,487,176 B，upem 2048，7787 字形，`FontQu Smile` v1.0，
`nameID 13` 内附 SIL OFL 1.1 全文，`nameID 0` 记 © 探火（深圳）品牌策划有限公司，原字带 DSIG 数字签名）。
先 `pyftsubset` 裁 GB2312 一级字，再用 `skia-pathops` 把每个字形的外轮廓等宽外扩 100/2048 em（每边约 2.4%，`stroke` round join 后与原形并集，
不是横向放大的「伪粗」），最后改 name 表为 `Wanhang Ximai / 万航渡喜脉体`。OFL 的保留字名条款要求修改版改名，故原名不再出现于字体族名，
只在版权行与 `nameID 13` 里留出处；原字 DSIG 在改字后失效，派生件里已删除。
`usWeightClass` 记 700、`@font-face` 声明 `700 900`：标题写 800 也只取这一档，不合成假粗。
⚠️ 2026-11-21 首版误用了另一款「字制区喜脉体」（马克笔粗写，`~/Library/Fonts (Removed)/…`），已按用户指正全部重做；
原字许可文本以 `nameID 13` 的 OFL 全文为准，随包仍建议附 `OFL.txt` 存档。

⛔ **摇醒青年黑的额外红线**：声明第三条禁止「任何场景下改变摇醒青年黑的原有名称，将其作为商品进行转售及牟利」。
所以子集的 `name` 表必须保留 `摇醒青年黑1.0` / `Yaoxing Youth Hei` 原值，⛔ 不许改名后当自有字体分发。
裁子集（`pyftsubset`）不改 name 表，合规；若将来要重命名字体族，先回来读这一条。

⚠️ **摇醒青年黑的嵌入风险（2026-11-21 新发现，未解决）**：zfont.cn 把该字体的许可范围标为
**「嵌入」禁止**、「衍生」禁止。而本库的用法正是**把 woff2 当网页字体嵌入**（`friendship-bldg.css`
的 `@font-face` 指向 `YaoxingYouthHei-Subset.woff2`）。

- 作者声明 PDF 列了 12 类免费商用场景，**没有一类是「网页字体嵌入」**，也没提再分发。
- 声明给的是「**不可转让**的非专有商业许可」——把字体文件随仓库分发，字面上与「不可转让」冲突。
- 裁子集算不算「衍生」？声明只说禁止「改变原有名称后转售牟利」，没直接回答。

**已处置（2026-11-21）**：两道动作，缺一不可。

1. `friendship-bldg.css` 的 `@font-face` **删掉 `url()`，只保留 `local()`**。
2. **子集文件从仓库删除**（`assets/fonts/yaoxing/YaoxingYouthHei-Subset.woff2` 已 rm），
   该目录下只剩作者的免费商用声明 PDF。原版 ttf 已装到本机
   `~/Library/Fonts/摇醒青年黑1.0-Regular.ttf`（5.6 MB，7026 字形，`usWeightClass 400`）。

⚠️ **`local()` 必须写全名 `摇醒青年黑1.0 Regular`**（nameID 4）。族名
`摇醒青年黑1.0`（nameID 1）和 PostScript 名 `1.0-Regular`（nameID 6）在 Chrome 里
都解析失败，尽管 CoreText 层面三个名字都能解析到同一字体。详见 FONTS.md 那张表。

效果：

- 用户自己装了摇醒青年黑 → 标题用他自己的摇醒。这是用户自己的使用行为，**不涉及本库再分发**。
- 没装 → 沿 `--font-display` 回落**宋骨黑体**（SIL OFL 1.1，随包），同为黑体，
  版式、色板、字距全不受影响，只是少了摇醒的撇点宋意。
- 预览页顶部有静态提示条，说明「未装则回落宋骨黑体，想要原设计可自行下载安装」。

⛔ 回退链顺序不能反：`'SongguHei','宋骨黑体'` 必须在 `'PingFang SC'` 之前，否则没装摇醒的
用户会掉到系统黑体，丢掉本主题「标题偏宋意」的设计意图。闸门 F4 盯这个。

⛔ **别再把子集放回仓库**。这次要消除的正是「随仓库分发字体文件」这个动作本身；
只删 `url()` 而留着 woff2，等于风险还在。若将来作者书面授权再分发，才可重新子集化并加回 `url()`。

**爱点风雅黑（2026-11-21 改为不随包）**：与摇醒青年黑同因同法，同一个坑踩了第二次。

zfont.cn（`font_657`）把它的许可范围标为**嵌入禁止、衍生禁止**，商标也禁止，只允许
文稿 / 互联网 / 视频 / 印刷。作者官网的《使用须知》全文只有一句「个人及企业可永久免费使用」，
没提嵌入、没提再分发，也没有任何标准协议（zfont 记作「无标准协议（作者文字声明）」）。
字体 `name` 表 `nameID 13/14` 无许可声明，`nameID 0` 只写「Typeface © (ideavi.cn). 2024.
All Rights Reserved」——「保留所有权利」和「永久免费使用」并排放着，能确定的只有「用」，
不能确定「嵌」和「再分发」。

本库的用法正是把 woff2 当网页字体嵌入，落在被禁止的那一项里。处置同摇醒：

1. `panyu-rd.css` 的 `@font-face` 删掉 `url()`，只保留 `local()`。
2. **子集文件从仓库删除**（`AidianFengYaHei-Subset.woff2` 已 rm，913 KB），
   `assets/fonts/aidian/` 下只剩作者的《使用须知》。

- 装了爱点风雅黑 → 标题用他自己的，不涉及本库再分发。
- 没装 → 沿 `--font-display` 回落**宋骨黑体**（SIL OFL 1.1，随包，`assets/fonts/songgu/`），
  同为黑体，版式色板不受影响，只是少了风雅的方硬转折。宋骨黑体的 `@font-face` 就写在本主题
  CSS 里（与 friendship-bldg / fuzhou-rd / longhua-si 共用同一个子集文件），不依赖 `assets/fonts.css`。
- 预览页顶部加了静态提示条（赤陶配色）。

⚠️ `local()` 用**英文族名 `Aidian FengYaHei` 或 PostScript 名 `AidianFengYaHei-Regular`**
都能命中（2026-11-21 实测）；中文族名「爱点风雅黑」在 Chrome 里解析失败，别只写中文名。
这与摇醒青年黑相反（那个只有全名能命中），所以**每款字体都得单独实测，不能套用结论**。

**两款主题标题字体的分工**：爱点风雅黑只被 `assets/themes/panyu-rd.css` 引用（标题），摇醒青年黑只被
`assets/themes/friendship-bldg.css` 引用（标题），其余主题不加载。两者都只有 Regular 一档
（`usWeightClass 400`），`@font-face` 一律声明 `font-weight:400 700` 区间，标题写 400 才不触发伪粗；
⛔ 标题写 700/800 会让浏览器合成假粗，笔画糊成一坨。

奶盖宋只被 `assets/themes/qiu-r.css` 引用（标题、引语），其余主题不加载；正文字体思源黑体**不内化**，直接引用系统字体（`Source Han Sans SC` → 苹方 → 黑体）。裁子集是为守住单文件 ≤ 8 MB 的体量门（`scripts/build-deck.py` 的 `MAX_BYTES`）：整字库 ttf 80 MB、裁出的 ttf 9.0 MB 都过不了，转 woff2 后 2.6 MB 才落得进去。

**爨八体（2026-11-21 内化）**：只被 `assets/themes/longhua-si.css` 引用（标题），其余主题不加载。
原字 `坚果云 字体/爨八体/爨八体2.00.ttf`（19,720,968 B，upem 1000，9182 字形，`CanBaTi2.0`，
`nameID 0/13/14` **原为空**——作者没在字体里写版权和许可）。

- **为什么选它**：龙华寺是禅寺主题，需要碑刻的顿笔与飞白。爨八体以二爨为基础，
  融篆隶行草飞白漆书八体，取法古爨碑「生拙雄强」的风骨，三角点、翅头横、竹节竖是它的标志笔法。
  比楷书更硬，比宋体更有手写气，与「香灰 · 塔檐 · 白墙」的碑石质感同源。
- **授权边界（关键）**：作者声明授权允许**免费商用**（含嵌入系统/软件/APP、商标注册、出版物），
  但**明令禁止修改与衍生**。所以本库只做**码位裁剪**（`pyftsubset` 删字形、不动轮廓），
  轮廓数据逐字节未改。⛔ 不许给它加墨点、调字重、改笔画——那就越线了。
  要做旧/派生必须换 OFL 字体（思源宋、霞鹜文楷都可派生）。
- **⚠️ 只有汉字，没有标点数字**：实测 `cmap` 里 GB2312 全集 6763 汉字全有，
  但 ASCII 95 个可打印字符、27 个常用全角标点**一个都没有**。
  所以标题链必须紧跟霞鹜文楷：`'CuanBaTi','LXGWWenKai','霞鹜文楷','Source Han Serif SC',…,serif`。
  标题里的「·」「，」「2026」会逐字回落到霞鹜文楷，呈现楷书笔意——这是设计上的混排，不是缺字。
- **⛔ 不许把霞鹜文楷从链里去掉**：去掉后标点会一路掉到系统默认宋体，楷书笔意断裂。
- **⛔ 不许给爨八体加 `unicode-range`**：它本来就没有标点码位，加了没用，反而增加误判。
- **伪粗已规避**：标题规则写 `font-weight:700`，但爨八体只有 400 一档。
  `@font-face` 只声明 `font-weight:400` **单值**，让 700 请求回落到 400 原字形。
  ⚠️ 若声明成 `400 700` 区间，浏览器会合成伪粗，书法字体的飞白和三角点会糊成一团。
- **han-only 策略已移除**：旧版 `longhua-si` 用 `@font-policy han-only` 强制标点回落系统宋体，
  因为当时的标题字体（法华文楷完整版）含标点。换成爨八体后该策略自然失效——
  爨八体根本没有标点码位，不存在截走标点的可能。

**法华文楷（2026-11-21 降为提示项）**：不再被任何主题的 `@font-face` 声明，也不随包。

- 原字 `坚果云 字体/法华文楷/法华文楷标准版.ttf`（7,430,744 B，upem 2048，6899 字形，
  `FahwaWenkai-Standard`，`nameID 0` 记 © 2026 谢宏雲，`nameID 8` 记「文徵字库」）。
- **为什么不随包**：zfont.cn（font_777）把许可标为**商标/嵌入/衍生三项禁止**，
  许可协议栏为「无标准协议（作者文字声明）」，原文在小红书笔记（需 App 扫码，抓不到）。
  本库的用法正是把 woff2 当网页字体嵌入——落在被禁止的那一项里。
  字体 `nameID 13/14` 空。页面另有「系统检测该字体疑似由 AI 生成」警告。
- **⛔ 子集已于 2026-11-21 从仓库删除**，`assets/fonts/fahwa/` 整个移除。别放回去。
- **想用的用户**：自己装「法华文楷标准版」，把 `--ff-title` 首位改成 `'法华文楷标准版'` 即可
  （系统字体，浏览器直接命中，不需要 `@font-face`）。
  实测可命中的名字：中文族名「法华文楷标准版」、PostScript 名「FahwaWenkai-Standard」。

**福州路的两款字体（2026-11-20 内化）**：南西油墨宋只被 `assets/themes/fuzhou-rd.css` 引用（标题、引语），
宋骨黑体只被同一文件引用（正文、按钮、注释），其余主题不加载。

- **南西油墨宋为什么只裁一级字**：整库 7630 字形，woff2 转出来 9.21 MB，单文件体量门 8 MB 过不了。
  它的体积全在油墨噪点上（98.7% 的轮廓面积 <10 units²，中位每字 2083 个点），删噪点就不再是这款字体，
  所以只能裁字量。裁 GB2312 一级字（3755）后 woff2 5.03 MB，预览页 10.5 MB。子集外的字回落华文中宋。
- **⛔ 南西油墨宋绝不承载正文**：作者公众号原话「图片就是字体直接打出效果了，**不适合小字**」。
  12px 正文下噪点会糊成一团。它只用于标题与引语（≥20px）。
- **⛔ 宋骨黑体的 metrics 被改过，重做子集时必须一起改**：原字体 `typoAscender 880 / typoDescender -120 / lineGap 200`，
  行盒 1200 units，而汉字实际墨迹只占 `-88..868`，汉字重心比行盒中心高 90 units（12px 字号下 1.34px）。
  后果是按钮、胶囊里的中文读作「偏上」，几何量却是居中的（DOM skew 只有 0.5px，查不出来）。
  已改为 `typoAscender 868 / typoDescender -88 / lineGap 0`（行盒 956 units，汉字重心与行盒中心精确重合），
  `hhea` 同步改成 868/-88/0，`winAscent/winDescent` 保持 1095/289 不动（Windows 剪裁用）。
  **代价**：行盒从 14px 缩到 11px（12px 字号），所以 `.cp-btn-2` / `.cp-anchor` 的 padding 从 9px 补到 12px、
  `.pill` 系列的 `13px 22px 11px` 非对称内距改回对称 `12px 22px`（那个 13/11 是给旧系统宋体做的基线补偿，
  换字体后反而把胶囊撑歪）。重跑 `pyftsubset` 会丢掉这些改动，须重新执行。
- **⚠️ 南西油墨宋的许可落点缺口**：字体 `name` 表里只有「此字体来自淘宝店铺松陵南西」，
  没有许可条款；随包目录也没有授权文件。
  授权依据是作者公众号（`mp.weixin.qq.com/s/I4iTxJRjeZ1orpAEqB1kEA`，标题「免费商用/一款油墨宋体」）
  与 zfont.cn 登记（`zfont.cn/cn/font_779.html`，标注 **SIL OFL**，七项许可范围全允许，S 级 / 指数 50）。
  **对外分发前应补一份作者授权截图或链接存档**，否则这一行是本库唯一没有随包许可原文的字体。
- **⚠️ 2026-11-21 修正上一轮的误判**：曾据「公众号原文没提思源宋体」推断南西不是 OFL 衍生，
  并据此认为它不能内化。这个推理有漏洞——**作者没提 OFL 不等于没有 OFL**。
  zfont 的登记显示它是 OFL 且允许衍生，所以「能不能内化」这一层**是通的**；
  真正缺的只是**随包许可原文**（作者公众号正文确实只写了「免费商用」，没写 OFL 条款）。
  结论不变（仍按自备处理），但理由要改：不是「授权不明」，而是「授权依据未落成随包文件」。

## 只吸收规则、未复制资产的

> **许可未标注 ⇒ 只许吸规则，⛔ 不许搬资产。**
> 下表里标「未标注许可」的三家（designkit-ppt-design / ppt / presentation-change-control）是
> 宿主内置库，没有可引用的许可文本。没有许可就没有复制权：只能吸收**纪律与判据**这类
> 不受版权保护的思想，脚本、样式、资产、工具名一行都不许搬。要搬资产，先拿到许可原文，
> 再按上面「复制进来的资产」那节的规格逐个登记（版本 / 许可 / 复制了什么 / 许可原文落点）。
> 判据：`grep -rn '<该来源名>'` 只应出现在本文件与本说明里；出现在 `assets/` 或 `scripts/`
> 就说明搬了资产，须撤回或补许可。

| 来源 | 许可 | 吸收了什么 | 没复制什么 |
|---|---|---|---|
| **ppt-master**（github.com/hugohe3/ppt-master，© Hugo He） | **MIT** | C 出口的路由口径与"在哪层坏在哪层修"的纪律 | 整个引擎**只作指针**（`path-c-editable.md`），一个文件都没复制。体量随上游变：2026-11-10 本地残本 12MB / 566 文件 → 同日按官方 v6.7.2 补齐为 78MB / 13,019 文件 → 2026-11-14 重测 13,117 文件。⛔ 这些数字都是历史读数，**引擎可用性只认 `attribution_guard.py` 当次退出码** |
| **deck-course-module / deck-pitch / deck-swiss-international** | 三个模板件，原件已归档 | 只取"场景 → 页序"这一层**事实性结构**（封面/目标/正文/自测/收束等），文字与版式全部重写 | 它们的 `example.html` / `SKILL.md` 文本一行未复制；三个原件已于 2026-11-10 移入 `_archive/20261110-模板副本并入html-anything/`（正本在 `html-anything/…/<同名>/TEMPLATE.md`） |
| **designkit-ppt-design**（豆包内置 · 美图设计室连接器，2026-11-15 检视） | 内置库，未标注许可 | 素材权属 / 外发边界、最小追问、真实产物才算完成、复用原任务不重复创建的纪律 | MCP 工具名与票据（room_id / task_id）、上传端点白名单、附件配额、充值恢复、幂等键协议、form 路由与导出话术；脚本与资产一行未复制 |
| **ppt**（豆包内置 · 飞书幻灯片，2026-11-15 检视） | 内置库，未标注许可 | 素材质量四条、附件权威性、图片纪律、逐页状态确认、大纲节奏、缺数据占位标注 | lark-cli、飞书 XML、file_token / wiki token、svg_lib / 图表库、IconPark、字体表、抠图流程、`--no-lint` 口径；脚本与资产一行未复制 |
| **presentation-change-control**（豆包内置 · 变更控制，2026-11-15 检视） | 内置库，未标注许可 | 变更清单字段、执行前确认、全稿残留检查、样式继承、不可逆操作确认、页码漂移映射、交付摘要口径 | REQUIRED BASE SKILL 绑定、verifier-hub / artifact-preview 工具名、Profile 交付机制；`page_map.py` 脚本未搬入，纯计算规则改写为文字口径 |
| **curio-zane**（珍奇柜材质 UI，2026-11-16 引风格；2026-10-21 起步时结构底子取自 animal-island-ui v2.0.0，**经 11-20 全批改造已彻底脱钩**，现无资产或代码关系） | 本库自身 MIT；随包四族字体 SIL OFL 1.1 / 作者免费（未复制） | `curio-cabinet` 风格键：P1–P10 结构规则（圆角三值制、深一号描边、贴纸白边、压平层级、实物缩略图标、暖色带色阴影、状态靠形状位移）与暖系色板档位，改写为本库七小节规格 | 四款字体文件（7.4M）、实拍材质贴图、任天堂画面/图标、商业字体 FOT-Rodin / 汉仪正圆、Aqua `backdrop-filter` 半透明皮；tokens.css 变量名与整份 CSS 未复制 |
| `marble-vein-mask` | 脉络 alpha 掩膜 | 512² RGBA | `assets/textures/marble/marble-vein-mask-512.png` | Seedream 5.5（同 vein-raw 派生） | self-generated |

## 本 skill 自身的边界

- **自制资产（非上游）**：`assets/demo-images/*.svg`（7 份中性占位图，2026-11-14 补，供 5 份 image-* 版式的示例引用落地）、`assets/themes/century-sq.css`（2026-11-19 由本库 `guanglan-rd.css` fork 改造，色板/材质规范来自用户云主机会话《世纪广场 UI 风格卡》，非上游复制）、`scripts/check_doc_claims.py`、全部 `references/*.md` 与 `SKILL.md` 正文。占位图只做「此处有图」的示意，⛔ 不当真实素材交付（见 `qa-checklist.md` 第 7 条）。

- **自制材质位图（2026-11-22 起的 v2 家族制）**：位图按「材质家族」分件，一条 = 一张 tile，可有多个消费方（`used_by`），⛔ 不按主题复制同一张图。全部由本库用 Seedream 5.5 生成源图、再用 `scripts/make-material-tile.py` 派生（去大块明暗 → 位移 + 余弦交叉淡化 → 压到极低对比），**没有第三方权属、不需要外部许可原文**：

  | 登记 id | 派生件 | 面 / 体积 | 消费方 |
  |---|---|---|---|
  | `marble-light` | `assets/textures/marble/marble-gray-1024.png` | 1024 ² / 315,551 B | 世纪广场、友谊大厦（汉白玉） |
  | `marble-dark` | `assets/textures/marble/marble-dark-512.png` | 512 ² / 143,347 B | 世纪大道（暗底，overlay） |
  | `grain-agg` | `assets/textures/grain/grain-gray-512.png` | 512 ² / 119,057 B | 虬江石面、番禺水磨石、龙华碑石与香灰（粒径由 background-size 分档） |
  | `fiber-paper` | `assets/textures/fiber/fiber-gray-512.png` | 512 ² / 99,088 B | 福州新闻纸、万航渡拷贝纸、龙华白墙（同上） |
  | `travertine-strata` | `assets/textures/travertine/travertine-gray-512.png` | 512 ² / 99,214 B | 番禺石灰华（方向性材质，只此一处） |
  | `marble-vein` | `assets/textures/marble/marble-vein-1024.png` | 1024 ² / 415,347 B | 世纪广场、友谊大厦（Calacatta 式大脉络，cover 不重复，各自换裁切） |
  | `marble-vein-dark` | `assets/textures/marble/marble-vein-dark-1024.png` | 1024 ² / 413,224 B | 世纪大道（同一张脉络反相，screen 出「黑底亮脉」） |

  源图（灰度，可随时重出派生件）：`assets/textures-src/century-sq/marble-raw.png`（1536²，2,926,644 B）、`assets/textures-src/{grain,fiber,travertine}/*-raw.png`（各约 0.5–0.75 MB）、`assets/textures-src/marble-vein/vein-raw.png`（1536²，967,071 B）。登记与判据：`assets/textures-src/registry.json` ＋ `scripts/check-bitmap-assets.py`（B1–B10：字段 / sha 与尺寸与色彩类型 / 体积 / blend 白名单 / 源图存在 / 许可落点 / 每个 used_by 逐处接线 / 源目录无孤儿 / **同图重复登记必红** / **分档预算不许写松**）。

- 不打包任何上游资产，因此 来雪亭Lesciotia 可按自有条款发布；**内部改写部分不留逐条出处**，只留上面这批可查的资产登记。

- **为什么这里没有第三方来源的逐条登记**（2026-11-20 核对，2026-11-24 复核，留档备查）：早前版本曾按「吸收了执行纪律与演讲者视图口径」登记过一家外部 skill，逐条核对后依据不成立，故移除：
  1. **演讲者视图不是它的**。`S` 键双窗同步、当前/下一页预览、逐字稿、分段计时全部实现在 `assets/runtime.js` 里（`BroadcastChannel` 同步、`transform:scale()` 预览），1.2.42 起整件自写。对方独有的激光笔与排练记录本库没有，`grep -c 'laser|rehearsal|排练|激光' assets/runtime.js` = 0。
  2. **「执行纪律」是通用工程常识**：先备份再改长文件、按行列表操作、改完核对结构，任何长文件编辑场景都成立；库级铁律有同族条目（§2.105、§2.334）。这类道理不构成「吸收某家规则」。
  3. 资产侧：外部 skill 的模板、背景与 references **一个字节都没进来**，`grep -rn` 全目录零命中。

  ⇒ 结论：本库不含可归因的资产或独创表述，无需声明。**若将来真并入外部模板，则按该模板的许可调整整份 skill 的条款并加署名**——判据是「有没有复制资产或可归因的独创表述」，不是「读过没读过」。
- 已无上游可取：`assets/` 与 `scripts/` 全部为本库自有件，改动只在本目录内做；要引外部件，先按本节规格登记许可原文。

## 外部样本（仅抽口径，未复制文件）

2026-11-23 为校准字号与几何，检视了本地样本库 `/Users/nath/Desktop/利兄原创PPT`（PPT 版式库 200 页、
模板 50 套 1011 页）。**只抽取统计口径**——字号档位与层级比、页边距百分比、卡片栏数分布、描边与行距频次、
主色与 accent 用法；**不复制任何版式文件、图片、配色方案或成页构图**。抽象结果记在
`references/style-audit.md`，落进 `assets/base.css` 的 `--t-*` 阶梯，源文件本身不随库分发。
