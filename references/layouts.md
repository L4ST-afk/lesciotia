# Layout Gallery

Optional layout hints for individual slides. Specify in outline's `// LAYOUT` section.

> **称呼**：B 出口的 17 族版式在本库叫「**梁架**」（木构承重骨架），9 个主题叫「**瓦作**」，
> 用户投进来的原始素材叫「**落雪**」。详见 `SKILL.md` §三层词汇。⛔ 只是称呼，目录名不改。
>
> **这是 A 出口的构图词表，不是 B 出口的文件名。** 下面 24 个名字（`title-hero`、`hub-spoke`…）是给**生图提示词**用的构图描述，`assets/layouts/` 里**没有**同名文件。
> B 出口（网页 deck）的 `layout` 字段只认 `assets/layouts/<stem>.html` 的 **14 个族**（`cover`、`data`…），口径见 `page-record.md` 与 `path-b-html.md` B1。
> 两套词表**零交集**，所以每行给了「B 参考」列做保守映射；标 **—** 的 9 个在 B 出口没有现成版式：要么换近似 stem 并在交付摘要明说降级，要么按 `path-b-html.md` B1 自组（写清为什么 17 族都不合适）。⛔ 别把 A 构图名直接填进 B 的 `layout` 字段。

## 归并：36 式 → 17 族（2026-11-23）

旧版按「一页一个文件」铺了 36 个单页，择页时要在 36 个名字里挑；实际大半是同一骨架换栏数、
换画法。现在并成 17 族 / 39 式，**一族一个文件**，族页里一段一式（`charts` 一页就能看完柱/线/饼/雷达）。
旧 stem 不再作为文件名存在，对照表在 `assets/layouts/_families.json`（唯一正本）：

| 族 | 段（`data-style`） | 旧 stem（只作别复活的针） | 什么时候用 |
|---|---|---|---|
| `cover` | cover | cover | 开场：标题、副标题、三 pill |
| `section` | section | section-divider | 分章：一句章名 + 一句提要 |
| `end` | end | thanks, cta | 收尾：谢谢 / 要一个动作（`cta` 加按钮） |
| `text` | text | bullets, two-column, three-column | 要点或分栏：默认单栏，`g2`/`g3` 换栏数；`rule=bottom` 走 `.cols3`（三列卡、段间虚线、卡底 accent 线）；`modules` 走 `.mod-grid`（2×2 模块格，末格可让给图） |
| `quote` | quote | big-quote | 一句可引用的话 + 出处 |
| `code` | code | code, terminal | 代码与终端输出（`chrome` 加窗框） |
| `compare` | compare, compare-image | comparison, pros-cons, diff, image-compare | 两栏对照（`mark=pc` ✓✗、`mark=diff` 旧→新）；两图对照单列一段 |
| `charts` | chart-axis, chart-pie, chart-radar, chart-unit, chart-waterfall, chart-dumbbell | chart-bar/line/pie/radar | 轴图（`line` 折线）、饼、雷达；另加可数点阵、瀑布、哑铃（自绘，C 出口无等价） |
| `image` | image-bleed, image-single, image-split | image-hero/full-bleed/single/text-split | 满幅图（压字与否）、单图+说明、左文右图 |
| `image-set` | image-set, image-band, image-round, image-card, image-phone | image-grid, image-gallery | 五式：`bento` 等分拼板 / `band` 图注压底 / `round` 圆切连排 / `card` 左文右图卡 / `phone` 窄图等高不裁（宽高比 < 0.9 过半自动选，图宽各自走）；`gallery` 错落已并入 bento。**图带压卡**走 `.ride`：图带 440px、结论行压在带内、两张白卡骑压带下沿 64px（卡内两段正文，小标题两行）|
| `process` | process-steps, process-timeline, process-roadmap, process-gantt | 同左 | 按顺序走：步骤卡 / 时间轴 / 泳道 / 甘特条（四种排布不合并）；`gantt` 走 `.gantt2`：日期算刻度、跨年分带、条内嵌完成度、模块间虚线；`timeline-arc` 走 `.tline`：贝塞尔曲线、圆点定位、日期竖杆交替上下 |
| `diagram` | flow, arch | flow-diagram, arch-diagram, mindmap | 流程链 / 分层；中心辐射并入 `ring-hub` |
| `data` | data-stat, data-table, data-todo | kpi-grid, stat-highlight, table, todo-checklist | 数字（`n=1` 即单数字）、表、清单 |
| `toc` | toc | toc | 目录页 |
| `ring` | ring-hub, ring-cycle, ring-map | ring-hub, ring-cycle | 枢纽辐条（任意 n，含原 mindmap）/ 环四步 / 环上节点缩略图＋编号（六点为上限） |
| `split` | split | split-table, split-flip | 左右不对称：`media=table` 表+结论 / `media=image` 判断+图；`bleed-img` 让图栏推到页边（-112px，去掉边框与圆角右缘）|
| `quiz` | quiz-ask, quiz-reveal, quiz-explain | quiz, mcq | 一道题的三态：问 / 揭 / 讲；题面逐字一致，差异只在标答案与解释位置 |

**并式的规矩（v1.2.36）**：只有「骨架同构、只差一个参数」才允许合段。合掉的是 12 个变体：
text 2（栏数）、compare 2（标记）、charts 1（柱＝线）、image 1（压字开关）、image-set 1（摆法，1.2.47 拆成 bento/band/round/card 四式）、
end 1（按钮）、code 1（窗框）、data 1（格数 n）、diagram 1（mindmap→ring-hub）、split 1（右栏载体）。
参数写在段的 `.params` 行里，⛔ 不再靠「另开一段」让人发现参数。
`charts` 一族曾靠 CDN 取 Chart.js，离线打开是空白；现随包在 `assets/vendor/chart.umd.min.js`（MIT，
归属见 `ATTRIBUTION.md`），同 `assets/layouts` 的离线口径。`code` 一族原本引了 highlight.js 却没引主题样式
（一个颜色都不出），已撤掉：按纯文本呈现，少背一份第三方。

## Slide-Specific Layouts

| Layout（A 构图名） | Description | Best For | B 参考（stem） |
|--------|-------------|----------|----------|
| `title-hero` | Large centered title + subtitle | Cover slides, section breaks | `cover`（章节页用 `section`） |
| `quote-callout` | Featured quote with attribution | Testimonials, key insights | `quote` |
| `key-stat` | Single large number as focal point | Impact statistics, metrics | `data` |
| `split-screen` | Half image, half text | Feature highlights, comparisons | `image` |
| `icon-grid` | Grid of icons with labels | Features, capabilities, benefits | — |
| `two-columns` | Content in balanced columns | Paired information, dual points | `text` |
| `three-columns` | Content in three columns | Triple comparisons, categories | `text` |
| `image-caption` | Full-bleed image + text overlay | Visual storytelling, emotional | `image`（或 `image`） |
| `agenda` | Numbered list with highlights | Session overview, roadmap | `toc` |
| `bullet-list` | Structured bullet points | Simple content, lists | `text` |

## Infographic-Derived Layouts

| Layout（A 构图名） | Description | Best For | B 参考（stem） |
|--------|-------------|----------|----------|
| `linear-progression` | Sequential flow left-to-right | Timelines, step-by-step | `process`（时间轴用 `process`） |
| `binary-comparison` | Side-by-side A vs B | Before/after, pros-cons | `compare`（利弊用 `compare`） |
| `comparison-matrix` | Multi-factor grid | Feature comparisons | `data` |
| `hierarchical-layers` | Pyramid or stacked levels | Priority, importance | — |
| `hub-spoke` | Central node with radiating items | Concept maps, ecosystems | `diagram` |
| `bento-grid` | Varied-size tiles | Overview, summary | — |
| `funnel` | Narrowing stages | Conversion, filtering | — |
| `dashboard` | Metrics with charts/numbers | KPIs, data display | `data` |
| `venn-diagram` | Overlapping circles | Relationships, intersections | — |
| `circular-flow` | Continuous cycle | Recurring processes | — |
| `winding-roadmap` | Curved path with milestones | Journey, timeline | `process` |
| `tree-branching` | Parent-child hierarchy | Org charts, taxonomies | — |
| `iceberg` | Visible vs hidden layers | Surface vs depth | — |
| `bridge` | Gap with connection | Problem-solution | — |

**Usage**: A 出口在 slide 的 `// LAYOUT` 段写 `Layout: <name>`；B 出口在 `pages/NN.md` 的 `layout` 字段写 stem。

## Layout Selection Tips

**Match Layout to Content**:
| Content Type | Recommended Layouts |
|--------------|-------------------|
| Single narrative | `bullet-list`, `image-caption` |
| Two concepts | `split-screen`, `binary-comparison` |
| Three items | `three-columns`, `icon-grid` |
| Process/Steps | `linear-progression`, `winding-roadmap` |
| Data/Metrics | `dashboard`, `key-stat` |
| Relationships | `hub-spoke`, `venn-diagram` |
| Hierarchy | `hierarchical-layers`, `tree-branching` |

**Layout Flow Patterns**:
| Position | Recommended Layouts |
|----------|-------------------|
| Opening | `title-hero`, `agenda` |
| Middle | Content-specific layouts |
| Closing | `quote-callout`, `key-stat` |

**Common Mistakes to Avoid**:
- Using 3-column layout for 2 items (leaves columns empty)
- Stacking charts/tables below text (use side-by-side instead)
- Image layouts without actual images
- Quote layouts for emphasis (use only for real quotes with attribution)
- 同一页并列 ≥4 个指标 / 价格 / 区间还堆文字卡：先换原生图表或刻度长条（骨架与栅格见 `design-guidelines.md` Card Skeleton / 数据图形化条）
