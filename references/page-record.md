# 逐页记录 `pages/NN-{slug}.md`

三出口共用的**唯一正本**。改内容先改这里，再让各出口重新派生；不要直接改产物（图/HTML/pptx）里的字，否则下次重出就丢。

## 模板

```markdown
# 03 · 增长曲线与三个硬指标

- **type**: data
- **archetype**: pitch
- **layout**: data                # B 出口：assets/layouts/ 里的族名（无 .html；族内换式见 _families.json）
- **density**: balanced
- **title**: 一年 8 倍，不靠补贴
- **kicker**: Traction
- **points**:
  1. 周活 12K → 96K（12 个月，自然增长）
  2. 付费转化 4.7%（行业均值 2.1%）
  3. 单客成本 ¥38，回收周期 2.4 个月
- **visual**: 左侧一根上升到画面右上方的粗折线，三个端点各一个数字；背景极浅网格，右侧留白放三条指标
- **notes**: 这一页只说三件事：涨了多少、凭什么涨、成本多低。先给 8 倍这个数，停一秒再解释。
- **refs**: [增长看板 2026-10](source-growth.csv)
```

字段语义（**槽位表**：空着的槽，这页就不成立——框架语义路径 B）：

| 字段 | 谁读它 | 必填 | 空着的后果 | 说明 |
|---|---|---|---|---|
| `type` | 三出口 | **必** | 闸门直接拒：`export-pptx.py` 报「type 未知」并 exit 2；B 出口挑不出版式 | 决定版式候选与页序角色。**词表见下方「type 词表」** |
| `archetype` | 三出口 | **必** | 页序骨架丢失，同一份 deck 内各页会各写各的 | 来自 `archetypes.md`，同一份 deck 内应一致 |
| `layout` | B（C 参考） | B 必 | B 出口组不出版式，只能手写 HTML——那就绕过了梁架闸 | `assets/layouts/<layout>.html` 的 stem；不存在就说明要自己组版式（先别硬造） |
| `density` | A / B | 选 | 用风格默认值，不会错 | minimal / balanced / dense，覆盖风格默认值时才写 |
| `title` | 三出口 | **必** | P8 判「正文太薄」；A 出口提示词没有主体 | 标题是**信息**不是标签（"增长曲线"是标签，"一年 8 倍不靠补贴"是信息） |
| `kicker` | 三出口 | 选 | 少一行眉标，不影响成立 | 页眉小字，A/B/C 都认 |
| `lede` | A / B | 选 | P3（lede 复述标题）无从判——**这一条会静默失效** | 标题下的一句理由/代价；⛔ 不复述标题 |
| `points` | 三出口 | **必** | P8 判「正文太薄」；B 出口 `<li>` 为空；A 出口提示词缺证据 | 3-5 条，每条带具体数字或具体名词。spec 里叫 `items` |
| `visual` | A 出口 | A 必 | A 出口的生图提示词缺画面描述，出图全凭模型猜 | 主体、构图、色调、留白。不写字体名，写外观 |
| `notes` | B / C / A(notes.json) | 选 | 演讲者模式/备注页为空 | 讲稿，150-300 字；口语；只有提示信号，不是逐字念稿。**C 出口写进 PowerPoint 备注页，⛔ 绝不上正页** |
| `captions` | C | 选 | 要点下面没有小注 | 与 `points` 一一对应的正页小注（一行）。⛔ 不是 `notes`：讲稿和观众可见的小注是两件事 |
| `refs` | 三出口 | 有数字时必 | P5 判「数字无出处」 | 数据来源/素材路径。spec 里叫 `source` |

**必填的最小集**：`type` + `title`（所有页型）；要论据的页型再加 `points`。
B 出口再加 `layout`，A 出口再加 `visual`。

缺 `type` / `title` / `points` 时 `check-prose.py` 报 **P0** 红（2026-11-23 补的真闸；
此前这里写「缺必填 P8 会红」是句假话——P8 只查字数，缺 `title` 会用 H1 兜底，
缺 `points` 只要 `title+lede` 满 30 字就不响）。
封面 / 收尾 / 引用 / 染层页**不要求** `points`——它们本来就靠一个数或一句话成立。
`archetype` 与 `layout` 仍然**没有闸**——靠人守。

### 字段别名（markdown ↔ spec）

正本是 markdown，`export-pptx.py` 吃 JSON。两个名字指同一件事，`check-prose.py` 的 `FIELD_ALIAS` 负责映射：

| pages/NN.md | spec.json |
|---|---|
| `points` | `items` |
| `refs` | `source` |

⛔ 改这张表就是改契约（库级铁律 §2.18）：`export-pptx.py` 认的是右列。

### type 词表（⚠ 三套并存，待收口）

当前库里有三套 `type` 词表，**互不完全重合**：

| 出处 | 词表 | 谁认 |
|---|---|---|
| `scripts/export-pptx.py` 的 `PAGES` | cover / bullets / kpi / end / comparison / timeline / table / quote / chart / wash | C 出口（硬校验，不认就 exit 2） |
| `assets/layouts/_families.json` | cover / section / end / text / quote / code / compare / charts / image / image-set / process / diagram / data / toc / ring / split / quiz | B 出口（17 族） |
| 本表旧版写的 | cover / section / content / data / quote / closing | **无任何脚本认** |

`content`、`closing` 两个词在两套真词表里都不存在。⛔ 写 `content` 会让 C 出口直接 exit 2。
**当前建议**：B 出口写 `_families.json` 的族名，C 出口写 `PAGES` 的键；两者都写不出的页，先回 `outline.md` 改页型。
收口方案待定（见 `SKILL.md` §还没验的）。


## 派生关系（别搞反）

```
pages/NN.md  ──┬─→ prompts/NN-slide-{slug}.md   （A：加 STYLE_INSTRUCTIONS + base-prompt）
               ├─→ <section class="slide"> … </section>（B：按 layout 组版式，points→列表）
               └─→ 页规格（C：type/layout/points/notes 映射到 ppt-master 的页 job）
```

**A 出口的 prompt 文件不复制 `pages` 的全部字段**：它只取 `title/kicker/points/visual`，加上 `outline.md` 的 `<STYLE_INSTRUCTIONS>`，按 `base-prompt.md` 的骨架拼装。这样换生图后端不用重写内容。

## 硬约束

1. **页数与大纲一致**：`outline.md` 说 N 页，`pages/` 就必须正好 N 份；增删页要先改大纲。
2. **编号从 01 连续**：不留空号；增删后重排 `NN`，但 `slug` 不动（引用与讲稿不会错位）。
3. **文件名唯一**：`NN-{slug}.md` 里的 slug 在同一份 deck 内不得重复。
4. **一页一个信息点**：`title` 说结论，`points` 是证据。两条并列结论就拆两页。
5. **不编数字**：拿不到的数据写成 `TODO(数据)` 并在交付摘要列出，不许填看起来合理的数。
6. **notes 不上面**：讲稿只进 `notes` 字段（B 出口进 `.notes`，A 出口进 `notes.json`，C 出口进备注页），绝不写进正页。
7. **⛔ 不手写 spec.json**：它是派生件。要喂 `export-pptx.py` 就跑
   `python3 scripts/check-prose.py pages/ --emit-spec deck.json`，机器生成。
   手写一份＝第二份正本＝库级铁律 §2.6 那颗炸弹。

## 复用与重出

- 单页重出：`--regenerate 3` 或 `3,7`；B 出口改完对应 `<section>` 重新打包；C 出口回引擎改该页。
- 换出口：`pages/` 不动，只重跑目标出口的渲染步骤（这是三出口最大的省事点）。
- 换风格：改 `outline.md` 的 `<STYLE_INSTRUCTIONS>`，然后**全量**重出，不要逐页硬改。
