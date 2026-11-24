# presenter-mode-reveal · 演讲者册（7 页）

给**要照着讲、但不能念稿**的场合：观众那屏只放观众该看的，讲稿、下一页、计时全在你自己那块屏上。
默认挂 `century-ave`（世纪大道），暖炭底、金标线。

## 页序

1. 封面 — 这一册讲什么
2. 目录 — 五件事（`toc` 族：六个键够用 / 四张可拖的卡 / 一条通道说话 / 稿子不上墙 / 按 S，然后别看观众）
3. 键位 — 六个键，一屏认完
4. 四张卡 — 当前 / 下一页 / 逐字稿 / 计时
5. 同步 — 两屏只通过 `BroadcastChannel` 说话，iframe 只加载一次
6. 讲稿 — 稿子写在 `.notes` 里，不上墙
7. 收束 — 按 S，别看观众

## 键位（runtime 真相）

| 键 | 动作 |
|---|---|
| `←` `→` / `Space` / `PgUp` `PgDn` / `Home` `End` | 翻页 |
| `F` | 全屏（退出 `Esc`） |
| `S` | 开合演讲者窗 |
| `N` | 讲稿抽屉（只在你那屏） |
| `T` | 换主题（读 `<html data-themes>` 列表，与 `theme-link` 换 href 等价） |
| `A` | 换当前页动效 |
| `B` | 黑屏 |
| `G` | 参考线（验边距与基线） |
| `O` | 总览缩略图 |
| `R` | 计时归零（演讲者窗） |

## 写讲稿

进 `<div class="notes">`，150–300 字/页（2–3 分钟一页）：是**提示信号**，不是逐字稿；口语写，
"因此"→"所以"。放映时 `.notes` 一律不显示，只有演讲者窗与 `N` 抽屉读得到。
`<strong>` / `<em>` / `<code>` / `<p>` 可用。

## 动效

页内元素挂 `data-anim="fade-up"` 一类属性即可，26 个类见 `../../../assets/animations/animations.css`；
放映时按 `A` 可只重放当前页动效，改类名不会动主题。

## 交付件与闸

只有 `index.html`（`base.css` → `layouts.css` → `theme-link`），没有私有 `style.css`。
`assets/decks.json` 源级登记（7 页）；`check-deck-sync.py` 核页数与主题，`check-fit.py` 核体量。
