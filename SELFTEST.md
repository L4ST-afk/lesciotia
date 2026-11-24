# 自检记录（SELFTEST）

实测日期 2026-11-10，本机 macOS / python3.14 / Google Chrome / python-pptx 1.0.2 + Pillow。**只记录跑过的命令与看到的产物**；没跑过的不写。

## 版本号归属登记（2026-11-24 收口）

并行两条线各用各的号，现状是：**1.2.55＝本线**（模度四色自备＋预览件字体子集化）；
**1.2.56／1.2.57＝另一批**（多图一页 figures、窄图第五式 image-phone，提交 `48f67dec` 自称 1.2.57）。
本条只记归属与要点，⛔ 不复制对方正文。`SKILL.md` 的 `version:` 已抬到 **1.2.57**（取已完成版本里的最高号）。
此后规矩：谁改谁报号，改动前先 `git log --oneline -8` 看有没有被人先用了。

## 1.2.55（2026-11-24 晚）模度阶梯四色改为「各瓦作自备」

**撞号登记**：`1.2.52`／`1.2.53` 各被两条并行线用过（本线=边角＋排障；另一批=md2deck --pptx／C 出口 figure）。
历史两段都留着；此后从 **1.2.55** 续（1.2.54 留给另一批）。

**改动**：`gen-theme-preview.py` 新增 `MOD_SCALE` 九主题四色 + `apply_mod_scale()`，覆盖模板的墨色阶兜底
（兜底留在模板当安全网）。第 1 档一律取该主题主色（最长条＝最重）。

**两个「闸门绿但页面错」的坑**：① 第 1 档必须写 `.ms:nth-child(1) i`——裸 `.ms i` 优先级低于各主题旧 override，
暗色版 100 条仍是旧奶白；② 插入点用 `s.index('</style>')` 而不是 `rindex`——番禺路页里有游离的 `</style>`，
`rindex` 会把 CSS 当正文打印到页顶。

**体积（同日补充）**：用户指的那类扩展查实为本机 Chrome 的 **SingleFile 1.39.0**（含 SingleFileZ 自解压件）。
照它做原型（整页 gzip+base64+`DecompressionStream`自解压）headless 渲染正常但只省 20%（字体 base64 已是 woff2）。
真杠杆是字体子集：新增 `--subset-fonts`，九份 56.4 MB → 8.1 MB（fuzhou 11.07→1.02 MB）。闸门 PASS 9/0/0；
截图核 福州路／龙华寺（龘体）／万航渡 无掉字。坑：`base64` 未导入会静默走「保留原字库」分支。

## 0. 前置条件：闸门依赖（2026-11-23 补）

`selftest.py` 与几道判据级闸门要四个第三方包。**缺包不会报「缺包」**——它会一路等子进程超时，
看起来像死循环（2026-11-23 实测：缺包时 selftest 静默 120 秒无输出，装齐后 3 分 06 秒跑完 9 PASS / 0 FAIL）。

| 包 | 谁要它 | 缺了会怎样 |
|---|---|---|
| `fonttools` | `check-fonts.py` | F1/F7 读不了 woff2，字体闸报 WARN（不是 FAIL，容易漏看） |
| `brotli` | `check-fonts.py` | 同上——woff2 解压要它，只装 fonttools 不够 |
| `lxml` | `check-wash.py` → `wash_bridge.py` | 瓦作翻译闸基线直接 traceback，曲线布尔判据被跳过 |
| `python-pptx` | `export-pptx.py` / `pptx-to-html.py` | morph 夹具造不出来、pptx-to-html 跑不起来 |

**系统 Python 装不上**（macOS 的 PEP 668 会拦 `pip install --user`）。venv 建在 **skill 目录外**：

```bash
python3 -m venv ~/.venvs/lesciotia
~/.venvs/lesciotia/bin/pip install fonttools brotli lxml python-pptx
cd <本 skill 目录>
~/.venvs/lesciotia/bin/python scripts/selftest.py; echo "EXIT=$?"   # 期望 9 PASS / 0 FAIL、EXIT=0
```

⛔ **不要把 venv 建在 skill 目录里**（`.venv/`）。`selftest.py` 的「库内不得有符号链接」判据会红：
venv 的 `bin/python*` 全是指向系统解释器的软链，打包分发后必断。2026-11-23 实测踩到，已改到库外。

跑闸门一律用 `~/.venvs/lesciotia/bin/python`，别用系统 `python3`。

## 1. B 出口 · 单文件打包（含写后回读）

```bash
python3 scripts/build-deck.py index.html -o out.html --json
```

| 判据 | 结果 |
|---|---|
| 内联资源数 | 5（fonts.css / base.css / themes/swiss-grid.css / animations.css / runtime.js） |
| 产物体积 | 76,315 B |
| **回读**校验（在落盘后的文本上重算） | 残留本地 link/script 0；含 `class="slide"`；`data-from=` 计数 = 内联数 5；体积 < 8MB |
| 机器可读摘要 | `{"ok": true, "skipped": false, "out": ".../out.html", "bytes": 76315}` |
| 幂等：再跑一次 | `= 已存在，跳过`，exit 0（不覆盖） |
| `--force` 覆盖 | 先留 `out.html.bak-20261110-164151`，再写新件 |
| `assets/` 前缀（不带 `../`） | 同样解析成功（5 个内联，75 KB） |

## 2. B 出口 · 逐页截图

```bash
bash scripts/render-png.sh selftest.html all png
```

- 首版曾报 **6 页**（实际 5 页）：内联 `runtime.js` 的注释里有一行 `<section class="slide" data-no-logo>`，被 `grep` 多数一页。
- 修法：`count_slides` 改为先用 python 剥掉 `<script>` 块再数。修后 **5 页，exit 0**。
- 产物 `png/selftest_01..05.png`，均 1920×1080；肉眼核验封面与双栏对比页无溢出。
- 幂等：目标 PNG 已存在且非空 → `= 已存在，跳过`；`FORCE=1` 才重截。

## 3. 暗色主题不塌

同一份 deck 换 `tokyo-night` 重打包 → 74 KB；截图核验深底浅字、渐变标题、页码 chrome 正常，对比度可读。

## 4. A 出口 · PNG → PPTX（回读核定）

```bash
python3 scripts/merge-to-pptx.py slides --notes slides/notes.json --force --json
```

| 判据 | 结果 |
|---|---|
| 页数 / 尺寸 | 5 页；13.33×7.50 in（首图 16:9 自动推导） |
| **回读**（重开 pptx 数页与图片形状） | 5 页、每页 1 个 PICTURE，与 PNG 数一致 |
| 备注写回 | `notes.json` 命中第 1、3 页，回读文本正确 |
| 页号断档（只有 01、03） | 拒绝：`✗ 页号不连续：[1, 3]`，exit 2 |
| 幂等 / `--force` | 已存在则跳过；覆盖前留 `slides.pptx.bak-<时间戳>` |

## 5. A 出口 · PNG → PDF（一次真实的假红）

```bash
python3 scripts/merge-to-pdf.py slides --force --json
```

- 第一版回读报 **`✗ 回读页数不符：6 != 5`**：`/Type /Page` 把页树节点 `/Type /Pages` 也算进去，多报一页。
- 修法：页对象数 = `count('/Type /Page') - count('/Type /Pages')`（两种写法都算）。修后 **5 页，exit 0**，字节 297,510。
- 这也说明「回读」的价值：文件一直是好的，是**判据**错了——只看退出码就会把假红当真失败，或反过来把真失败当成功。

## 6. C 出口 · 引擎恢复（本次的真实事故）

现象：`python3 <ppt-master>/scripts/attribution_guard.py` 返回 **78**（integrity check failed）。

诊断（导入 guard 内部函数逐项判定，不绕过）：

| 不变量 | 结果 |
|---|---|
| frontmatter 固定身份字段（copyright/license/repo/sponsors/gate marker） | 通过 |
| 9 个路由脚本的活体 guard 调用 + `console_encoding.py` 的二级闸 | 通过 |
| 归属文件 `LICENSE` / `SPONSORS.md` / `SPONSORS_CN.md` | **`LICENSE` 缺失**（其余在） |

进一步比对官方 `v6.7.2` 的 git tree：官方 `skills/ppt-master` 有 **13,018 个文件**，本地只有 **567 个**——这是一份被删过资产的残本（缺 12,452 个，多为 references 配图与 templates 品牌素材）。

修复（可回滚）：

1. 现状备份到 `_archive/20261110-ppt-master-trimmed/`（12MB）。
2. 从 GitHub 取官方 `v6.7.2` 源码包（tar，避开 zip 的中文名编码问题），`rsync -a` 合入 skill 目录（不删本地独有的 `VAX-NEEDED.md`）。
3. 校验：官方 LICENSE 的归一化 sha256 = `80cefc23…0921`，与 guard 内置摘要**一致**。

结果：`attribution_guard.py` → **exit 0**；`svg_quality_checker.py --help`、`project_manager.py --help` 正常启动（这两个入口都带 guard 调用）；文件数 13,019（官方 13,018 + 本地 `VAX-NEEDED.md`）。

**遗留缺陷（同日发现，第 13 节修掉）**：第 6 节修好引擎之后，`references/path-c-editable.md` 的 C0 还留着「返回 78 ⇒ C 出口当前不可用」，两边自相矛盾。出口路由读的是 path 文档，于是「要可编辑 pptx」被降级成 A 的位图合图——产物后缀、页数、能不能打开全对，只有形状层是错的。

⚠️ 体积：补齐后 ppt-master 是 **78MB / 13,019 文件**（guard 要求的完整分发，2026-11-10 读数）。2026-11-10 已整体迁到 `~/Library/CloudStorage/坚果云-tsingford@qq.com/Ob/Kroma/ppt-master`，仓库内 `skills/ppt-master` 只留**软链指针**；经软链跑闸门仍 exit 0，`svg_quality_checker.py --help` / `project_manager.py --help` 照常起。
⚠️ **2026-11-14 重测**：`find -L skills/ppt-master -type f | wc -l` = **13,117**（引擎自身有增补）。⛔ 别拿 13,019 当当前值——文件数不是判据，**C 能不能用只认 `attribution_guard.py` 当次退出码**。另注：`find` 不跟软链，量这个目录必须带 `-L`，否则返回 0（本轮踩过）。

## 7. 疫苗与结构闸

```bash
python3 <judgement-skill>/scripts/vaccinate.py .            # 14/14（`<judgement-skill>` 见 SKILL.md 说明；没装跳过）
python3 <judgement-skill>/scripts/vaccinate.py . --upgrade  # vaccineVersion: e8d93bf0731f
python3 <judgement-skill>/scripts/check_limits.py .          # 无硬超限
```

- 疫苗 **14/14**：V1 体量预算、V2 引用只一层、V5 写操作门禁、V6 写后回读、V7 基线不落临时目录、V8 写入幂等、V9 生成背景、V10 失败样本三要素、V11 non-goals、V12 腐化信号、V13 反例优先。
- `--version` 校验一致（`e8d93bf0731f`）。

## 8. 结构变更（为过 V1/V2 做的重构）

- **引用扁平化**：`styles/` `dimensions/` `paths/` `config/` 四个子目录并入 `references/` 顶层（`styles-<key>.md`、`dimensions-<name>.md`、`path-a-image.md` / `path-b-html.md` / `path-c-editable.md`、`preferences-schema.md`），SKILL.md 逐份列出全部 42 个文件名（1.1.0 时点；2026-11-14 为 **44** 份，SKILL.md 的清单与目录已逐份双向对齐）。
- **三份超 200 行的拆开**：`confirmation.md`(211) → 97 + `confirmation-more.md`(127)；`design-guidelines.md`(208) → 102 + `design-visual.md`(120)；`outline-template.md`(271) → 160 + `outline-slide-templates.md`(130)。
- **补顶部目录**：`design-guidelines.md`、`dimensions-density/mood/presets`、`outline-template.md`、`path-b-html.md`，另给 `analysis-framework.md`、`archetypes.md` 补了目录。
- 结果：`check_limits.py` 无 ❌；当时 `SKILL.md` 338 行（软 400 / 硬 500）。**2026-11-10 第二版重构后 238 行、第三版后 244 行**，见第 12、13 节。

## 9. 引用与体量

- SKILL.md 与 references 内的本地引用审计：**缺失 0**（`references/**`、`assets/**`、`scripts/**` 逐条对文件）。
  ⚠️ **更正（2026-11-14）**：这条当时漏网了两处——`assets/full-decks/presenter-mode-reveal/README.md` 的快速开始照抄上游目录名（`templates/…` 而非本 skill 的 `assets/…`），末尾又指向一份本 skill 并不存在的 animations 参考卷；`assets/layouts/` 里 5 份版式引用 `assets/demo-images/*.svg` 而该目录当时不存在。两处已修（README 改本 skill 真实路径、补 7 份占位 SVG）。当时的审计只扫了 `SKILL.md` + `references/`，**没扫 `assets/` 内的 md 与 html**——判据覆盖面不够，不是「缺失 0」成立。现由 `scripts/check_doc_claims.py` 全目录扫。
- 目录 549 KB（SKILL.md + 43 references + 4 scripts + `assets/` 516 KB）。⚠️ 这是 2026-11-10 的 `du` 读数（含 4KB 块对齐）。
- **2026-11-14 重测（实际字节，排除 `__pycache__`，本轮末次读数）**：全目录 **621,531 B ≈ 607 KB** = assets 281,555 + references 164,726 + examples 76,331 + scripts 51,063 + 根文件 47,856（SELFTEST 在 §16 落笔前量，§16 自身未计入）；references **44** 份、scripts **7** 支（本轮 +1 = `check_doc_claims.py`）、SKILL.md **258 行 / 13,084 字符**（软限 400 行未触）。
- `examples/demo-deck.html` 76,331 B（改名导致 `<title>` 多 16 字节），是第 1–3 节的产物，双击可开。

## 10. 没验到的（别当已验）

**2026-11-10 那批已清空**：原登记的五条已全部验完并删除——演讲窗、双窗同步、真实生图、主题版式见第 14 节；C 出口完整出件见第 15 节。⛔ 本节**不是空表**：下面还有 11-14、11-16 两条在册，读的时候别只看这一行就以为「没有未验项」。

**2026-11-14 新登记**：C 出口外部引擎实测已升 **6.9.0**（ppt-master frontmatter），第 15 节的 3 页出件读数是 6.7.2 时期——引擎升级后未重跑。用 C 出口时按 SKILL.md 口径**每次现场跑闸门**，⛔ 别拿第 15 节读数当当前可用性。

**2026-11-16 新登记**：从三个豆包内置 PPT skill 吸收的规则（权属 / 素材标准 / 附件权威 / 变更清单 / 残留检查 / 样式继承 / 页码漂移 / 完成标准，见 `content-rules.md` §5–8、`modification-guide.md` 变更控制、`qa-checklist.md` 完成标准）只过了四道静态闸，**未在真实改版件 / 真实素材外发场景跑过**。怎么验：下次改已有 pptx/网页稿时走一遍变更清单 → 残留检查 → 页码漂移映射；下次带人物 / 商标 / IP 素材时核对权属提醒与确认口径。验过即删本条。

**2026-11-16 新登记**：新风格键 `curio-cabinet`（`styles-curio-cabinet.md`）只过静态闸，**未出真实样例**，封面 / 正文 / 数据三类页在该风格下是否不塌未验；B 出口复用 `soft-pastel` 近似，mood/typography 落地度未核。怎么验：下次教学卡片 / 生活方式类 deck 选该键，出 3 页样例过 qa 组 1 三类页。验过即删本条。

**2026-11-16 新登记**：`design-guidelines.md` Type Scale 的角色参考档位表（宽幅 16:9 PPTX、33.87×19.05cm 口径：眉标 10.5b / 页标题 29b / 窄卡说明 12 / 横排正文 14–16 / 表格表头 10b、单元格 10.5 等）只在毛里求斯泳衣品牌 v4.8 一份投资人 deck 上实测标定，**跨风格键、跨受众（beginners / experts）、跨出口（B 出口 1920×1080 px 口径）未复跑**；表内 pt 是该画布落点，换画布须按 `qa-checklist.md` #4 px 地板等比换算，⛔ 别把 pt 值搬到 HTML 出口。怎么验：下次另一份 deck 定角色档位表时对照本表取档，出封面 / 内容 / 数据三类页截图核层级；B 出口复核 px 地板不被本表 pt 带偏。验过即删本条。

规则保留：新发现的「没验的」写进本节，验过就删、把读数补进对应小节，⛔ 别留「大概能用」。

## 11. 待办（要用户拍板）

1. ~~`AGENTS.md` 技能计数~~ 已改：271 → 205，`check_agents_wiring.py` exit 0。
2. 宿主入口若是指向 skills 根目录的整目录软链，改名后自动跟随，无需再挂。
3. 库里 6 个重叠件仍原样保留；`VAX-NEEDED.md` 仍在 ppt-master 目录（那是库级疫苗缺口清单，不属于官方分发）。
4. ppt-master 已落在 Kroma、仓库内只留软链，**不进 git**。⚠️ 该软链依赖坚果云同步盘在本地可用；盘未登录或文件未下载时，C 出口会指向空路径（闸门会立刻报 78，不会静默降级）。

## 12. 第二版（1.1.0）· 两塔经验怎么落进来的

**先说错的那一步（失败样本）**：第一轮我把两塔的**制度形态**直接搬过来了——「交付结论只许三态」当标题、L0–L4 证据阶梯、`pending/` 待验证池加 90 天过期、自建 `check-structure.py` 结构闸。结果是：一个做 deck 的 skill 多出四套它用不上的治理装置，其中结构闸还与库里 `check_limits.py`、`vaccinate.py` 的 V2 重复。
缺的上下文是「两塔判的是学习与工程合规，本 skill 判的是产物能不能交」——判据可以借，机构不能借。重来改成：**只留能改善产物的那几条，其余按库里的现成尺走**。

| 两塔的做法 | 搬过来会变成什么 | 本 skill 最终落成什么 |
|---|---|---|
| 主文件只做路由 | — | `SKILL.md` 348 → 238 行，Step 0–9 细节进 `references/workflow.md`；风格表/archetype 表/改版表改成指针 |
| 结论只许三态 | 一套「达标/未达标/证据不足」的话术 | 收进 `qa-checklist.md` 开头的**能交 / 不能交 / 没验到**，并说清「截图看过只算目检」 |
| 证据阶梯 L0–L4 | 五级术语，读 deck 的人用不上 | 一句判据：截图＝目检，页数三方对齐/单文件无残留/文本真能改＝结构事实才算过 |
| 待验证池＋过期规则 | 多一个 `pending/` 目录和一套计时 | 只留一处：`SELFTEST.md` 第 10 节，加一列「怎么验」，验过即删 |
| 自建闸门 | 与 `check_limits`、V2 重复的第三把尺 | 撤掉，改跑现成的两条＋一条「引用悬空」grep（那两个脚本查不出悬空） |

**保留下来的都是能改产物的**：页数三方对账（来自「产物为证」）、体量双限与同轮下沉、反例优先段、`SELFTEST` 只记跑过的、交付摘要写出没验到的。

**实测**：

```bash
python3 <judgement-skill>/scripts/check_limits.py .   # exit 0，❌ 计数 0
python3 <judgement-skill>/scripts/vaccinate.py .      # 14/14（vaccineOrigin: local 严格档）
python3 -m py_compile scripts/*.py && bash -n scripts/render-png.sh   # 全过
grep 悬空审计                                        # 无输出
```

## 13. 第三版（1.1.1）· C 出口恢复 + 可编辑性变成机器判据

**现象（用户报告）**：来雪亭产出的 pptx 全是位图，字改不了。

**根因**（不是渲染坏，也不是引擎坏）：引擎当天已修好（`attribution_guard.py` exit 0），但 `references/path-c-editable.md` 的 C0 还挂着旧读数「返回 78 ⇒ C 出口当前不可用」。路由读的是 path 文档 ⇒ 每一次「要可编辑」都走降级路 A ⇒ `merge-to-pptx.py` 逐页贴图，产出每页一张全幅图的 pptx。**后缀对、页数对、双击能打开，只有形状层是错的**——没有一条判据读它。

**修法三条**：

1. `path-c-editable.md` 的 C0：判据改成「只认**当次**退出码」，旧读数明确标注为历史；补复测记录（exit 0 两连、`LICENSE` sha256 `80cefc23…0921` 与闸门内置值一致）。
2. 新增 `scripts/verify-pptx-editable.py`：读形状层——每页文本形状数 ≥1、且不存在「图片占页 ≥90% 且无文本」的整页位图；exit 0 才算可编辑。
3. 接线：`SKILL.md` 脚本表 + 分流表、`qa-checklist.md` C-11 与自动段、`path-c-editable.md` C3-1 与新增 C3.5；主文件加一句「文档里的旧读数不是当前状态」。

**实测（2026-11-10）**：

```bash
# 引擎闸门（当次）
python3 skills/ppt-master/scripts/attribution_guard.py        # exit 0（连跑两次 0）
# C 出口最小复现：1 页 SVG → 原生 pptx
python3 <ppt-master>/scripts/svg_quality_checker.py /tmp/pptx-probe --canonical-authoring --stage final --json  # 0 blocking，WARN
python3 <ppt-master>/scripts/svg_to_pptx.py /tmp/pptx-probe
# → exports/pptx-probe_20261110_173111.pptx（POSTFLIGHT status=passed-with-warnings）
```

| 对象 | 形状层读数 | `verify-pptx-editable.py` |
|---|---|---|
| C 出口原生件 | 3 shape：`TEXT_BOX` ×2（`LEI-EDITABLE-PROBE`、`second text`）+ `AUTO_SHAPE` ×1；**picture 0** | **exit 0**，`✓ 可编辑` |
| A 出口合图件（`merge-to-pptx.py` 合成 2 页） | 每页 1 张 picture 铺满 100%、文本 0 | **exit 1**，两页均报「整页位图」 |

两侧都跑过 ⇒ 判据有区分力，不是恒绿。⛔ 单跑正例不算验（会分不出「检查器坏了但恰好过」）。

**体积**：SKILL.md 244 行 / 12,075 字符（软限 400 行未触）；references 无超 200 行项。

**边界**（别当已验）：本节点只验到「引擎可用 + 转换器出原生件 + 判据能红」。**完整出件（3 页从 `pages/NN.md` 走 generate-pptx 全流程）仍未跑**，仍列在第 10 节。

### 12.1 重构后的回归（用真成品件跑，不用测试桩）

输入：`assets/full-decks/weekly-report`（7 页，1.2.42 前的版本自带一份 `style.css`，该件已删、改由基座原语接管；当时的链接改写为 `../assets/`，`assets/` 用软链指回本 skill）。

| 步 | 命令 | 产物 / 读数 |
|---|---|---|
| 1 B 打包 | `build-deck.py deck/index.html --assets assets` | 84,872 B，内联 5（fonts/base/animations/style/runtime），残留本地链接 **0**，`{"ok":true}` |
| 2 截图 | `render-png.sh out.html all png` | **7 页**（不是 8——内联 runtime 注释没被当页），1920×1080，目检封面正常：logo / 周次 chip / kicker / 标题 / lede / 页码 1/7 |
| 3 A 合并 | `merge-to-pptx.py slides --json` | 7 页，13.33×7.50 in，回读**每页 1 张 PICTURE**；二次运行 exit 0（幂等跳过） |
| 4 A 合并 | `merge-to-pdf.py slides --json` | 7 页，451,659 B，`/Type /Page` 计 7（已减 `/Pages`） |

**这一轮撞到的接缝**（已写进 `path-a-image.md` A3 第 5 条）：把 `render-png.sh` 的 QA 图（`out_NN.png`）直接喂给 merge，会立刻 exit 2「没有 `NN-*.png`」——merge 只认 `NN-` 前缀。改名为 `NN-slide-*.png` 后 7 页一次通过。这属于「判据对、命名不对」，不是脚本坏。

## 14. 第四版（1.1.2）· 把「没验的」逐条验掉

**验法本身要能红**：每条都用「有明确读数」的手段，不靠「打开看了觉得没问题」。

### 14.1 S 键演讲者窗（真按了一次 S）

没有前台窗口可点，用 CDP 派发真实 `keydown`（`document.dispatchEvent`，key=`s`）。第一次派发没反应——因为监听挂在 `document` 上，我派发到了 `window`，事件不向下传；改到 `document` 后一次成功。

```
target 列表出现 ('page', 'Presenter View')
演讲窗读数：CURRENT 1/7 ｜ NEXT 2/7 ｜ SPEAKER SCRIPT · 逐字稿（本页无稿）｜ TIMER 00:02 ｜ SLIDE 1 / 7
```

⇒ 窗能开、页码对、计时在走、逐字稿区在。**截图见 `qa/` 之外的临时目录，未入库。**

### 14.2 `file://` 双窗同步（两臂）

| 臂 | 做法 | 结果 |
|---|---|---|
| A 同进程子窗（**这就是 runtime 的真实形态**） | `window.open('', 'html-ppt-presenter')` + `document.write` 子窗，通道名 `html-ppt-presenter-<pathname>` | **收到 31 次**回传 ⇒ 同步可用 |
| B 跨进程（两个 Chrome、不同 profile） | 同一 URL、不同 `--user-data-dir` | 收不到 → **属预期**，不同 profile＝不同存储分区，不是 bug |

### 14.3 新发现的限制：`file://` 下演讲窗预览是空白（三臂对照）

| 臂 | iframe 读数 | 画面 |
|---|---|---|
| `file://`（默认） | `ACCESS-DENIED` | CURRENT/NEXT **空白** |
| `file://` + `--allow-file-access-from-files` | `complete`、7 页、文字对 | 正常 |
| `http://127.0.0.1:8765` | `complete`、7 页、封面「Growth Squad W15…」/ 指标页「HIGHLIGHTS · KPIS…」 | 正常 |

根因是 Chrome 把每个 `file://` 页面当**不透明源**，父窗读不到子 iframe。不是我们改坏的，也不是键盘坏——讲稿、计时、页码、翻页都正常。已写进 `path-b-html.md` B6（含三条出路）与 `qa-checklist.md` B-12（「`S` 要在 http 下验」）。

### 14.4 A 出口真实生图（不再是占位图）

用真实后端出 1 页（同一份 `weekly-report` 封面）：

```
落盘：2730×1536，比例 1.777（16:9 = 1.778）
文字：`本周：付费转化率 / 回到了 3.8%` 清晰可读，页码 `1 / 7`、进度条位置正确
merge：1 页 13.33×7.50 in；PDF 1 页 167,333 B
```

⇒ **「生图 → 落盘 → 合并」这条链通了**，中文大字不糊。仍未覆盖「5 页小样 + 换后端复现」这一层。

⚠️ **验收口径更正（2026-11-14）**：上面把「页码 `1 / 7`、进度条位置正确」当成合格读数，**这条判据本身是错的**。A 出口明令生图里不得出现页码/页脚/logo——`base-prompt.md:21`「NO slide numbers, page numbers, footers, headers, or logos」＋17 份 `styles-<key>.md` 的 Don't 段＋`content-rules.md` 的 Footers 行，共 **19 份一致**；页码只由 B 出口 runtime 的 `.slide-number` 出。所以那一页的页码与进度条属于**应当返工的违规元素**，不是「位置正确」。本节其余读数（尺寸/比例/文字清晰度/合并页数）仍成立。

### 14.5 主题 × 版式全量渲染（当时主题 43 = 7 自建 + 36 软链；2026-11-20 起为 7 自建 + 1 指针）

把每个主题套进同一版式、每个版式用自己的默认主题，逐个 headless 截图，判据＝**方差 > 5 且墨迹占比 > 0.3%**（纯白页会被拦下）：

```
主题 41 + 版式 36 = 77 张，异常 0
样例：academic-paper var=422 ｜ arctic-cool var=663 ｜ aurora var=764, ink=0.99（深色底）
```

范围说清：只验到「都渲染出来了、不是空白」。**没有 77 张逐张目检**，版式内文字溢出仍要靠单页截图看。
⚠️ 2026-11-20 起 `assets/themes/` 只剩 7 件自建（36 条软链收成 `upstream` 目录指针），再跑这节应是 7 + 36 = 43 张主题、版式仍 36；判据不变。

### 14.6 顺带记一条页数判据的坑

`document.querySelectorAll('section.slide').length` 在 7 页 deck 上返回 **14**——`runtime.js` 为 `O` 总览克隆了一整套 slide。数页只认 HTML 源（剥 `<script>`）或 `data-total`，别用 DOM 总数。

## 15. 第五版（1.1.3）· C 出口 3 页完整出件

**路线**（按 ppt-master 自己的 Quick Generate，不跳步）：`project_manager.py init lx-c3 --quick-generate` → 手写 3 页 SVG 到 `svg_output/` → `notes/total.md` 经 `total_md_split.py` 拆成 3 份 → `svg_quality_checker.py --quick-generate --canonical-authoring --stage final --json` → `svg_to_pptx.py --quick-generate --with-notes`。

| 关 | 读数 |
|---|---|
| 末检查器 | **exit 0**，报告落 `validation/svg_quality_report.json` |
| 导出 | `exports/lx-c3_20261110_230442.pptx`，`Slides: 3`，`[POSTFLIGHT] status=passed-with-warnings` |
| 我们的判据 | `verify-pptx-editable.py` → **exit 0**；三页文本形状 4 / 10 / 7，**图片 0**，无整页位图 |
| 形状层 | 3 页 13.33×7.50 in；P1 `AUTO_SHAPE`×2 + `TEXT_BOX`×4，P2 全文本 ×10，P3 全文本 ×7 |
| 备注 | 三页都有，文字与 `notes/total.md` 一致（如 P3「结论：转化回来了，留存要盯…」） |

**两条实测发现**（已写进 `path-c-editable.md`）：

1. **字体是引擎钉的**：即便 SVG 写 `PingFang SC`，导出后 run 级字体是 `Arial` + `Microsoft YaHei`。本机（macOS）没有 `msyh`，打开必提示替换 ⇒ C3-3 的判据要写成「版式没走形」，不是「零替换提示」。
2. **19 条警告全是编辑级 advisory**：`Noncanonical compact authoring`×6（`font-family` 写到每个 `<text>` 而非根默认）、`ungrouped top-level element`、`missing root data-pptx-page-role`、`Quick roster declares no deck language`。POSTFLIGHT 仍判 `passed-with-warnings`，它们指出的是**手写 SVG 的写法**，不是引擎缺陷。

⇒ C 出口从「引擎可用 + 转换器出原生件」补到了「3 页真出件 + 我们的判据为绿 + 备注在位」。

## 16. 第六版（1.1.5）· 三方评估反哺落地＋文档对账闸

**背景**：2026-11-14 六维三态评估三方平行（三家不同厂商的外部评审，汇总 3/5），本轮把可实施建议全部落地。

**改动清单**：

1. `build-deck.py`：本地图内联成 data URL（单文件真自包含，移走目录不破图）；写后回读剥 `<script>`/`<style>` 再数页、查破图（六项）；`--json` 机器可读摘要。
2. `render-png.sh` 的 `count_slides` 与 build-deck 同源剥 `<style>`（base.css 注释含 `<img src>` 字面，曾假红）。
3. 新增 `scripts/check_doc_claims.py`：七类 258 项文档对账（数字漂移／锚点消失／悬空引用／破图破链／字段名过期／幽灵路径／状态词当当前／无日期版本断言／行数／取值集／漏登记／空壳复活）；事实量不到硬中止 exit 2。
4. `assets/demo-images/` 补 7 份占位 SVG；删 FX 空壳（`fx-runtime.js`，依赖的 `fx/` 不在本 skill）；cover pills 41/36/26 订正。
5. layouts 词表归一：A 构图词表 vs B 36 stem 零交集，两表互加参考列。
6. 文档对账约 25 处（状态词／计数／字段名／路径／口径）；版本 bump 1.1.5。

**本轮末次复跑读数（全部当次退出码）**：

| 闸 | 读数 |
|---|---|
| `run_skill_gates.py --skill` | exit 0，3/3 道（离线自检 rc=0／疫苗 14/14／体量预算 rc=0） |
| `check_doc_claims.py` | 258 项全过 exit 0 |
| `check_limits.py` | exit 0，❌0（SKILL 258 行） |
| `vaccinate.py` | 14/14 exit 0 |
| fixtures | allfull 0／brokenimg 1／deeplink 1／noslide 1 |
| 注入红测试 | 13/13 按预期红（含 exit 2 硬中止），基线绿 |

**E2E 回归（当前脚本重建）**：

| deck | 字节 | 源 section＝渲染张数 |
|---|---|---|
| weekly-report | 84,896 | 7＝7 |
| course-module | 85,755 | 7＝7（multi-class `slide full` 回归） |
| gallery（3 页 7 图） | 77,920 | 3＝3；7 图全 data URL、本地残留 0 |

14 张 PNG 全 1920×1080、var>5、ink>0.3%；gallery 3 页渲染目检占位 SVG 全显示（data URL 内联生效）。

**V13 事件（判据是库级共享资产）**：轮中 run_skill_gates 曾报疫苗 13/14、V13 ❌「规则在反例之前」——其时另一并发会话把 V13 暂改成结构化锚（`**反例**`/`**规则**` 比顺序），本 skill 的 `**踩坑**` 标签不命中锚。随后并发会话独立复核回退该判据（195 件误伤 6 件合规），恢复「剥 frontmatter＋700 字窗口」；复跑 14/14，**本 skill 正文零改动**。教训：库级闸红先查判据自身是否刚被改，⛔ 别急着改正文迁就判据。

**范围声明（本轮没判到的）**：只验 B 出口机制、文档对账与库级闸；A 出口真实生图、C 出口 3 页出件本轮未重跑（§15 读数是 6.7.2 时期，引擎已升 6.9.0，见 §10 新登记）；77 主题版式未逐张重渲染（§14 读数属 1.1.2 时期）。

---

## 17. 与 lewis（html-ppt-skill）的相似度实测（2026-11-20）

**方法**：逐文件 `difflib.SequenceMatcher` 对全文求比，按字节加权；对照组是
同级的 `html-ppt-skill/`（lewis 上游本地快照）。剔除 19.9 MB 机器生成的
预览产物与二进制字体，只算手写代码/规格。

| 层 | 件数 | 字节 | 占手写总量 | 与 lewis 相似 |
|---|---|---|---|---|
| ① 版式 `assets/layouts/` | 36 | 62,090 | 8.0% | **99.3%** |
| ② 整册 `assets/full-decks/` | 10 | 67,084 | 8.6% | **99.4%** |
| ③ 上游主题 `themes/upstream/` | 36 | 35,366 | 4.5% | **100.0%** |
| ④ 基础资产 base/runtime/anim | 3 | 70,071 | 9.0% | **100.0%** |
| ⑤ 自建主题 `themes/` 8 件 | 8 | 115,582 | 14.9% | 4.7% |
| ⑥ 脚本 12 件 | 12 | 222,774 | 28.7% | 6.1% |
| ⑦ references 48 卷 | 48 | 204,589 | 26.3% | 3.5% |
| **合计** | **153** | **777,556** | 100% | **33.4%** |

**两个口径，结论相反，都得说清楚**：

- **手写总量口径 33.4%**：lewis 原件占 30.2%（234,611 B），原创占 69.8%（542,945 B）。
  原创的大头是脚本（28.7%）与 references（26.3%）——这两层是本库真正的价值所在。
- **设计层口径 68.3%**：只看「会被人看见的东西」（版式＋整册＋主题＋基础资产，350,193 B），
  lewis 原件占 67.0%，自建主题只占 33.0%。

**逐字节相同的 14 个文件**：`base.css`、`runtime.js`、`animations/animations.css`、
`INTERNAL.md`、`covers/guanglan-rd-hills.jpg`、`course-module/{index.html,README.md}`（自带 `style.css` 已于 1.2.42 删除）、
`pitch-deck/{index.html,README.md}`、`tech-sharing/{index.html,README.md}`、
`weekly-report/{index.html,README.md}`。

**36 个版式的差异只有两类**：主题路径 `themes/` → `themes/upstream/`，以及品牌字样
（`html-ppt` → `示例品牌`、`24 themes` → `8 themes`）。版式结构、类名、DOM 一行未动。

**8 个自建主题是原创**：与 lewis 36 个主题的最高相似度 12.9%（旧「柔和自然光」版 ↔ magazine-bold；该版 2026-11-20 已重建为 `kichijoji`（2026-11-21 改名 `wanhang-fy`），重建后未再比对），
其余 3.0–8.4%。这是本库唯一在设计层真正原创的部分。

**结论**：本库是 lewis 的**下游分发版**，不是独立实现。它的原创性集中在「脚本化的质量闸」
（配色体检、预览一致性、文档对账、符号链接闸）与「references 的方法论」；版式、整册、
基础运行时是 lewis 原件的搬运。ATTRIBUTION 已如实登记，MIT 合规靠 `LICENSE-html-ppt.txt`。
⛔ 对外别说「独立实现」或「原创框架」——设计层 67% 是 lewis 的。

**顺带修掉的分发硬伤**：`themes/upstream/` 原为符号链接指向同级的 `html-ppt-skill/assets/themes`，
本机跑得通，单独打包后链接即断，36 个版式全取不到主题，`build-deck.py` 报
`✗ 仍残留 1 个本地 <link>` 直接失败。已改为实体目录（36 个 css，35.2 KB），
并在 `selftest.py` 加「库内不许有符号链接」闸（造链接验证过会红）。

## 18. 第七版（1.1.7）· 瓦作 → A/C 的桥（2026-11-21）

**问题**：主题（`assets/themes/`）原先只服务 B 出口。`path-a-image.md` 与 `path-c-editable.md` 里 0 处提到 themes——
A 出口靠 21 风格键逐页生图、C 出口交外部引擎，两侧都不读 CSS。所以给「每个主题做位图素材」在结构上无处可读。

**做法**：不新画素材，把主题里**已有**的材质渲染出来。`scripts/export-theme-textures.py` 读 `:root` 与材质类，
用 headless Chrome 截成 PNG；`scripts/check-theme-textures.py` 对账源与产物。

### 实测读数（2026-11-21 本机）

| 项 | 读数 |
|---|---|
| 出图主题 | 9/9（覆盖率闸要求每个瓦作都有 manifest） |
| 合计 PNG | **74** 张（材质类 57 + 内联纹理 8 + 材质板 9，其中板 9 张按主题各一） |
| 单主题张数 | 最少 4（guanglan-rd：3 材质 + 板）；最多 13（panyu-rd：10 材质 + 2 纹理 + 板） |
| 板尺寸 | 1128×(524 / 928 / 1332 / 1736)，按材质数换行 |
| 体积 | `assets/textures/` 2.7 MB（不并入预览页，预览页单文件已 3–11 MB） |
| 出图耗时 | 全量约 9–11 分钟（Chrome 冷启 ~8–15 s/张，幂等复跑 9 主题 0 张重出） |

### 三道负例（闸存在性自证，已接进 `selftest.py`）

| 负例 | 期望 | 实测 |
|---|---|---|
| 篡改 `source_sha256` | 红：源已变、图未重出 | 红，1 项问题 |
| 删一张 manifest 内的 PNG | 红：文件不存在或不是 PNG | 红，1 项问题 |
| 撤掉某主题的 manifest | 红：该主题没有出图 | 红，1 项问题 |

负例条数本身也被断言（≠3 即 FAIL）——跑了 0 条也会「全绿」，那等于没验。

**闸门读数**：`check-theme-textures.py` PASS 9 主题 / 0 问题 / 0 提醒；`selftest.py` PASS；
`check_doc_claims.py` 452 项全过；`check_limits.py` / `vaccinate.py` exit 0 / 0 ❌。

### 本轮踩到的三个静默错

1. **data URI 里的单引号会截断解析**：`[^)"']*` 在 `xmlns='http://…'` 的第一个单引号就断，
   四个纹理 token 的 `width/height` 全读不到 → 一律退回 200×200 默认值，平铺密度错 4 倍。
   页面照样出图、退出码照样 0。改法：按 `)` 收尾，再从解出的 SVG 读 `width/height`，缺则读 `viewBox`。
2. **低 α 纹理落在白底上等于空白**：纸纤维 α .12、麻点 α .10，铺在 `#fff` 上肉眼几乎看不见。
   改法：样片与材质板一律落主题自己的 `--bg`（九个主题都有这个 token）。
3. **`textures/` 根目录有 README**：自检拿 `listdir()[0]` 当主题目录，第一个是 `README.md`，
   `NotADirectoryError`。改法：只挑目录项。

### 没做的（留给下一轮）

- `assets/covers/guanglan-rd-hills.jpg` 全库 0 引用，是悬空资产，未处置。
- A/C 出口的**端到端**用法只在文档层接通（`path-a-image.md` §A1.5、`path-c-editable.md` C1 表），
  尚未真跑一份 deck 验证 `board.png` 作 style 参考的实际效果；C 出口的 `FULLBLEED_RATIO=0.9` 拦底纹这一条也只有判据没有实测。

## 19. 第八版（1.1.8）· 位图材质进库：灰度 tile × multiply（2026-11-22）

**起点是用户的判断，不是任务**：看了 `assets/textures/longhua-si/board.png` 之后，用户说
「HTML 光靠 CSS 达到的细腻感抵不过位图，比如世纪大道和世纪广场的大理石其实模拟得不好」。
目检 `assets/textures/century-sq/mat-cp-marble.png` 坐实了这一点：320×320 里几乎就是白底 +
两道极淡斜向柔光，没有层理。瓦作导出能给「通路」，给不了「质感」。

**做法**：灰度无缝 tile ＋ `mix-blend-mode:multiply` 压在 `--marble` 上——颜色不进图，
色相仍只在 `:root` 一处；同一张 tile 供亮色版（世纪广场）与暗色版（世纪大道）共用。
新增 4 件：`scripts/make-material-tile.py`（出 tile）、`scripts/check-bitmap-assets.py`（B1–B8 闸）、
`assets/textures-src/registry.json`（登记表）、`assets/textures-src/century-sq/marble-raw.png`（源图）；
派生件 `assets/textures/marble/marble-gray-1024.png`。

### 实测读数（2026-11-22 本机）

| 项 | 读数 |
|---|---|
| 源图 | 1536×1536 RGB，2,926,644 B（Seedream 5.5 生成，提示词记在 registry） |
| tile | 1024×1024 **gray（PNG color type 0）**，315,551 B，min 241 / max 255 / mean 247.5 |
| 无缝读数 | `seam = 0.76/255`（左右与上下边缘像素差取大者） |
| 3×3 拼接 | 目检无接缝、无对称痕迹 |
| ppduck 试压 | 534,154 → 398,757 B（−25.3%），`maxΔ=4`、`px>8=0.00%`、verdict PASS；**未收编**（见下） |
| `check-bitmap-assets.py` | PASS 1 条目 / 0 问题 / 1 提示（staged 未接线） |
| `check-theme-textures.py` | PASS 9 主题 / 0 提醒 / 位图豁免 1 张 |
| `selftest.py` | PASS，exit 0（位图闸负例 3 条全部红） |
| `check_doc_claims.py` | 458 项全过（references 49 → **50**） |
| `check_limits.py` | exit 0（拆卷后 `theme-to-export.md` 73 行、`theme-bitmap.md` 95 行，均 ≤100） |
| `vaccinate.py` | exit 0，0 ❌ |
| `check-theme-colors.py` | exit 0（amb_waived=0 / amb_stale=0） |
| `check-preview-sync.py` | PASS 9 主题，0 FAIL 0 WARN |

### 负例（闸的存在性自证，4 条全红）

| 负例 | 报出的判据 |
|---|---|
| 改 `derived_sha256` | B2 sha 漂移：磁盘 60938b59… ≠ 登记 0000000000000000 |
| 删派生 tile | B2 派生件不存在 |
| 往源目录塞未登记的 `stray.png` | B8 源目录里有未登记的图 |
| 把 tile 存成 RGB | B2 色彩类型不符 PNG color_type=2 ≠ L(0) |

`selftest.py` 里接了前三条（`bmp_neg == 3` 断言），第四条手工验过一次。

### 本轮三个静默错

1. **镜像四联是「假无缝」**。第一版把 640 中心块按四象限镜像铺成 1024，缝确实没有，
   但整张图中心浮出一个蝴蝶形对称（两层菱形+连线），目检一眼就露。改「位移半幅 + 余弦
   交叉淡化（band 110）」才有真实石材的连续性——这条已写进 `theme-bitmap.md` 的 ⛔。
2. **`check_doc_claims.py` 把 `.json` 截成 `.js`**。它的悬空路径正则交替是
   `md|py|sh|js|css|html|json|...`，`js` 先命中 `registry.json` 的前两位，于是报
   「指向 …/registry.js，磁盘上没有」——一个根本不存在的路径。
   加 `\b` 修正。这类「闸报的是错地址」比漏报更难查。
3. **孤儿 WARN 会训练人忽略警告**。`check-theme-textures.py` 起初把登记过的真位图报成
   「手工塞进来的孤儿」——每跑必响、永远不消。改为读 `registry.json` 取豁免名单，
   印「位图豁免 1 张」。消不掉的警告等于没有警告。

另有两处小坑：`SKILL.md` 里写占位路径 `assets/themes/‹theme›.css` 会被文档闸当真实引用判悬空
（改 `<theme>.css`）；`make-material-tile.py` 必须抽掉大块明暗（高半径低通相减），
否则原图的大片灰斑铺出来像「脏」而不是「层理」。

### 没做的（明写）

- **主题 CSS 未接线**。`century-sq.css` 一个字节没动，`.cp-marble--grain` 只活在
  `examples/marble-bitmap-ab.html` 里；`registry.json` 的 `stage` 仍是 `staged`。
  等用户对 A/B 样点头后再进主题。
- **接线时两处必改尚未落地**：`build-deck.py` 的图片 `url()` 内联（现在只转字体）、
  受影响主题的预览页重生成。不补这两处，单文件里 `../textures/...` 会 404。
- **ppduck 未收编**。理由：有损调色板量化只换 25% 体积，却让 tile 不能由脚本逐字节复现。
  渐变占比高的图一律不走它（口径写进 `theme-bitmap.md`）。
- **A/C 出口端到端仍未跑**（旧账）：`board.png` 当 `--ref style` 只通到文档层，
  C 出口底纹撞 `FULLBLEED_RATIO=0.9` 只有判据没有实测。
- `assets/covers/guanglan-rd-hills.jpg`（219,810 B）仍悬空 0 引用，未处置。
- `dia-skills` 改动未提交；坚果云镜像与 GitHub 未同步。

## 20. 八版续（1.1.8）· 世纪广场接线落地（2026-11-22）

**这一轮是用户一句「全批」触发的**：§19 停在「A/B 样已交、主题 CSS 未动」。批下来后，
一次做完三处接线并把产物全部出检视。

### 实测读数

| 项 | 读数 |
|---|---|
| `century-sq.css` | `.cp-marble` 加 `position:relative;isolation:isolate` ＋ `::after` 灰度 tile × multiply，默认 `opacity:.85`；另有 `--flat`（`content:none`）与 `--soft`（0.62）两个开关 |
| 预览页 | 3,190 → **3,609 KB**；HTML 里内联的那张 PNG 与 tile **逐字节一致**（sha 前缀 60938b59） |
| `build-deck.py` 实测 | 用例：`_tmp-check/deck.html` 引 `century-sq.css` → 单文件 3,588 KB，`data:image/png` ×1，残留 `../textures/` 0 处，内联体与 tile 逐字节一致；`--json` 的 `ok:true` |
| 瓦作样片重出 | `mat-cp-marble.png` 11.8 → 39.4 KB，目检出现真实层理；`board.png` 246 KB，5 个材质格里 `cp-marble` 已是石面 |
| 闸门 | `check-theme-textures` PASS 9 主题 / 0 提醒 / 位图豁免 1；`check-bitmap-assets` PASS（stage 改 `wired`，B7 现场核对 CSS 里确有该文件名）；`selftest` / `doc_claims`(458) / `preview-sync`(9 主题) / `colors` / `limits` / `vaccinate` 全部 exit 0 |

### 本轮第三个静默错（重要）

**导出脚本的样片会「假装有纹理」**。`export-theme-textures.py` 把主题 CSS 拷进临时目录再截图，
CSS 里的 `../textures/…` 按**临时页面**解析 → 404。结果 `mat-cp-marble.png`、`board.png` 画出来的
还是 CSS 那几道斜光，尺寸、颜色、退出码全部正常——只有对着图看才发现「材质的层理没进来」。
`prepare_css()` 已把本地图片 `url()` 一并改绝对 `file://`，与字体那条同源处理。

另外两条同族：`gen-theme-preview.py` 只调 `bd.inline_fonts`、不走 `read_css`，所以 `build-deck` 修好
不代表预览页修好——必须单独串一次 `inline_images`；`build-deck` 的 `verify_on_disk` 只查 `<img src>`，
查不到 CSS 里的 `url()`，所以 404 的 texture 不会被它抓（已由「逐字节比对内联体」这条手工判据兜住）。

### 仍然没做的

- **瓦作样片与真位图在语义上开始重叠**：`century-sq/mat-cp-marble.png` 现在已包含位图内容，
  但它仍是「CSS 截图」，`manifest.json` 的 `source_sha256` 只对 CSS、不对 tile。要不要让它同时记
  tile 的 sha（即「这张样片 = CSS + 哪张 tile」），留到下一次动导出脚本时定。
- 其余 8 个主题的同类材质（水磨石、水刷石、香灰、宣纸纤维、砖、木饰面）还没做；暗色姐妹版
  `century-ave` 的 `.cp-marble` 仍走纯 CSS（暗底上 multiply 几乎不可见，需要另定 blend 口径）。
- A/C 出口端到端、covers 悬空图、git 提交与坚果云/GitHub 同步：照旧未动。

## 21. 第九版（1.1.9）· 家族制：材质按物理家族共享 + 大理石改「大脉络 cover」（2026-11-22）

这一节记的是**口径变化**和**三个静默错**，不是进度汇报。

### 为什么从「按主题存图」改成「按家族存图」

先按主题各存一张时，同一块「白石面」在世纪广场、友谊大厦、世纪大道各存一份灰度 PNG——
三份内容几乎一样，只多了三倍体积，还让「同一材质的两个主题看起来不一样」变成默认结果。
改成家族制后，`assets/textures/<family>/` 是**源**（登记表里一条 = 一张图），
`assets/textures/<theme>/` 只留按主题截图的样片与材质板；消费侧在 `registry.json` 的
`used_by[]` 里逐条写清 `{theme, sel, blend, opacity, bg}`。

⛔ 不按主题复制同一张图。闸 B9 堵这个退化：同 sha、或同 `derived` 路径被登记两次 → 红。

### 大理石口径改判：从「细层理 tile」到「大脉络 cover + 细层理次级」

用户贴出 Calacatta Borghini 参考图后，口径才定下来。原来那张 1024 tile 的灰度落在 241–255，
即**对比只有 14 级**的均匀细层理——按 multiply .85 铺上去，整面几乎还是白的，只是「不那么平」。
而 Calacatta 的特征是：白底、几道 **100–300px 宽的蜿蜒巨脉**、脉间夹角状碎块网络。
两者的特征尺度差了一个量级，不是调参数能追上的。所以拆成两个角色：

| 角色 | 图 | 用法 | 为什么不能合并 |
|---|---|---|---|
| 主角 `hero-vein` | plain cover，**不做无缝化** | `::after` z-index:-1，`background-size:cover` | 巨脉本身比整张 tile 还宽，位移淡化会把穿缝的脉揉成软影；重复铺开就是壁纸 |
| 次面 `tile` | 512/1024 位移+余弦淡化 | `::before` z-index:-2，`repeat` | 只负责「不是一块塑料」，尺度小、必须无缝 |

同一张脉络在不同主题靠**裁切点**分化：世纪广场 `0% 0%`、友谊大厦 `60% 40%`。
暗底走**反相 + screen .55**（`multiply` 在 `#1a1410` 上几乎不可见，
`invert+screen` 配细层理会把平白区抬成雾）。

### 静默错一：检视页把选择器带点号写进 class

`<div class=".cp-marble">` —— 类名里带点号，永远匹配不到。11 张 A/B 截图全空，而 Chrome
**退出码 0**、文件也都写出来了。判据是「不同主题的截图字节数完全相同」——11 张尺寸一样才对，
字节一样必有鬼。真判据只能是看图或量像素。

### 静默错二：`--amp` 太低，等于接了一层看不见的东西

三族 tile 首版 `amp=9/5/10`（灰度range 18/10/20，均值 243/249/243）。接线、闸门、预览全绿，
但实测 A/B 的 `|Δ|=0.6–3.0/255`：肉眼与数据都等于没接。**闸查不出这个**——B7 只核
「文件名/选择器/blend/opacity 四要素在不在」，不核「看不看得见」。
二次调到 `26/18/26`（range 37/23/37），Δ 才进入可见区。教训：
**接位图之后必须量 `|Δ|`，不能只看闸绿**。

### 静默错三：绝对 seam 值对高频图是假信号

`seam` 打印的是边缘像素差均值。颗粒/纸纹本来相邻就差 4–7/255，于是「seam=7.57/255」
看着像有缝，其实无。改成**比值判据**：`跨缝差 / 图内典型相邻差`，≈1 即跨过接缝与挪一像素无异。
实测五张：marble-light 0.93–1.04、marble-dark 1.04–1.07、grain 1.06–1.19、
fiber 1.06–1.11、travertine 0.92–1.07。

### 实测读数

| 项 | 读数 |
|---|---|
| 家族目录 | `assets/textures/{marble,grain,fiber,travertine}/` 4 族 7 条登记 |
| tile 体积 | marble-gray-1024 315,551 / marble-dark-512 143,347 / marble-vein-1024 415,347 / marble-vein-dark-1024 413,224 / grain-512 158,960 / fiber-512 141,748 / travertine-512 126,796（B） |
| 预算闸 B10 | 1024 ≤400KB、`hero-vein` ≤520KB、512 ≤**180KB**（原 160KB，颗粒噪声压不到 160 以内） |
| 逐字节可复现 | `marble` profile 重跑仍出 315,551 B / `60938b59fd0b7252` |
| 接线 | 11 处 8 主题，每处都有 `<sel>--flat` 回退（`::before,::after{content:none}`），世纪广场另有 `--soft` |
| 闸门 | `check-theme-textures` PASS 9/0/位图豁免 0（共享件已移出主题目录，按父目录名匹配不到，属预期）；`check-bitmap-assets` PASS 7 条目 0 问题（B1–B10）；`selftest` 位图段 `bmp_neg==4`；`doc_claims` 全过；`preview-sync` 9 主题 |

### 本轮仍未做

- `assets/covers/guanglan-rd-hills.jpg` 悬空（全库 0 引用），未删未挂。
- A/C 出口端到端仍未跑：`board.png` 当 `--ref style` 只通到文档层；
  C 出口若把材质当底纹，会撞 `FULLBLEED_RATIO=0.9` 的红线，目前只有判据没有实测。
- `dia-skills` 未提交，坚果云镜像与 GitHub 未同步。

### 21.1 收尾复核又抓到三个（都是「闸绿了但页面是错的」）

写 §21 时我按「已交付」写，随后做可见性实测，三个问题连着暴露：

**① 拼接少一个 `}`，整段位图规则被浏览器丢弃。** 往 `.cp-marble` / `.pg-terrazzo` 这类已有规则后面
粘新规则时，把上一条规则的右括号吃掉了。浏览器解析到 `.cp-marble{ ... background-repeat:...;`
再遇到下一个 `.something{` 时，把这段当**无效声明**整段丢弃——选择器、`mix-blend-mode`、`opacity`
全都还在文件里，B7 判它绿，页面上一个像素都没有。九份 CSS 里**七份**中招（只有 century-sq 与
guanglan-rd 干净）。修复方式是把每条规则末尾多出来的那个 `}` 移回接缝处；`diff` 求证：全是括号搬家，
没有内容改动。

新增 **B11 结构闸**：接线主题 CSS 必须括号配平，且不允许「声明行紧接选择器行」。自检里加了第五条负例
（删掉一个 `}` 必须红），`bmp_neg=5`。

**② 闸只能证「写进文件」，证不了「画出来」。** 于是增 `scripts/probe-texture-visibility.py`：
每个 `used_by` 渲 A/B（`<sel>--flat` / 默认），headless Chrome 截图后量
`Δhf = hf(B) - hf(A)`（半径 2 高斯残差）与低通差（缩到 1/4 再比）。判据是像素，不是文本。

**③ 判据本身也踩了坑：不能用 hf(B)/hf(A) 比值。** A 完全平坦时 `hf(A)≈0`，比值被除零放成
847750.01。改成绝对增量：`Δhf ≥ 0.35` 或 `低通Δ ≥ 3.5`（灰度级）。实测 14 处：

| 主题 · 选择器 | Δhf | 低通Δ | Δ均值 |
|---|---|---|---|
| century-sq `.cp-marble` | 1.94 | 18.56 | 18.6 |
| friendship-bldg `.cp-marble` | 1.94 | 17.38 | 17.3 |
| century-ave `.cp-marble` | 1.27 | 6.59 | 6.5 |
| qiu-r `.cp-marble` | — | 7.15 | 7.1 |
| panyu-rd `.pg-terrazzo` | — | 8.61 | 8.7 |
| panyu-rd `.pg-travertine` | 0.11 | 8.43 | 8.6 |
| longhua-si `.lh-granite` | 0.02 | 5.03 | 5.0 |
| longhua-si `.lh-ash` | 0.28 | 4.64 | 4.6 |
| longhua-si `.lh-wall` | 0.55 | 6.02 | 6.0 |
| fuzhou-rd `.fz-paper` | 0.98 | 3.91 | 4.0 |
| wanhang-fy `.wf-paper` | 0.46 | 3.81 | 3.8 |

好看的读数背后是三次返工：`amp=9/5/10` 太低（等于没接）→ 拉到 26/18/26；
`.wf-paper .60`、`.fz-paper .45`、`.lh-wall .35` 三处仍在阈值下 → 抬到 .75/.60/.48。

**④ 顺带挖出一个更早的缺陷：panyu 的 `.pg-travertine` 引用了不存在的 `var(--paper)`。**
该主题 :root 里只有 `--bg / --bg-soft / --surface / --paper-deep`，于是这块「石灰华」面板
底色一直是透明的（在深色页上就是一块黑）。改成 `var(--surface)` 后 Δ均值从 156（假象）回到 8.6（真材质）。
Caveat：century 三份还引用 `--font-body-song / --font-ui-zhizao`，它们由共享字体声明提供，
按「同文件未定义」扫会误报，所以没把这条做成闸。

### 21.2 第三角色（1.2.0）· 掩膜：形状与颜色彻底分开（2026-11-22）

参照 tinostone 的 Portoro 页（黑结晶底 + 金脉爆发 + 白 effervescence，并按 finish 分抛光/哑光/
喷砂），世纪大道的暗底脉络从「反相灰度 + screen .55」换成**掩膜**。

为什么必须换：screen 是屏幕混合，只能把脉染成灰白，**染不出金**。用户要的是 Portoro 那种金线。
掩膜把两件事拆开——alpha 给形状，`background-color: var(--marble-gold-vein)` 给颜色；
颜色因此仍在 `:root`（符合本库铁律），换色不重导图。

实测读数：`century-ave .cp-marble` 的 A/B 从 Δhf 1.27 / 低通Δ 6.59 升到 **Δhf 3.43 / 低通Δ 10.42**。

**这一步踩到的坑（重要）**：`mask-image: url(file://…png)` 在 Chromium 里被当跨源请求拦掉，
**不报错、不 404、静默不画**。判据三步：
1. CSS 渐变 mask 正常 → mask 本身可用；
2. 同一张 PNG 走 `file://` → 空白；
3. 同一张 PNG 走 `data:image/png;base64` → 立刻出现。
所以掩膜**必须内联**。`century-ave.css` 因此 +约 137KB 文本，换来直开 / 导出截图 / 单文件 deck
三种场合行为一致。用 ego-browser 起本地 http 服务复核过同一页：http 下 `file://` 引用也不出
（跨源），http 路径与 data URI 都出。

配套：`make-material-tile.py` 加 `--profile mask`（512² RGBA，floor .28 / γ1.5 去雾）；
登记 +1 条 `marble-vein-mask`（blend 记作 `mask`），`vein-dark` 退册；
闸 B4 允许 `mask`，B7 对 mask 改查 `mask-image` 内联体与 token 上色，不再查 `mix-blend-mode`。

### 21.3 γ 2.0 · 面板底改暖黑 · 删平铺斜光（2026-11-22）

用户看实块截图提了三点，逐条落地：

1. **CSS 斜光很假。** 面板里那几束平行光其实是两条按 500 / 400px 平铺的 `linear-gradient`
   重复出来的——大面板尚可，缩成窄带就成了假光源。已删掉这两条，只留一块盖满整幅、
   `rgba(255,241,214,.045)` 的斜向高光；它不复用、不平铺，读成「面」而不是「线」。
   若仍嫌多余，`.cp-marble--flat` 之外还可临时把 `background-image` 设成 `none`。
2. **黑得不够，太泛蓝。** `--marble-black` 原为 `#0f172a`（slate −900，天生带蓝），
   改为 **`#0d0c0a`** 暖黑；左上角那块 `rgba(30,41,59,.80)` 的蓝调 radial 一并换成暖棕 `rgba(44,33,24,.55)`。
3. **脉要更细。** 掩膜 γ 1.15 → **2.0**（floor 仍 .28）：不透明占比 11.2% → 5.8%，
   文件 115,093 → **90,354 B**。三档并排（γ1.15 / 2.0 / 2.4）时 2.0 最像石脉，2.4 开始断线。

`make-material-tile.py` 因此加了 `--mask-floor` / `--mask-gamma` 两个开关，
默认值就是 0.28 / 1.15（老行为可复现），要复现当前产物必须显式写 `--mask-gamma 2.0`。

### 21.4 灰白脉：一张掩膜两用（2026-11-22）

用户搜了 Portoro 大板照片后指出：黑色大理石不只有金脉，还有灰白细脉与白斑。核过大板照片确实如此。
试了三档（不转、放大 130%、放大 150% 换位）都不行——不转的话白脉就是金脉外面套一圈灰边，像描边；
放大只是把同一条线放大。

最终解法是**同一张掩膜，整层旋转 180° 再放大 1.06**，几何就与金色那组错开了；浓度 15% 灰白 +
`blur 1.6px` 让它「透出来」而不是「贴上去」。`::after` 仍是金脉，`::before` 让给白脉；
原来的层理 tile 挪到元素自身的 `background-image`，用 `background-blend-mode:overlay` 与底色合成。

副作用是两个闸要跟着改：B7 现在认三种接线形态（`mask-image` 内联、`:root` 自定义属性内联、
`background-blend-mode` 合成）。登记里 `marble-dark` 的 `blend` 记作 **`overlay(bg)`**、`opacity` 记 `1`。
base64 只存一份，CSS 从 278KB 降到 140KB；可见性 Δhf 3.55 → **3.85**。

### 21.5 glass：从「棕色哑光板」到「磨砂玻璃」（2026-11-22）

用户看素材板问「glass 是这样的材质吗？感觉和 steel 很像」。诊断三处：

1. 填充 `rgba(90,70,52,.66)→rgba(58,46,36,.50)` 几乎不透明 —— 玻璃的成立条件是**看得见后面**，这里后面什么都没有；
2. 底色是暖棕，与 `.cp-steel` 的 `#4a3c2f→#2e251d` 同一族 —— 两只都读成青铜；
3. 没有任何镜面高光 —— 玻璃靠「反的那一下」被认出来，没有高光就只是一块板。

改法（只动 `.glass`，未加任何图）：填充压到 **38%/28%**，底色改中性暖灰 `rgba(122,106,90)`/`rgba(68,58,48)`
（不再与钢同色系）；加一道 **105°** 斜向高光带（`transparent 58% → .13 63% → .05 68% → transparent 74%`），
`blur` 14 → **20px**、`saturate` 108 → **112%**；上缘 inset 高光 `.30`→`.46`，补下缘 inset 暗边 `.30`。

三种真实语境复核（`_probe-glass2.html`，只引主题 CSS、不引 base.css —— 引了 base.css 会把 probe 页
压成 slide 横排）：纯暗底靠高光与上缘反光立住；压在黑金大理石上金脉被 blur 成散光；压在暖灯箱上
高光划过、暗角压边，读成磨砂夹胶玻璃。

闸：`check-theme-textures` PASS 9 主题 / `check-bitmap-assets` PASS 7 条目 0 问题 4 提示 /
`probe-texture-visibility` PASS 14 处 / `selftest` PASS / `check-preview-sync` PASS 9 /
`check-theme-colors` exit 0 / `check_doc_claims` exit 0 / `check_limits` 0 红。

**加一档（同日）：让玻璃自带 LED。** 纯被动透射的玻璃在暗底上仍读成灰板（暗底后面没有光可透），
于是给它一层从内部溢出的暖光：`radial-gradient(112% 92% at 26% -8%,rgba(255,226,168,.30) → 66%)`
（顶部偏左、无硬边），配 `inset 0 0 54px rgba(255,222,160,.20)` 与 `0 10px 80px rgba(255,200,120,.10)`
外圈 bloom，填充再顺压到 34%/26% 并转暖（124,104,84 / 66,54,42）。
三档 A（LED .20）/ B（.30 更暖）/ C（B 上再压薄到 24·17）同屏比对：B 最稳，C 薄过之后 blur 把暗底
拉成灰浆，压在石面上反而更脏。判据写在注释里：⛔ 是弥漫光，不做条纹、不做硬边光斑。

### 21.6 脉的排列组合（2026-11-22）

用户指出「金中有灰白、白中黑里也有灰白」后才意识到：只靠一张图刷满，真正会枯竭的不是颜色而是**排列**。
于是把「裁切点 / 旋转 / 缩放 / 对比」做成四个旋钮，同一张 tile 出几种石面，并给每个主题配一个 `--alt`：

- 白大理石：本体是「近观」（转 180 ×1.08 / contrast 1.14），`--alt` 是「远观」（转 180 ×1.45 / contrast 1.06）；
  友谊大厦再错开一档（×1.34 / contrast 1.08 与 ×1.05 / contrast 1.12），两块白石料从此不撞。
- 黑大理石：`--alt` 把金脉掩膜从 35% 65% 挪到 82% 18%、灰白脉从转 180 改转 90，金与灰的走向同时换。

`contrast` 是顺手捡到的收益：黑脉压得更黑时，夹在脉间的灰白细纹会一起浮出来，白底上就有了「黑中带灰白」。

**两次失败（都记在这一版）**：
1. 想用「一层半透明白 + 第二层同图放大」造出淡次脉 → 白纱盖下去主脉也一起被洗白，改前后截图几乎无差；
   要淡就走 `contrast`，别用叠层。
2. 试过转 90° 换走势 → `cover` 按旋转前的框算，转完盖不满，右半截露出白块。180° 可以，90° 不行。

闸：`check-theme-textures` PASS 9 / `check-bitmap-assets` PASS 7 条目 / `probe-texture-visibility` PASS 14 处 /
`selftest` PASS / `check-preview-sync` PASS 9 / `check-theme-colors` 0 / `check_doc_claims` 0 / `check_limits` 0 红。
（`century-ave` 因为新增 `--alt` 规则改动了源 CSS，必须重出素材板，否则 `check-theme-textures` 报「源已变、图未重出」。）

### 21.7 玻璃回到「底 + 描边 + 光」配方（2026-11-22）

用户提醒本库有过一个 glass 关键词的 skill，回去读 `liquid-glass-ppt/references/glass-tokens.md` §1–2，
发现自己重新发明了一遍但漏了三条：

1. **三层缺一不可**（底 / 描边 / 光）——我只有底和光，描边是一条整圈 .26 的实线；
2. **⛔ 别画环绕一圈的常亮白边**——那圈 .26 就是；方向性该由「顶缘 / 某一条缘」的窄 inset 反光给；
3. **宽而弱的环境反射撑厚度**——我只做了 26px 的小光晕，不够宽。

改法：玻璃参数全部提成 `:root` 的 `--glass-*`（blur / sat / tint-a / tint-b / edge / led / halo），
`.glass` 只引用变量；描边降到整圈 `.22`，方向性交给 `inset 0 1px 0`（顶）与 `inset 1px 0 0`（左），
底缘 `inset 0 -1px 0` 吃暗；外圈反射换成 `0 10px 80px` 的宽弱 halo。

口径差异要写清楚：那份 skill 的 blur 红线是 **≤12px**（老演示机），本主题取 20px 是**屏幕阅读单块浮层**的
有意越线，不是抄漏了；tint α 34/26 落在它给的 .18–.40 安全区间内。

### 21.8 白大理石的光影：删平铺斜光（2026-11-22）

用户说白石的渐变光影「比较死板」，要求按黑石那次的处理法——要么不画，要么拉成一大束均匀的光。

查出根源和黑石一模一样：世纪广场那两层 `linear-gradient` 是按 **400px / 300px 平铺**的，
一块长面板上会重复成一排平行亮带，读的是「打光」不是石头；友谊大厦那条 112° 暖金带则是
`26%→28%→33%` 的硬边三停靠，长面板上像贴了一条胶带。

改法（两处同一口径）：**删掉所有按 px 平铺的 linear-gradient**，各留一条盖满整幅、不成周期的极弱斜光
（世纪广场 `.055` 冷灰 118°、友谊大厦 `.14→.03` 暖调 120°），柔光斑从 50% 半径放大到 120–140%。
新判据写进注释：出现按 px 平铺的 `linear-gradient` 就是「假光线」的来源。

同时把 `--alt` 接进 deck：第 5 页窄带改 `cp-marble cp-marble--alt`，与第 2 页实块成两种石面；
顺手改掉第 2 页过期文案「深蓝黑结晶底」→「暖黑结晶底」（底色早在 1.2.1 就转暖，文案没跟上）。

闸：`check-theme-textures` PASS 9 / `check-bitmap-assets` PASS 7 / `probe-texture-visibility` PASS 14 /
`selftest` PASS / `check-preview-sync` PASS 9 / `check_doc_claims` 0 / `check-theme-colors` 0 / `check_limits` 0 红。

### 21.9 hero 玻璃卡：真折射只作 opt-in（2026-11-22）

用户「先做一版 hero 玻璃卡试试」。做法：`.glass` 之外新增 `.glass--hero`，把 `backdrop-filter`
换成 `url(#lg-refract) blur(4px) saturate(118%)`——`#lg-refract` 是页面自带的 `feTurbulence`
+`feDisplacementMap`（baseFrequency `0.012 0.018`、octaves 2、seed 7、**scale 62**），
在卡片边缘把背后的石脉、灯箱、细竖纹真实掰弯，读成「一块有厚度的玻璃压在纸上」。

三档实测（同页同景）：A 纯 `blur(10px)` 只剩雾、边缘没有弯折；B scale 62 + blur 4 弯折清晰、
仍是玻璃质感；C scale 92 + blur 3 位移过大，竖纹被揉成波浪，**判为拆台档**。

三条硬约束写进注释：① 页面里没有 `#lg-refract` 时整条 `backdrop-filter` 失效，
自动落回 `.glass` 的 blur（不需要 JS 判断）；② 只有 Chromium 真渲染，Safari/Firefox 拿到未折射的原帧，
所以只作 hero 单卡 opt-in，不做全局；③ 填充必须比 `.glass` 更薄（22/16），
否则透上来的位移被盖掉——第一版填充 34/26 + blur 10 就是「看不出弯折」的真正原因。

坑记两条：`backdrop-filter:url(#filter)` 同页并排多档会**串扰**（无过滤档也被扰动），
判读必须单页单档；探针页不要引 `base.css`，会把卡片压成 slide 横排。

### 21.10 圆角曲率改 G2：跟浮龟的连续曲率（2026-11-22）

用户说「来雪亭的圆角可以看看浮龟，现在用的是贝塞尔形式」。查 `浮龟Vudgio/references/corner-geometry.md`：
浮龟把圆角分 G1（`border-radius` 四段圆弧拼直边，曲率在接点跳变）与 G2（超椭圆 $|x/a|^n+|y/b|^n=1$，$n\approx5$），
并明确 ⛔ 把 `0.5522847` 当超椭圆系数（那只是四分之一圆的贝塞尔近似，仍是 G1）、⛔ 用比例单位的
`clipPathUnits="objectBoundingBox"` 路径（3:1 与 1:3 各扁各尖）。落地顺序是「先 `border-radius`，
`@supports` 里升级到真路径或规范直写」。

本机实测（Chrome 158）：`corner-shape:squircle` 真渲染，曲率连续、角部收得慢；而
`corner-shape:superellipse(5)` 被当非法值，连同一元素上的 `border-radius` 一起失效——整块变方角，**弃用**。
所以走规范直写这条（浮龟的四条路线里的 C），不引入 `clip-path: path()` 管线：超椭圆必须按实际像素尺寸算，
主题 CSS 不知道元素多大，而 `overflow:hidden`+`border-radius` 又会把 G2 裁回 G1。

作用范围**只按半径量级挑**：`border-radius` ≥10px 的字面声明 + 七个 `--radius-lg ≥10` 的主题（
century-ave 14 / century-sq 14 / fuzhou-rd 10 / guanglan-rd 28 / longhua-si 10 / panyu-rd 10 / wanhang-fy 28）；
友联 8px、qiu-r 3px 不动，4/6px 的 `--radius`/`--radius-sm` 也不动——12px 以下本来就看不出 G1/G2 的差别。

⛔ 一条踩过的坑：先写成全局 `*,::before,::after{corner-shape:squircle}`，结果胶囊（`999px`）被掰成圆角矩形、
圆点（`50%`）变成圆角方块——squircle 会把「半径已到半高」的形状也按超椭圆重画。必须排除 `999px`/`9999px`/`50%`。

验收照浮龟的做法：截图放大 4–8 倍看弧与直边接界有无折点。14px 的卡角放大后是连续过渡、没有折点；
28px 的广兰路面板差别最明显（更「收得慢」）。不支持该属性的引擎当未知声明丢掉，退回原 `border-radius`。

### 21.11 半径抬到 20px、友谊大厦正名（2026-11-22）

用户「ok」批准把 `--radius-lg` 抬到 18–20，取 **20px**（世纪大道、世纪广场两处；广兰路与万航渡本来就是 28，
福州路/龙华寺/番禺路 10px 不动，友谊大厦 8px 不动）。半径一抬，G2 的曲率收益才真正显出来：
hero 玻璃卡的角不再像「圆弧忽然接直边」，而是一路收过去；同一张卡在 14px 时这个差别几乎读不到。

另：用户指出主题正名是**友谊大厦**，不是「友谊会堂」，也不是早年 SKILL.md 里写错的「友好大厦」。
`friendship-bldg`（目录名 ⛔ 不改）在 SKILL.md / SELFTEST / 预览模板 / check-fonts / check-preview-sync /
theme-preview / theme-bitmap / ATTRIBUTION / themes README / 主题 CSS 注释里统一改成**友谊大厦 Friendship Bldg**；
只有「原中苏友好大厦」这处历史名保留——那是上海展览中心的旧称，是事实，不是误写。

闸：`check-theme-textures` PASS 9 / `check-bitmap-assets` PASS 7 / `probe-texture-visibility` PASS 14 /
`check-preview-sync` PASS 9 / `selftest` PASS / `check_doc_claims` 470 项 / `check-fonts` FAIL 0 WARN 0。

### 21.12 胶囊能不能更顺滑：只有「真路径」这一条（2026-11-22）

用户追问「有没有能让接界处更顺滑的胶囊」。先给结论：**几何上不存在既保胶囊形又曲率连续的形**——
直段曲率是 0、半圆端是 1/r，要连续就得在接界处插一段曲率 0→1/r 的过渡，插进去端头必然变"满"，
那就是「超椭圆盘」而不是胶囊。

三条实测：

1. **`corner-shape:squircle` 不行**。带 `border-radius:999px` 会是圆角矩形；把半径压到半高也一样，
   而且 Chrome 的 `superellipse(n)` 参数比直觉激进——`superellipse(2.4)` 在 240×64 上已经是"板"，
   和「宽胶囊曲率」不是同一个量。
2. **`999px` 真胶囊**在 6 倍放大下接界折点其实读不出来（`/tmp/pill-junction.png`）；
   只有做到 240px 级别的大 CTA，折点才开始显形。
3. **真路径可行**。用 `浮龟Vudgio/scripts/squircle_path.mjs --width 240 --height 64 --radius 32 --n X`
   生成 `clip-path`／SVG 用的路径，n 控制端头饱满度：**n=2.4 几乎还是胶囊但接界已顺**，
   n=3 开始像"板"，n=4 端头最满。

所以落法：**大尺寸 CTA 用真路径（n=2.4），小标签继续用真半圆**。⛔ 别拿 CSS `corner-shape` 去凑——
参数语义对不上，做出来直接是板。⛔ 真路径必须按实际像素算：胶囊宽度会变，不能一个类名通吃；
固定尺寸的 deck 页可行，流式布局不可行。

样例：`examples/cta-capsule-ab.html`（黑金石面 + 暖灯箱，A 真胶囊 / B n=2.4 / C n=3 / D n=4）。

### 21.13 封面接入 hero CTA（2026-11-22）

把 21.12 定下的「大尺寸才走真路径」落进世纪大道：主题新增 `.cta-hero`（240×64，内联 SVG 真路径，
n=2.4 的超椭圆端 + 1px 暗描边 + 错开 0.3/0.7 的内高光路径），deck 封面在标签行下面接了一枚「往下看石面」。

三条写进注释的边界：① 路径按 240×64 算死，改宽改高要用
`浮龟Vudgio/scripts/squircle_path.mjs --width W --height H --radius H/2 --n 2.4` 重生成；
② ⛔ 套在流式胶囊上——宽度一变端头就被拉扁；③ 端头用 SVG 而不是 `border-radius`，
因为 `corner-shape:superellipse()` 的参数和路径里的 n 不是一个量（21.12 已实测）。

deck 重打包 3,639,004B；封面截图 1x 下 CTA 与旁边四枚小标签（真半圆）并置不打架，
小标签保持半圆、只有大 CTA 是连续曲率，这正是分档的用意。

收尾时本机掉线一次，写入（素材板 17:55 / 预览 17:58）落地已核对，七道闸补跑全绿：
`check-theme-textures` 9 / `check-bitmap-assets` 7 / `probe-texture-visibility` 14 /
`check-preview-sync` 9 / `selftest` / `check_doc_claims` 468 / `check-fonts` 0 红 / `check_limits` 0 红 / `check-theme-colors` exit 0。

### 21.14 把「主题 → deck」这条链焊上（2026-11-22）

用户问「主题和 ppt 之间的链通了吗」，核对结果是：主题 → 预览页（`gen-theme-preview` + `check-preview-sync`）
与主题 → 单文件 deck（`build-deck --assets` 内联）都通，但有两个断点：
① 那份世纪大道 deck 的**源**还留在 `/tmp/deck-ave/index.html`，库里没有，`/tmp` 一清就重建不了；
② deck 与主题之间**没有闸**，主题改了 deck 不会自己变——此前出过拿 11:18 旧产物截图的事故。

补法两条：

1. **源进库**：`examples/decks/century-ave-materials/index.html`（相对路径改到 `../../../assets/`），
   交付路径登记在 `assets/decks.json`（`src` / `theme` / `built` / `pages`）。交付路径在本机，
   换机器或换输出目录时该条降为 WARN，不误报红。
2. **加闸 `check-deck-sync.py`**：`build-deck.py` 现在给每个内联块写 `data-sha256`（源 CSS 字节的
   前 16 位），闸拿它和主题源文件当前指纹比——**不等就是「主题已改、deck 未重打包」**，
   并直接把该跑的命令打出来；另查「源里有 `id="theme-link"` 且主题名与登记一致」「不留本地
   link/script」「页数与登记一致」。

负例已验：往 `century-ave.css` 追加一行注释 → 闸红（`1137a96c84d6eb41 ≠ ea71abc44095e0ae`）；
复位后绿。另修一个假阳：页数必须先剥掉 `<style>/<script>` 内容再数——主题 CSS 注释里就写着
`<section class="slide …>`，不剥会多数一页。

仍**没通**的一条（本条只是记录，不是本次范围）：`assets/full-decks/` 那五套模板只链 `base.css` + 自带
`style.css`，不吃主题——「选主题套模板」这条链还没建。

## 外部评审整改（2026-11-23，v1.2.15）

用三家不同厂商的外部评审审本库，挑单分批落地。九道闸现状全绿。

**批一——闸门真实性**

1. `check-deck-sync.py`：页数比对提到 source 分支之前，源级登记也数页。负例：登记 7 页、实际 6 页 → 红 1。
2. `built` 文件缺失从 WARN 改 **FAIL**，并打出重打包命令。负例：改名 built 路径 → 红 1。
3. 指纹从「只比主题块」改为遍历所有 `data-from` + `data-sha256` 的 `<style>`，逐个回源比 sha，缺 sha 也红；另用 `seen_theme` 保证主题块存在。负例：往 `assets/base.css` 追加注释 → 红 2。
4. `check-theme-colors.py` 收尾 `sys.exit(1 if with_fail else 0)`。负例：塞一对 ΔL* 过近的色 → rc=1（改造前恒 0）。
5. `check-fonts.py` F6 正则由 `--font-` 单边改为 `(--(?:font|ff)-…)`。负例：`var(--ff-nope)` → 红 1（改造前漏报）。
6. `fontTools` 提成模块级硬依赖，缺库 `return 2` 并打 FAIL。负例：`PYTHONPATH=/tmp/nofont` → rc=2（改造前静默跳过）。

**批二——覆盖缺口**

7. `check-preview-sync.py` 的 `discover()` 改为「主题 CSS 全集」，缺预览页 WARN→**FAIL**。复跑 9/0/0。负例：挪走 `fuzhou-rd` 预览页 → 红「缺预览页产物」1。
8. `check_doc_claims.py` 新增 `check_script_table()`：SKILL.md + references 的 `scripts/*.py|sh` 并集 ↔ 磁盘双向对账（漏登／悬空）。负例：塞一个未入册的 `zzz_probe.py` → 漏登 1；正文写一个不存在的 `ghost-tool.py` → 悬空 1。首跑即抓到 `make-ximai-bold.py` 漏登。
9. 脚本表补 `selftest.py` / `check-installed-fonts.py` / `make-ximai-bold.py` 三行（17→20），「六道」→「七道」，负例覆盖改成事实（只有 theme-textures 与 bitmap-assets 带负例）。
10. `check-deck-sync.py` 扫 `examples/decks/*/index.html` 与 `assets/full-decks/*/index.html`，未登记即 FAIL。负例：建 `_negtest` 目录 → 红「未登记的 deck 源」1。

**批三——卫生与体积**

11. 23 个 `*.bak*` 与 `__pycache__` 移入 `/Users/nath/dia-skills/_archive/20261123-来雪亭-备份/`（保留相对路径）。
12. 整张脚本表下沉为 `references/scripts-inventory.md`（唯一清单），`SKILL.md` 490→346 行；文档闸改为扫 references 并集，避免表下沉后误报。

**复跑**：`check-theme-textures` / `check-bitmap-assets` / `probe-texture-visibility` / `selftest` / `check_doc_claims`（499 项）/ `check-theme-colors` / `check-preview-sync` / `check-deck-sync` / `check-fonts` 全 PASS；`check_limits` 仅既有 references 超建议长度（未动）。

## 模板 kicker 可读性（2026-11-23，v1.2.16）

五套模板的 `.kicker` 都是 12–14px 小字，原先直接吃主题色。实测世纪广场 `--accent` 主黄在 `#eef3f7`
只有 **1.8:1**、`--accent-2` 蓝 3.2:1，`SEED ROUND · 2026` 投屏基本不可读。

改法统一为「字走墨、色留标记」：

- pitch-deck：`--text-2`（5.8:1）＋ 22×3 主色短线
- course-module：`--text-2` ＋ 18×3 `--accent-2` 短线
- weekly-report：`--text-2` ＋ 18×3 主色短线
- tech-sharing：暗底模板（slide 硬编 `#0d1117`），字改模板亮墨 `#e6edf3`，`>` 提示符显式写模板绿
  `#7ee787`——⛔ 这里不能借 `var(--accent)`，主题（无层）会盖掉层内 token
- presenter-mode-reveal：本来就是 `--text-3`，不动

判据仍归 `check-deck-sync.py`：改模板 CSS 后已重建的 deck 必须重打包，否则指纹红。
本次已重打包 `模板pitch-10页-世纪广场.html`，闸复跑 6 登记 / 2 比对 / 0 问题。

## tech-sharing 封面页脚压字（2026-11-23，v1.2.17）

封面讲者行底边离页底约 23px，`.deck-footer`（绝对定位 `bottom:24px`）的 hashtag 行正好压上去。

- 改法：`.slide[data-title="Cover"] .speaker{margin-bottom:56px}`——居中块增高 56、上移 28，
  讲者行底边让到 footer 上方约 30px。
- 验过但走不通的两条：`padding-bottom` 加到 132／400 只把内容挤出页底（slide 是 flex 居中且内容接近满高）；
  `margin-top:auto` 会把封面从居中改成顶对齐。
- tech-sharing 在 `assets/decks.json` 里是源级登记（无 built），不需重打包；`check-deck-sync` 复跑 0 问题。

## 渐变中段掉饱和（2026-11-23，v1.2.18）

来源：一条公开视频《什么是电影感的渐变？》＋渐变实验室。落地两件：

- `check-theme-colors.py` 新增 `audit_grad()`：按 sRGB 路径取 8 点/段，算 **OKLCH 彩度**；
  两端 ΔH ≥60° 且路径彩度相对两端最低值掉 ≥25% ⇒ `D`（⚠️）；沿路径 L* 反向跳 >3 ⇒ `M`（ℹ️）。
  负例：把广兰路 `--grad` 改回两端直连 `#1a7fb8,#a04018` ⇒ `D: 1`。
- 广兰路补两个中间色标（`#b26ebb 71%` / `#b1495a 90%`，按 OKLCH 色相弧取）：路径彩度掉 37%→0%。
  复跑主题体检：9 主题 0 fail、`D` 归零（剩下的 `BLK: 1` 是既有项）。

为什么不用 `max-min` 口径：深棕 RGB chroma 0.53 但肉眼不艳，用它会得出「越走越艳」的假阴性。


## 梁架适配中文混排（2026-11-23，v1.2.19）

来源：用户要求「让梁架更适配 CJK」，采纳罗蛇 Rassarpa 的判据（T07 字距不为负 / T08 禁合成斜体 /
T11 最小字号 / T13 字体栈显式声明）。**根因不是没判据，是判据被模板层盖掉了**：
`base.css` 早已把 `--letter-tight` 定 0 并注明「罗蛇 T07」，五个满版模板却各自写 `-.02em`
（最后加载的 `style.css` 一压，等于改回去），且标题写死 `'Playfair Display',serif` 绕过
`--font-serif` token。

改动四件，都有样张对照（中文封面 A/B，本轮对话内已出图）：

| 层 | 改法 | 判据 |
|---|---|---|
| 四个模板 `style.css` | 含中文的标题 `.h1/.h2/.big-q/.brand/.logo` 字距 → `var(--letter-tight)`；字体 → `var(--font-serif)`；`11px` 中文位 → 12px | T07 / T13 / T11 |
| `base.css` | 全局 `font-synthesis: none` | T08 |
| `course-module` | 封面 `::after` 幽灵期号，内容取 `attr(data-period)` | 留白当信息位，⛔ 不写死期号 |

实测证据（旧版 / 新版，同一份中文文案）：旧版 h1 落通用 `serif`，**中文句号「。」被 Playfair 截走**、
渲染成基线小点；新版落 `--font-serif`（思源宋体），句号回中宫、字距舒展、`<em>` 不再被合成斜体硬歪。
纯数字位（`.mega`／`.metric .n`／`.section-num`／`.kpi .value`）保留负字距，不受影响。

闸：`check-deck-sync` 因 `base.css` 改动先红（两条交付件指纹不符）→ 重打包
`世纪大道-材质deck-5页.html` 与 `模板pitch-10页-世纪广场.html` 后 PASS（6 登记/2 比对/0 问题）；
`check-theme-textures` 因广兰路渐变旧账红 → `export-theme-textures.py` 重出后 PASS；
`check_doc_claims` 494 项全过。判据与负例写进 `references/theme-full-decks.md`。

## 中文半角标点闸（2026-11-23，v1.2.20）

`build-deck.py` 打包前扫正文文本节点，半角 `, . : ; ! ?` **紧邻汉字**即报，退出码 1、不写产物
（罗蛇 T03：中文句子一律全角，半角夹汉字是硬失败）。`--allow-punct` 降为警告。

三条例外都是实测出来的：`.pdf`/`v1.2.19`/`3.8%` 这类**点后接 ASCII 字母数字**不算句末；
`<code>/<pre>/<kbd>/<samp>` 块整段跳过（示例字符串本来就该带半角）；隔空格不报
（「用 iPhone 拍，ok」这种夹带是正常的）。

负例实测：`tech-sharing` 封面标题原文 `…调度什么?`（`?` 紧贴 `么`）→
`✗ 半角「?」紧邻汉字 → 应写「？」：…异步运行时到底在调度什么? …`，退出码 1；
把 `?` 改全角后复跑 PASS。全库复扫：5 模板 + 1 示例 deck 全 0 处。

## C 出口·原生 PPTX（2026-11-23，v1.2.21）

问题不是「能不能出 pptx」，是「同一份落雪，HTML 与 PPT 能不能长成一个样」。现状三份真源
各抄一份（CSS / A 出口的 prompt 图 / 外部引擎模板），换主题时 HTML 秒变、PPT 不动。
新脚本 `scripts/export-pptx.py` 改成只读一方：主题 `:root` 的 hex 与一套 1600×900 栅格
（1 in = 120 px，版式参数可直接照抄 CSS），用 python-pptx 摆原生文本框与形状。

四件在这个脚本里定死的事：

| 事 | 做法 | 为什么不能省 |
|---|---|---|
| 字体三槽 | 每个 run 同时写 `a:latin`/`a:ea`/`a:cs` | 只写 `run.font.name` 或只写 `a:ea`，会让「3.8%」落到中文字面，数字骨架歪掉 |
| 中/西劈栈 | 按 `is_cjk_family()` 把声明栈分两半，各取第一个装得上的 | 声明栈是 `Playfair Display → Source Han Serif SC`，顺位取第一个装得上的，本机没 Playfair 时中文衬线就去排拉丁 |
| 字体降级声明 | 主题声明栈 → 本机（`fc-list`）→ 同类骨架，命中非首项即打印 ⚠ 并写进 `--json` | PPT 没有 `@font-face`，字体只能靠打开文件那台机器找；不声明就是静默漂移 |
| 变体名归一 | `Source Han Serif SC VF` 与 `Source Han Serif SC` 视为同族 | 按整串比会把「装了」读成「没装」，然后白降一档 |

闸是**回读产物**：页数对齐 spec；逐页数形状、字符；整页 `PICTURE` 占满 90% 面积即红。
负例实测（一份把整页截图贴进去的 pptx）：

```
第 1 页是整页贴图（截图 deck） / 第 1 页只有 1 个形状，像截图不像排过版 / 第 1 页正文 0 字，读不出内容
```

正例 4 页 spec 回读 0 条。本机字体实测：中文首选思源宋/黑（已装），拉丁 Playfair/Inter **没装**，
降级到 Times New Roman / Arial——这是 HTML 与 PPT 目前最长的一条缝，要合上得随包字体或在
pptx 里嵌字体（本库暂不做）。

⛔ 不做什么：不内化 ppt-master 的 2.3 MB SVG→PPTX 管道（依赖 skia-pathops/uharfbuzz，
且它仍是「另一套作者层」，解决不了同源）；不把「逐页截图塞 pptx」当 C 出口的兜底
（`verify-pptx-editable.py` 会红）。

## C 出口补全：8 页型 + 字体三路 + 断行锁定（2026-11-23，v1.2.22）

上一节把管道立起来了，这一节补的是「同一份落雪，两边真的像一个模子」还缺的三块。

**页型扩到 8**：comparison（1fr 90px 1fr，卡顶 3px 色条）、timeline（贯线＋圆点＋年份）、
table（**原生表格**，不是贴图；列宽随 `col_widths` 按比例分）、quote（引号 140px＋正文 56px）。
几何不另起一套：标题 54px 走 `--font-display`、kicker 14px `--accent`，都照 `base.css` 的
`.h2` / `.kicker` 抄；卡片圆角取 `--radius` 18px。表格的下边框要自己塞 `a:lnB`
（python-pptx 没有边框 API），塞进 `tcPr` 时位置必须在 fill 之前，否则 PowerPoint 报修复。

**字体三路**：声明栈 → 随包 → 本机 → 同类骨架。随包那一路是本节的实质改动：
`assets/fonts/latin/` 收了 Playfair Display 与 Inter 的 Regular/Bold 两面（OFL 1.1），
`fonts.css` 改成 `@font-face`，HTML 侧不再依赖 fonts.googleapis.com。只收 RIBBI 族——
ExtraBold/SemiBold 的实例族名带后缀，PowerPoint 的 bold 开关够不着它们。

**断行锁定**：按 HTML 侧那副字面的真实字宽（PIL + 同一批 ttf）贪心断行，把一个 run
拆成多段硬回车，并关掉自动换行。收件人机器缺字面时 PowerPoint 会拿更宽的字顶上，
行会重排；锁了断行，重排不发生，只有字形差异。三个例外是实测定的：中文按字断、
拉丁按词断、禁头标点（，。」）宁可悬挂也不甩到行首。

**近似预览**（`--preview`）：本机没有 LibreOffice，PowerPoint 的 AppleScript 导出 PDF
报 `-1712`/`-1728`，qlmanage 只出首页。于是按产物里的形状自己画一遍，逐页 PNG。
⛔ 它只核位置、断行、色块；阴影/渐变/字距核不了，也不许拿它冒充 PowerPoint 的渲染。

这一轮抓到的三个真缺陷（都由预览看出，不是靠退出码）：

| 症状 | 真因 | 修法 |
|---|---|---|
| 卡片在预览里等于不存在 | 自动图形也 `has_text_frame`，被当文本框画了 | 先判「有没有字」，再判形状 |
| 时间线的点与线全墨色 | 只抓 `#hex`，`--accent:var(--primary)` 被读成兜底黑 | token 解析递归解 `var()` |
| 卡片分隔线是黑实线 | `--border` 是 `rgba(34,34,34,.14)`，非 hex | 按 `--bg` 合成成实色 |

另有两条是闸自己的毛病：字体闸 F4 只看本主题 CSS，不认 `assets/fonts.css` 里的全局
`@font-face`（已把全局声明并入白名单）；`--preview` 里表格先把行高累加了一遍才画，
整张表被推到页脚（删掉那段空转）。

交付面：`--bundle-fonts` 把用到的 ttf 拷到 `<out>-fonts/`，附 `安装字体.command`（macOS）
与 README（Windows 双击装）。⛔ 不走 pptx 内嵌字体：`fntdata` 要 EOT 包裹，raw TTF 会被
静默忽略，且 macOS PowerPoint 与 Keynote 都不认嵌入字体——做一个看不见有没有生效的
字段，不如把文件给到位。

## C 出口收口：标题字号从 CSS 读 + 两族内化（v1.2.23）

v1.2.22 把 8 个页型补齐时，标题字号是脚本里的常数（54px / sans）。换到 `century-sq`
主题上立刻露出两个问题：主题把 `h2` 写到 68px、族名走 `--font-display`，脚本不读它，
出件就比 HTML 小一号；手工传参又会把「单一真源」拆成两份。本版改为读 CSS。

**改动**

1. `--deck-css` 可选传入模板/主题的 CSS，`head_metrics(theme, deck_css)` 按
   「base.css → 主题 CSS → 传入的 deck CSS」三层顺序解析 `h2` 的 `font-family` 与
   `font-size`，取最后一层命中的值。`century-sq.css` 的 `h1,h2,…{font-family:var(--font-display)}`
   与 `h2.title,.h2{font-size:68px}` 都能被这条正则抓到。
2. `head_size` 一读出来就派生出 `head_bottom = 128 + size × 1.42`，四个内容页型
   （comparison / timeline / table）的起始 y 改成 `max(旧值, head_bottom + 20)`。
   原因见下条。
3. `bundled_fonts()` 不再扫目录，改为解析 `assets/fonts.css` 的 `@font-face`：
   CSS 族名（`Space Grotesk`）与文件内部族名（`Space Grotesk Light`）分开存，
   声明写内部名。`assets/fonts/latin/` 新增 Space Grotesk、JetBrains Mono 各两面，
   `fonts.css` 对应两条 `@import` 删掉。

**踩到的坑**

- 68px 标题的字面高比 54px 多出约 30px，而卡片色条仍从 y=224 起——预览里「言」字的
  最后一笔压在红条上。这不是字号错，是内容起点没跟着标题走。`head_bottom` 就是为此
  加的；同一次修正把 timeline 的贯线、年份、标题、说明整体下移同样的 `dy`。
- Space Grotesk 的 400 实例内部族名是 `Space Grotesk Light`。若照 CSS 族名写进
  `a:latin`，PowerPoint 找不到这一族，静默回落到系统字；照内部名写，浏览器那边又会
  对不上 `@font-face`。故两边分开存，各用各的名字。
  同类情况在 Inter 上不存在（内部名就是 `Inter`），所以只有 Space Grotesk 需要这条特例。

**验证**

- `export-pptx.py spec8.json -o v5.pptx --bundle-fonts --preview`：`ok:true`，8 页 40 817 B，
  `head: 68px / sans`（source=century-sq），四个西文槽全部 `首选`、`real_bold:true`，
  `locked_boxes:1`。
- 近似预览 8 张逐页看：标题与色条之间留出 20px，timeline 五站等高排布，
  表头与四行文字未压页脚。
- `--preview` 只核位置、断行、色块；阴影、渐变、字距仍不可核（本机无 LibreOffice，
  PowerPoint AppleScript 导出 PDF 报 −1712/−1728，Keynote 未安装）。

**补测（整册模板的标题覆盖，1.2.42 前的读数）**：course-module 当时自带的 `style.css` 里
`.tpl-course-module .h2{font-family:var(--font-serif);font-size:48px}`（该件已删，读数留档） 走 `--deck-css`
时命中 `('serif', 48.0)`，三层顺序（base 54/sans → 主题 68/sans → 模板 48/serif）成立，
后一层覆盖前一层，不是叠加。

## 染层与墨线，以及真渲染核验（v1.2.24）

上一版 C 出口只到「8 页型 + 字体三路」，渐变与布尔是空缺。这一版补上，并且找到了
本机一直在但没人用的真渲染器。

**渐变：可换算，但按层解释。** `linear-gradient`（角度与 `to <side>` 两种写法、多色标、
rgba 的 alpha）→ `a:gradFill` + `a:gsLst`，角度按 `(css−90)×60000` 换算；
`radial-gradient(circle at x% y%)` → `a:path path="circle"` + `a:fillToRect`。
CSS 的多层 `background` 与单层 `gradFill` 从来不等价，等价的是**多层绘制**：
层数、z 序、每层 alpha 对上即可（纯 src-over）。所以「渐变叠加」在 C 出口是几个同位置形状，
不是一个形状里写两个渐变。

**布尔：PPTX 没有布尔指令，所以在导出时求值。** 结果写成一条 `a:custGeom` 路径。
两条合法路径：① 结果式——瓦作里直接写 `clip-path: path()` 或内联 SVG，B/C 各自解释同一串 `d`，
曲线原样（C 走 `cubicBezTo`，A 段按圆弧采样）；② 计算式——声明 op 与形状参数，导出时求，
当前只覆盖两圆解析解（差/交）与直线多边形。并集不需要布尔：同色叠放即可。

**不换算的写死**：`conic-gradient`、`repeating-*`、`background-blend-mode`、`filter`、
多焦点径向。它们只会得到近似或空白，按红处理，不许静默降级。

**找到了 officecli（`~/.local/bin/officecli`，1.0.161）**：`validate` 做 OpenXML 序列校验，
`view screenshot --page N` 出逐页真渲染（含阴影、字体、形状合成），`view pdf` 可整册导出。
`export-pptx.py --render-check` 把它接进出件流程。

**它当场抓到一个真缺陷**：`spPr` 里 `<a:ln>` 排在 `<a:effectLst>` 之后。
OpenXML 是序列校验的——填充、线、效果必须按 `xfrm → 几何 → 填充 → ln → effectLst` 排。
PowerPoint 容错，别的渲染器与校验器不容错。v1.2.23 及以前所有 C 出件都带这个错
（8 页样张里 2 处，都在 comparison 页的卡片上）。新增 `normalize_sp_pr()`，保存前按
CT_ShapeProperties 的次序重排，不改语义只改次序；重出后 `Validation passed: no errors found`。

**驻留缓存坑（两次假红）**：officecli 有 60 秒驻留进程，`validate` 可能读「上一次」的副本，
于是已经修掉的错还继续报。判据改为：校验前先 `officecli close <file>`（`render_check()` 里已内置）。

**证据**（`wash.css` 三页样张，v6/v8 各一次，均 `Validation passed`）：

- 三色标：`pos=0/45000/100000`，`val=1B2A4A/2F5D8A/D6A63A`，第三枚 `a:alpha val=75000`，
  `a:lin ang=2700000`（= CSS 135°）。
- 径向：`a:path path="circle"`，`fillToRect 30000/30000/70000/70000`（中心 30%/30%）。
- 差集：`custGeom` 193 段，bbox 内归一化后无负坐标；交集同；`path()` 四段 A 弧翻出 49 段。

**仍未闭合**：动效不做——`p:timing` 手写可行，但 XML 体量大、PowerPoint 与 Keynote 解释不一，
HTML 侧保留动效、PPT 侧出静版更稳。渐变插值空间差异（premultiplied sRGB vs sRGB+alpha）是近似，
不是逐像素；`--render-check` 只能看见渲染结果，量不出这项差异。

## 页切换：读瓦作，先探针，再出件（v1.2.25）

上一版把动效整块划掉。这一版拿走能验的那一半：**页级切换**。对象级入场仍不做。

**判据先立：切换必须是纯增量。** 出件前后 `--render-check` 的逐页 PNG 要逐字节相同，
否则就不是「加了一个切换」，而是顺手改了版面。实测 v9（8 页 fade）与 v7（无切换）的
8 张 md5 全等——**说明切换不参与静态绘制**，这条就钉住了。

**速度不猜，读瓦作。** `assets/base.css` 的 `.slide` 声明块里写着
`opacity:0; transform:translateX(30px); transition:opacity .5s var(--ease), transform .5s …`
——页切换在 B 出口就是「淡入 + 30px 横移」。C 出口读同一块：时长取 `transition` 的第一个
时间值（500ms），位移取 `translateX()` 的符号（+30 → 从右侧来）。摘要里写明**是哪份文件给的数**
（`source: base.css`），不拿主题文件冒领。

**为什么不默认 push。** 30px / 1600px = 1.9%；PowerPoint 的 `push` 是整页宽度推移。
把 1.9% 映射成 100% 不是「同源翻译」，是换了个观感。默认 `fade`（透明度本来就是主效应），
要位移感就 `--transition push`，方向自动 `from-right`。

**24 种切换全探针过 schema，两个真错是探针抓的：**

1. `p:blind` 不存在，元素名是 **`p:blinds`**；而且它吃 `dir="horz|vert"`，不是 `orient=`。
   `split` 才是 `orient=` + `dir="in|out"`——`dir` 在两处是**两套不同枚举**，混用直接报 KeyError
   （第一次探针就是这么死的）。
2. morph 的 `mc:Choice Requires="p159"`，**`p159` 前缀必须在 `mc:AlternateContent` 上声明**。
   只写在 `<p159:morph>` 自己身上不够——校验器报 `MarkupCompatibility: prefix not defined`。
   PowerPoint 对这条是宽容的（它按 Requires 去猜），所以不探针就以为写对了。

**收的口径**：只收 OOXML 里能验的 20 种（fade/cut/dissolve/random/zoom/circle/diamond/plus/
wedge/newsflash/push/wipe/cover/pull/split/blinds/comb/strips/wheel/morph）。飞书幻灯片那套
`slides-flip` / `page-curl-double` / `peel-off` 是它自己的转写，不是元素名，**硬映射等于编一个
PowerPoint 不认识的东西**，所以按红：`✗ 页切换 slides-flip 不是 OOXML 的切换类型`。
参数写错同样报红（`fade` 收到 `speed` → `不接受参数 speed`；`split` 收到 `from-left` → `只认 in / out`）。

**未闭合（写在这里，别当已解决）**：
- 播放效果仍核验不了。`officecli` 的 screenshot 是静帧，`validate` 只证 schema；
  真正「翻页时确实淡了」只有 PowerPoint 实机点一次才知道。交付说明里必须写明。
- morph 的补间靠**跨页同名对象**配对。python-pptx 自动起名是每页独立计数的
  （slide1 的 `TextBox 3` 与 slide2 的 `TextBox 3` 是两个不同角色），所以现在 morph 只在
  「同一页型相邻」时近似可用，其余会落成淡入淡出。要真准，得在摆件时按角色写死 `cNvPr` 名——
  那是下一步，不是这一步。

## 染层进产线：`fill` / `boolean` 与瓦作翻译闸（v1.2.26）

v1.2.24 只把渐变与布尔做成了**样张器**（`wash_bridge.py` 单独出件）。这一版把它们接进
`export-pptx.py` 的 spec：页面或形状上写 `fill` / `boolean` / `path`，出件时求值，成为产线能力。

**三个真 bug，都是「声明写了但没生效」那一类：**

1. `root_vars()` 只取第一块 `:root`。`export-pptx` 把 `base.css` 与主题 CSS 拼在一起喂进去，
   于是 base 的 `:root` 把主题的整块顶掉，主题 token 全「未定义」。改成收全部 `:root`、后者覆盖。
2. 同一个函数按 `;` 切声明而不剥注释。主题里 `/* 世纪广场色板 */` 挂在一个声明前面，
   键名就成了「注释 + `--primary`」，被 `--` 前缀判断静默丢掉——**token 明明写了，报的是未定义**。
   实测 `century-sq` 从 28 个 token 恢复到 48 个（`--primary` / `--line-2` / `--steel-hi` 全部回来）。
3. `resolve()` 遇到没定义的变量，拿**整串自己**顶回去：`var(--x)` 被替换成「含有 `var(--x)` 的整串」，
   四轮之后长成一团，最后报 `认不出的颜色：linear`——错指得离病根十万八千里。改成直接报
   `瓦作里没有定义 --x`。

另有两个「渲染对了才算数」的修正：`add_shape` 自带 `<p:style>`（主题 effectRef），
真渲染出来每个形状都挂着投影，而瓦作里它们是平的 → 建完就删 `p:style`；
`Deck.c()` 只认 token 名，传 `#FFFFFF` 会落成默认黑 → 深底白字看不见，改成 hex 直通。

**瓦作翻译闸 `check-wash.py`**：只验**这一份 spec** 要翻的染层。
`conic-gradient`、`repeating-*`、`background-blend-mode`、`filter`、`mask`、`polygon()`、
`union`、未定义 token 一律红；不给 spec 时只报瓦作里的「已知不换算」清单（INFO，不红）。
为什么不全库按红：主题里的 `filter × 24`、`repeating-* × 52` 是装饰，C 出口本来就不还原它们，
把它们算红，闸就永远红、然后被人关掉——那是闸的失败。

**证据**（`examples/pptx/wash-sample.json`，3 页）：

- `wash_bridge` 版 `v8.pptx` 与产线版 `w9.pptx` 都是 `Validation passed`；
  `w9` 页 1 是线性三色标 + 径向亮斑叠加，页 2 是两圆差集（月牙）与交集（透镜），页 3 是 `path()` 四弧圆。
- 页切换仍是 `fade 500ms`（读 `base.css` 的 `.slide`），与染层互不干扰。
- 闸正例 exit 0；负例（conic 渐变 / union / 未定义 token / 未知 shape）exit 1，四条各自点名。
- 四条负例已进 `selftest.py`（存在性自证：把闸改成永绿再跑一次，四条各自报「不会红」，自检 rc=1；恢复后 rc=0）。
  负例还用 `wash-sample.json` 的**真形状**构造，不另编 spec——样例就该兼作判据用的样本。

**未闭合**：布尔仍只有两圆解析解与直多边形；任意曲线的布尔需要真裁剪算法。
`clip-path: polygon()` 不收（`path()` 的字母表里没有 polygon）。`mask` 与混合模式在 C 出口永远缺席。

## 断行三态：把「全册单行」从「量宽失败」里摘出来（v1.2.26）

`export-pptx.py` 一直有句「⚠ 断行未锁定（量字宽失败或缺字体文件）」，只要
`locked_runs == 0` 就打印。**这是个假警报**：断行其实有三种状态，被压成了一个 0——

1. 量了、折了（`locked_runs > 0`）→ 写死硬段，关自动换行。
2. 量了、**每段都单行** → 根本不需要锁定，这是最正常的情况。
3. 压根没量成（缺字体文件 / 缺 Pillow）→ 这才是「收件人换字面会重排」的风险。

实测：`wash-sample.json` 13 段全部单行，却一直顶着那条 ⚠；
`spec8.json` 66 段里只有 1 个框折行，其余全是单行。
也就是说这条警告此前**大部分时候报的是状态 2**，等于把一个健康的产物标成可疑。
现在分开计 `runs_measured` / `measure_fail`，只在状态 3 报红，状态 2 打「全部单行，无需锁定」。

连带清掉了账上的未决项「`--render-check` 在某些 spec 上报断行未锁定、原因未查清」：
原因不是 render，是这条判断本身；跟真渲染无关。

## 折线布尔、角色名与双出口漂移（v1.2.27）

上一版布尔只覆盖「两圆解析解」。这一版把 `boolean` 的操作数扩到 `{path}` 与 `{points}`，
任意两条简单折线都能算差/交，结果可以是**多轮廓**（挖洞、咬成几块）。

**算法与它买的账。** 走「切段 + 分类 + 接力」：双方边在所有交叉点处切开，每段按中点
落在对方内部与否决定留不留，再把留下的**有向**段接回轮廓。比 Greiner–Hormann 好理解，
账也很清楚——共线重合边只能靠 `_on_seg` 的 eps 兜，兜不住的地方直接报而不是硬扛。

**三个真坑，都是「算错了照样出图」那种：**

1. **方向**：交集要两边都按自己的绕向走，差集里 B 的那截必须反向。这条一开始写反了，
   症状是「两条轮廓同向、接力接不上」，报出来的点还正好在交点上，看着像浮点噪声。
2. **端点退化**：圆的 0°/90° 顶点正好压在某条竖直边上，两条相邻边各是 t=1 与 t=0，
   只认「真交叉」就一条都逮不到——整条边零交叉点，布尔看着像「两形相离」。
   改成端点也算、参数夹回 [0,1]，交叉点坐标**双方共用同一个**（各自按参数插值会差 1e-12，
   落进 1e-5 的网格就分到两格，接力还是会断）。
3. **自交折线**：蝴蝶结形状「内部」本身没有定义，算出来的东西能过 schema 只是看着莫名其妙。
   现在先 `is_simple` 判，判到自交直接拒。

**验证不是「看着对」，是拿解析解与栅格当标尺。** 两圆 lens 有闭式解
`2r²acos(d/2r) − (d/2)√(4r²−d²)`；10 组随机「圆 × 凸多边形（3–6 边）」× 差/交共 20 例，
布尔面积与栅格真值差全部 ≤0.25%。这两条已进 `selftest.py`（lens 容差 1%、自交必拒），
并且做过存在性自证：把 `is_simple` 改成恒真，自检立刻红两条。

**角色名（morph 的前提）。** python-pptx 自动名是每页独立计数（`TextBox 3` 这名字在每页都有，
但指的是不同角色），morph 因此对不上。出件时统一改写成 `页型-sN` / `页型-bgN`，
spec 里写了 `name` 的一律不动。实测 4 页样张的 5 个内容框，跨页序号完全对齐。
限制照旧：只同页型相邻可配；可选块忽有忽无会错位（要严格配对就给形状写 `name`）。

**双出口漂移 `--html`。** `check-wash.py spec.json --html deck.html`：spec 里那串声明
（渐变原文、`--token`）归一空白后必须能在 HTML 里找到同一串，找不到就红并指名页/形状。
证的是「两边写着同一份瓦作」，不证「两个渲染器画得一样」。同样进了 `selftest.py`，
负例是「少一条声明仍判绿」——破坏后实测红。

**证据**：`examples/pptx/wash-sample.json` 加了第 4 页（六边形 path 减圆 path、再求交），
`wash-sample.pptx` 4 页 `Validation passed`、真渲染 4 张：页 4 左侧金色缺口月牙、右侧蓝色
六-圆交集，几何正确；页 2 月牙与透镜不变。

**仍未闭合**：共线重合边（两形共享一段直边）在 eps 之外仍会报错；真裁剪（沿曲线切）不做，
弧一律采样折线，段数由 `n` 控制。morph 的播放效果依旧无法核验（screenshot 是静帧）。

## 共享边、系数贝塞尔与 morph 结构闸（v1.2.28）

上一版留了三笔没闭合：共线重合边会报错、曲线被采样成折线、morph 只能声明不能验。这一版逐条收。

**① 共线重合边：换成「同侧 / 异侧」分类。** 旧口径是「中点落在对方边界上就当在里，保留」，
两形共享一段直边时，那段边对两个形都算「里」，于是交集留两次、差集也留，接力就断成开口折线。
新口径先求重叠参数区间（`collinear_overlap`），把区间两端也当切点塞进切点表，再按
**两个形的内部在这条边的哪一侧**分：

- 同侧（都算里）→ 交集留、差集丢；异侧（一边里一边外）→ 反过来。
- 判同侧靠沿法线各探一次（`±off`，`off = max(1e-6, 0.002·L)`），探到自己内部在哪边。
- 重叠那段**只留 A 的那一份**：两份都留就是双线，接力照样接不上。
- 兜底：若 A、B 的首点都落在对方边界上（`pt_in_poly` 返回 None），交集返回 `[A]`、差集报
  「两形边界完全重合，差集为空」。

六条用例（边长 200 的方块，均按真值手算）：

| 用例 | 期望 | 实测 |
|---|---|---|
| 贴边（横移 100）差集 | 40000−20000 = 20000 | 20000.0 |
| 贴边（横移 100）交集 | 100·200 = 20000 | 20000.0 |
| 部分共享（错开 100,100）差集 | 40000−10000 = 30000 | 30000.0 |
| 部分共享 交集 | 100·100 = 10000 | 10000.0 |
| 自差（同一方块相减） | 0 | 报「两形边界完全重合，差集为空」 |
| 相交（同一方块求交） | 40000 | 40000.0 |

⚠️ 这里有两处**旧读数是错的**：上一版记的「贴边差集 40000 / 交集为空」「部分共享差集 10000 /
交集 30000」其实是把同侧/异侧判反的结果（贴边两方块明明重叠 100×200），当时被当成「几何上正确」。
两圆回归不动：交集 86009.4（解析 86084.4）、差集 39564.6（解析 39579.3）。

**② 曲线：保真放在出口，不在求值。** 同类的曲线布尔答案是 Skia 的 `pathops`，正是 `ppt-master`
依赖的 `skia-pathops`（C++ 扩展，与「纯 python3、零外部渲染器」冲突，仍不引）。能拿的是出口保真：

- `arc_to_cubics()` 把每段圆弧拆到 ≤90°，换成 `k = 4/3·tan(θ/4)` 的三次贝塞尔；
- `svg_segments()` 把 `d` 解成 `('move'|'line'|'cubic', …)`——`Q` 升阶、`A` 转贝塞尔、`Z` 收口；
- `custgeom_segments()` 写 `a:cubicBezTo`；spec 的 `path` 默认走它，`"curve":"polyline"` 才回折线。

样张第 3 页的四弧圆改成贝塞尔出件：`wash-sample.pptx` 4 页 `Validation passed`，真渲染页 3
边缘平滑（放大看没有采样折线的棱），页 4 的布尔结果（六边形减圆 / 六-圆交集）不变。
布尔结果仍是折线——只改了「声明里的曲线」，不改「求值出来的曲线」。

**③ 弧的 sweep 方向：两个独立渲染器互证。** 本机 Chrome 可 `--headless --screenshot`，
于是同一条 `M 100 100 A 150 150 0 0 1 250 250` 叠一条 `sweep=0` 的虚线渲一张：
`arc_points((100,100),(250,250),150,150,0,1,4)` 算出的点序 `(157.4,111.4) … (250,250)` 向右上鼓，
Chrome 截图的黑实线也向右上鼓，sweep=0 两处都向左下。这是本轮唯一一次「两个渲染器互证」，
此前只有 `officecli` 一侧。Chrome 报 `CVDisplayLinkCreateWithCGDisplay failed`，不影响出图。

**④ morph：结构能验，播放验不了。** 新建 `scripts/check-morph.py`，验 `p159:morph` 在
`mc:AlternateContent/p159:Choice` 内、`Ignorable` 带 `p159`、`p14:dur` 在 1..2147483647、
以及与下一页的同名形状数（0 个 → 这页的 morph 实际退化成 fade，判红）。

实现里先抓到自己一个错：`p159:morph` 是 `p:transition` 的**子元素**，用直接子元素查找时
每页都误报「没有 p159:morph」，`v10.pptx` 8 页全红。改成 `.//` 后正常：

| deck | 结论 |
|---|---|
| `v10.pptx`（1.2.27 之前出的，未改角色名） | 每页配 2–10 个，配到的全是 `TextBox 1/3/4` 这类**默认名**——正是「假配对」的样子 |
| `morph.pptx`（本轮样张，4 页全 morph） | 5 / 6 / 6 个 `wash-s0…` 与 `wash-bg0` 配对；第 4 页是末页，出注记「空转」不判红 |

末页声明 morph 的口径定为**注记不红**：全册默认 morph 时它必然出现，判红只会变成噪声。

闸接进了 `selftest.py`（两份现造夹具）：同页型相邻 → 必须配对成功（rc 0）；跨页型相邻、零同名
（负例挂在「还有下一页」的那页上，末页不算）→ 必须红。存在性自证做过：把闸改成永绿，自检立刻
报 `FAIL morph 闸不会红` 并整体 `FAIL`。

**仍未闭合**：曲线布尔的真裁剪（沿曲线切）仍要 `skia-pathops`，不引；morph 的播放效果仍是盲区——
本机没有能播放并回报的工具，`officecli` 截图是静帧、`validate` 只证 schema。同类同此处境：
`jsamuel1/PptxGenJS` 的 morph 分支在自家验收清单里也只勾了「schema 通过」。

## 可选后端与逆流出口（v1.2.29）

两件事：把「零依赖做不到、但同类都在做」的曲线布尔与整段 shaping 做成可选后端；再加一个反方向出口（PPTX → HTML）。

**① 曲线布尔：装上就真裁，没装就说降级。** `wash_bridge.curve_bool` 把两串 `path` 读成 pathops 的 `Path`，
求完从 `dump()` 的文本读回轮廓（`Path` 没有稳定的遍历 API，`dump` 的格式是 FontTools 同款，比猜 API 稳）。
`dump()` 只往 stdout 写、签名里没有 stream，所以捕获必须 `contextlib.redirect_stdout`。

精度口径要分清两件事：

- pathops 自己报的面积 `path.area` = **12288.7**，解析 lens（r=100、心距 100）= **12284.4**，差 **0.03%**——
  这点误差来自「圆被三次贝塞尔近似（k=0.5523）」，不是布尔算错。
- 我们 `curves_area()` 是**把结果曲线按 8 段采样**再算面积，得 12228.9（差 0.45%）——这是**对账工具的采样误差**，
  别拿它当产出精度。所以自检容差放在 2%，并对账只用解析 lens 与 pathops 的 `area`。

出件实测：样张第 4 页的「六边形 − 圆 / 六 ∩ 圆」原走折线，装上 pathops 后自动改走真裁剪，
`Validation passed` + 4 页真渲染正常（第 4 页圆弧边平滑，直边仍是直边）。出件摘要打
`曲线布尔：2 个走 skia-pathops 真裁剪（结果带 cubicBezTo）`；`--json` 的 `wash.backend` 带
`{"pathops": true, "uharfbuzz": false}`。

降级与强制两档都造了负例（用 `PYTHONPATH` 塞一个 `raise ImportError` 的 `pathops.py` 假模块）：

| 场景 | 期望 | 实测 |
|---|---|---|
| 缺后端 + `curves` 不写（auto） | 出件成功，但必须报降级 | `⚠ 降级：2 个布尔退回折线——本机没装 skia-pathops` |
| 缺后端 + `curves:"require"` | 必须红 | `✗ 第 1 页 curves=require：spec 要真曲线裁剪，但本机没装 skia-pathops` |
| 有后端 + auto | 不报降级 | `曲线布尔：2 个…`，无降级行 |

两条都进了 `selftest.py`（屏蔽 pathops 的整轮自检也跑过：打 `INFO 未装 skia-pathops…` 后仍 `PASS`，
说明缺后端不等于坏件）。

**② uharfbuzz：接好了，但这台机器没有装。** `wash_bridge.hb_width` 走 `Buffer.add_str` → `guess_segment_properties`
→ `shape` → 累加 `x_advance`，`export-pptx.py --hb-measure` 才启用；缺后端时打
`量宽：要 --hb-measure 但没装 uharfbuzz，已回落逐字` 并继续出件（实测这一支）。

⚠️ **整段 shaping 那一支没有实测过**——本机 `import uharfbuzz` 失败。同时它是**默认关**的：整段 shaping
与逐字累加在长句上会差 1–3%，足以挪动断行点，换后端等于换一份断行。要用的人自己开，出了问题也看得见是哪一档。

**③ 逆流：PPTX → HTML。** `pptx-to-html.py` 读形状不抓渲染。实测：

| 输入 | 产物 | 读到的 |
|---|---|---|
| `examples/pptx/wash-sample.pptx` | 17 KB，4 页 | 形状 30（图 0 / 表 0 / 文本框 16） |
| `v7.pptx`（早前的 8 页 deck） | 28 KB，8 页 | 形状 82（表 1 / 文本框 64） |

三处关键映射各验了一次：`a:gradFill`（含 `<a:path path="circle">` 的径向）反解成 CSS 渐变；`custGeom` 的
`moveTo/lnTo/cubicBezTo` 读成内联 SVG（月牙、透镜、切角六边形在三页上都还原了轮廓）；表格出 `<table>`。
Chrome headless 截整页核对：页 1 的斜向三段渐变 + 径向亮斑、页 3 的四弧圆、页 4 的两个布尔结果都在。
⚠️ 第四页的圆在 HTML 里只剩首色（SVG 兜底不铺渐变），这是已知的近似。

**仍未闭合**：曲线布尔只在装了 pathops 的机器上有效（没装仍是折线，且已明说）；uharfbuzz 的 shaping 分支未实测；
逆流不还阴影/3D/艺术字，图表与 SmartArt 只留占位框。

---

## 1.2.30（2026-11-23）：往返只改字、渲染核验降耗时

**① 往返闭环。** `retext-pptx.py` 在**原文件**上换文字节点，不重排。实测（`wash-sample.pptx`，4 页 16 个文本框）：

| 场景 | 期望 | 实测 |
|---|---|---|
| `--dump` | 每页非空文本框都列出，带几何指纹 | 16 行，`slide/id/name/text/paras/runs/geom` 齐 |
| 3 处改动（页 1 两行标题、页 1 备注、页 2 按 name） | 全部落、几何一动不动 | `applied 3 / skipped 0`，16 个形状 `geom` 全同；`validate` 通过，`issues` 0 |
| 点不存在的 id | 进 `skipped`，不误伤别的形状 | `skipped 1`，其余零变化 |
| 只改备注（不点名形状） | 直接落到该页 notes | notes 回读即新句 |
| 改完再渲一页 | 版式不变、只有字变 | `rt1.png`：标题换了、行高与位置未动 |

修过一处口径：最初要求备注也必须点名形状，用例里会误报 `skipped`；改成 `{"slide": N, "notes": …}` 直接落。
另给 `pptx-to-html.py` 的每个形状 div 加了 `data-slide/data-id/data-name`——HTML 里看得见身份，
照 id 填 `edits.json` 就能闭环。

自检落点：`selftest.py` 加一段往返判据（dump → 改字 → 回读比 `geom` → 备注非空），跑通打
`PASS 往返闭环：只改字、几何指纹未动、备注已落`。

**② 渲染核验的耗时账（据此改 `render_check`，不是内化 officecli）。**

| 调用 | 实测 | 说明 |
|---|---|---|
| `close` | 0.4 s | 驻留可能拿着旧副本，validate 前必跑 |
| `validate` 冷/热 | 0.93 s / 0.27 s | schema 通不通 |
| `view issues --json` | 0.24 s | 样张 `count=0`；有值时给 `low_contrast`/`picture_aspect_distorted`/`preset_adjust_refused` 等类型 |
| 单页截图 1600×900 | 5–7 s / 页 | 4 页 ≈ 23 s |
| `--page 1-4 --grid 2` | 5.27 s | 一次调用出整册缩略拼图（1600×916） |
| `--page 1-4 -o 前缀.png` | 5.64 s | 产物是 852×1920 竖排拼图，**不是**逐页全分辨率 |
| 多页 `-o` 目录 | 报 No headless browser | 不可用 |
| `view … pdf` | 报 No exporter plugin | 不可用 |

结论：耗时在渲染器，二进制内化省不了；可拿的是合同。`render_check(out, pages, grid, only)` 与
`--render-grid` / `--render-pages` 已接线，样张实跑：
`真渲染核验：OpenXML 通过，整册缩略 grid.png → g1-render/；结构问题 0`（4 页 5.3 s，对比逐页 23 s）。
落点：`issues` 前置（先拿可判问题，再等渲染器）、`grid` 一次调用管炸版、点名页只重渲。

---

## 1.2.31（2026-11-23）：成稿闸——文字不够密度就不出片

**来雪亭不生成文字，只当判官。** 九条判据里七条红、两条警告，全部可复算（同一份 spec，谁跑同一个结论）。

| 场景 | 期望 | 实测 |
|---|---|---|
| 套话版 `bad-spec.json`（「全方位赋能…打通全链路…」） | 必红，且要点名到字段 | 26 条红：P1 套话 17 / P2 标题空转 / P4 单条 27–31 字 / P8 空页，`exit 1` |
| 同一份走 `export-pptx.py` | **拒出件** | 「✗ 成稿闸拦下：26 条红」，退出即止，`bad.pptx` 未生成 |
| `--allow-prose` 放行 | 出件但留记录 | 「⚠ 成稿闸 26 条红，按 --allow-prose 放行」，`--json` 里 `prose.red=26` |
| 抬密度版 `good-spec.json` | 全过，直接能出片 | `--strict` 也 0 红 0 警告；出 3 页 32 KB，整册缩略 grid.png 结构问题 0 |
| 空页 `kpi`/`end`/`quote` | 不判「太薄」 | 三页 KPI 页不报 P8 |
| 单位缩写 `8 GB` | 不判「术语无注」 | 只报过一次，加 `UNITS` 白名单后不再报 |

误判修过两处：`kpi` 页只数标签会把「一个数一页」判成空页（改按页型豁免，并把数值一起计入）；
`GB`/`PDF` 这类单位本来就不括注（加白名单）。

落点：`scripts/check-prose.py`（九条，`--strict`/`--json`）；`export-pptx.py` 的 `prose_gate()` 挂在
spec 载入后、形状落版前（闸在出件前，不在渲染后）；`references/prose-gate.md` 记判据与三步；
`examples/prose/` 三件对照。

---

## 1.2.32（2026-11-23）：五型提示词配方与判型

**为什么加**：九条判据判「密不密」，判不出「型对不对」。一份该写提案的东西按汇报写，每页都过闸、整体跑偏。
所以加一层：先判型（触发词×2＋结构信号），再出该型的固定提示词；提示词与闸同源，写的时候就把判据满足掉。

| 场景 | 期望 | 实测 |
|---|---|---|
| 五份夹具各自判回自己 | 5/5 判对，无并列 | `briefing→briefing`、`proposal→proposal`、`teaching→teaching`、`retro→retro`、`launch→launch` |
| 抬密度版 `good-spec.json` | 判成汇报，且分差不含糊 | `汇报 5 分（win 3）`；早先误报「发布 2／提案 1」是取文漏了 kicker，改 `collect_text` 后修正 |
| 两型分数接近 | 明说「两型都对」，不硬判 | 头名与次名差 ≤2 时输出「分段写」，不自动选一型 |
| 五条提示词 | 都有「硬要求」与「四问」两段 | 5/5 齐（缺任一段自检即红） |
| 每份没说给谁看 | 0 分时说「先补一句这是给谁看的」 | `--detect` 0 分走提示分支，不硬套型 |

落点：`scripts/pick-recipe.py`（RECIPES 是提示词唯一正本）；`check-prose.py --suggest` 闸后判型；
`references/prose-recipes.md`（判型规则与五型骨架，⛔ 不抄提示词）；`examples/prose/recipes/*.md` 五份夹具。
自检新增 `PASS 提示词配方：五型自判自回、提示词齐（硬要求＋四问）`。

⚠️ 判型只覆盖中文触发词；英文稿会落到 0 分，此时按「汇报」起步——这一支没实测。

---

## 1.2.33（2026-11-23）：判型扩到三语，中文优先

**为什么**：只认中文触发词，一份英文稿会落到 0 分，进入「按汇报起步」的兜底——等于外文没有判型。
扩到中/英/日，但**不改中文的地位**：中文命中计 2 分，外文计 1 分。

| 夹具 | 期望 | 实测 |
|---|---|---|
| `briefing.md` / `proposal.md` / `teaching.md` / `retro.md` / `launch.md` | 各自判回自己 | 5/5 对（13/11/5/14/8 分） |
| `en-proposal.md`（英文预算申请） | proposal | 4 分，次名 launch 1 |
| `en-retro.md`（英文 postmortem） | retro | 4 分，其余 0 |
| `ja-teaching.md`（日文仕組み说明） | teaching | 5 分，其余 0 |
| `mixed-zh-first.md`（中英混排，中文为主） | briefing，不被 budget/proposal 带偏 | briefing 7 vs proposal 2 |

实现口径：中文按子串计数（中文无词边界），英文按 `(?<![A-Za-z])词\w{0,4}(?![A-Za-z])` 词边界匹配
（`report` 不命中 `reporter`，允许复数与时态）；外文结构信号只计 0.5，避免一条 `next step` 就把中文稿判成提案。
`--show` 的提示词仍是中文，末尾附折算规则（26 字 ≈ 54 字符、禁词按同义替换），⛔ 不另出一套英文提示词。

自检扩到九份夹具（原五份＋英 2＋日 1＋混排 1），全过：`PASS 提示词配方：五型自判自回、提示词齐（硬要求＋四问）`。

⚠️ 法/西/韩语未收触发词；命中会是 0 分并提示「补一句这是给谁看的」。要不要再加，看实际用不用得上。

---

## 1.2.34（2026-11-23）：梁架 36 式并成 14 族

**为什么并**：36 个单页文件里，大半是同一骨架换栏数、换画法。挑版式时面对 36 个名字，选择成本高、
差别又说不清——那就不是「多」，是「没归位」。

| 族 | 含几式 | 旧名 |
|---|---|---|
| `cover` / `section` / `end` | 1 / 1 / 2 | cover；section-divider；thanks+cta |
| `text` | 3 | bullets, two-column, three-column（栏数改 `g2`/`g3`） |
| `quote` / `toc` | 1 / 1 | big-quote；toc |
| `code` | 2 | code, terminal |
| `compare` | 4 | comparison, pros-cons, diff, image-compare |
| `charts` | 4 | chart-bar, chart-line, chart-pie, chart-radar |
| `image` / `image-set` | 4 / 2 | image-hero, image-full-bleed, image-single, image-text-split；image-grid, image-gallery |
| `process` | 4 | process-steps, timeline, roadmap, gantt |
| `diagram` | 3 | flow-diagram, arch-diagram, mindmap |
| `data` | 4 | kpi-grid, stat-highlight, table, todo-checklist |

做法：族页里每段是一条旧页的完整 `<section>`（示例数据原样保留），一个文件 1–4 段；`_families.json` 是
族↔式的唯一正本。实测：`charts` 族离线渲染出柱状图（此前 CDN 断开时是空白，截图见交付记录）；
`code` 族离线出代码页。

**顺手修的两处**：① Chart.js 随包（205,637 B，MIT，`assets/vendor/`）——「全部离线可跑」这句以前在
charts 页上是假的；② highlight.js 撤掉——原来只引了 core 与语言包、没引主题样式，屏上一个颜色都不出，
要么连主题一起收要么不收，选了不收。

**闸**：`scripts/check-layouts.py` 六条（L1 族↔文件、L2 段数↔式数、L3 旧名复活、L4 文档旧名、
L5 族页指外网、L6 vendor 存在）。负例实测：故意造一个 `bullets.html`，闸报 `L3 旧名又长回来了：['bullets']`，
自检整轮红；删掉后 `PASS 梁架闸：14 族可过、旧名复活必红`。

**连带改的锚点**：`check_doc_claims.py` 里「B 出口版式数」与「归属表版式数」两条正则随词汇改成「族版式」
「族」；否则闸会报「锚点消失」，而那种红是假红，会教人学会忽略闸。

---

## 1.2.35（2026-11-23）：字号阶梯、结构层、装得下闸

**起因**：用户让拿外部真件（`/Users/nath/Desktop/利兄原创PPT`，200 页版式库 ＋ 50 套模板 1011 页）反查
我们的版式口径。实测结论写进 `references/style-audit.md`：画布 960×540pt（1920×1080 上 1pt＝2px）；
字号只用 7 档（32pt 页标题 517 页最众、14pt 正文主力 296 次、12pt 图注），层级靠**少档位＋大跳步**；
页左边距众数 6%；卡片 4 栏 123 / 3 栏 102 / 2 栏 79；无描边 2112 ≫ 1pt 描边 662；主色黑白＋单 accent。

对照下来，我们原来的 72/54/32/22/24/14/13 有两处硬伤：54→32 掉到 0.59（跳步不成立），
最下一档 13px＝6.5pt 已跌破投影下限；而且把 12pt 配 1.7 行距，等于把 Word 文档压进一页。

**改法**：

| 层 | 改了什么 |
|---|---|
| `assets/base.css` | 新增 `--t-hero/display/h1/h2/h3/h4/body/body-sm/cap` 九档（200/144/80/64/48/40/32/28/24px）＋ `--lh-body:1.6` / `--lh-tight:1.15`；`.slide` 正文改 `var(--t-body)`，padding 收到 `72px 112px`（6%） |
| 9 套主题 ＋ 5 份整册 | 硬编码 `font-size` 共 204 处机械吸附到阶梯（92→h1、68→h2、44→h3、30→body、16/17→cap），主题不再各开一套字号 |
| 族页内联字号 | data 56→h2、260→hero；end 180→display、96→h1、14→cap；quote 140→display、56→h3、20→cap（顺带把 `margin:-40px` 改 `-8px`，修 26px 上越界）；section 112→h1；text 13→cap、40→h4 |
| **`assets/layouts.css`（新建）** | 发现 `flow/node/arr/arch/tier/cells/steps/tl/rm/gantt/gg/gal/hero/bleed/split/cmp/vs/pc/diff/term/todo` 这些结构类**在 base.css 与主题里一个都没定义**，`diagram` 页裸渲染成「一列竖排文字」。新建 16 节结构层，并把 `<link>` 插进 16 个族页 |
| 新增两族 | `ring`（枢纽五向 / 环四步）、`split`（表左结论右 / 判左图右）；`_families.json` → 16 族 40 式 |
| **`scripts/check-fit.py`（新建）** | 装得下闸 F1–F4 |
| `scripts/check-layouts.py` | 加 L7：族页用到的 class 必须在 CSS 里真有样式；`{1,30}` 改 `{0,30}`（否则单字母类 `.p/.c/.b/.t/.n` 抓不到） |
| `scripts/check-prose.py` | 阈值随 32px 正文重算：单条 27→20 字；正文下限 36→30、上限 300→260 |

**踩的坑（写下来免得重犯）**：`check-fit.py` 初版把页面复制到临时目录再软链 `assets`，探针注入文件
**写穿 symlink 改了 14 个族页源码**（`code.html` 里出现两份探针脚本），同时让早期「装得下」全是假绿
（CSS 没加载，dump 只有 4.7KB）。改成本机只读 HTTP 服务、请求 .html 时注入，不落文件；用
`git show HEAD:…/code.html` 还原并重挂 `layouts.css`。另修：`.gg .cell.c6/.c7` 曾映射到同一格重叠、
`.split` 右栏被图片固有宽度挤成 138px（改 `minmax(0,1.05fr)`）、甘特条 26px 高装 24px 字必裁（条高 34）。

**自检**：新增两条负例——① 灌 40 行的一页必须红（`PASS 装得下闸：16 族都装得下、溢出页必红`）；
② 往 `text.html` 塞一个没样式的类必须红，塞完原样还原（`PASS 梁架闸 L7：没样式的类必红`）。
`python3 scripts/selftest.py` → `PASS 冒烟自检`（rc=0）。

**连带**：主题 CSS 一改，瓦作纹理的 `source_sha256` 全部失配（`qiu-r` / `panyu-rd` / `wanhang-fy` 等 9 项），
重跑 `scripts/export-theme-textures.py` → 9 主题 74 张；`check-theme-textures.py` 转 `PASS 瓦作出图闸`。

**照做与不照做**：照做的是字号档位、6% 页边距、少描边、单 accent；不照做的是「一页一主题」的成品版式
（那是成品不是骨架，照搬会退回 36 个单页）、以及它 28.5 个形状/页的密度（我们的族页是骨架，
到成稿阶段才由内容撑满）。

---

## 1.2.36（2026-11-23）：16 族 / 28 式——只合「骨架同构」的变体

**判据**：把每段 HTML 的标签与 class 抽成骨架串（丢文案）比相似度，外加语义判断——**只有“骨架同构、
只差一个参数”才允许合段**。合掉的 12 个变体与依据：

| 族 | 合掉 | 依据 |
|---|---|---|
| `text` | two-column, three-column | 同段换栏数（`g2`/`g3`），文档早已这么写，记成 3 式是记名 |
| `compare` | pros-cons, diff | 同两栏骨，只差标记（`mark=pc` ✓✗ / `mark=diff` 旧→新） |
| `charts` | line | 柱↔线骨架相似度 **1.00**（同样 12 个节点，仅 canvas 配置不同） |
| `image` | full-bleed | 与 hero 差“压不压字＋要不要 scrim”，是开关 |
| `image-set` | gallery | 与 grid 差 bento 的 span 摆法（`c6/c7` 已在用 span 2） |
| `end` | cta | 只多一行按钮 |
| `code` | terminal | 只差窗口框（`chrome` 开关） |
| `data` | stat-highlight | 与 kpi 差“N 个数字 vs 1 个数字”（`n=1`） |
| `diagram` | mindmap | 与 `ring-hub` **跨族重复**（中心＋辐条），并入辐条数参数 |
| `split` | split-flip | 与 table 差右栏载体（`media=table/image`） |

**不合并的**（骨架相似度 0.13–0.18，真不同排布）：`process` 四式（步骤卡／时间轴／泳道／甘特条）、
`charts` 的饼与雷达、`table` 与 `todo`、`ring-hub` 与 `ring-cycle`。

**做法**：族页删掉 12 段，参数写成段末 `.params` 注记（`layouts.css` 新增 `.params` 与 `.params code`）；
每段加 `data-style="…"`。`_families.json` 改结构：`styles` 是段与式的一一对应，`of` 退为
「旧名别复活」的针（不再等于段数）——这是关键，否则合段就会顺手丢掉 L3/L4 的防护针。

`check-layouts.py` 的 L2 随之改成**按 `data-style` 集合与段数双向对账**（只数段数会漏“两段标了同一个
data-style”）。实测：`梁架闸：16 族 / 28 式 —— 可以交付`。

**代价**：原来看一眼就能看到的 12 个小样没了，改成一行参数文字。这是有意的——「式」是给人挑版式用的
名字，不该由“演示了几张脸”决定；参数能不能生效，靠 C/B 出口的渲染与 `check-fit` 保证。

---

## 1.2.37（2026-11-23）：图表——自绘三式 + C 出口原生 chart

**缺口**：C 出口原先只认 8 页型（cover/bullets/kpi/end/comparison/timeline/table/quote），**没有图表**——
带图的 deck 出可编辑 pptx 时，图表页无处安放。B 出口也只有轴图/饼/雷达三画法，汇报里最高频的
「小数据可数单位」「增减分解」「前后对比」都没有。

**补的三式（B 出口，纯 CSS，不引新依赖）**：

| 式 | 画法 | 硬规则 |
|---|---|---|
| `chart-unit` | 10×10 点阵，一点＝一单位 | 副标题写单位；>100 改百分比条 |
| `chart-waterfall` | 正负同轴细块，期初/期末实心 | 柱不断轴；≤6 级 |
| `chart-dumbbell` | 两时点串珠＋连接线 | 前后对比 ≤6 类，别用双柱假装 |

**C 出口图表页**：`type: "chart"` → python-pptx `add_chart`，**真 chart part**（PowerPoint 里能改数据、
换系列、改配色），不是贴图。`kind` 只认 `bar / bar-h / line / pie / doughnut / radar`；系列配色从
`--accent` 向 `--bg` 分级淡出（不写死第二份调色板）；饼图按点配色并标百分比。

**不许静默降级**：瀑布/哑铃/点阵在 DrawingML 里没有原生等价，`export-pptx.py` 遇到这三种
**点名拒绝**并说明理由，不许塞成柱状图——这与瓦作「conic、混合模式一律报错」是同一条纪律。

**自检新增两条**：① 图表页导出后回读 `has_chart`，系列 2 / 类目 4 必须对得上；② `kind=waterfall`
必须红且报 `chart kind`。实测 `PASS 图表页：原生 chart part、2 系列 4 类目`。

**判据卷**：新建 `references/chart-grammar.md`（数据形状→图型 17 条 + 语法四条 + B/C 差异）。
图型选型思路参考了 `lieflat-charts`，但**未复制其代码、模板、命名与配色**——它的许可是
PolyForm Noncommercial 1.0.0，商业使用需另议，所以只内化判据、实现自写。

**顺手修的旧 bug**：`charts.html` 三段的 `<canvas>` 全用 `id="c"`，Chart.js 取的是第一个画布，
饼图与雷达实际画进了同一块。已改 `c-axis / c-pie / c-radar`。

---

## 1.2.38（2026-11-23）：bento 补层级

旧 `.gg` 的 c2–c5 共用一条底色规则，七格同灰＝等分网格，不像 bento。改法只在**层级**上动，不碰几何：

- `c1`（2×2）铺一层 accent 22% 的斜向渐变，字升到 `--t-h4`、600 字重——它是唯一的主图格；
- `c7` 是全页唯一强调格，铺 `--accent` 实底、字用 `--accent-ink`（逐主题换算过，不用硬编码白字）；
- `c2/c4` 走 `--surface-2`、`c3/c5` 走 `--surface` + 发丝边，两级明度交替；
- 5 格版本（去掉 c6/c7）仍是 4×2 满格，不塌成空洞。

---

## 1.2.39（2026-11-23）：削上游主题至 28 件

先答一个事实：**36 个单页版式确实已经不在了**——2026-11-23 并成 16 族（`check-layouts.py` L3 一条硬闸：
并掉的旧 stem 不许以 `<stem>.html` 复活）。上游留存下来的只有 `assets/themes/upstream/`。

逐件数引用后（全库 md/json/html/py 文本扫描 + 显式 `<link>` 扫描）：

| 上游主题 | 引用情形 |
|---|---|
| `minimal-white` | 16 个族页的 `theme-link` 默认皮肤 + `examples/` 若干 |
| `swiss-grid` | `examples/demo-deck.html`、`references/path-b-html.md` 示例、styles-unified 第 18 式映射 |
| `tokyo-night` | `presenter-mode-reveal` 整册 |
| 其余 33 件 | 零 `<link>`，只作文档里的可选色板 |

其中 **8 件连文档都没点过名**（零提及零链接，真孤儿）：`bauhaus`、`catppuccin-latte`、
`glassmorphism`、`gruvbox-dark`、`news-broadcast`、`rose-pine`、`sharp-mono`、`solarized-light`。已删，36 → 28。

⚠️ 但**声明仍不能撤**：`runtime.js`（1162 行）、`base.css`、`animations.css`、`fonts.css`、`render-png.sh`
与 5 套整册仍建立在这套底座上，MIT 要随附版权声明；主题减法只是把第三方面从 36 件收到 28 件。

---

## 1.2.40（2026-11-23）：主题层彻底去上游 + 字体层重写

**动作一：上游主题 28 → 0。** 把余下 28 件全删，`assets/themes/` 只剩 9 件自建瓦作。
随之要断的三处硬引用：
- 16 个族页的 `theme-link`：`themes/upstream/minimal-white.css` → `themes/guanglan-rd.css`（冷调浅底，最接近原先的中性观感）；
- `examples/demo-deck.html`：`swiss-grid` → `guanglan-rd`；
- `presenter-mode-reveal` 整册：`tokyo-night` → `century-ave`（暗底＋暖 accent），`assets/decks.json` 登记名同步改成「× 世纪大道」，`data-themes` 三件换成本库瓦作。
`check-deck-sync.py` 曾报「源引用 century-ave，登记的是 tokyo-night」——登记与页面必须同一口径，改完 0 问题。

**动作二：备选配色不落成文件。** 新建 `references/palette-atlas.md`：六组骨架（素灰 / 终端墨 / 和纸 / 暖刊 / 铁线 / 霞粉），
只写 token 值与挑组四问（投影明暗 / 数还是话 / 几处彩 / 撞不撞瓦作）。色值按本库口味重调，不是任何上游色板的抄本。
判据四条：单 accent、纸底不用纯白（铁线例外）、`--accent-ink` 逐组算对比、明度至少四档。

**动作三：`assets/fonts.css` 重写。** 原文件头挂 `html-ppt ::` 标记、结构沿上游 `@import` 四行＋逐条 `@font-face`。
现改为自写版本：删标记、删没人引用的 Archivo Black 远程 import、八个西文字面压成单行块、中文内化与语义槽位分节注释。
功能等价（字体族名、字重区间、相对 url、`--font-ui-zhizao` / `--font-body-song` 两个槽位一字未改），代码是新写的。

**已验证**：文档对账 449 项（references 59 份）、装得下 16 族 + 5 册、字体闸 9 主题 0 FAIL、整册同步 0 问题、
预览页一致 0 FAIL、配色体检 9 件全 OK。

**仍未动的上游件**：`assets/base.css`（294 行）、`assets/runtime.js`（1162 行）、`assets/animations/animations.css`（138 行）、
`scripts/render-png.sh`（98 行）。这四件是真正的底座，要连「L-* 网格 / 演讲者视图 / 键位」一起重写，属下一批。

---

## 1.2.41（2026-11-23）：基座层与动效层自写；色板三律落进 token

**一、`assets/base.css` 重写（294 → 246 行）。** 结构从「英文上游注释＋变量堆」改成「判据在前、token 在中、原语在后」：
文件头立**色板三律**（单 accent／明度阶梯四档／`--accent-ink` 逐主题算），再补一条主色压底不足 3:1 的解法——
新 token `--accent-edge`（默认取 `--text-1` 30% 混合），配 `.accent-fill` 与族页里五处主色实底块统一带 1px 内描边。
网页语义与类名一个没丢：`.deck` / `.slide` / `.is-active` / `.is-prev` / `body.single` / `data-fit="fluid"` /
`.card*` / `.pill*` / `.img-frame*` / `.deck-header/footer` / `.progress-bar` / `.deck-logo` / `.notes` /
`.overview` / 九档 `--t-*` / 印刷块全部照旧，`runtime.js` 不用改。

**二、`assets/animations/animations.css` 重写（138 行）。** 26 个 `.anim-*` 类名一字不改（runtime 的 ANIMS 表与文档计数都以它为准），
`@keyframes` 统一改 `lx-` 前缀，曲线按本库口味收（.65s 基准、stagger 前八条等差 .1s），并写明六条纪律：
只动 opacity/transform/filter/clip-path、入场一次不循环、五个循环类单列、3D 透视不超过 1600px、
路径长于 1000 的图形要自改 dash、`prefers-reduced-motion` 全关。

**三、色板体检（YouTube 4 条判据）跑过 9 件。** 结果：**0 件正文对比度硬伤**、8 件全清、1 件 ⚠️——
`century-sq` 的主色 `#dab406` 压底色 `#eef3f7` 仅 **1.79:1**（BLK 判据要 3:1）。按规范给的第二种解法落地：
不压深标线黄（那会换掉主题身份），改「1px 描边」，并在 `century-sq.css` 头登记依据
（主色不作大面积底色＋五处实心块带 `--accent-edge`）。⚠️ 闸仍报 1 项 W：它只读 `:root` 的 hex，看不见描边——
这是判据的边界，不是新问题。

**四、顺手修的两处。** `.gg .cell.c1 span` 原写 `color:var(--text)`（库里没有 `--text` 这个 token，属 1.2.38 引入的笔误），改 `--text-1`；
`century-sq.css` 加注释后纹理源 sha 变了，重跑 `export-theme-textures.py` 出图 74 张，`check-theme-textures` 回 0 提醒。

**五、第三方面收缩。** 自写后 `base.css` / `fonts.css` / `animations.css` 不再挂 `html-ppt ::` 标记、不再计入「复制进来的资产」；
ATTRIBUTION 与 THIRD_PARTY 均改为「仅 `runtime.js` 一件是上游派生」。**声明仍不能撤**，但只剩一件待重写。

**已验证**：文档对账 449 项（themes=9 / references=59 / animclasses=26 / anims=27）、装得下 16 族 + 5 册、
梁架闸 16 族 31 式、配色体检 0 FAIL、预览一致 0 FAIL、瓦作出图 9 主题 74 张、自检全 PASS。

## 1.2.42（2026-11-23）：运行层与出图层自写，整册改写，上游声明整份撤除

**一、`assets/runtime.js` 整件重写（自写，`node --check` 通过）。** 页面契约一条未改：16 族页与 5 套整册不用动一行。
重写的六件事：画布缩放、`go(n)` 唯一状态出口、入场动效重触发与 `counter-up` 缓出计数、讲稿抽屉与总览克隆、
演讲者窗、`#/N` 深链与 `?preview=N` 锁定。文件头写三条纪律（页数不数 DOM／状态只从一个出口写／两屏只通过通道说话）
与完整键位表（含新增的 **B 黑屏、G 参考线**）。演讲者窗自写成**四张可拖卡**（当前／下一页 iframe／逐字稿／计时），
`BroadcastChannel` 双向同步、`R` 重置计时，与 `references/path-b-html.md` 的口径对齐。

**二、实跑验证（不是只看语法）。** 无头 Chrome 打开多页 deck，`--dump-dom` 里读到：`progress-bar` 1 个、
`data-total="8"` 2 处、`is-active` 9 处、`overview` 容器 1 个 —— 说明缩放、注入、状态与总览克隆都真的跑了。
单页族页（`body.single`）不注入进度条，属预期。

**三、`scripts/render-png.sh` 整件重写。** 保留 CLI（`<html> [N|all] [out-dir]`、`CHROME_BIN`、`FORCE=1`），
去掉旧的 `?render` 查询串（改直开 `file://$ABS#/$i`），头注改成四条判据：① 数页先剥 `<script>/<style>` 且用词界匹配；
② Chrome 写不出文件也给 0，成败只认「目标文件非空」；③ 已有且非空默认跳过，重出要显式 `FORCE=1`；
④ 逐页靠深链落位，不靠键盘模拟。失败页数非零即非零退出。

**四、五套整册改写，这是撤声明的前提。** 先用 `SequenceMatcher.quick_ratio()` 量旧件与上游示例：
`weekly-report` / `pitch-deck` / `course-module` / `tech-sharing` / `presenter-mode-reveal` 与对应上游模板
**相似度≈0.99** —— 即「只改了品牌字样」的搬运件。故本批把五册连各自那份 `style.css` 一并改写：
内容换成本库自己的语域（周报讲本周拆上游、讲义册、路演册讲三出口、技术分享讲规格化、演讲者册讲键位与四张卡），
结构只吃 `base.css` + 主题（`style.css` 五份**全部删除**），页码与 `assets/decks.json` 登记值对齐（7/10/6/8/7）。
讲义册主题改挂 `qiu-r`（虬江），与「讲义」气质相配；登记名同步为「模板 · 讲义单元 × 虬江」。

**五、声明整份撤除。** `LICENSE-html-ppt.txt` 删除；`ATTRIBUTION.md` 的 lewis 行改为「2026-11-23 起 0 件」，
并写明判据是「有没有复制件」而非「读过没读过」；`THIRD_PARTY_NOTICES.md` 的捆绑代码表改为「无上游代码件」。
`runtime.js` 头注也不再挂任何上游标记。**两件已交付 deck 同步重打包**（`模板pitch-10页-世纪广场.html`、
`世纪大道-材质deck-5页.html`），指纹回到一致。

**六、踩坑两处。** ① 周报第 3 页六张卡两列排，`check-fit` 报上越界 51px／下越界 13px：改三列、每卡只留一句，
复跑「装得下闸：可以交付」。② `check_doc_claims` 抓到 `SELFTEST.md` 仍指向已删的 `course-module/style.css`，
三处改为「1.2.42 前的读数，该件已删」的留档口径后归零。

**已验证**：梁架闸 16 族 / 31 式；装得下 16 族 + 5 册全绿；deck 同步（2 份产物指纹一致）；文档对账全过；
色板体检 0 FAIL（`century-sq` 的 1 项 W 仍是「闸看不见描边」的判据边界）；瓦作纹理 9 主题 0 提醒。

**七、整册排版两处实测修正。** ① 周报第 4 页柱状图柱高全为 0：`.wr-bar .c` 高按内容自适应，
`height:%` 解析成 0 —— 改 `align-items:stretch` + `.c{height:100%}`，出图后柱体与数值对齐。
② 演讲者册第 4 页三张 `card-soft` 米白面板上的 `.dim` 仍是暖灰 `#b7a995`（深底专用），
落米白底对比度不足；主题原本只写了 `.lele`→`.lede` 一条换墨规则，补 `.card-soft .dim,.dim2,p{color:#5f4d38}`。
判据与「面板换底、字跟着换」同源，只加规则不动色板；改后重出 `century-ave` 材质图，瓦作闸回 0。

## 1.2.43（2026-11-23）：周报册接真图表族；出图态 `?render`

**一、周报册从「手画柱」换成 charts 族。** 头部接 `assets/layouts.css` 与 `assets/vendor/chart.umd.min.js`，
第 4 页改用 `chart-axis` 的柱状（Chart.js，`maintainAspectRatio:false` 让画布填满卡片——
默认 2:1 宽高比会在 520px 高的卡片里只占一半，右侧空出一整块），第 5 页新增 `chart-pie` 式的环图讲时间去向。
页数 7 → 8，`assets/decks.json` 登记值同步；封面与收束页的 `data-total` 改 8。

**二、环图不用五色。** 上游示例的 `chart-pie` 取 `accent / accent-2 / accent-3 / good / warn` 五色，
一页五个色相直接违反色板三律①。改为**单色相明度阶梯**：读出 `--accent` 与 `--bg` 的 rgb，
按 1 / .7 / .52 / .38 / .26 混合出五档 —— canvas 里 `color-mix()` 不保证解析，所以在 JS 里算 rgb 字符串。

**三、出图态 `?render`（本轮真正的坑）。** 逐页截图发灰、整页像压了一层白纱：CSS 过渡不吃
`--virtual-time-budget`，跳页后在过渡半路（opacity≈0.5）就被截下来。1.2.42 重写 `render-png.sh` 时
把旧的 `?render` 查询串当成冗余删掉，正好删掉了这个开关。恢复手法：
runtime 见 `?render` 给 `<html>` 打 `data-render="1"`；`base.css` 加两条规则——`.slide` 掐过渡、
`.slide *` 掐动效并强制 `opacity:1 / transform:none`；`render-png.sh` 的 URL 带回 `?render`。
⛔ 别把 `.slide` 自身的 `opacity` 也 `!important` 抬到 1，那会让八页叠在一起显影。

**已验证**：装得下闸 8 段全过；deck 同步 6 份登记 0 问题；文档对账 444 项全过；逐页出图 8 张，
柱状填满卡片、环图为单色相阶梯、收束页页码 8/8。

## 1.2.44（2026-11-23）：其余四册各接一族；五份 README 重写

**一、四册从「手写样式」换成族页。** 1.2.43 只把周报册接到了 charts，其余四册仍是自己写类名，
版式和字号各偏一格。本批各接一族，且删掉随之作废的私有规则：

| 册 | 换的族 | 页数 | 删掉的旧写法 |
| --- | --- | --- | --- |
| course-module | `process-steps`（四步，带 `~20min` 级 tag） | 7 → 8 | 旧的四段并列 |
| presenter-mode-reveal | `toc`（五件事，05 跨两列） | 6 → 7 | 旧的一行行 `<p>` |
| pitch-deck | `compare` 的 `.vs`（`bad-side` / `mid` / `good-side`） | 10 | `.pt-cmp` 三行规则 |
| tech-sharing | `code`（`pre.card > code`，两页都换） | 8 | `.ts-code` 规则 |

四册头部补 `<link ... layouts.css>`——族页不在 `base.css` 里，漏这一行会裸渲染。
`check-fit` 全绿：course 8 / pitch 10 / presenter 7 / tech 8 / weekly 8 段全"装得下"；
逐页出图核对 course p7（四步卡）、presenter p2（五件事）、pitch p8（对照）、tech p3（画布页）。

**二、踩坑两处。** ① tech-sharing 第一次替换用了"首个 `.ts-code` 起点 + 末个锚点终点"切片，
把中间 3 页连根删了（段数掉到 5）；`git checkout HEAD -- .../tech-sharing/index.html` 复原后，
改为在 `data-title="闸门"` 段内定位替换，再把画布页一并转换，段数回 8、`.ts-code` 残留 0。
② `render-png.sh` 默认跳过已存在且非空的图，旧目录里的同名页会冒充新结果——本批 presenter p2
就是先读到 1.2.42 的旧图（显示"键位"而非"目录"），`FORCE=1` 重出才见真页；核图前先确认时间戳。

**三、文档残影清掉。** 1.2.42 删了五份 `style.css`，但 `references/theme-full-decks.md` 的现状表
（页数 7/10/6/8/7、主题仍写 century-sq）、"正确包法"整节（教人写 `@layer tpl-palette`）、
`SKILL.md` 的「满版模板吃主题」段、`references/path-b-html.md` 的「把配套 style.css 一起抄」
都还在讲旧结构。本批按现状重写：模板只剩 `index.html`，接线固定为 `base.css` → `layouts.css` →
`theme-link`，配色只有主题一个来源；旧包法降级为"考古判据"（自定义属性按「元素自身声明 > 继承」
解析，层序不参与——这条仍然有效）。
五份 `assets/full-decks/*/README.md` 里四份还是上游英文原文（`7-slide`、`left sidebar`、
`#0d1117`、`override --grad in style.css`），既与现状不符、也违背"0 件上游文案"的自我声明，
全部按本库风格重写为「页序 / 吃什么 / 怎么用 / 闸」，页数与主题与 `decks.json` 对齐。

**四、重打包与出闸。** pitch 源改过 → `build-deck.py` 重出 `模板pitch-10页-世纪广场.html`
（内联 6 个资源、4553 KB），否则 `check-deck-sync` 报"源比产物新"。

**已验证**：装得下闸 5 册全过；deck 同步 6 份登记 0 问题；文档对账 444 项全过；版本 1.2.44。

## 1.2.45（2026-11-23）：描边可放行、quiz 成族、两句骨架、一块玻璃

**一、配色体检闸补「读描边」。** 1.2.44 起 `century-sq` 的主色 `#dab406` 压底只有 1.79:1，闸只能
判 W、贴一行「登记边界」，放不放行靠人。本批把它变成可算的门：主题 CSS 注释里写
`blk-ok: <token> | <依据>`，依据须点明是哪几个实心块、是否带 1px 描边；闸按
`--accent-edge` 的真实配方（`text-1` 30% 压 accent 合成线色）算「描边对主色」的对比度，
**≥1.2:1 才放行**，报实测值。三态：依据合格且描边够亮 → `BLKOK`（OK，不静默），依据在但描边太弱
→ `BLKJ`（W），无登记 → `BLK`（W）。`century-sq` 实测合成描边对主色 **1.73:1**，五处实心块
（`.flow .node.hl` / `.rm .col.now` / `.gg .cell.c7` / `.ring .hub` / `.mm .n.root`）均已接线，放行。

踩坑：首版拿 `brand_main[0]` 当 token 名去查豁免，结果拿到的是 hex、永远查不到；改判
`primary` / `accent` 后才命中。⛔ 「描边」不等于可读——阈值 1.2 是底线不是目标，低于 3:1 的配色
仍要少用实心大块。

**二、quiz 成族（第 17 族，3 式）。** `quiz-ask` 问 / `quiz-reveal` 揭 / `quiz-explain` 讲，
同一道题三段逐字一致（题面改一个字，三页的口径就散了）。正确项 `.ok` 实心 accent、错项 `.no`
划线、解释用 `.why` / `.hook`。修了两处观感：`.opt.ok p code` 去底色、`code` 加
`white-space:nowrap`（否则 `var(--text-1)` 在连字符处断行）。族页三段同为 `is-active` 会叠在一屏，
核第 N 式须临时抽单段 HTML 出图（临时文件已删）。

**三、`.sk12` 十二列。** `l1`–`l12` 跨度类 + `full`，只决定「东西放哪」。⛔ 不替代族页——
族页说的才是「这一页是什么」。

**四、玻璃透镜 `assets/effects/`。** `lens.js` 自写 ≈150 行：圆角矩形 SDF → `t=sin(π/2·(1-d/band))`
剖面 → `mag=bend·(1-t)²`、方向取 `-∇SDF` → RGB 三通道按 `mag·(1±aberr%)` 采样做色散；按 820 长边
出 canvas 再放大。尖角零位移、只在棱带弯。读不到像素（`file://` 下 canvas 判跨源、`getImageData`
抛 SecurityError）落回 SVG 湍流：先插一张 `<img>` 当底（否则卡是空白、滤镜无可晃之物），角标改
「湍流兜底 · 读不到像素」。实测两条：`http://127.0.0.1:8899/...` → 四边线弯折、中心仍直、角部
品红/青边，角标「透镜位移场」；`file://...` → 整面网格同步起伏，角标「湍流兜底」。
机制与参数见 `references/effects-lens.md`（新增一份，references 59 → 60）。

**五、声明收成「同类项目勘察」。** 机制不是某一家独有：本批核了 18 个公开项目（reveal.js、impress.js、
Slidev、Marp、WebSlides、remark、bespoke、Spectacle 等 deck 框架，六七个 liquid-glass 折射实现，
四五个 HTML→PPTX 转换器），确认「SDF 折射 / 三通道色散 / 离屏采样 / DOM 测量」都在生态里公开。
`ATTRIBUTION.md` 把原来的逐家声明改成一张「项目 / 比对过什么」表，并写明**无复制件、不随包分发
许可原文**；`THIRD_PARTY_NOTICES.md` 同步。⛔ 不逐家吹「借鉴」，也不许把「读过」写成「复用了」。

**六、口径与产物同步。** `16 族 / 31 式` → `17 族 / 39 式`（14 个文件）；`SKILL.md` 版本 1.2.45、
「全部 60 份」、「全部 17 个梁架」；README 补「两个可选件」、`layers` 表 36 → 17 族 / 39 式；
`path-b-html.md` 补可选件引法。`century-sq.css` 改了注释 → 重跑 `export-theme-textures.py`
（6 张）；`layouts.css` 改过 → 重打包 `模板pitch-10页-世纪广场.html`（4556 KB、内联 6 件）。

**已验证**：梁架闸 17 族 / 39 式；装得下闸 5 册全绿；deck 同步 6 份登记、2 份产物比对 0 问题；
文档对账 **450 项**全过（themes=9 / layouts=17 / fulldecks=5 / references=60）；瓦作出图 9 主题
0 提醒；字体闸 9 主题 FAIL 0 WARN 0；预览页一致性 9 主题 0 FAIL 0 WARN；配色体检 9 主题
`with_fail 0 / with_warn 0 / clean 9 / blkok 1`；自检闸全 PASS。版本 1.2.45。

## 1.2.46（2026-11-24）：data 族首进整册；声明收成「同类项目勘察」

**一、周报册接 `data` 族（第 2、6 页）。** `data` 是 17 族里最后一个「有族无册」的数据族，本批先拿周报试装：

| 页 | 原来 | 现在 | 理由 |
| --- | --- | --- | --- |
| p2 三个数 | 手写 `.wr-kpi` 三卡 | `data-stat` 四卡（0 / 9 / 450 / 17） | 周报开头就是 KPI，族页正好；补第四格「梁架 17 族」使 2×2 不空心 |
| p6 阻塞 | 手写 `.wr-row` 三行 | `data-todo` 四件（不预勾） | 「还差什么」天然是清单，`done` 留给做完再勾 |

随页替换删掉整块 `<style>`（`.wr-kpi` / `.wr-row` / `.wr-bar` 全部作废，`grep -c '<style' ` = 0）；
`.wr-bar` 那两个 id（`wr-bars` / `wr-pie`）只作 canvas 句柄，不参与样式。页数仍 8，`decks.json` 不动。

**踩坑：计数动画会截在半路。** 第一版沿用族页的 `<span class="counter" data-to="450">`，
`render-png.sh` 在 `?render` 下截到的是 5 / 236 / 9 ——计数走 `requestAnimationFrame`，
`data-render` 只掐 CSS 过渡与动效，管不了 JS。**整册里数字一律写静态**，`counter` 只留在族页演示。

**踩坑：`ul.todo` 固定两列。** 三条会排成 2+1，右列空一格；补成四条（另加「data / ring / split /
image-set 四族仍空着」）才成 2×2。

**二、声明从逐家改成勘察表。** 机制不是某一家独有，把同赛道 18 个项目一起过：
deck 框架（reveal.js / impress.js / Slidev / Marp / WebSlides / remark / bespoke.js / Spectacle）、
玻璃折射（nikdelvin / clean99 / archisvaze / liquidGL / dashersw / rt-liquid-glass）、
HTML→PPTX（HTMLtoPPTX / html2pptx / html-to-pptx ×2）。`ATTRIBUTION.md` 改成一张
「项目 / 比对过什么」表，写明**无复制件、不随包分发许可原文**、实现可独立复算；
`THIRD_PARTY_NOTICES.md`、`references/effects-lens.md` 头注同步。
`century-ave.css` 两条注释里指向外部模板的措辞也改成「由公开玻璃材质参数归纳」，避免读起来像派生。

**三、连带重出。** `century-ave.css` 注释变更 → `export-theme-textures.py`（6 张）＋
`gen-theme-preview.py century-ave … --dark`（预览 3874 KB）；周报无私有样式后不再需要重打包
（它本来不登记交付件）。`references/theme-full-decks.md` 补「各册吃到哪些族」，周报 README 页序改写。

**已验证**：梁架闸 17 族 / 39 式；装得下闸 6 份全绿（周报 8 段）；deck 同步 6 登记 0 问题；
文档对账 450 项；瓦作出图 9 主题 0 提醒；预览一致 9 主题 0 FAIL；配色体检 9 主题
`clean 9 / blkok 1`；自检闸全 PASS；出图核对周报 p2（四卡静态数）与 p6（2×2 四件未勾）。版本 1.2.46。

## 1.2.47（2026-11-24）：Markdown 入口、元素级分步、图集三变体与 ring-map

**一、Markdown 入口。** 新脚本 `scripts/md2deck.py`：`#` 出封面、`##` 切页，正文按内容自动配族
（≥2 图→`image-set` 系（3 张 bento / 4-5 张 round / 6 张 card）、代码块→`code`、表格→`split`、
列表→`text` 卡列），收束页自动补。只认这几条映射，不承诺「任意 Markdown 变漂亮幻灯片」；
装不下仍要过 `check-fit.py`。示例 `/tmp/sample.md` → 5 页册（century-ave），出图核对封面、
卡列页、圆切图页、代码页均可用。脚本登记见 `references/scripts-inventory.md`（二十四支）。

**二、元素级分步（HTML）。** `runtime.js` 加 `data-build` / `.step`：进页只显第一条，空格逐条放出，
放完才翻页；`?render` 态一律全显（避免出图截在半路）。CSS 落在 `animations.css` 末节。
**边界要说清**：这只到 B 出口。C 出口（PPTX）仍是页级构建，`export-pptx.py` 不写 PowerPoint 的
逐元素动画 XML —— 要逐条出现就留 B 出口讲。

**三、图集三变体（抽象自并列图组样本，0 复制件）。** `image-set` 由 1 式拆成 4 式并各占一段：
`image-set`（原 bento）、`image-band`（图注压底，accent 88% 全宽条，c7 反色）、`image-round`
（五圆连排，`overflow:visible` + 圆只切 `img`，图注才不被裁）、`image-card`（3×2 左文右图卡，
图贴右缘 42%）。两个坑：圆切若把 `overflow:hidden` 留在 `figure` 上，图注会被一起裁掉；
band 里 `img{height:100%}` 在 `height:auto` 的 cell 里会撑破版面，改成 cell 定高 + 图 `absolute inset:0`。

**四、ring 第三式。** `.rmap`：中心一句话（250px 圆）+ 环形六节点（96px 圆缩略图 + 数字角标），
六点按正六边形写死 px 偏移，不写角度、不写旋转；节点多于六个改用 `ring-hub`。
中途试过 CSS `rotate + translateY` 与三行三列网格，都会把环压成椭圆或让标注撞中心，最终改绝对定位。

**五、族吃满的第一步。** 周报册加第 8 页「取材」（`image-set` 的 band 式，五张纹理），册子 8 → 9 页，
`decks.json` 与页脚 `data-total` 同步。`ring` / `split` 仍未进整册，记为下一步。

**六、口径。** 17 族 / 39 式 → **17 族 / 39 式**（image-set +3、ring +1）；`SKILL.md` 1.2.46 → 1.2.47；
`_families.json` 的 image-set `styles` 与 ring `styles` 同步；`check-layouts` L2「段数 == styles 长度」
是本轮改式的硬约束（四段同 `data-style` 会红）。

**已验证**：梁架闸 17 族 / 39 式；装得下闸 6 份全绿（周报 9 段）；deck 同步重打包 pitch 后 0 问题；
文档对账 452 项；瓦作 9 主题 0 提醒；预览一致 9 主题 0 FAIL；字体 9 主题 0 FAIL；自检闸 PASS。
HTML 逐条揭示在 `?render` 下全显（出图态不截断）。版本 1.2.47。

## 1.2.48（2026-11-24）：ring / split 进整册，md 表格页有真结论

**一、ring-map 进材质册。** `century-ave-materials` 5 → 6 页，第 5 页「六道工序」用 `.rmap`：
中心「六道工序」、六个节点各挂一张真纹理缩略图与编号。踩到一个必须记的坑：这册原来只链
`base.css` + 主题 + `animations.css`，**不链 `layouts.css`**——直接抄族页的 `.rmap` 会全部失效
（圆变成原尺寸方块、排版散架）。补上 `layouts.css` 后正常；以后往旧册塞族页，先查链接表。

**二、split 进技术册。** `tech-sharing` 8 → 9 页，第 7 页「出口对照」用 `split` 的 1.45:1 主次分栏：
左表（HTML / PNG·PDF / PPTX 三种交付 × 可改到多细 × 适合谁），右栏一句结论。同时改掉原第 8 页
「对象级动效」那条旧口径——它写的是「只做页级、逐元素时间轴不进这套」，与 1.2.47 的 `data-build`
直接冲突；改为「B 出口可逐条，C 出口仍页级」。表头从四列收成三列，四列在 1.45 栏宽里会挤到看不清。

**三、md2deck 表格页有真结论。** 新增 `>` 引用块解析：md 里写一行 `> 结论`，就落到 `split` 的右栏；
不写才回退到占位提示。示例讲稿加「三种出口」一页后，`md2deck` 直接吐出可用的表＋结论，不再需要手改右栏。

**四、页数同步。** `decks.json`：材质册 5 → 6（`built` 改为 6 页件）、技术册 8 → 9、周报 8 → 9（1.2.47 已改）；
两册均过 `check-fit`。材质册按新资产重打包为 `世纪大道-材质deck-6页.html`（5842 KB，内联 12 个资源）；
旧的 5 页件属已作废产物，已删，避免同时留两份。

**已验证**：梁架闸 17 族 / 39 式；装得下闸全绿（材质 6 段 / 技术 9 段 / 周报 9 段）；deck 同步 0 问题；
文档对账 452 项；出图核对材质册 p5（环上六节点）、技术册 p7（表＋结论）、周报 p8（五格图注压底）、
md 成册 p4（表＋结论）。版本 1.2.48。

## 1.2.49（2026-11-24）：md 入口补 process 与 --inline

**一、编号列表进 process 族。** `md2deck` 原来把 `1. 2. 3.` 摊成三张编号卡（`text` 族的变通），
不算真的配族。现改为：没有图、没有代码、没有表，且编号条目 ≥3 → `process-steps` 式，
用 `.steps` + `.step` + `.num`。踩到的小坑：`.num` 在主题里是右上角绝对定位，长句会压上去；
生成时给每个 `.step` 加 `padding-right:72px`，并在 kicker 写「步骤 · N 步」而不是重复页标题。

**二、`--inline` 一键出单文件。** 以前要两步（`md2deck` 出可改件 → `build-deck.py --force` 内联）。
现加 `--inline`：先写到临时目录，再调 `build-deck.py` 落到目标，仍是 11-12 个资源全内联。
示例讲稿加到 7 页（多了「三步改稿」），一条命令出 5420 KB 单文件。

**三、没做的事也说清。** 曾试做一支「族吃到闸」（每族至少被一册用过），实际跑下来发现整册里
几乎没有 `data-style`（族标记只在族页上），靠猜 class 反推族名会误判，于是**放弃这支闸**，
只保留人工登记与 `references/theme-full-decks.md` 的文字口径。宁可少一支闸，也不留一支会骗人的。

**已验证**：梁架闸 17 族 / 39 式；装得下闸与 deck 同步沿用 1.2.48 结论；文档对账 452 项；
出图核对 md 成册 p5（三步卡，编号不压字）。版本 1.2.49。

## 1.2.50（2026-11-24）：md 入口的三种"少配"补齐

**一、单图页。** 只有 1 张图（没有代码、没有表）时原来落到 `image-set` 的三格 bento，一格被拉满很难看。
现改为 `image-single`：`.fig` + `.img-frame.contain`（不裁）+ `.img-cap`，图下的第一段当图注。

**二、纯引用页。** 一页只有一个 `>` 时配 `quote` 族，下一段当署名；加了引号符号、限制 1180 宽，
避免整行横穿页面。**踩坑**：不限制宽度时 50px 的正文会一行排到 1900px，读起来散架。

**三、`### 分节` 各自成页。** `## 章名` 下若直接写 `###`，`##` 不占页、只当小注（kicker），`###` 各成一页。
**踩坑**：`##` 与 `###` 之间的空行会被当成正文，判"有内容"而不删空页 —— 判空必须 `any(x.strip())`。
另：kicker 曾与 h2 同文重复（同一标题写两遍），现统一为"有父章则写父章，无父章则写「第 NN 页」"。

**四、示例讲稿扩到 9 页**（多一页引用、`出册` 拆成 `出可改件 / 出单文件` 两页 code），
一条 `--inline` 出 5420 KB 单文件；出图核对 p3 引用、p5 单图、p7 分节 code 三页。

**已验证**：梁架闸 17 族 / 39 式（未新增式，只是把已有的式配给 md 入口）；文档对账、自检闸见提交前读数。

## 1.2.51（2026-11-24）：C 出口的逐组揭示

**一、写 `p:timing`。** 之前 C 出口只有 `p:transition`（整页翻），逐元素不做。现在 `--animate`
给每页写一棵 timing 树：内容形状按阅读顺序切成 ≤4 组，每组一次 `clickEffect`，组内其余形状挂
`withEffect`、共用同一个 `grpId` —— 放映时一次回车淡入一组，而不是整页一起出现。

**二、为什么要分组。** 第一版是「一个形状一次点击」，示例 spec 三页出了 27 次点击，没人受得了。
改分组后同一份 spec 是 12 次点击（每页 4 次）。`animate_groups` 可逐页改组数。

**三、两个坑。**
- timing 树的 `cTn id` 必须在本页内唯一：第一版每个效果只把计数 +2，但实际用了 3 个 id（base/base+1/base+2），
  于是 id 撞车。改成 +3，并写了检查：三页 `cTn ids` 分别 25/43/43，`unique` 与总数相等、`dup` 为空。
- 染层形状（`*-bg*`）不参与揭示：底色先铺、内容再逐块出，否则第一击会把底色一起带出来。

**已验证**：`export-pptx.py examples/prose/good-spec.json --theme century-sq --animate --render-check`
→ 3 页 / 27 形状 / 12 次点击；officecli `validate` 通过、结构问题 0；三页 PNG 真渲染无炸版。
**四、母版残留的页脚占位。** 出件后真渲染发现每页底部多出一行 `1/27/13` 和一个小页码——
不是我们的内容，是 python-pptx 自带模板在母版/版式上留的「日期 / 页脚 / 页码」空占位，
PowerPoint 里通常不显示，第三方渲染器却照画。现导出时统一删掉（本例 36 个），重渲染干净。

**边界**：这是「形状级、点击分组」，不是 PowerPoint 的逐字符/路径动画；放映效果需人工在 PowerPoint 里点一遍确认。

## 1.2.52（2026-11-24）：边角成判据（预览板第七类漂移）

**问题**：预览板只展示配色/材质/模度/组件，**边角从未成判据**。主题把 `--radius` 从 20px（广兰路）
压到 2px（虬江），旧六类检查一条都不会红，样本页上也看不出差别。

**改法**：`scripts/preview-template.html` 的组件格（Component）里加 `data-block="corners"` 三档样片
（同一形状分别用 `--radius-sm` / `--radius` / `--radius-lg`，下方标 token 名不标 px）；
`scripts/check-preview-sync.py` 加 `check_corners`：模板源与主题侧判红（样片区必须在、区内半径必须引
`var(--radius*)`、三档标签齐、每个主题必须定义 `--radius`），既有产物缺样片区只 WARN（待重生成）。
文档 `references/theme-preview.md` 加「边角」一节、验收改「七类」、接入 checklist 加「边角三档」。

**外部对照（软链不搬）**：同骨架多主题对照读法参考 Astryx 沙盒（Meta，MIT），按卡片/按钮/字体/边角
四项并排展示七套主题；⛔ 不抄色值、字体与 token。

**踩坑（2026-11-24，样片排版）**：第一版把三档样片竖排在 Geometry 格里（标题+三格+标签 ≈ 60px），
headless 截图一看——`.board` 是 1080×720 的定高框，Geometry 格已占满 173.5px，样片直接顶出板底，
标签被压在草地带下面，而闸门照样 PASS（闸门只查「有没有写死 px」，查不到「装不装得下」）。
第二版改放右侧 Component 格（那里有竖向余量），仍溢出约 40px；第三版压成**单行**（标签 + 三枚
34×14 的样片 + token 名，共占 14px）才装下。**判据**：样式板任何新增块都要先截图看是否在 720 板内，
⛔ 只看闸门绿不绿。

**造错验证**：把 `--radius` 改写成 `999px` → 红「边角样片的半径必须读主题 token」；把
`data-block="corners"` 改名 → 红「模板源缺边角样片区」；复原 → PASS。九份预览页已按新模板全部重生成，
闸门 0 FAIL／0 WARN；截图目视世纪广场（直角 6px 档）／广兰路（20px 玻璃圆弧）／虬江（2px 纸面直角）
三份，样片区都在板内、随主题变档。

## 1.2.53（2026-11-24）：预览页两处静默失效排障（字号档、模度阶梯）

**症状**：虬江、番禺路、万航渡的模度阶梯有条子看不见（广兰路其实正常，是我早先在小图上误读——
四条渐变都在，长度 100/62/38/24 成比例）。

**根因一（模度阶梯）**：模板四条读的是 `--concrete-deep` / `--steel` / `--lawn`——这三个材料 token
只有世纪广场一系主题定义过。其余主题读到未定义变量时，CSS 把**整条声明丢弃**，条子变透明；
页面不报错、渲染正常、闸门只查色板/材质/组件/语汇，一条都抓不到。改法：四条各带 `var()` 兜底
（`var(--concrete-deep,var(--text-3))` 这类），落到每个主题都有的墨色阶；自备模度色的五个主题
（广兰路/龙华寺/福州路/万航渡/番禺路）仍由各自 override 后写覆盖。

**根因二（字号档，更大的坑）**：`--t-h1`…`--t-cap` 这 20 档字阶定义在 `assets/base.css` 的 `:root`，
主题只引用不重写；而预览页只内联**主题 CSS**，于是 `font-size:var(--t-h1)` 全是死引用——浏览器
退回继承值，字号档形同虚设，同样静默。改法：生成器加 `_backfill_base_tokens()`，把 base.css 里
**主题未定义**的 token 补在 `</style>` 之前（主题自己的值仍优先）。

**新闸**：`check-preview-sync.py` 加第八类 `check_modscale`——逐主题取四档**最终** `background`，
要求能解析成字面色／已定义的 var／带可用兜底的 var；解析不了或某档缺失即红。改前拿旧产物验证过：
番禺路、万航渡两条被判红（正是死引用），修后 9 主题 0 FAIL／0 WARN。

**已验证**：九份预览页按新模板重生成；截图目视世纪大道（暗色）、福州路、万航渡、虬江、番禺路，
四档条子都可见且比例 100/62/38/24；边角样片区仍在 720 板内。

## 1.2.52（2026-11-24）：一份 md 出两种件（--pptx）

**一、映射只落在 C 真有的页型上。** `md2deck --pptx out.pptx` 把 md 的页翻成 C 出口 spec：
cover / bullets / quote / table / end 五类有对应；**图组、单图、代码页在 C 出口没有等价页型**
（C 的图只能是版式装饰，代码没有等宽块），一律跳过并逐条打印「第 N 页为什么没出」，
不硬塞成卡片。示例讲稿 9 页 → PPTX 6 页，跳过 3 页（1 图组 + 2 代码）。

**二、长句要拆，不然 19 字就撞墙。** C 的 bullets 正文 32px、单条位置只有 19 字。
md 里的句子普遍 20–50 字，直接塞会溢出。新增 `split_item()`：在 5–24 字间找第一个标点
（`：` 优先，其次 `，。；`）断成「主句（items）+ 小注（captions）」，找不到才硬切加省略号。

**三、引用页字号按字数回退。** 56px 一行只装得下 14 个汉字，18 字会留一个孤字「话。」。
现按长度回退 56 / 44 / 36，宽度放到 1200，署名跟在字下（`300 + size*1.9`），不再悬在页面中间。

**四、两个映射 bug。** ① `family_of` 把「表格 + 一行结论」判成 quote（当时条件写成
`quote==1 且 para<=1 且 len(kinds)<=2`，表格页正好 len=2），导致表格页整页变引用；现改成
只认 `[quote]` / `[quote,para]` / `[para,quote]` 三种组合。② 署名出现 `— — 项目复盘`，
因为 md 里已经写了破折号，映射时又加了一遍；现 `lstrip('—')`。

**已验证**：示例 md 9 页 → HTML 9 页（5420 KB）+ PPTX 6 页；PPTX 真渲染 OpenXML 通过、结构问题 0；
逐块揭示 6 页 / 43 形状 / 24 次点击；`verify-pptx-editable.py` 通过。

## 1.2.53（2026-11-24）：C 出口补「一图一页」

**一、`figure` 页型。** spec 写 `{"type":"figure","title":…,"image":…,"caption":…}`，
图按原比例缩进版心（宽先铺满、超高按高度回缩），水平居中、不裁边，图注贴在图下、宽度跟图走。
图片路径相对 spec 所在目录解析，`deck.base_dir` 在 main 里设一次。

**二、SVG 点名拒绝。** python-pptx 塞不进 SVG（`UnidentifiedImageError`），别让它半路崩：
`figure` 页遇到 `.svg` 直接报「pptx 里只能塞位图，矢量请先在 B 出口出 PNG」；
md 侧也提前把 SVG 单图页记进 skipped，不浪费一次导出。

**三、md 单图页不再被跳过。** 示例讲稿加了一页「一块石头」（单张大理石纹理），
-md 10 页 → HTML 10 页 + PPTX 7 页（cover/bullets/quote/figure/table/bullets/end），
跳过 3 页仍是「5 张图组」与两页命令。

**四、EMU 换算踩坑。** 第一版拿 `9525 EMU/px` 折算图片尺寸（那是 96 dpi 的换算），
本库版心是 120 px/inch（7620 EMU/px），图会被算大 25%、压到图注。改成 7620 后图注贴住图底。

**已验证**：`g10` 真渲染 7 页 OpenXML 通过、结构问题 0；逐组揭示 7 页 / 48 形状 / 28 次点击；
可编辑闸通过（每页有文本形状；figure 页的图是原生 picture，不是整页位图）。

## 1.2.64（2026-11-24）：C 出口图片按 `--radius` 同值裁圆角

**一、圆角落到 PPTX 的图片形状上。** 此前 B 出口的 `.gg .cell` / `.gal figure` / `.gal.phone img`
都吃 `--radius`（18px，手机图 16px），C 出口的 `add_picture` 出来一律直角，两边同构只到摆法、没到边角。
现给 `p:pic` 的 `spPr` 写 `a:prstGeom prst="roundRect"`，`a:avLst` 里 `adj = 18/min(w,h)*100000`
（手机图取 16，上限 50000）。PowerPoint 用形状裁切图片填充，所以图仍是**原图**：可换、可裁、不重采样，
`verify-pptx-editable.py` 仍认它是原生 picture。

**两条排除的路**：① 四角贴底色块——底色可能是渐变或材质图，贴纯色角会留下四块假边；
② 先做圆角遮罩再贴图——那要把每张图重新栅格化，图就从「可换的原图」变成「一张定死的位图」，
与可改件的承诺相反。代价是圆角由 PowerPoint 渲染，网页件与可改件的圆角抗锯齿不完全一致。

**二、图注条只圆底角。** band bento 的 accent 图注条压在图内底边，卡片裁切会把条的下两角也切圆。
条改用 `ROUND_2_SAME_RECTANGLE` 转 180°（同侧两角在下），`adjustments[0]=0.5`，上沿保持平口——
和 HTML 里「图片圆角、条贴在卡底」的观感对齐；条本身不带文字，旋转不影响图注。

**三、`figure` 单图页一并处理。** 单图页先前只居中不裁，直角；现按 `--radius` 同值裁形，
居中坐标不变（`pic.left` 在裁形之前算，圆角只改几何、不改位置）。

**四、切片不进自检（用户口径）。** `docs/themes/*.png` 由 `gen-theme-slices.py` 手动重出；
主题色或材质一改，切片可能旧，这由使用者自行重跑并承担，⛔ 不把切片重出挂进 `selftest.py`——
理由是它会拖慢每次自检，且切片本身不是交付物。

**五、补记 1.2.59–1.2.63（这几节落账时漏写）。** 图组同构：B 侧 4–5 张宽图改 `gg band`
（1 主 4 辅、图注压底），C 侧 `figures` 辅图由一列竖叠改 2×2，≤3 张走 `gal three`；
出口改名：网页件 / 可改件 / 影像件，A/B/C 只留命令与脚本；主页加九瓦作风格切片（`gen-theme-slices.py`）
与每主题一段灵感；地名口径改正——九个名字是路/广场/河道/楼/寺，只有世纪大道、广兰路恰好也是站名，
「友好大厦」不是站；`hex` 声明为按意象调色、非取样。

**已验证**：示例 11 页重出 PPTX（`--animate --render-check`），OpenXML 通过、结构问题 0；
渲染核过第 3 页（bento 主图 + 2×2 辅图，四角圆、图注条底角圆）、第 4 页（三屏等高不裁，16px 圆角）、
第 6 页（单图页圆角、图注贴底）；`verify-pptx-editable.py` 通过；`check_doc_claims` 全过；
`check-deck-sync` / `check-layouts` / `check-fit` 无新增红。

## 1.2.65（2026-11-24）：册级导航条（吸收「导航栏」）＋次按钮比主按钮大

**一、导航条两式。** 自公众号《PPT 最上面这个是什么》的「导航栏」吸收，但只取能站住的两式：
文字型（`.deck-nav`，当前节 accent + 2px 下划线）与色块型（`.deck-nav.is-block`，44px 通栏底 +
当前节 accent 实块）。位置只放顶部——左侧竖排要重排版心，底部与页脚抢行，图标型没有图标体系。
条高上限 44px，页面内边距 72px，超过就压标题。

**二、数据显式给，不猜。** md 首部 `<!-- nav: 序 > 现状 > 判断 -->`，每页 `<!-- sec: 现状 -->`；
`nav-block:` 切色块型。`parse_pages()` 把 sec 注释吃掉记进 `page['sec']`（留在正文会被当成段落，
把 `family_of` 判歪），md2deck 往 B 侧每页注入 `<nav>`，并把 `nav`/`nav_form` 与每页 `sec`
写进 C 侧 spec。C 侧 `draw_nav()` 挂在 `slide()` 建页这一步——列表页、数字页等 C 页型不走 `head()`，
挂在 head 里会漏页（第一版就是这么漏的，渲染里整条不见）。

**三、C 侧字号不同尺。** C 用 11pt（图注档），B 用 13px；两边看齐的是「谁是当前节」，不是像素。
色块型块宽按 11pt 中文字宽估算（18.3px/字，西文 0.55），起点从 `LEFT-18` 起，文字落 112。

**四、次按钮比主按钮大（广兰路预览）。** 主题 `.cp-btn-2` 用 `--t-cap`（24px），预览板里主按钮
`.board .pill` 降到 13px，次按钮没跟，于是 Cancel 比 Submit 大一圈。修法是在预览层补
`.board .cp-btn-2{font-size:13px;padding:8px 14px}`：加进 `GHOST_BTN_OVERRIDE`，广兰路 `--aero`
分支不吃幽灵覆盖，单独在 `AERO_OVERRIDE` 再补一条；九份预览逐份补同一行。⛔ 不动主题本体——
24px 的按钮在正页里是对的，坏的只是「板内缩字号」这一层。

**已验证**：4 页示例 md（nav + 三条 sec）出 HTML 5 页、PPTX 5 页，B 侧第 2 页导航条在顶部、
当前节「现状」亮；C 侧文字型与色块型各渲一版，OpenXML 通过、结构问题 0；广兰路预览重渲染后
Submit 与 Cancel 同高、次按钮略小；世纪大道预览复核同高。


## 1.2.66（2026-11-24）：四式反哺 ＋ 九份预览次按钮普查

**一、把广兰路的修法推到九份。** 用无头 Chrome 量每份预览板里 `.pill` 与 `.cp-btn-2` 的实际高度：
century-ave 34/34、century-sq 34/34、friendship-bldg 34/34、fuzhou-rd 37/37、guanglan-rd 34/34（另一组 36/36）、
longhua-si 37/37、qiu-r 37/37、wanhang-fy 37/37——八份主次同高或次按钮略小，只有番禺路一份是 **41/53**。

**二、番禺路那份的根因不是漏加规则，是规则没进样式表。** 那行 `.board .cp-btn-2` 被写在第二个
`</style>` 之后（这份页的正文里另有一枚模板遗留的游离 `</style>`），成了正文文字，浏览器不执行。
生成器更早就踩过同一个坑：`gen-theme-preview.py` 补 token、补番禺路补丁都用 `rfind/rindex('</style>')`，
也会挑到那枚游离的。修法是 `_style_close_in_head()`：以 `</head>` 为界找最后一个真正的 `</style>`，
两处注入都改走它；番禺路预览重出（--subset-fonts，766 KB），实测主 41 / 次 37，与前八份同向。
⛔ 教训：改完预览不能只看「生成成功」，要量高度——写在样式块外面的规则，页面上是静默失效的。

**三、四式反哺。** ① 图带压卡 `.ride`：图带 440px，结论行压在图带内（`.rt-thesis` 必须在 `.rt-img` 里，
放在外面会被卡盖住），两张白卡骑压带下沿 64px，卡内「小标题两行 + 正文两段」。② 左文右图出血
`.split.bleed-img`：沿用既有 `.split` 骨架，图栏 `-112px` 出血，并清掉主题相框的 padding/白瓷底，
否则出血图上会留一圈白边。③ 底线三段卡 `.cols3`：三列等宽，两段正文之间虚线，卡底 3px accent。
④ 胶囊 chips `.chips`（组件，`.chip` / `.on` / `.more`）。
按本库并式规矩，前两者是参数、后两者是参数与组件，**17 族 39 式不变**——不靠「另开一段」让人发现。

**四、踩过的两个布局坑。** `.ride` 最初把结论行放在 `.rt-cards` 之前、以 `.ride` 定位，卡一压上来就
把结论盖成半透明鬼影；挪进 `.rt-img` 内才对齐。`pc.bleed` 最初撞了 hero 族的 `.bleed`（`display:flex` 纵排），
图直接掉到下一行、通栏；改用 `.split.bleed-img` 才复用对骨架。⛔ 新类名先全局搜一遍，别跟既有语义撞。

**已验证**：三张 1600×900 样张（图带压卡 / 三段卡＋chips / 出血分栏）逐张看；九份预览按钮高度实测；
番禺路重出后结构（2 开 2 闭）与旧件实质差异 0。

## 1.2.67（2026-11-24）：四式接进 md 指令 ＋ C 侧降级 ＋ 广兰路标题改粗体

**一、页级指令。** `parse_pages()` 多认两条注释：`<!-- layout: ride|cols3|bleed -->` 与
`<!-- chips: A｜B｜C -->`，与 `sec` 一样从正文删掉（留下会被 blocks() 当段落，把 `family_of` 判歪）。
`layout` 优先于自动配族：ride 认一图当带、首段当结论、列表项当卡；cols3 认三张卡；bleed 认两段正文 + 一图。
卡片字段用全角「｜」切，半角 `|` 留给表格——`标题｜副标｜段一｜段二` 是图带卡的写法，
`标题｜段一｜段二` 是三段卡的写法。

**二、C 出口是降级不是硬塞。** ride → 列表页（卡片小标题 + 首段），cols3 → 列表页（标题 + 两段并作注），
bleed → 单图页（左栏正文折进图注）。`to_spec()` 多返回一个 `notes` 列表，`emit_pptx()` 逐页打印
「降级第 N 页」，与 `skipped` 分开——跳过的页是真的没有内容，降级的页有内容、只是结构没保住。
⛔ 别把降级塞进 skipped：那会让人以为整页丢了。

**三、广兰路标题粗体。** `--font-display` 的 CJK 回落原先是「华文黑体」，它只有 Light/Medium 两档，
700 是浏览器合成出来的，放大后偏细。在 Nunito 与华文黑体之间加 `'PingFang SC'`，标题走 Semibold，
西文仍走 Nunito。只动 display 栈，不动 `--font-sans`；正文字重不受影响。

**已验证**：`demo66.md`（三页各带一条 layout 指令）→ HTML 5 页、PPTX 5 页；B 侧第 2/3/4 页分别出
图带压卡、三段卡 + chips、出血分栏，逐张看过；C 侧三条降级提示逐条打印，`verify-pptx-editable` 通过
（5 页、每页 ≥1 文本形状、无整页位图）。标题换栈后重渲第 2 页，笔画明显加粗，字宽未胀出标题区。

## 1.2.68（2026-11-24）：甘特二式、模块格、质感三件

**一、甘特从「画条」进到「读日期」。** 老 `.gantt` 只认固定 12 格、没有完成度。新 `.gantt2` 由
`<!-- layout: gantt -->` 触发，读表里的起止日期（`2026-07` 与 `2026-07-15` 同认月粒度），
最早与最晚之间自动算月份数，刻度写成 inline 的 `--cols/--step`，CSS 不猜月份。三件随之成立：
跨年自动分带（年份行按月份数 span）、条内实色段按完成度裁切、模块变更处一道虚线。
条右端百分比用 tabular-nums，100% 时字色翻成 `--accent-ink`（压深色实条）。
⛔ 别把日期解析放进 CSS：一旦跨 15 个月，12 格的老网格就必然错位。

**二、模块格只做「一格给图」。** `<!-- layout: modules -->` 收最多四张卡（`标题｜段一｜段二`），
插图则独占末格。行高固定 250px——首版写 `1fr`，两张文卡被撑到 430px，整页越过 900 的版心、
标题被 `overflow:hidden` 切掉；固定行高后两行 524px，连同标题区落回版内。
与 `image-set` 的 `bento` 分界：bento 整页都是图，modules 是文图混排。

**三、质感三件是装饰件，不是主题。** `.soft-cast` 用两层阴影（远模糊＋近接触）替掉描边；
`.glass-pane` 走 `--glass-bg`/`--glass-blur`，缺省退回中性 Aqua 参数；`.bubble` 是径向透明渐变叠两层。
三者都不改九瓦作各自的玻璃语言（广兰路 aero、世纪大道液玻），C 侧玻璃只能降成半透明填＋内高光。

**四、顺手修掉两个老毛病。** `parse_pages` 现在跳过独立成行的 `---`（写作习惯的分页线，
原先会当成正文段落混进 `paras[-1]`，甘特的结论带会读到一串破折号）；`to_spec` 的 `cards/paras/imgs`
提到循环开头，此前只在 ride 分支里赋值，走 gantt/modules 会 `UnboundLocalError`。

**已验证**：`demo68.md`（甘特 5 行跨 2026-07→2027-03、模块格 3 卡＋1 图）→ HTML 4 页，
第 2 页年份带 2026（6 格）/2027（3 格）、100% 条字色翻深、模块虚线对；第 3 页四格等高、图占末格。
C 侧 4 页，两条降级逐条打印（甘特→表格、模块格→列表），`verify-pptx-editable` 通过。

## 1.2.69（2026-11-25）：弧形分割、弧线时间轴、底部口号带

**一、弧形分割不是「圆角」。** 十五张参考图里，封面、双栏、封底反复用同一条 S 弧当分界。
首版用 `border-radius` 试过：椭圆角只能弯一次，做出来是个缺口，不是 S。改成
`clipPathUnits="objectBoundingBox"` 的 clipPath（路径坐标 0–1），换画布尺寸不跑形。
图栏要**相对 slide 定位**（`.arc` 改 `position:static`），否则图从标题下开始、够不到页顶；
`top:0;bottom:0;right:-112px` 之后才通到页顶与页右。曲线也调过一版：首版中段凹得太深（像个海湾），
压平成 `.34→.20→.10` 的缓 S 才像参考图。

**二、弧线时间轴是「算出来的」不是「摆出来的」。** 曲线一条三次贝塞尔
（`(0,285)(330,245)(1046,335)(1376,285)`），圆点在 `t=(i+0.5)/n` 处用 De Casteljau 求 x/y，
卡片按圆点的 x 百分比定位、按 y 定 top，奇偶决定在曲线上方还是下方，竖杆从圆点连到卡边。
⛔ 别用 flex 均分：竖杆长度得跟着曲线 y 走，均分一定脱线；也别用 `preserveAspectRatio` 缺省值，
`none` 才让 1376 的 viewBox 铺满实际栏宽（圆点会被拉 1% 左右，肉眼无感）。
首版卡片 152px 高，三段说明被裁成一行；加到 200px、说明降到 18px/1.5 才放得下三行。

**三、口号带是页级开关。** `<!-- band: 一句话 -->` 挂在任意页，`.claim-band` 通栏压底、
字距 .22em、两侧各一段短横。挂带的页加 `has-band`：`padding-bottom` 收到 150px、页脚隐藏，
否则 78px 的带会把页码盖住。⛔ 带不是页脚，别让它跟 `.deck-footer` 同时出现。

**已验证**：`demo69.md`（弧形页 2 段正文＋1 图、时间轴 5 节点＋口号带）→ HTML 4 页；
弧形页图通到页顶页右、S 弧缓；时间轴 5 张卡交替、说明三行完整、圆点与竖杆对齐；口号带压在页底、
页脚隐藏。C 侧 4 页，两条降级逐条打印（弧形→单图、时间轴→列表），`verify-pptx-editable` 通过。

## 1.2.70 · 横条比例 / 团队卡

**一、横条比例的标签必须出轨道。** 首版照参考图把标签放进轨道，深色字压在实色段上：
长条勉强能读，短条（31%）的标签横跨实色段与浅轨道，两侧都不够。1.2.71 改成三列网格——
`236px 标签 / 1fr 轨道 / 84px 数值`，轨道只剩色段，行与行仍靠网格对齐，扫描不会乱。
⛔ 别再为了「像参考图」把字塞回条里；要嵌字就得双色分层，代价大于收益。
数值 >100（例如「266000 座」）按最大值归一，⛔ 别直接截断成 100%。
表后一段自动收进 `.note` 当注脚，不另起一行正文。

**二、团队卡的有机形靠错位，不靠形状本身。** `border-radius` 四组百分比只能拧出「近椭圆」，
单看会像头像墙的圆框；真正出效果的是**后景形状比人像大一圈、并向右下探出**：
`.back` 232×208、`left:calc(50% - 106px)`、`top:20px`、`rotate(-9deg)`，
`.mask` 186×206、`translate(-16px,-8px)`——左边窄、右下宽，才有一角探出来。
⛔ 人像必须抠底：白底棚拍图会在有机形里留一圈白，读起来像描边。
无图时只留 `.back`，同形淡色块仍占位，版心不塌。

**已验证**：`demo70.md`（bars 5 条 76/74/67/55/31% + 注脚；team 4 人各一句简介 + 4 张人像）
→ HTML 4 页：条长与数值一致、注脚在条下 20px；四张人像同形、形状右下探出、姓名/职务/分隔线/简介
四层齐。C 侧 4 页，两条降级（bars→两列表格、team→列表页），`verify-pptx-editable` 通过。

## 1.2.71 · 品牌色实心块上的字（全库排查）

**病型**：token 层的色对是合法的（`--accent-ink` 压 `--accent` 过 4.5），但组件把 `--text-1` 或
`#fff` 放到了品牌色实心底上。`check-theme-colors.py` 原先只查 token，查不出组件层。

**排查口径**：扫 `base.css` / `layouts.css` / 九个主题 css 的每个 CSS 块；
`background`（或 `background-color`）恰为 `var(--accent)`、`var(--accent-2)`、`var(--accent-3)`、
`var(--primary)`，且同块 `color` 命中 `#fff`/`white`/`--text-1..3` ⇒ FAIL。
`color-mix` 的 tint、渐变、`rgba` 不算实心块，跳过（那是深字的合法底）。

**扫出并修掉**（广兰路）：`.tag-chip` 白字压紫玻璃 `#9c8feb` 仅 2.78:1；`.cp-anchor` 白字压主蓝
`#1a7fb8` 4.40:1，差 0.1 没过 AA。两者都改 `var(--accent-ink)`（7.18 / 4.54）。
其余 481 块合规；甘特条内百分比落在 26% tint 上、100% 完成态另有 `.is-done` 切 `--accent-ink`，不计违规。

**已验证**：`check-theme-colors.py assets/themes` → `comp_fills: 0`，九主题仍全清；
`check_doc_claims` 事实项不变（未新增脚本、未增族式）。
