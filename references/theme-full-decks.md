# 满版模板吃什么（`assets/full-decks/` → 主题）

> 2026-11-22 建，2026-11-23 随 1.2.42 全面改写重写。解决的是一类"看起来接线了、其实没生效"的假绿：
> 模板里挂了 `theme-link`，但封面颜色仍是模板自带蓝紫。判据只认产物像素，不认 CSS 文本。

## 现状表

| 模板 | 页数 | 默认主题 | 私有样式 |
| --- | --- | --- | --- |
| `course-module` | 8 | `qiu-r` | 无 |
| `pitch-deck` | 10 | `century-sq` | 无 |
| `tech-sharing` | 8 | `guanglan-rd` | 无 |
| `weekly-report` | 8 | `century-sq` | 无 |
| `presenter-mode-reveal` | 7 | `century-ave` | 无 |

五套只剩 `index.html` 一件事（另各有一份本库风格 README）：底子吃 `assets/base.css`，
版式吃 `assets/layouts.css` 的族页，配色吃一件主题，三者都从 `../../../assets/` 相对引用。
`theme-link` 是主题那一行的 `id`，顺序固定为 `base.css` → `layouts.css` → `theme-link`。

各册吃到的族（2026-11-24）：`course-module` process · `pitch-deck` compare(`.vs`) · `tech-sharing` code ·
`weekly-report` charts ＋ `data` ＋ `image-set`（第 2 页 `data-stat`、第 6 页 `data-todo`、第 8 页 `.gg.band` 五格图注压底；9 页）· `presenter-mode-reveal` toc；`tech-sharing` 8→9 页加 `split`「出口对照」；`century-ave-materials` 5→6 页加 `ring-map`「六道工序」。
`data` 族此前只存在于 `assets/layouts/`，这是它第一次进整册；随页替换，周报原有的 `.wr-kpi` / `.wr-row`
私有规则一并删除，整册仍无 `<style>`。

**1.2.42 之前的状态（供考古，勿照抄）**：每套自带一份 `style.css`，调色板是模板自己的
蓝紫/深色 GitHub 色，靠 `@layer tpl-palette` 与主题抢位。那一层已随 1.2.42 全面改写删除——
模板不再有自己的色板，配色只有主题一个来源。

## 一条仍然有效的判据：自定义属性按「元素 > 继承」解析

旧模板的坑值得记下来，因为它在任何"模板 + 主题并存"的写法里都会复活：

```
.tpl-x{--accent:#3b5bff} 在 @layer 内   → 元素取值 #3b5bff
主题 :root{--accent:#dab406} 未分层      → 根取值 #dab406
```

层叠层只在**同一个元素**的多条声明之间排序。主题的 `:root` 声明落在 `<html>`，到 `.tpl-x`
是**继承值**，而"元素自身声明"永远优先于"继承值"——层序不参与这场比较。所以只要模板在
自己的根元素上重挂调色块，无论包不包 `@layer`，都会压过主题。

结论：本库现在的做法是**模板不挂调色块**。新加模板若确需一个专属色，把它写成主题
（`assets/themes/<slug>.css`，过色板闸），而不是塞进模板的 `<style>`。

## 换主题 / 加新模板

1. 换主题：只改 `index.html` 里 `theme-link` 的 href（`../../../assets/themes/<slug>.css`），
   同步改 `assets/decks.json` 的 `theme` 字段，跑闸。
2. 加模板：页全用 `layouts.css` 的族页（17 族 39 式），不写私有 CSS → 插 `theme-link`
   → `build-deck.py <template>/index.html -o out.html --force` 打包 → 截图看封面是否变色
   （⛔ 不接受"CSS 里写了"当证据）→ 登记 `decks.json`。

## 闸与负例

`scripts/check-deck-sync.py` 覆盖模板：源必须存在、必须有 `id="theme-link"`、href 的 slug
必须等于登记的 `theme`、主题文件必须存在、页数必须等于登记值；并且按改动时间判
"源比产物新"——源改过而产物没重打包，直接红。
`"mode": "source"` 的条目表示"只登记源、不预生成交付件"，报 INFO 不算 WARN。

负例已验（2026-11-22）：把 `pitch-deck` 的 href 临时改成 `guanglan-rd.css` →
`FAIL 源引用主题 guanglan-rd，登记的是 century-sq`，退出码 1；复位后 PASS。

## 已知观感差异

`base.css` 的网格底纹与草坪色带会铺到模板页底部（`pitch-deck` 封面右下角即此），
这是主题/base 的装饰在起作用，不是接错线。若某套模板不需要，在本页 section 内挂一个
工具类局部关掉（如 `data-no-grid`），⛔ 不要回退主题/base。

## 模板页照样不许绕过 token（中文混排）

模板没有私有 CSS 之后，混排仍可能被**页内手写样式**破坏——一个 `style="font-family:…"`
就够。`base.css` 里写着「罗蛇 T07：中文不用负字距」、`--letter-tight: 0`、
`text-autospace`、`line-break: strict`，页内写死等于把已修好的判据改回去。三类必须走 token：

| 写死的形态 | 后果 | 应该写成 |
|---|---|---|
| `letter-spacing:-.02em` 在**含中文**的标题上 | 中文笔画挤在一起、标点贴字（T07 硬伤） | `letter-spacing: var(--letter-tight)`；纯数字位（`.mega`／`.metric .n`／`.section-num`／`.kpi .value`）可以保留负距 |
| `font-family:'Playfair Display',serif` | 中文掉进通用 `serif`：既不受控，又会让**中文标点被西文字体截走**（实测旧版中文句号渲染成基线小点，只因 Playfair 里有该字形，浏览器按字形回退就不换字体） | `var(--font-serif)`（主题已映射到 `--font-body-song` 等中文衬线） |
| `font-size:11px` 的中文位 | 汉字糊成一团（T11 要求中文 ≥12px） | 12px 起 |

另有一条已落在 `base.css`：`font-synthesis: none`（T08）。中文字体没有真 italic，
`<em>`／`font-style:italic` 在旧设定下会被浏览器**合成斜体硬歪**；全局禁掉合成之后，
英文仍走 Playfair 的真斜体字面，中文保持正体。

⛔ 新写页时不要凭"英文 PPT 的排版习惯"写字面负字距，那是上游英文模板的假设，
中文语境下默认必须是 0；确实要收紧的拉丁大标题在具体 deck 里另写，别写进族页。
