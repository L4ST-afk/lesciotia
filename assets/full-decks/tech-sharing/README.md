# tech-sharing · 技术分享（8 页）

讲工程细节的册子：**能测的才叫规格**。默认挂 `guanglan-rd`（广兰路），浅青底、深青标线，代码块走 `code` 族。

## 页序

1. 封面 — 题目 + 讲者 + 时长
2. 痛点 — 观众正踩的三个坑
3. 画布 — 1920×1080 是设计画布（`pre.card > code` 放 CSS 片段）
4. 字号 — 九档 px，`1pt = 2px`
5. 色板 — 三律：单 accent / 明度阶梯四档 / `--accent-ink` 逐主题算
6. 闸门 — 一条命令跑完七道闸（`pre.card > code` 放命令）
7. 取舍 — 哪些不做（附理由，`compare` 或清单）
8. Q&A — 留一个真问题

## 吃什么

只有 `index.html`：`base.css` → `layouts.css` → `theme-link` 三行；没有私有 `style.css`。
代码块一律 `<pre class="card"><code class="language-x">`，别回退到页内手写 `<div class="ts-code">`（1.2.44 已删该类）。

## 闸

`check-deck-sync.py`（页数 8 + 主题 slug）、`check-fit.py`（8 段体量）。
