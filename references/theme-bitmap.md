# 位图材质：两个角色（细层理 tile / 大脉络 hero）

> 本卷只讲「CSS 画不出的那层质感」怎么补。瓦作导出（`export-theme-textures.py`，把 CSS 截成 PNG）
> 见 [theme-to-export.md](theme-to-export.md)。

## 目录

- 两个角色（为什么大理石要分两层）· 形态与接线 · 无缝化（只给 tile 做）
- 家族制与登记（registry v2 / used_by / B1–B10）· 容量账（三档面 + 粒径旋钮）
- 压缩（ppduck）· 验收 · A/B 样 · 踩坑台账
- **两面照妖镜（CSS 结构 / 像素可见性）** · 第三角色：掩膜（Portoro 金脉）

## 两个角色：为什么大理石必须分两层

2026-11-22 用户给了参考图（Calacatta Borghini）：**几道 100–300px 宽的巨脉**横贯白板。
这与「241–255 极低对比的细层理」不是同一个物种，而且暴露出一个结构性冲突：

- 细层理的特征尺度 **远小于** tile，位移 + 余弦交叉淡化能把它做得无缝，重复也看不出来；
- 巨脉的特征尺度 **大于** 整张 tile。硬做无缝，110px 的淡化带就会把穿缝的脉揉成软影——
  **缝没了，脉也毁了**；就算做成 tile，1024 周期在大面板上准点重复，Calacatta 正是靠
  「每块切片都不一样」读成石材，一重复就成壁纸。

所以分成两个角色，各自用不同铺法：

| 角色 | 文件 | 铺法 | 用在哪 |
|---|---|---|---|
| 细层理 / 颗粒 / 纸纤维 | `*-gray-<n>.png` | `repeat` + `background-size` 取固有尺寸 | `::before`，次级结构、大面积不抢眼 |
| 大脉络（hero） | `marble-vein-1024.png` | **`no-repeat` + `cover` + `background-position`** | `::after`，主角版面 |

`background-position` 是 hero 的第二个旋钮：一张 1024 的脉络图，世纪广场取 `0% 0%`、
友谊大厦取 `60% 40%`、世纪大道取 `35% 65%`——**三块面看起来是三种石料，代价是一个文件**。

## 形态与接线

```css
.cp-marble{position:relative;isolation:isolate}
.cp-marble::before{                     /* ① 细层理，重复 */
  content:"";position:absolute;inset:0;z-index:-2;pointer-events:none;
  background-image:url("../textures/marble/marble-gray-1024.png");
  background-repeat:repeat;background-size:1024px 1024px;
  mix-blend-mode:multiply;opacity:.85
}
.cp-marble::after{                      /* ② 大脉络，不重复 */
  content:"";position:absolute;inset:0;z-index:-1;pointer-events:none;
  background-image:url("../textures/marble/marble-vein-1024.png");
  background-repeat:no-repeat;background-size:cover;background-position:0% 0%;
  mix-blend-mode:multiply;opacity:.90
}
.cp-marble--flat::before,.cp-marble--flat::after{content:none}   /* 回退纯 CSS */
```

五条硬约束，每条都对应一个踩过或预见得到的坑：

1. **位图必须是灰度**（PNG color type 0）。颜色只在 `:root` 一处；灰度 + 混合模式让色相仍由 token
   决定，一张图可供亮底与暗底共用。⛔ 别把彩色石子做成像素。
2. **`z-index:-1 / -2` + 父级 `isolation:isolate`**。伪元素是最后绘制的子节点，不给负层级会压正文；
   父级不隔离，混合模式会漏到页面底色而不是只跟自身背景相乘。两层时 `::before` 用 -2、`::after` 用 -1。
3. **tile 的 `background-size` 取固有尺寸**，用 `cover`/`100%` 会拉伸，接缝回来、颗粒被拉糊。
   （反向也成立：**换整数倍尺寸＝换粒径**，见容量账。）
4. **hero 必须 `no-repeat` + `cover`**。巨脉一旦 `repeat` 就是壁纸。
5. **C 出口只许局部**：整页铺底会撞 `verify-pptx-editable.py` 的 `FULLBLEED_RATIO=0.9`，
   被判「这页就是一张图」，可编辑性归零。

## 无缝化：位移 + 余弦交叉淡化（**只给 tile 做**）

`scripts/make-material-tile.py --profile <marble|grain|fiber|travertine>` 三步：抽掉大块明暗
（高半径低通相减）→ 位移半幅把接缝移到正中，余弦权重交叉淡化 → 压到极窄灰区间。

- ⛔ **别用「镜像四联」**：确实无缝，但 1024 里会浮出蝴蝶形对称，目检一眼就露（2026-11-22 第一版）。
- 余弦带宽 `--band 110` 是权衡：窄了缝在，宽了脉被抹平。
- 读数看两个：`seam`（左右/上下边缘像素差）与 `min/max`。
- ⚠️ 颗粒/纸纹这类高频图的 `seam` 天然是 2–5/255（相邻像素本来就有差），
  **不能拿 0.76 的阈值去卡它们**；判据是 3×3 目检有没有「一条线」。

`--profile vein / vein-dark` 是**例外档**：不做位移淡化，只做分位重映射（`vein` → 200..255、
`vein-dark` 反相 → 0..58），因为大脉络不允许被淡化带揉。

## 家族制与登记

一条登记 = **一张 tile**，可以有多个消费方。⛔ 别按主题复制同一张图——那只是把 sha 抄一遍。

| 文件 | 作用 |
|---|---|
| `assets/textures-src/registry.json` | 登记表 v2：id / family / role / source / derived / builder / blend / license / sha / 尺寸 / 预算 / `used_by[]` |
| `assets/textures-src/<family>/<name>-raw.png` | 源图（灰度），派生件全部由它重出 |
| `assets/textures/<family>/<name>.png` | 共享件，按**材质家族**归档（`marble/` `grain/` `fiber/` `travertine/`） |
| `assets/textures/<theme>/board.png` `mat-*.png` | 瓦作**按主题**导出的截图，与共享件分开 |
| `scripts/make-material-tile.py` | 出图，打印 profile / 尺寸 / min-max / seam / 体积 / sha |
| `scripts/check-bitmap-assets.py` | 闸 B1–B10 |

```bash
python3 scripts/make-material-tile.py \
  --raw assets/textures-src/grain/grain-raw.png \
  --out assets/textures/grain/grain-gray-512.png --profile grain --size 512
python3 scripts/check-bitmap-assets.py            # --root 指临时拷贝可做负例
```

- `used_by[]` 每项 `{theme, sel, layer, blend, opacity, bg}`。`stage:"wired"` 时闸会逐处核对
  **文件名 / 选择器 / `mix-blend-mode` / `opacity`** 四项，任一不符即红——登记表是这些数字的唯一源头。
- `license:"self-generated"` 时 `ATTRIBUTION.md` 必须出现该 id；外部图先拿许可原文，`license` 不许留空。

## 容量账（2026-11-22 实测）

| 面 | 用途 | 预算 | 实例 |
|---|---|---|---|
| 1024 | 主 tile（大理石细层理） | ≤ 400 KB | `marble-gray-1024` 315,551 B |
| 1024 | hero 大脉络（不重复） | ≤ 520 KB | `marble-vein-1024` 415,347 B |
| 512 | 次面（颗粒 / 纤维 / 石灰华 / 暗底） | ≤ 160 KB | 99,088–143,347 B |

两个旋钮能把一张图摊到多处：

- **`background-size` 换粒径**：同一张 `grain-gray-512` 在番禺水磨石用 512、龙华碑石 384、香灰 256
  ——三种粒径，一个文件。
- **`background-position` 换裁切**：同一张 `marble-vein-1024` 三处不同裁切（见上）。

按家族共享 vs 按主题各出一套：7 条登记 **≈1.5 MB** 覆盖 8 个主题的 11 处消费；
按主题做要 14 张 ≈4.4 MB。**省约 66%**，而且省掉的是「同一材质出现第二张、第三张」的隐患。

## 压缩（可选，ppduck）

`cli-anything-ppduck compress <png> --out <abs> --report <abs.tsv> --sbs <abs>`：两步协议
（`Include → Compress`），产物异步落盘，必须绝对路径 + 轮询。
实测白 marble tile：534,154 → 398,757 B（−25.3%），`maxΔ=4`、`px>8=0.00%`、PASS。
**但没有收编**：它是有损调色板量化（RGBA→P），收益只有四分之一，换来的是「tile 不可逐字节复现」。
口径：**渐变/照片型图不走 ppduck**；⚙️ 本库 tile 一律无损 PNG（hero 图 1024 也宁可 415 KB）。

## 第三角色：掩膜（形状与颜色分开）

2026-11-22 起，暗底大理石的金脉改成「alpha 掩膜给形状、`:root` token 给颜色」。这张掩膜还一图两用：
`::after` 上金色（主角），`::before` 转 180° 做灰白底脉。完整规格、变形参数与 `file://` 拦截的坑
见 [`theme-bitmap-mask.md`](theme-bitmap-mask.md)。


## 两面照妖镜：结构闸与像素实测

位图这条链上出现过两次「闸全绿、页面什么都没有」，都不是文本能查出来的：

**第一面：CSS 结构。** 往已有规则后粘新规则时少了一个 `}`，浏览器把整段当无效声明丢弃——
文件名、选择器、`mix-blend-mode`、`opacity` 全在文件里，B7 判绿，页面上一个像素都没有。
九份 CSS 曾七份中招。判据：
```
python3 scripts/check-bitmap-assets.py      # B11：括号配平 + 不许「声明行紧接选择器行」
```

**第二面：像素。** 层真的画出来了，也可能因为 tile 对比太低而等于没接（`amp=9` 时 A/B 的
|Δ| 只有 1–3/255）。判据只能渲染后量：
```
python3 scripts/probe-texture-visibility.py        # 14 处约 1 分钟
```
每处渲 A（`<sel>--flat`）/ B（默认）两格，量 `Δhf = hf(B) - hf(A)`（半径 2 高斯残差）
与低通差（缩到 1/4 再比）。**达标线：Δhf ≥ 0.35 或 低通Δ ≥ 3.5 灰度级。**
⛔ 别用 `hf(B)/hf(A)` 比值——A 完全平坦时会被除零放成天文数字（实测出现过 847750.01）。

## 验收（缺一条不算做完：结构 / 像素 / 登记 / 体积 / 预览）

1. `make-material-tile.py` 打印的 `min/max/mean` 与登记一致，sha 与 `derived_sha256` 对得上；
2. tile 拼 3×3 目检无接缝、无对称；hero 图目检脉络不断、无拉伸（机器判不了，必须看图）；
3. `check-bitmap-assets.py` exit 0、0 ✗；
4. `selftest.py` 的位图负例（改 sha / 删派生件 / 塞未登记源图 / 同图重复登记）必须红；
5. 改了主题 CSS 后重出该主题材质图 + 重生成预览页，`check-theme-textures.py` 与
   `check-preview-sync.py` 都要绿——否则图与 CSS 已脱钩，页面照常渲染。

## A/B 样

- `examples/marble-bitmap-ab.html`（2026-11-22 首版）：A 纯 CSS / B multiply 1.0 / C multiply 0.72
  ——证明「CSS 版是白底 + 两道斜光」。
- 大脉络的两层版与暗底版对照在 `/tmp/vein-ab2.html`、`/tmp/dark3.html`（一次性检视，未入库）：
  A 只有脉络 / B 脉络 .90 + 层理 .85（**采此档**）/ C 脉络 .72 / D 暗底 `screen .55`（采此档）。
- 暗底三档的结论：`multiply` 在 `#1a1410` 上几乎不可见；`invert+screen` 配细层理会把平白区抬成雾；
  **脉络反相 + `screen .55` 才是「黑底亮脉」**，`.28` 太弱、`multiply .5` 读成污渍。

## 脉的排列组合

见 `references/theme-marble-veins.md`：`--alt` 四旋钮（裁切点 / 旋转 / 缩放 / 对比）、三主题的配对表，
以及两条做不通的路（白纱叠层造次脉、转 90° 露白）。

## 踩坑台账

- 截图退出码不可作判据（写不出文件也返 0），只能读 PNG 头 + 宽高。Chrome headless 并发过多时
  会**整个挂住**（一次 8 主题串跑卡在第二个主题），此时进程还在、CPU 几乎为 0——`ps` 看不出，
  必须看日志时间戳。
- 检视页里把选择器（带点号）写进 `class` 属性 → 类名不匹配，页面全空但截图正常生成。
  判据：四张不同主题的截图**字节数完全相同**就是没命中。
- `[^)"']*` 解析 data URI 必截断；白底上低 α 纹理视觉等于空白。
