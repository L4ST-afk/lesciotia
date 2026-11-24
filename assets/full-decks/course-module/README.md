# course-module · 课程单元（8 页）

一份讲一件事的教学册：**一页一个判据，讲完就走流程**。默认挂 `qiu-r`（虬江），纸色偏暖，衬线标题。

## 页序

1. 封面 — 单元名 / 讲者 / 时长
2. 目标 — 三件学完能做到的事
3. 三层 — 词汇、族页、出口的分层
4. 控量 — 一页装多少字（体量预算）
5. 四问 — 动笔前的四个问题（浮沙言语域判据）
6. 反例 — 先讲错的怎么写，再讲对的
7. 四步 — 旧稿改造的 `process-steps`（先删 / 再认族 / 换主题 / 过闸，带 `~20min` 级 tag）
8. 收束 — 一句话 + 下一步

## 吃什么

只有 `index.html`：`../../../assets/base.css` → `../../../assets/layouts.css` → `theme-link` 三行。
没有私有 `style.css`，没有模板调色块；改配色只换主题那一行的 href（详见 `references/theme-full-decks.md`）。

## 怎么用

抄 `<section>` 块进自己的 deck，别整文件复制（`../../../assets/` 的相对深度是按这个目录算的）。
页内手写样式要守 token（不写死字体与负字距），判据见 `references/theme-full-decks.md` 末节。

## 闸

`assets/decks.json` 登记为源级（`mode: source`）；`scripts/check-deck-sync.py` 核页数与主题 slug，
`scripts/check-fit.py` 核每段装不装得下。
