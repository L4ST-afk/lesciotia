# Design Guidelines

Detailed design principles for slide decks.


> 本文件只讲受众、层级、密度、一致性。颜色 / 字体 / 视觉元素 / 四维组合见 `design-visual.md`。

## 目录

- `Audience Guidelines`
- `Visual Hierarchy Principles`
- `Type Scale（字号档位收敛）`
- `Card Skeleton（卡片骨架与栅格）`
- `Content Density`
- `Consistency Requirements`

## Audience Guidelines

Design decisions adapt to target audience. Use `--audience` to set.

| Audience | Content Density | Visual Style | Terminology | Slides |
|----------|-----------------|--------------|-------------|--------|
| `beginners` | Low | Friendly, illustrative | Plain language | 8-15 |
| `intermediate` | Medium | Balanced, structured | Some jargon OK | 10-20 |
| `experts` | High | Data-rich, precise | Technical terms | 12-25 |
| `executives` | Low-Medium | Clean, impactful | Business language | 8-12 |
| `general` | Medium | Accessible, engaging | Minimal jargon | 10-18 |

### Audience → Density Mapping

Recommended density dimension based on audience:

| Audience | Recommended Density | Rationale |
|----------|-------------------|-----------|
| `executives` | minimal | One insight per slide, respect time |
| `beginners` | minimal → balanced | Single concepts, build understanding |
| `general` | balanced | Accessible but informative |
| `intermediate` | balanced | Standard information density |
| `experts` | balanced → dense | Can handle more data per slide |

**Automatic Density Selection**:
- If `--audience executives` → default to `minimal` density
- If `--audience beginners` → default to `minimal` or `balanced`
- If `--audience experts` → allow `dense` density
- Otherwise → default to `balanced`

### Audience-Specific Principles

**Beginners**:
- One concept per slide
- Visual metaphors over abstract diagrams
- Step-by-step progression
- Generous whitespace

**Experts**:
- Multiple data points per slide acceptable
- Technical diagrams with precise labels
- Assume domain knowledge
- Dense but organized information

**Executives**:
- Lead with insights, not data
- "So what?" on every slide
- Decision-enabling content
- Bottom-line upfront (BLUF)

## Visual Hierarchy Principles

| Principle | Description |
|-----------|-------------|
| Focal Point | ONE dominant element per slide draws attention first |
| Rule of Thirds | Position key elements at grid intersections |
| Z-Pattern | Guide eye: top-left → top-right → bottom-left → bottom-right |
| Size Contrast | Headlines 2-3x larger than body text |
| Breathing Room | Minimum 10% margin from all edges |

## Type Scale（字号档位收敛）

**反例（2026-11-16 投资人 deck 实测）**：初稿同是卡片正文，字号散在 8.5 / 9.5 / 9.8 / 10.2 / 10.8 / 11.0 / 11.2 / 11.5 八档相邻碎片，扫读时层级全糊；成稿收敛到少数角色档位后，卡片正文一眼可分主次。

**规则**：

- 一份 deck 开工先定一张**角色 → 字号档位表**：眉标 / 大标题 / 导语 / 卡片小标题 / KPI 主数字 / 卡片正文 / 单位注 / 页码注释，各占一档。
- **同角色同字号**：相邻两页同类卡片不许各用一档；要调先查表，⛔ 不新造相邻半磅值（10.5 与 10.8 并存就是碎片信号）。
- 内容过多先拆卡 / 换版式，不靠缩字号硬塞（口径见 `modification-guide.md` 样式继承）。
- 数值随画布口径换算：px 地板仍按 `qa-checklist.md` #4（1920×1080 画布）；本卷只锁**角色档位**，不写死 pt/px 绝对值。

### 参考角色档位（2026-11-16 投资人 deck 实测）

口径：宽幅 16:9 PPTX，画布 33.87×19.05cm。下表 pt 是这份 deck 上的实测落点；**锁的是角色间相对层级，绝对值随画布口径等比换算**，换 B 出口 1920×1080 时按 `qa-checklist.md` #4 的 px 地板重算，不照搬 pt。

| 角色 | 参考 pt | 字重 | 层级说明 |
|---|---|---|---|
| 眉标 CHAPTER / kicker | 10.5 | 粗 | 导航行，全篇最小一档标识 |
| 页标题（内容页） | 29 | 粗 | 单页主标题 |
| 章节大序号 | 72 | 粗 | 章节封面装饰序号 |
| 章节标题 | 36 | 粗 | 章节封面主标题 |
| 章节导语 | 14 | 常规 | 章节封面一句导语 |
| 章节副注 | 11 | 常规 | 章节封面补充注 |
| 卡片 / 区块小标题 | 15 / 18 | 粗 | 按卡宽与层级选档 |
| 宽卡正文 | 16 | 常规 | 宽列、带图三栏卡 |
| 窄卡说明 | 12 | 常规 | 宽 ≤5.5cm 的并列窄卡 |
| 横排标签（左窄列） | 16 / 18 / 20 | 粗 | 标签＋说明行的标签 |
| 横排说明正文（右宽列） | 14–16 | 常规 | 标签＋说明行的正文 |
| KPI 主数字 | 18 / 24 / 30 | 粗 | 按数字长度与焦点选档 |
| KPI 卡名 | 10.5 / 12 | 常规 | 主数字下一行 |
| 强调结论句 | 20 | 粗 | 页面收束结论 |
| 表格表头 | 10 | 粗 | 拼表文本框表头 |
| 表格单元格 | 10.5 | 常规 | 密集表正文 |
| 表格脚注 | 10 | 常规 | 表下口径注 |
| 图注 / 小注 | 10.5 / 12 | 常规 | 附图与卡下口径 |
| 页脚脚注 | 7–9 | 常规 | 最低层口径补充 |
| 页码 | 9 | 常规 | 页脚序号 |

**分档要点（同轮实测踩出）**：

- **跨段同档**：补写 / 后段页面必须回查前段同角色已用档位，⛔ 不许沿用初稿偏小值。本轮后段说明散在 9.5 / 10 / 10.5，返工对齐到窄卡 12、横排 14、表格单元格 10.5、表头 10。
- **宽窄卡分档**：宽卡正文 16，窄卡（≤5.5cm 宽）说明降到 12；把宽卡 16 塞进窄卡会挤成三行，把窄卡 12 用到宽卡又显小。
- **表格不破地板**：表头不低于 10 粗、单元格不低于 10.5；密集表（≥8 行 / ≥3 组）单元格 10.5 两行可容，再低扫读发糊。
- **放大后核验**：单行框高约 0.6cm 时 14pt 行高临界，长句会换两行；字号抬完逐页截图，溢出先回调 12 或拆行 / 换版式，不靠继续压字号硬塞。
- 层级对比靠**字重＋颜色**造，不靠字号往上喊（与 `taste-deck.md` §一.14 一致）。

## Card Skeleton（卡片骨架与栅格）

**反例（同轮实测）**：初稿卡片宽窄不一、数字与单位挤在同一行、左竖条时有时无；成稿统一为下列骨架后，并列卡可以横向扫读。

**卡片骨架**：

- 卡片＝底 shape ＋ 左侧细竖条 accent；标题在上、内容在下。
- 并列卡**等宽等高**、间距对称；栅格左右边距全篇一致。
- **KPI / 价格卡**：主数字大字号一行，单位 / 口径小字另起一行；数字与单位分行，不挤同一行。
- 扉页（section divider）：眉标（CHAPTER / kicker）＋ 大标题 ＋ 分隔线 ＋ 一句导语；⛔ 不放数据卡与 KPI。

**边界**：卡内必须有真实数字或具体口径；空壳「图标＋标题＋一句话」三列属 taste-deck §一.15 禁型，不在本骨架豁免内。

## Content Density

See `references/dimensions-density.md` for full density dimension specs.

| Level | Description | Use When |
|-------|-------------|----------|
| High | Multiple data points, detailed charts, dense text | Expert audience, technical reviews |
| Medium | Key points with supporting details | General business, mixed audiences |
| Low | One main idea, large visuals, minimal text | Beginners, keynotes, emotional impact |

**High-Density Principles** (McKinsey-style):
- Every element earns its space
- Data speaks louder than decoration
- Annotations explain insights, not describe data
- White space is strategic, not filler

**数据罗列优先图形化（2026-11-16 实测）**：同一页并列 ≥4 个指标 / 价格 / 区间时，先考虑原生图表或带状对比图（刻度长条＋端点数字），不要堆一排文字卡；长段落拆成模块卡，一卡一事。初稿把 6 个指标写成文字卡、定价带写成文字罗列，成稿分别换成原生 chart 与刻度长条后，对比关系一眼可见。

**Density by Slide Type**:
| Slide Type | Recommended Density |
|------------|-------------------|
| Cover/Title | minimal |
| Agenda/Overview | balanced |
| Content/Analysis | balanced or dense |
| Data/Metrics | dense |
| Quote/Impact | minimal |
| Summary/Takeaway | balanced |

## Consistency Requirements

| Element | Guideline |
|---------|-----------|
| Spacing | Consistent margins and padding throughout |
| Colors | Maximum 3-4 colors per slide, palette consistent across deck |
| Typography | Same font families and sizes for same content types |
| Visual Language | Repeat patterns, shapes, and treatments |
| Separators | 标题 / 卡片标签内并列短语统一用间隔号「・」；正文分句用分号 / 逗号；同一份 deck 不混用顿号、斜杠、破折号做并列分隔（2026-11-16 实测收口） |

