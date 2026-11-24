# 瓦作出图：主题 → A/C 出口的桥

**一句话**：瓦作（`assets/themes/*.css`）原先只服务 B 出口。这一步把主题里的材质渲染成 PNG，
让 A 出口（影像 deck）能当风格参考、C 出口（可编辑 pptx）能当底纹，**而不新增第二份色值**。

## 为什么要有这条桥（2026-11-21 定的背景）

A 出口是逐页 AI 生图，C 出口交给外部引擎 `ppt-master`——两侧都不读 CSS。所以在此之前，
「主题」在 PPT 侧等于不存在：`path-a-image.md` 与 `path-c-editable.md` 里 0 处提到 themes。
给主题手做一套位图素材是没用的，因为没有任何环节会去读它；要成立必须先把图**能导出、能引用、能被闸守**。

## 产物形态

```
assets/textures/<theme>/
├── manifest.json      # 源 sha256 / palette / 每张图的类名与尺寸
├── board.png          # 材质板：一张看全该主题，A 出口当 style 参考图
├── mat-<class>.png    # 单个材质类样片，320×320（如 mat-cp-marble.png）
└── tex-<token>.png    # 内联 SVG 纹理平铺样（如 tex-qj-brick-tile.png）
```

- **material class**：`.cp-marble` / `.fb-stone` / `.lh-eave` / `.pg-arch` / `.wf-paper` / `.glass` 这类
  「块里有 background」的语义材质。词表在 `scripts/export-theme-textures.py` 的 `MATERIAL_WORDS`；
  ⛔ 新增材质名必须加进词表，否则脚本只在 WARN 里提一句，不会自动导出。
- **svg token**：`--qj-fiber` / `--fb-grain` 这类 `url(data:image/svg+xml,…)`。导出时按 SVG 固有尺寸 ×2 平铺，
  manifest 里留 `tile_w/tile_h`，贴图端按这个尺寸平铺才是原设计密度。
- **覆盖**：9 个自建瓦作全部有图（最少 3 项，最多 12 项）。某个主题想不出图，闸会红，不许静默缺。

## 两条用法

**A 出口 · 风格参考**（`path-a-image.md`）：用户说「要和某个瓦作同款视觉」时，
把 `assets/textures/<theme>/board.png` 作为 `--ref` 的 `style` 图传给生图后端，
并把 `manifest.json` 的 `palette` 里 3–5 个主色 hex 写进每页 prompt 的正面描述。

- 主题不是风格键（21 个风格键在 `assets/styles-*.md`）。主题给的是**具体场所的材质与配色**，
  风格键给的是**版式语汇与四维**。两者的映射不写死，按需组合。
- 后端不吃参考图时，降级成纯文字（把材质词与 hex 抄进 prompt），并在交付摘要里说明降级。

**C 出口 · 底纹贴图**（`path-c-editable.md`）：把 `mat-*.png` / `tex-*.png` 作为局部装饰或低面积底纹交给引擎。

- ⛔ 整页铺底会撞 `verify-pptx-editable.py` 的 `FULLBLEED_RATIO=0.9`：单页图片面积 ≥ 页面 90% 即判「铺满」，
  可编辑判据当场红。底纹只做局部（页眉带、栏侧、卡片底）或要求引擎把它设为**版式背景**而非图片形状。
- 需要真无缝的平铺底纹，只用 `tex-*`（SVG 纹理本就是按 tile 设计的）；`mat-*` 是材质样片，不平铺。

## 幂等与更新

```bash
python3 scripts/export-theme-textures.py            # 全部；源未变且产物齐全则跳过
python3 scripts/export-theme-textures.py --only qiu-r --force
python3 scripts/check-theme-textures.py            # 闸：覆盖/来源/产物/色值/孤儿
```

- 改了主题 CSS ⇒ 必须重跑导出，否则闸红（`source_sha256` 不符）。
- PNG 是**派生件**，⛔ 不手改、不手塞（闸会对 manifest 之外的孤儿报 WARN，色值会被回查）。
- 改了 `MATERIAL_WORDS` 或板式 ⇒ `--force` 全量重出。

## 验收（缺一条不算做完）

1. `export-theme-textures.py` 末行 `--json` 的 `ok` 为 true，且 `images` 与磁盘张数一致；
2. `check-theme-textures.py` exit 0，零 ✗；
3. 打开任意一张 `board.png`，目检材质是否真是该主题的材质（不是通用灰）——这步机器判不了；
4. `python3 scripts/selftest.py` 里两条负例（改 sha / 删图）必须**红**，否则闸是摆设。

## 已知坑

- **截图退出码恒 0**：Chrome 写不出文件也返回 0，判据只能是「PNG 头 + 宽高对得上」（脚本已这么判）。
- **`@import` 外链字体**：截图前脚本会剥掉 `https://` 的 `@import` 并把 `../fonts/` 改成绝对 `file://`，
  否则 headless 会去联网、CSS 可能超时。
- **色值真源仍在 `:root`**：manifest 的 palette 是 build 记录，不是第二份规格；闸会逐字回查。

## 位图材质（2026-11-22）

**真位图补的是 CSS 补不出的那一层**（细层理、颗粒、云斑）。形态、无缝化、登记与闸、接线两处必改、ppduck 口径全在 [theme-bitmap.md](theme-bitmap.md)。
