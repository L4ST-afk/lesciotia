# assets/textures · 瓦作出图（派生件）

这里的东西**全部是生成的**，没有一件是手工素材。真源是 `assets/themes/<theme>.css` 的 `:root` 与材质类。

```
<theme>/
├── manifest.json   源 sha256 / palette / 每张图的类名与尺寸
├── board.png       材质板：一张看全该主题
├── mat-<class>.png 单个材质类样片 320×320
└── tex-<token>.png 内联 SVG 纹理平铺样（tile 尺寸见 manifest）
```

重新出图（源未变会自动跳过）：

```bash
python3 scripts/export-theme-textures.py --force
python3 scripts/check-theme-textures.py           # 闸：sha/宽高/palette/覆盖/孤儿
```

⛔ 不许手改 PNG、不许手塞图：`check-theme-textures.py` 会把 manifest 之外的 PNG 报成孤儿，`palette` 逐字回查 `:root`。
用法、A/C 两出口接法、验收四条见 `references/theme-to-export.md`。

为什么单独放目录、不并入预览页：预览页已经把字体内联成 10MB 级单文件；材质图若走 data URI 会再翻一倍，
而 A/C 出口要的是**独立文件**（参考图、贴图），塞进 HTML 对它们没收益。

## 例外：位图 tile 是手做的真素材（2026-11-22 起）

上面说「全部是生成的、没有一件手工素材」——**有一条例外**：`century-sq/marble-gray-1024.png`。

它不是为了把 CSS 截成图，而是反过来：CSS 画不出白大理石的细层理，所以用一张真位图去补。
形态是**灰度无缝 tile ＋ `mix-blend-mode:multiply`**（颜色仍取 `:root` 的 `--marble`，
一张 tile 供亮色版与暗色版共用）。所以：

- 它**不能**被 `export-theme-textures.py --force` 重出（那个脚本只截 CSS）——重出它要用
  `scripts/make-material-tile.py`，源图在 `assets/textures-src/century-sq/marble-raw.png`；
- 它**必须**登记在 `assets/textures-src/registry.json`，由 `scripts/check-bitmap-assets.py` 守
  （sha / 尺寸 / 灰度 / 体积预算 / blend / 许可 / 接线 / 孤儿）；
- `check-theme-textures.py` 不认识它，会把它当「manifest 之外的 PNG」报**孤儿 WARN**——这是已知且可接受的：
  两者分工不同（一个管派生件，一个管真位图）。

⛔ 位图一律灰度。放进彩图就等于把色值从 `:root` 搬进像素，`check-theme-colors.py` 再也查不到。
