# 可选效果：玻璃透镜位移场（`assets/effects/lens.js`）

> 归属：B 出口的可选件，不在 `base.css` 里，不装也能出整册。
> 用途：玻璃 / 亚克力 / 水面的「边缘折射」质感——一张底图，四边棱带弯折、中心保持原样。
> 这类「边缘折射」在公开项目里已有多种做法（SVG `feDisplacementMap` 位移、IOR 可调折射、离屏采样等，
> 名单见 `ATTRIBUTION.md`「同类项目勘察」）。**本库这份是自写**：公式在下文，可逐行复算，未复制任何实现。

## 为什么不是 blur

`backdrop-filter: blur()` 是把整面糊掉，观众看到的是「雾」；真玻璃的观感是**边上折、中间不动**：
光线穿过棱带时被偏折，穿过平面时直线通过。所以折射层只在棱带做功，中心位移必须为 0。

## 四步机制

1. **距离场（SDF）**：圆角矩形的有向距离，内部为负、外部为正；棱带宽度 `band` 就是 `0 < d < band` 这一圈。
2. **剖面**：`h(t) = sin(πt/2)`，`t` 从棱带外缘的 0 到内部平台的 1。缘陡内平——斜边陡，平面平。
3. **Snell 偏折**：取 `n = 1.5`（玻璃），位移量 `bend × (1-t)²`，方向沿 `-∇SDF`（内向法线）。
   位移在棱带最强、到平台收敛为 0；不做近全反射封顶（PPT 尺度上看不出来）。
4. **色散**：R/G/B 三通道各乘 `(1 ± aberr/100)` 后再采样一次，合成即边缘彩边。
   蓝紫彩边是物理结果，不是滤镜——`data-lens-aberr="0"` 可关。

## 用法

```html
<link rel="stylesheet" href="assets/effects/lens.css">
<div class="lens" data-lens-src="assets/covers/guanglan-rd-hills.jpg"
     data-lens-bend="56" data-lens-aberr="8" data-lens-band="0.14">
  <span class="lens-badge">初始化…</span>
</div>
<script src="assets/effects/lens.js"></script>
```

| 属性 | 默认 | 作用 |
|---|---|---|
| `data-lens-bend` | 20 | 棱带最大位移（px，按 820 长边的 canvas 坐标） |
| `data-lens-aberr` | 3 | 色散强度：三通道位移差百分比 |
| `data-lens-band` | 0.10 | 棱带宽度（占短边比例）；越大越像厚玻璃 |
| `data-lens-round` | 0.34 | 圆角半径（占短边比例） |

JS 只在 `window.LescioLens` 挂 `mount / fallback`，不接管翻页、不改字体色板。
`data-lens-state` 记录当前走哪一层：`lens` = 真折射，`turb` = 湍流兜底。

## 兜底：为什么必须有

折射要逐像素读底图（`getImageData`）。`file://` 直开时 canvas 被判跨源，**读像素直接抛
SecurityError**——出图脚本、双击打开的 deck 都走这条路。所以：

- **升级层**：读得到像素 → 挂 canvas，按上面四步算位移。
- **兜底层**：读不到 → 给卡补一张 `<img>`，套 SVG `feTurbulence + feDisplacementMap`（整面均匀波纹），
  并给卡打 `data-lens-state="turb"` + 角标写「湍流兜底」。⛔ 不静默降级成一张普通图。
- 想看真折射：`python3 -m http.server` 起本地服务再打开，或给 Chrome 加
  `--allow-file-access-from-files`（只作核对用，不进交付流程）。

## 已验证（2026-11-23）

同一张格子测试图（`assets/effects/demo-grid.svg`，含竖/横线）：

- `http://127.0.0.1:8899/examples/effects/lens.html` → 角标「透镜位移场」；四边竖线向棱带弯折、
  **中心线段仍直**，左右角出现品红／青色边（色散生效）。
- `file://…/lens.html` → 角标「湍流兜底 · 读不到像素」；整面网格同步起伏（兜底生效，未静默失败）。

## 取舍

- 只在 820 长边出图再放大：折射是低频效果，逐像素代价降到 1/5，肉眼无差。
- 不做真实环境反射（没有背景光场可采），只做折射与色散。
- 不做动画：`feTurbulence` 的 `seed` 动画在 PPT 截图里没有意义，网页里也易掉帧；
  要动态质感请用 `animations.css` 的页级动效，别在这里加 rAF。
