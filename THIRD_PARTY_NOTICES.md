# 第三方资产声明 / THIRD-PARTY NOTICES

本 skill 随包捆绑的第三方资产（字体、代码、版式）及其许可，**完整清单与改动登记见 [`ATTRIBUTION.md`](ATTRIBUTION.md)**。
本文件是机器可读的落点：交付检查器的 P9 判据只认 `NOTICE` / `THIRD_PARTY_NOTICES.md` /
`README.md` 这三个文件名，故在此单独列出捆绑资产的可识别名。

## 捆绑字体（`assets/fonts/`）

| 资产文件 | 字体 | 许可 | 许可原文 |
|---|---|---|---|
| `assets/fonts/素材集市智造黑1.02.ttf` | 素材集市智造黑 1.02 | SIL OFL 1.1 | `assets/fonts/OFL-素材集市智造黑1.02.txt` |
| `assets/fonts/cheesefoam/CheeseFoamOolongSong-Subset-Bold.woff2` | 芝士奶盖乌龙宋 0.103 Lite Bold | SIL OFL 1.1 | `assets/fonts/cheesefoam/OFL.txt` |
| ⛔ **无字体文件**（子集已于 2026-11-21 从仓库删除） | 爱点风雅黑 1.00（**不随包、不内化**） | 商用免费（广州爱点视觉文化有限公司）；⚠️ zfont.cn（font_657）标「嵌入」「衍生」「商标」禁止，故本库零分发，只走 `local()`，未装时标题回落宋骨黑体 | `assets/fonts/aidian/使用须知.txt`（仅声明） |
| ⛔ **无字体文件**（子集已于 2026-11-21 从仓库删除） | 摇醒青年黑 1.0 Regular（**不随包、不内化**） | 永久免费商用（贝塞尔教育科技（重庆）有限公司 / 摇醒实验室）；⚠️ zfont.cn 标「嵌入」「衍生」禁止，故本库零分发，只走 `local()`，未装时标题回落宋骨黑体 | `assets/fonts/yaoxing/免费商用声明.pdf`（仅声明） |
| `assets/fonts/nanxi/NanxiYoumosong-Subset.woff2` | 南西油墨宋 1.000 | 免费商用（松陵南西 / nanxiiii.taobao.com）；⚠️ 无随包许可原文，依据作者公众号与猫啃网登记，见 ATTRIBUTION.md | ⚠️ 无（分发前须补授权存档） |
| `assets/fonts/cuanba/CuanBaTi-Subset.woff2` | **爨八体 1.000**（张济海独创书法新书体，© 张济海；GB2312 一级字 3757 汉字子集，woff2 3.4 MB） | **作者声明授权**（非 OFL、非 CC）：企业与个人均可免费商用，无需授权文件；⛔ **不允许修改字体或制作衍生版本**；⛔ 禁止将字库本身作为商品出售。本文件仅做码位裁剪，轮廓未改 | `assets/fonts/cuanba/授权依据.md`（含猫啃网原文摘录） |
| ⛔ **无字体文件**（子集已于 2026-11-21 从仓库删除，`assets/fonts/fahwa/` 整个移除） | 法华文楷标准版 1.000（复刻敦煌经卷气韵的楷书，© 2026 谢宏雲 / 文徵字库）（**不随包、不内化、不声明 `@font-face`**） | 免费商用（作者文字声明，无标准协议）；⚠️ zfont.cn（font_777）标「嵌入」「衍生」「商标」禁止，另有「疑似 AI 生成」警告，故本库零分发。2026-11-21 起降为**提示项**：用户自装后改 `--ff-title` 首项即可用 | ⛔ **无**（零分发，无需授权存档） |
| `assets/fonts/songgu/SongguHei-Subset.woff2` | 宋骨黑体 1.310 Medium | SIL OFL 1.1（奇文云海设计顾问 / chivaltype.com） | `assets/fonts/songgu/OFL.txt` |
| `assets/fonts/lxgw/LXGWWenKai-Subset.woff2` | 霞鹜文楷 Regular（© 2021-2026 LXGW，Reserved Font Name `LXGW WenKai`）；GB2312 一级字 3755 汉字＋ASCII＋全角标点 27 个，共 3877 码位 | SIL OFL 1.1（字体 `nameID 13` 内附全文，`nameID 14` 指向 openfontlicense.org） | `assets/fonts/lxgw/OFL.txt` |
| `assets/fonts/ximai/WanhangXimaiBold-Subset.woff2` | 万航渡喜脉体 Bold（派生自字制区「喜脉喜欢体」v1.0 / FontQu Smile，© 探火（深圳）品牌策划有限公司） | SIL OFL 1.1（派生件同 OFL，已按保留字名条款改名） | `assets/fonts/ximai/OFL.txt` |

⛔ **摇醒青年黑**：授权声明禁止「改变原有名称、作为商品转售及牟利」。子集已保留原 `name` 表
（`摇醒青年黑1.0` / `Yaoxing Youth Hei`），⛔ 不许改名后当自有字体分发。

⚠️ **2026-11-21 起零分发**：zfont.cn 标该字体「嵌入」「衍生」禁止，作者声明 PDF 的
12 类免费商用场景不含「网页字体嵌入」，且声明为「不可转让」许可——随仓库分发字体文件与
「不可转让」字面冲突。

两道动作：`friendship-bldg.css` 的 `@font-face` 删掉 `url()` 只留 `local()`；
**子集 woff2 已从仓库删除**，`assets/fonts/yaoxing/` 下只剩作者的免费商用声明 PDF。
用户装了就用他自己的摇醒，没装则标题回落**宋骨黑体**（SIL OFL 1.1，随包）。
⛔ 别再把子集放回仓库；拿到作者书面授权再分发后才可恢复。

⚠️ **爨八体（2026-11-21 内化）的两条硬约束**：

1. **不许改字形**。作者声明原文：「这款字体不允许修改，任何人不得修改或制作衍生版本。」
   本库只做 `pyftsubset` 码位裁剪（删字形、不动轮廓），轮廓数据逐字节未改。
   ⛔ 不许加墨点、调字重、改笔画——要做旧/派生必须换 OFL 字体（思源宋、霞鹜文楷都可派生）。
2. **只有汉字，没有标点数字**。实测 `cmap` 里 GB2312 全集 6763 汉字全有，
   但 ASCII 95 个可打印字符、27 个常用全角标点一个都没有。
   标题链必须紧跟霞鹜文楷接住标点数字，否则会掉到系统默认宋体。

## 捆绑代码与版式

| 资产 | 出处 | 许可 | 许可原文 |
|---|---|---|---|
| ⛔ **无上游代码件**（2026-11-23 起）：`runtime.js` / `base.css` / `fonts.css` / `animations/animations.css` / `render-png.sh` 全部自写；`layouts/` 并成 17 族并重写；`full-decks/` 5 套连自带 `style.css` 一并改写；`themes/upstream/` 0 件 | — | — | 无（`LICENSE-html-ppt.txt` 已随复制件一起删除） |

判据：`LICENSE-html-ppt.txt` 只承载「复制进来的上游资产」的许可原文。复制件归零，该文件就该消失；
若哪天又从上游搬进一件，先按 `ATTRIBUTION.md` 的规格登记，再把这个文件和它一起加回来。

## 只吸收规则、未复制资产的

ppt-master、deck-course-module、deck-pitch、deck-swiss-international、designkit-ppt-design、
ppt（飞书幻灯片）、presentation-change-control、curio-zane（已脱钩）。
另有十余个公开项目（HTML deck 框架、玻璃折射效果、HTML→PPTX 转换器）只做过机制比对：
名单与「比对过什么」见 `ATTRIBUTION.md` 的「同类项目勘察」一节。**未复制任何文件**，
故不随包分发它们的许可原文；本库对应实现可直接读 `assets/effects/lens.js` 与 `references/effects-lens.md`。
