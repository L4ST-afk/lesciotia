# 第三角色 · 掩膜（只给形状，颜色给 token）

> 从 [`theme-bitmap.md`](theme-bitmap.md) 拆出（2026-11-22，原文件超 200 行硬上限）。
> 掩膜的规格、两用（金脉 + 灰白脉）、以及 Chromium 对 `file://` 掩膜的拦截，都在这里。

2026-11-22 参照 TINO 的 Portoro 页改成这一档。Portoro 的结构是**三层**：黑结晶底、
金色脉络的爆发、白色 effervescence；而且同一种石料还会按 **finish**（抛光 / 哑光 / 喷砂）再分档。
我们此前的暗底做法是「灰度反相 + screen」，它能出灰白脉，**染不出金**——这是屏幕混合的硬限制。

改成掩膜后：

- `make-material-tile.py --profile mask` 出 **RGBA 掩膜**：alpha = 脉络形状，RGB 全黑，
  `floor .28 / γ 2.0` 把脉边的灰阶过渡削掉（否则整块板面留一层雾；γ 从 1.15 提到 2.0，不透明占比 11.2%→5.8%，窄带里才不再读成金箔碎屑）；
- CSS 里 `background-color: var(--marble-gold-vein)` + `mask-image: url(掩膜)`——
  **颜色永远只在 `:root`，形状永远只在图里**。换主题只改 token，不必重导图；
- 白喷发继续由元素自身那道 CSS 白裂渐变承担，抛光反光也用 CSS 斜光，两层都不进图。

⛔ **掩膜图必须内联成 data URI。** Chromium 把 `file://` 的 mask 图按跨源请求拦掉：
页面直开 CSS、headless 导出截图这两种场合会**静默不画**（不报错、不 404），只有 http 或
data URI 才出。实测：CSS 渐变 mask 正常，`file://…png` 作 mask 全空，同一张图改成 data URI 立刻出现。
代价是 `century-ave.css` +约 137KB 文本；换来「直开 / 导出 / 单文件 deck」三种场合行为一致。

`vein-dark`（反相 screen 那档）随之退册，需要时可由 `vein-raw` 重出。

### 一张掩膜两用：金脉是主角，白脉是底子

真实 Portoro 不只是「黑底 + 金线」（2026-11-22 按大板照片核过）：金脉之间还夹着大量更细更淡的
灰白纹，局部有成片白色结晶。只做金脉，石头会显得干净得不像石头。

做法是**同一张掩膜用两次**，不新增图：

| 层 | 谁 | 怎么变形 | 颜色 |
|---|---|---|---|
| `::after` | 金脉（主角） | 原样，`cover`，pos 35% 65% | `var(--marble-gold-vein)` |
| `::before` | 灰白脉（底子） | 整层 `rotate(180deg) scale(1.06)`，`blur 1.6px` | `rgba(228,225,217,.15)` |

旋转是关键：不旋转就是「同一条线画两遍」，金色外面套一圈灰边，看着像描边；旋转之后两组脉
的几何不同，白的那组才读成「透出来的、在更深处」。白脉要「透」不要「贴纸」，靠 15% 浓度 + 一点模糊。

代价：`.cp-marble::before` 原先是层理 tile，现在被白脉占了，tile 挪进元素自身的
`background-image`，用 `background-blend-mode:overlay` 与底色合成（登记里记作 `blend: "overlay(bg)"`）。
base64 提到 `:root` 的 `--marble-vein-mask`，一份掩膜只存一次——CSS 反而从 278KB 降到 140KB。
