# weekly-report · 周报（8 页）

让人三分钟看完一周：**三个数、做成了什么、卡在哪**。默认挂 `century-sq`（世纪广场）。

## 页序

1. 封面 — 第几周 / 团队 / 汇报人
2. 三个数 — `data-stat` 四张 KPI 卡（静态数字；⛔ 不挂 `.counter`，否则出图会截在计数半路）
3. 本周做的 — 六卡三列，一行一件
4. 趋势 — `charts` 柱状（Chart.js；⛔ 必须 `maintainAspectRatio:false`，否则 520px 卡里只占一半）
5. 时间去向 — `charts` 环图，**单色相明度阶梯**（读 `--accent`/`--bg` 按 1/.7/.52/.38/.26 在 JS 里混，别用五色）
6. 阻塞 — `data-todo`（`ul.todo`，两列四件；不完成别预勾 `done`）
7. 下周 — 三件要做完的
8. 收束 — 一句话

## 吃什么

`base.css` → `layouts.css` → `theme-link`，另加 `../../../assets/vendor/chart.umd.min.js`（只有这本带图表）。
没有私有 `style.css`。

## 坑

柱状图的 `height:%` 在自适应高的 `.c` 里会解析成 0——必须 `align-items:stretch` + `.c{height:100%}`（1.2.42 已修，改版时别改回去）。

## 闸

`check-deck-sync.py`（页数 8 + 主题 slug）、`check-fit.py`（8 段体量）。
