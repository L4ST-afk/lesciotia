# 工作流（Step 0–9 的判据正文）

> 主文件只列清单与一行判据，细节在本卷。**每一步的出口条件都在这里**，判「这一步算不算过」时读本卷。

## Step 0 · 读配置

按序找第一个命中的文件，读到就打印摘要（默认出口/风格/受众/语言/评审开关）：

| 路径 | 作用域 |
|---|---|
| `.来雪亭Lesciotia/EXTEND.md` | 当前项目 |
| `${XDG_CONFIG_HOME:-$HOME/.config}/来雪亭Lesciotia/EXTEND.md` | 用户级（XDG） |
| `$HOME/.来雪亭Lesciotia/EXTEND.md` | 用户级（老路径） |

没有就按默认走，首次使用不阻塞。字段见 `preferences-schema.md`。

## Step 1 · 分析内容

按 `analysis-framework.md` 做六件事：核心信息一句话、受众、语言、信号词、页数区间、**archetype 判定**（表见 `archetypes.md`）。
产出：`analysis.md`（topic / audience / signals / archetype / 推荐风格 / 推荐页数 / 语言 / slug）。
同时把原始内容存成 `source-{slug}.{ext}`。

**判型**：随手跑 `scripts/pick-recipe.py --detect <原稿>`，把结果写进 `analysis.md` 的 type 行（briefing/proposal/
teaching/retro/launch）；两型都对就记两型，Step 5.5 分页时明说换型。细则见 `prose-recipes.md`。

**页数启发式**：<1000 词 5-10 页；1000-3000 词 10-18；3000-5000 词 15-25；>5000 词 20-30（再多就拆成上下篇）。archetype 自带的页序比这个区间优先级更高。

**已有产物检查** ⚠️：若 `slide-deck/{slug}/` 已存在，先问怎么处理（重出大纲 / 重出图 / 备份后重出 / 退出），选项见 `confirmation.md`。

## Step 2 · 确认门 ⚠️ 必须

一次批量问六个问题（选项原文见 `confirmation.md`）：**出口形态 / 风格 / 受众 / 页数 / 是否评审大纲 / 是否评审逐页记录**。
问之前先说清四件事：内容类型 + 主题、识别到的语言、推荐风格（依据信号词）、推荐页数（依据长度与 archetype）。

Round 2（仅当风格选了「自定义维度」）：再批量问 texture / mood / typography / density，四答案替换 preset（第二轮文案见 `confirmation-more.md`）。
确认后把最终选择回写 `analysis.md`，并记下两个评审开关。

## Step 3 · 出大纲

风格 → `styles-<preset>.md`；自定义维度 → 组合 `dimensions-*.md`。
按 `outline-template.md` 写 `outline.md`：头部元信息（含 **Exit** 与 **Archetype**）+ `<STYLE_INSTRUCTIONS>` 块 + 逐页条目（页模板见 `outline-slide-templates.md`）。
`STYLE_INSTRUCTIONS` 是后续所有出口的风格唯一真源，后面只引用它，不再回头读风格文件。

`--outline-only` 到此为止；`skip_outline_review` 跳过 Step 4。

## Step 4 · 评审大纲（条件）

展示「# | 标题 | 页型 | 版式」表 + 总页数 + 解析出的风格。问：继续 / 先改大纲 / 重出。
选「先改」就让用户改 `outline.md`，改完再问一次；选「重出」回 Step 3。

## Step 5 · 出逐页记录

每页写一份 `pages/NN-{slug}.md`（字段规范见 `page-record.md`）：页型、archetype、版式（B 用）、画面（A 用）、要点、讲稿。
**这份记录是唯一正本**；A 出口的 `prompts/NN-slide-{slug}.md` 由它派生（把画面 + STYLE_INSTRUCTIONS 拼成生图提示词），B 出口的 HTML 片段、C 出口的页规格都从它读。

`--pages-only` 到此为止；`skip_pages_review` 跳过 Step 6。

## Step 5.5 · 成稿闸（每次出片前）

逐页记录写完就自查文字密度——**直接喂正本，不用手抄 spec**：

```bash
python3 scripts/check-prose.py pages/            # 目录或单个 NN-*.md 都认
python3 scripts/check-prose.py pages/ --strict   # 警告也当红
```

细则九条见 `prose-gate.md`。按判定的型写（`pick-recipe.py --show <型>` 出提示词），
红一条就回去改文字，**别指望版式救**；改到 `可以出片` 再出片。

C 出口要 spec.json 时，由闸门派生，⛔ 不手写：

```bash
python3 scripts/check-prose.py pages/ --emit-spec deck.json
```

`export-pptx.py` 出件前会再跑一遍同样的闸，红即拒（`--allow-prose` 才放行，且摘要里留记录）。
三件反例在 `examples/prose/`。

## Step 6 · 评审逐页记录（条件）

展示「# | 页标题 | 页型 | 版式」索引，问：继续 / 先改记录 / 重出。分支同 Step 4。

## Step 7 · 渲染（按出口）

| 出口 | 去做 |
|---|---|
| A | `path-a-image.md`：派生 prompts → 逐页生图 → merge to pptx/pdf |
| B | `path-b-html.md`：选主题+版式 → 写 `index.html` → `build-deck.py` 单文件化 → 截图核验 |
| C | `path-c-editable.md`：转 plan 交 ppt-master → 回读核验 |

混合（A+B 都要）：先出 HTML（结构定稿），再按同一 pages 记录出图，图与 HTML 页序必须一一对应。

## Step 8 · 质检门

逐页过 `qa-checklist.md` 的 13 条（通用 11 条 + 出口专属 2 条）。**任一页不过就不算完成**；能自动查的用脚本查（B 出口的单文件自检由 `build-deck.py` 自带，A 出口的页数与图片数由 merge 脚本自带）。
每条质检必须留下**证据**（截图路径、脚本 `--json` 摘要、或回读出的页数）；没有证据的那条只能记「证据不足」，不许记「通过」——「能交/不能交/没验到」的三种答法见 `qa-checklist.md` 开头。

## Step 9 · 交付摘要

模板：

```
Deck 完成
主题：<topic>    archetype：<course/pitch/...>
出口：A 影像 / B 网页 / C 可编辑 PPTX
风格：<style>（四维：texture+mood+typography+density）
位置：slide-deck/<slug>/
页数：N（与 pages/ 份数、产物张数三方一致：✓）
结论：能交 / 不能交（哪页哪条）/ 没验到（哪几条、怎么验）

交付：
- <slug>-single.html      （B）
- <slug>.pptx / .pdf      （A）
- outline.md / pages/NN-*.md（正本，可复现）
质检：<逐条通过数>/12，证据见 qa/ 与脚本 JSON 摘要；未取证项列在「证据不足」
```

**摘要里不许出现「13/13 通过」而无据**：三种答法与范围句的唯一正本见 `qa-checklist.md`。
