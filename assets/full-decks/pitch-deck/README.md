# pitch-deck · 路演册（10 页）

讲给不读你文档的人：**先给问题，再给一条能验的路**。默认挂 `century-sq`（世纪广场），冷白纸、标线黄。

## 页序

1. 封面 — 一句话定位 + 谁在讲
2. 问题 — 现状坏在哪（`compare` 的 `bad-side` 用法见第 8 页）
3. 解法 — 一件事的三步
4. 结构 — 一件产物吃三样文件：base / 族页 / 主题
5. 出口 — 同一份内容三条出口（影像 / 网页 / 可编辑 PPTX）
6. 闸门 — 质量靠什么拦（`pre.card > code` 跑命令）
7. 数字 — 三个大数字，一个不吹
8. 对照 — 和模板站的做法比（`compare` 族 `.vs`：模板站 `bad-side` ↔ 来雪亭 `good-side`）
9. 路线 — 接下来三个月
10. 收束 — 一句要求

## 吃什么

只有 `index.html`：`base.css` → `layouts.css` → `theme-link` 三行；没有私有 `style.css`。

## 交付件

已登记 `built`：`模板pitch-10页-世纪广场.html`（单文件，内联六个资源），改源后必须
`scripts/build-deck.py assets/full-decks/pitch-deck/index.html -o "<built>" --force` 重打包，
否则 `check-deck-sync` 报"源比产物新"。

## 闸

`check-deck-sync.py`（页数 10 + 主题 slug + 产物新鲜度）、`check-fit.py`（10 段体量）。
