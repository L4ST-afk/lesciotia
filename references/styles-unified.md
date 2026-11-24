# 风格系统（统一版）

一套风格键，三处实现。**风格键是唯一命名**——不要再用上游主题名或别的叫法另行称呼同一件事；同一个视觉只许有一个名字，否则选型时会挑出两个其实一样的选项。

- **A 出口**读 `references/styles-<key>.md`（18 份，规格已按本 skill 改造，出处见 `ATTRIBUTION.md`）
- **B 出口**用 `assets/themes/<theme>.css`（9 个主题里挑出最贴近的自建皮肤，备选气质按 `references/palette-atlas.md` 的六组起手式临时改 token，不另存主题）
- **C 出口**不规定皮肤：走客户品牌模板，风格键只决定"密度/字重/配色倾向"

## 四维定义（A 出口精确生效，B 出口近似）

| 维度 | 取值 | 管什么 |
|---|---|---|
| Texture | clean / grid / organic / pixel / paper | 背景处理：纯色、网格、手绘、像素、纸张 |
| Mood | professional / warm / cool / vibrant / dark / neutral / macaron | 色温与配色 |
| Typography | geometric / humanist / handwritten / editorial / technical | 标题与正文的气质（描述外观，不写字体名） |
| Density | minimal / balanced / dense | 每页信息量与留白 |

B 出口只有 texture/density 能被主题+版式精确承接；mood/typography 只能近似——**要在交付摘要里如实写"近似"**。

## 21 个风格键

| # | key | 中文 | 四维 | A 实现 | B 主题 | 适合 | 别用在这 |
|---|---|---|---|---|---|---|---|
| 1 | `blueprint` | 蓝图（默认） | grid+cool+technical+balanced | `styles-blueprint.md` | `engineering-whiteprint` | 架构、系统设计、技术方案 | 生活方式、情感类内容 |
| 2 | `corporate` | 商务 | clean+professional+geometric+balanced | `styles-corporate.md` | `corporate-clean` | 投资人 deck、提案、正式汇报 | 创意发布、潮牌 |
| 3 | `minimal` | 极简 | clean+neutral+geometric+minimal | `styles-minimal.md` | `minimal-white` | 高管简报、一句话结论 | 教学（信息量不够） |
| 4 | `notion` | 产品文档 | clean+neutral+geometric+dense | `styles-notion.md` | `academic-paper` | 产品介绍、SaaS、指标页 | 发布会主视觉 |
| 5 | `bold-editorial` | 杂志主张 | clean+vibrant+editorial+balanced | `styles-bold-editorial.md` | `magazine-bold` | 发布、keynote、品牌宣言 | 严肃合规材料 |
| 6 | `editorial-infographic` | 信息图 | clean+cool+editorial+dense | `styles-editorial-infographic.md` | `editorial-serif` | 技术解释、研究综述、科普 | 极简结论页 |
| 7 | `intuition-machine` | 直觉机器 | clean+cool+technical+dense | `styles-intuition-machine.md` | `swiss-grid` | 技术文档、学术、双语 | 儿童/轻松内容 |
| 8 | `scientific` | 科研 | clean+cool+technical+dense | `styles-scientific.md` | `academic-paper` | 生物/化学/医学/实验 | 营销页 |
| 9 | `dark-atmospheric` | 暗调氛围 | clean+dark+editorial+balanced | `styles-dark-atmospheric.md` | `tokyo-night` | 娱乐、游戏、氛围发布 | 打印/投影环境差的场合 |
| 10 | `pixel-art` | 像素 | pixel+vibrant+technical+balanced | `styles-pixel-art.md` | `retro-tv` | 游戏、开发者、复古梗 | 正式商务 |
| 11 | `vintage` | 复古 | paper+warm+editorial+balanced | `styles-vintage.md` | `midcentury` | 历史、人文、传承 | 数据密集型 |
| 12 | `watercolor` | 水彩 | organic+warm+humanist+minimal | `styles-watercolor.md` | `soft-pastel` | 生活方式、健康、旅行 | 硬核技术 |
| 13 | `sketch-notes` | 手绘笔记 | organic+warm+handwritten+balanced | `styles-sketch-notes.md` | `soft-pastel`（降级） | 教程、入门、图解 | 需要精确数据 |
| 14 | `hand-drawn-edu` | 手绘教学 | organic+macaron+handwritten+balanced | `styles-hand-drawn-edu.md` | `soft-pastel`（降级） | 教学图解、流程解释 | 高管汇报 |
| 15 | `chalkboard` | 黑板 | organic+warm+handwritten+balanced | `styles-chalkboard.md` | `academic-paper`（降级） | 课堂、教学 | 品牌发布 |
| 16 | `vector-illustration` | 矢量插画 | clean+vibrant+humanist+balanced | `styles-vector-illustration.md` | `memphis-pop` | 儿童、创意、轻松内容 | 严肃研究 |
| 17 | `fantasy-animation` | 奇幻 | organic+vibrant+handwritten+minimal | `styles-fantasy-animation.md` | `aurora` | 故事、奇幻、动画感 | 数据汇报 |
| 18 | `swiss-grid` | 瑞士网格 | grid+cool+technical+dense | 无（用 `custom: grid+cool+technical+dense`） | `swiss-grid` | 数据汇报、设计/工程、强网格 | 温情叙事 |
| 19 | `neo-brutalism` | 新粗野 | clean+vibrant+geometric+balanced | 无（`custom: clean+vibrant+geometric+balanced`） | `neo-brutalism` | 反精致、潮牌、先锋 | 政府/金融正式件 |
| 20 | `xiaohongshu` | 小红书 | clean+warm+humanist+balanced | 无（`custom: clean+warm+humanist+balanced`） | `xiaohongshu-white` | 小红书图文、种草卡 | 长文深度稿 |
| 21 | `curio-cabinet` | 珍奇柜 | paper+warm+humanist+balanced | `styles-curio-cabinet.md` | `soft-pastel`（近似，暖系） | 教学卡片、生活方式、亲子/友好品牌、插画讲解 | 硬核数据汇报、严肃合规、暗调氛围 |

> 18-20 是 B 优先的新增风格。A 出口要它们时走自定义维度（第 5 列），不要假装有专门的 style 文件。

## 降级规则（照做，不要静默替换）

1. **B 出口没有手绘/粉笔皮**：`sketch-notes` / `hand-drawn-edu` / `chalkboard` → 用 `soft-pastel` 或 `academic-paper` 承接，并在交付摘要写「手绘质感需 A 出口」。
2. **A 出口没有 theme 概念**：B 主题名对 A 无意义，A 只认 `<STYLE_INSTRUCTIONS>`。
3. **命中多个风格**：取内容**气质**最近的一个，不要混搭两套（混搭会让整份 deck 失去一致性）。
4. **用户指定的风格不在表里**：走 `custom` 四维，并在 `outline.md` 里把这四个词写清楚；不要硬塞到某个 preset 假装匹配。

## 主题选择速查（B 出口）

| 场合 | 首选主题 | 备选 |
|---|---|---|
| 投资人/提案 | `pitch-deck-vc` · `corporate-clean` | `swiss-grid` |
| 技术分享 | `tokyo-night` · `terminal-green` · `engineering-whiteprint` | `catppuccin-mocha` |
| 学术/报告 | `academic-paper` · `editorial-serif` · `minimal-white` | `nord` |
| 小红书/社媒 | `xiaohongshu-white` · `soft-pastel` | `rainbow-gradient` |
| 发布/潮 | `neo-brutalism` · `cyberpunk-neon` · `vaporwave` | `y2k-chrome` |
| 温暖叙事 | `sunset-warm` · `japanese-minimal` · `midcentury` | — |
| 动画 / 纸与线（手工工序） | `japanese-minimal` · `editorial-serif` | `wanhang-fy` |
| 报纸 / 印刷 | `editorial-serif` · `newspaper` | `fuzhou-rd` |
| 寺院 / 东方宗教建筑 | `japanese-minimal` · `editorial-serif` | `longhua-si` |
| 城市 / 公共导览 · 建筑风格 | `century-sq` | `guanglan-rd` |

`assets/themes/` 里 9 个自建主题全在（这 9 件是活的正本）；要临时换气质就打开 `references/palette-atlas.md` 取一组起手式，⛔ 不要凭名字猜色。`century-sq` 是 2026-11-19 由 `guanglan-rd` fork 的「世纪广场」主题：柯布西耶模度网格、混凝土/大理石/拉丝钢/磨砂玻璃、亮黄主色 + 2/4/6 号线次色；新增 B 主题要同步改这几处计数并跑 `check_doc_claims.py`。

## 加一个新风格要改哪里

1. A 出口：写 `references/styles-<key>.md`（按现有 18 份的七小节结构：Design Aesthetic / Background / Typography / Color Palette / Visual Elements / Style Rules / Best For）。
2. 在本表加一行（四维、A 实现、B 主题、适合/别用）。
3. B 出口若需要新主题：在 `assets/themes/` 加一个 `.css`，必须覆盖 `--accent-ink`（保证 accent 上的字能过对比度）。
4. 跑一遍 `qa-checklist.md` 的组 1，确认新风格在封面/正文/数据三类页上都不塌。
