# Presentation Analysis Framework

Deep content analysis for effective slide deck creation.

> Exit-agnostic：本框架在 Brief 阶段跑一次，结果供 A/B/C 三个出口共用。分析结论写进 `analysis.md`，其中 **archetype** 与 **exit 建议** 是 来雪亭Lesciotia 在原框架上新增的两项。

## 目录

- `0. Archetype 与出口判定（先做，30 秒）`
- `1. Message Hierarchy`
- `2. Audience Decision Matrix`
- `3. Visual Opportunity Map`
- `4. Presentation Flow`
- `5. Content Adaptation`
- `6. Analysis Checklist`

## 0. Archetype 与出口判定（先做，30 秒）

**Archetype**（页序骨架，详见 `archetypes.md`）：按交付目的而不是题材定——

| 目的 | archetype | 典型信号 |
|---|---|---|
| 教 | `course` / `tech-talk` / `explainer` | 讲义、培训、教程、科普、讲清 |
| 说服 | `pitch` / `launch` | 融资、招商、发布、demo day |
| 交代 | `weekly` / `review` | 周报、进展、复盘、评审、决策 |
| 证 | `research` | 研究、白皮书、答辩、实验 |

**Exit 建议**（只是建议，最终由 Step 2 确认）：

| 内容特征 | 建议出口 |
|---|---|
| 阅读/传播为主、视觉说了算、无模板约束 | A 影像 |
| 要上台讲、要动效、要讲稿 | B 网页 |
| 文本要被改、要套母版、要原生动画 | C 可编辑（先验引擎门） |

两者都判不出时，写 `archetype: review`（最通用的骨架）+ `exit: image`，并在确认门里让用户定。

## 1. Message Hierarchy

Identify the core message structure before designing slides.

### Core Message (One Sentence)
- What is the single most important takeaway?
- If the audience remembers only one thing, what should it be?
- Can you state it in ≤15 words?

### Supporting Points (3-5 Maximum)
- What evidence supports the core message?
- What sub-topics must be covered?
- Prioritize by audience relevance, not source order

#### 独立性：并列会伪造证据数量

三条支撑里如果有两条其实是同一件事换个说法，排成并列就变成「看起来有三条证据，实际只有两条」。
读者数条目，不数论据——**并列本身就是一种声称**。

每条支撑点落进 `pages/NN.md` 的 `points` 之前，问一句：

> 把这条删了，剩下那几条的说服力会降吗？

- 会降 → 它是独立的一条，留着。
- 不会降 → 它是另一条的变体。**合并**，或把它降为那条的状语，⛔ 不并列。

| 形态 | 例 | 处理 |
|---|---|---|
| 同一数字换单位 | 「省了 40% 工时」＋「每人每天省 3 小时」 | 合并成一条，选信息量大的那个 |
| 同一事实换主语 | 「三个厂在用」＋「客户包括 A、B、C」 | 合并 |
| 因果拆两半 | 「数据不通」＋「所以推不动」 | 合并成「推不动，卡在数据」 |
| 真独立 | 「省的是巡检工时」＋「拦住推广的是数据」 | 两条都留——它们各自能单独被推翻 |

⚠️ 这不是要求每条都不同维度。**同一维度的两个不同事实是独立的**（「周活 12K→96K」与「付费转化 4.7%」都是增长，但删任一条都会少一个证据）。判据是「删了会不会降」，不是「像不像」。

⚠️ 找不到重复时，明写「三条独立」，⛔ 不硬凑一条合并。

### Call-to-Action
- What should the audience DO after viewing?
- Is it clear, specific, and achievable?
- Where does it appear (slide position)?

## 2. Audience Decision Matrix

| Question | Analysis |
|----------|----------|
| Who is the primary audience? | [Role, expertise level, relationship to topic] |
| What do they currently believe? | [Existing knowledge, assumptions, biases] |
| What decision do we want them to make? | [Specific action or conclusion] |
| What barriers exist? | [Objections, concerns, missing information] |
| What evidence will convince them? | [Data types, credibility sources, emotional hooks] |

### Audience Adaptation

| Audience Type | Content Focus | Visual Treatment |
|---------------|---------------|------------------|
| Executives | Outcomes, ROI, strategic impact | High-level, clean, data highlights |
| Technical | Architecture, implementation, specs | Detailed diagrams, code, schematics |
| General | Benefits, stories, relatability | Visual metaphors, simple charts |
| Investors | Market size, traction, team | Growth charts, milestones, comparisons |
| Learners | Step-by-step, examples, practice | Progressive reveals, exercises |

## 3. Visual Opportunity Map

Identify which content benefits from visualization.

### Content-to-Visual Mapping

| Content Type | Visual Treatment | Example |
|--------------|------------------|---------|
| Comparisons | Side-by-side, before/after | Feature comparison table |
| Processes | Flow diagrams, numbered steps | Workflow illustration |
| Hierarchies | Org charts, pyramids, trees | Organizational structure |
| Timelines | Horizontal/vertical timelines | Project milestones |
| Statistics | Charts, highlighted numbers | Key metrics with context |
| Concepts | Icons, metaphors, illustrations | Abstract idea visualization |
| Relationships | Venn diagrams, networks | Ecosystem or dependencies |
| Lists | Structured grids, icon rows | Feature bullets with icons |

### Visual Priority

Rate each piece of content:
- **Must Visualize**: Complex data, key differentiators, memorable moments
- **Should Visualize**: Supporting evidence, secondary points
- **Text Only**: Simple statements, transitions, minor details

## 4. Presentation Flow

Structure for impact and retention.

### Opening (First 2-3 Slides)

| Element | Purpose |
|---------|---------|
| Hook | Capture attention (surprising stat, question, story) |
| Context | Why this matters now |
| Preview | What audience will learn/gain |

### Middle (Content Slides)

| Pattern | When to Use |
|---------|-------------|
| Problem → Solution | Introducing new products/ideas |
| Situation → Complication → Resolution | Complex business cases |
| What → Why → How | Educational content |
| Past → Present → Future | Transformation stories |
| Claim → Evidence → Implication | Data-driven arguments |

### Closing (Final 2-3 Slides)

| Element | Purpose |
|---------|---------|
| Synthesis | Tie back to core message |
| Call-to-Action | Clear next steps |
| Memorable Close | Resonant quote, image, or statement |

### Transitions

- Each slide should answer: "What comes next?"
- Use narrative connectors between sections
- Build logical progression, not topic jumps

## 5. Content Adaptation

Decide what to keep, transform, or omit.

### Keep (High Value)
- Core arguments and evidence
- Unique insights or data
- Audience-relevant examples
- Memorable quotes or statistics

### Simplify (Medium Value)
- Technical details → Visual summaries
- Long explanations → Bullet hierarchies
- Multiple examples → Best 1-2 examples
- Background context → Brief framing

### Visualize (Transform)
- Data tables → Charts or highlighted numbers
- Process descriptions → Flow diagrams
- Comparisons in text → Side-by-side visuals
- Abstract concepts → Concrete metaphors

### Omit (Low Value)
- Tangential information
- Redundant examples
- Excessive caveats
- Background the audience already knows

## 6. Analysis Checklist

Before outline creation, confirm:

### Message Clarity
- [ ] Core message stated in one sentence
- [ ] 3-5 supporting points identified
- [ ] **每条支撑点过了「删了会降吗」这一问**（并列的变体已合并）
- [ ] Call-to-action defined

### Audience Fit
- [ ] Primary audience identified
- [ ] Existing beliefs mapped
- [ ] Desired decision clear
- [ ] Evidence matches audience needs

### Visual Planning
- [ ] Key visualizations identified
- [ ] Chart/diagram types selected
- [ ] Visual priority assigned

### Flow Design
- [ ] Opening hook defined
- [ ] Middle pattern selected
- [ ] Closing approach planned
- [ ] Transitions considered

### Content Decisions
- [ ] Keep/simplify/visualize/omit applied
- [ ] Source material fully processed
- [ ] No important content overlooked
