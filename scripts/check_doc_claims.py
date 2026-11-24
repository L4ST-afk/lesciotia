#!/usr/bin/env python3
"""文档断言对账闸：把 md/html 里写的数字与名字，逐条对回磁盘上的事实。

为什么要有这支：`check_limits.py` 管体量、`vaccinate.py` 管结构，两支都不读
「43 个主题」这句话是不是真的。本 skill 实测过三次这类漂移（cover 的 pill 写
24/30/25、动效数 26 写成 27、taste-deck 7 条写成 6 条），全靠人眼发现。

判据必须能红：每条断言都带**锚点**（file + 正则）。锚点匹配不到＝文档被改写、
断言失去覆盖，同样算不过；⛔ 不许因为「找不到那句话」就静默跳过。

用法：
    python3 scripts/check_doc_claims.py          # 人读报告，exit 0 全过 / 1 有不过
    python3 scripts/check_doc_claims.py --json   # 末行追加一行机器可读摘要
"""
from __future__ import annotations

import glob
import os
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

# 这些是「示意占位」而不是真路径，出现在文档里是合法的
PLACEHOLDER_TOKENS = ('{', '<', '*', '…', 'NN', 'my-talk', '$')
# 历史读数登记处：这里的旧数字是史料，不是当前状态断言
HISTORY_FILES = {'SELFTEST.md'}
STALE_PHRASES = ('当前校验不过', '当前不可用', '本机当前')


class Abort(Exception):
    """量不到事实就硬中止——⛔ 不许把「测不到」当「没有」处理。"""


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        raise Abort(f'锚点文件不存在：{rel}')
    return p.read_text(encoding='utf-8', errors='replace')


def count_files(pattern: str) -> int:
    n = len(list(ROOT.glob(pattern)))
    if n == 0:
        raise Abort(f'磁盘上量不到 {pattern}（0 个）——目录结构变了，先修闸再跑')
    return n


# 扫描要跳过的目录：缓存与本地 venv（2026-11-23 加 .venv——闸门依赖装在目录内，
# 不排除会把 site-packages 里 pip/pygments 的 .py 当成本库文件扫，1472 项、4 处假红）。
SKIP_DIRS = {'__pycache__', '.venv', 'node_modules', '.git'}


def _skipped(p: Path) -> bool:
    return any(part in SKIP_DIRS for part in p.parts)


def md_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob('*.md')) if not _skipped(p)]


def html_files() -> list[Path]:
    return [p for p in sorted(ROOT.rglob('*.html')) if not _skipped(p)]


def table_rows(section: str) -> list[list[str]]:
    """取一段 markdown 里的表格正文行（去掉表头与分隔行），按 | 切列。"""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def section(text: str, heading: str) -> str:
    """取某个标题（## 或 ###）到下一个同级/更高级标题之间的正文。"""
    out, on, level = [], False, 0
    for line in text.splitlines():
        m = re.match(r'^(#{2,4})\s+(.*)$', line)
        if m:
            hashes, title = m.group(1), m.group(2)
            if on and len(hashes) <= level:
                break
            if heading in title:
                on, level = True, len(hashes)
                continue
        if on:
            out.append(line)
    if not on:
        raise Abort(f'找不到小节「{heading}」')
    return '\n'.join(out)


# ---------------------------------------------------------------- 事实测量

def measure() -> dict:
    t: dict = {}
    t['themes'] = count_files('assets/themes/*.css')
    # 上游主题残留数：目录已删＝0（2026-11-23 起）。ATTRIBUTION.md 的「36→0」读数靠它核。
    # ⛔ 不走 count_files：那个函数把 0 当「目录结构变了」硬中止，而这里 0 是合法且期望的值。
    t['upstreamthemes'] = len(list(ROOT.glob('assets/themes/upstream/*.css')))
    t['layouts'] = count_files('assets/layouts/*.html')
    t['fulldecks'] = len([p for p in (ROOT / 'assets/full-decks').iterdir() if p.is_dir()])
    t['references'] = count_files('references/*.md')
    t['stylespecs'] = len([p for p in ROOT.glob('references/styles-*.md')
                           if p.name != 'styles-unified.md'])
    if t['stylespecs'] == 0:
        raise Abort('量不到任何 styles-<key>.md')

    css = read('assets/animations/animations.css')
    t['animclasses'] = len(set(re.findall(r'\.anim-[a-z0-9-]+', css)))
    if t['animclasses'] == 0:
        raise Abort('animations.css 里量不到 .anim-* 类')

    rt = read('assets/runtime.js')
    m = re.search(r'const\s+ANIMS\s*=\s*\[(.*?)\]', rt, re.S)
    if not m:
        raise Abort('runtime.js 里找不到 ANIMS 数组')
    t['anims'] = len(re.findall(r"'[^']+'", m.group(1)))

    arch = read('references/archetypes.md')
    t['archetypes'] = len(re.findall(r'^## \d+\.\s+`', arch, re.M))
    if t['archetypes'] == 0:
        raise Abort('archetypes.md 里量不到编号 archetype 小节')

    taste = read('references/taste-deck.md')
    for key, head in (('taste_use', '一、'), ('taste_swap', '二、'), ('taste_skip', '三、')):
        sec = section(taste, head)
        rows = table_rows(sec)
        if not rows:
            raise Abort(f'taste-deck.md「{head}」小节量不到表格行')
        t[key] = len(rows)
        hm = re.search(re.escape(head) + r'[^（(]*[（(](\d+)\s*条', taste)
        if not hm:
            raise Abort(f'taste-deck.md「{head}」标题里没有条数')
        t[key + '_claimed'] = int(hm.group(1))

    presets = read('references/dimensions-presets.md')
    prows = table_rows(section(presets, 'Mapping Table'))
    if not prows:
        raise Abort('dimensions-presets.md 的 Mapping Table 量不到行')
    t['presets'] = len(prows)
    t['preset_details'] = len(re.findall(r'^### ', presets, re.M))
    for idx, dim in ((1, 'texture'), (2, 'mood'), (3, 'typography'), (4, 'density')):
        vals = {r[idx] for r in prows if len(r) > idx}
        t[dim] = len(vals)
        t[dim + '_values'] = vals
        cm = re.search(r'\*\*' + dim.capitalize() + r'\*\*\s*\((\d+)\):\s*([^\n]+)', presets)
        if not cm:
            raise Abort(f'dimensions-presets.md 里找不到 {dim.capitalize()} 的取值声明')
        t[dim + '_claimed'] = int(cm.group(1))
        t[dim + '_listed'] = {v.strip() for v in cm.group(2).split(',')}

    unified = read('references/styles-unified.md')
    krows = table_rows(section(unified, '个风格键'))
    if not krows:
        raise Abort('styles-unified.md 的风格键表量不到行')
    t['stylekeys'] = len(krows)
    t['stylekeys_with_a'] = sum(1 for r in krows if len(r) > 4 and r[4].startswith('`styles-'))
    km = re.search(r'##\s*(\d+)\s*个风格键', unified)
    if not km:
        raise Abort('styles-unified.md 的「N 个风格键」标题没了')
    t['stylekeys_claimed'] = int(km.group(1))

    qa = read('references/qa-checklist.md')
    t['qa_common'] = len(table_rows(section(qa, '组 1')))
    for outlet in ('A ·', 'B ·', 'C ·'):
        n = len(table_rows(section(qa, outlet)))
        t['qa_' + outlet[0]] = n
    return t


# ---------------------------------------------------------------- 断言表

# (相对路径, 正则（一个捕获组＝文中写的数字）, 事实键, 说明)
CLAIMS: list[tuple[str, str, str, str]] = [
    ('references/path-b-html.md', r'(\d+)\s*个主题', 'themes', 'B 出口主题数'),
    ('references/path-b-html.md', r'(\d+)\s*族版式', 'layouts', 'B 出口版式族数'),
    ('references/path-b-html.md', r'(\d+)\s*套成套模板', 'fulldecks', 'full-deck 套数'),
    ('references/path-b-html.md', r'(\d+)\s*族都不合适', 'layouts', '「不从零写版式」铁律里的版式族数'),
    ('references/path-b-html.md', r'(\d+)\s*个 CSS 动效类', 'animclasses', 'CSS 动效类数'),
    ('references/path-b-html.md', r'ANIMS`?\s*共\s*(\d+)\s*项', 'anims', 'runtime ANIMS 项数'),
    ('assets/layouts/cover.html', r'(\d+)\s*themes', 'themes', '封面 pill 主题数'),
    ('assets/layouts/cover.html', r'(\d+)\s*layouts', 'layouts', '封面 pill 版式数'),
    ('assets/layouts/cover.html', r'(\d+)\s*animations', 'animclasses', '封面 pill 动效数'),
    ('ATTRIBUTION.md', r'`themes/`（(\d+)\s*个）', 'themes', '归属表主题数'),
    ('ATTRIBUTION.md', r'`themes/upstream/`（\d+\s*→\s*(\d+)）', 'upstreamthemes', '归属表上游主题残留数'),
    ('ATTRIBUTION.md', r'`layouts/`\s*并成\s*(\d+)\s*族', 'layouts', '归属表版式族数'),
    ('ATTRIBUTION.md', r'`full-decks/`\s*(\d+)\s*套', 'fulldecks', '归属表 full-deck 套数'),
    ('SKILL.md', r'全部\s*(\d+)\s*份', 'references', 'References 段份数'),
    ('SKILL.md', r'(\d+)\s*个风格键跨出口通用', 'stylekeys', '风格键总数'),
    ('SKILL.md', r'(\d+)\s*类页序', 'archetypes', 'archetype 类数'),
    ('SKILL.md', r'(\d+)\s*条照用', 'taste_use', 'taste 照用条数'),
    ('SKILL.md', r'(\d+)\s*条换说法', 'taste_swap', 'taste 换说法条数'),
    ('SKILL.md', r'(\d+)\s*条不适用', 'taste_skip', 'taste 不适用条数'),
    ('SKILL.md', r'(\d+)\s*照用／', 'taste_use', 'References 表 taste 照用'),
    ('SKILL.md', r'／(\d+)\s*换说法', 'taste_swap', 'References 表 taste 换说法'),
    ('SKILL.md', r'／(\d+)\s*不适用', 'taste_skip', 'References 表 taste 不适用'),
    ('references/styles-unified.md', r'`references/styles-<key>\.md`（(\d+)\s*份', 'stylespecs', 'A 规格份数'),
    ('references/styles-unified.md', r'按现有\s*(\d+)\s*份', 'stylespecs', '加新风格 checklist 份数'),
    ('references/styles-unified.md', r'(\d+)\s*个主题里挑', 'themes', 'B 主题总数'),
    ('references/dimensions-presets.md', r'Maps\s*(\d+)\s*preset', 'presets', 'preset 总数'),
    ('references/outline-slide-templates.md', r'full\s*(\d+)-preset', 'presets', 'preset 映射指针'),
    ('SKILL.md', r'(\d+)\s*类场景页序', 'archetypes', 'References 表 archetype 类数'),
    ('references/taste-deck.md', r'(\d+)\s*类 archetype', 'archetypes', 'archetype 类数'),
    ('references/qa-checklist.md', r'组 1 · 通用\s*(\d+)\s*条', 'qa_common', '通用质检条数'),
    ('references/qa-checklist.md', r'出口专属\s*(\d+)\s*条', 'qa_A', '出口专属条数'),
    ('references/preferences-schema.md', r'风格键（(\d+)\s*个之一）', 'stylekeys', '偏好文件风格键数'),
    ('SKILL.md', r'风格键（(\d+)\s*个之一）', 'stylekeys', '选项表风格键数'),
    ('assets/full-decks/presenter-mode-reveal/README.md', r'(\d+)\s*个类见', 'animclasses', '动效类数'),
]


def check_claims(t: dict, problems: list[str]) -> int:
    n = 0
    for rel, pattern, key, label in CLAIMS:
        n += 1
        text = read(rel)
        hits = re.findall(pattern, text)
        if not hits:
            problems.append(f'[锚点消失] {rel}：匹配不到 /{pattern}/（{label}）——断言失去覆盖')
            continue
        for h in hits:
            if int(h) != t[key]:
                problems.append(f'[数字不符] {rel}：{label} 写 {h}，磁盘事实 {t[key]}')
    return n


def check_rowcounts(t: dict, problems: list[str]) -> int:
    n = 0
    pairs = [
        ('taste-deck 一、照用', 'taste_use'),
        ('taste-deck 二、换语域照用', 'taste_swap'),
        ('taste-deck 三、不适用', 'taste_skip'),
        ('styles-unified 风格键表', 'stylekeys'),
    ]
    for label, key in pairs:
        n += 1
        if t[key] != t[key + '_claimed']:
            problems.append(f'[行数不符] {label}：标题写 {t[key + "_claimed"]} 条，实际 {t[key]} 行')
    n += 1
    if t['presets'] != t['preset_details']:
        problems.append(f'[行数不符] presets 映射表 {t["presets"]} 行 vs Preset Details {t["preset_details"]} 个小节')
    for dim in ('texture', 'mood', 'typography', 'density'):
        n += 1
        if t[dim] != t[dim + '_claimed']:
            problems.append(f'[取值数不符] {dim}：声明 ({t[dim + "_claimed"]})，映射表实际用了 {t[dim]} 种')
        n += 1
        if t[dim + '_values'] != t[dim + '_listed']:
            miss = t[dim + '_values'] - t[dim + '_listed']
            extra = t[dim + '_listed'] - t[dim + '_values']
            problems.append(f'[取值集不符] {dim}：表里用到但没声明 {sorted(miss)}；声明了但没用到 {sorted(extra)}')
    n += 1
    if t['stylespecs'] != t['stylekeys_with_a']:
        problems.append(f'[A 规格数不符] styles-<key>.md 有 {t["stylespecs"]} 份，'
                        f'风格键表里标了 A 实现的有 {t["stylekeys_with_a"]} 行')
    n += 1
    if not (t['qa_A'] == t['qa_B'] == t['qa_C']):
        problems.append(f'[质检条数不齐] A/B/C 三出口专属条数 {t["qa_A"]}/{t["qa_B"]}/{t["qa_C"]} 不一致')
    n += 1
    arch_toc = re.findall(r'^- `\d+\.\s', read('references/archetypes.md'), re.M)
    if len(arch_toc) != t['archetypes']:
        problems.append(f'[目录不齐] archetypes.md 目录列了 {len(arch_toc)} 条，正文有 {t["archetypes"]} 个 archetype')
    return n


def check_skill_ref_list(t: dict, problems: list[str]) -> int:
    text = read('SKILL.md')
    listed = set(re.findall(r'references/([A-Za-z0-9._-]+\.md)', text))
    actual = {p.name for p in (ROOT / 'references').glob('*.md')}
    for name in sorted(listed - actual):
        problems.append(f'[悬空] SKILL.md 列了 references/{name}，磁盘上没有')
    for name in sorted(actual - listed):
        problems.append(f'[漏登记] references/{name} 在磁盘上，SKILL.md 的清单没列')
    return 1


def check_dangling(problems: list[str]) -> int:
    """全目录扫本地路径引用（md/py/sh/js）。跨 skill 与上游路径靠「前面有 /」排除。"""
    # ⚠️ 扩展名交替必须加 \b：否则 `registry.json` 会被 `js` 抢先匹配成 `registry.js`，
    # 于是「磁盘上没有」这条报的是个不存在的路径（2026-11-22 实测踩到）。
    pat = re.compile(r'(?<![\w/.-])((?:references|assets|scripts|examples)/[A-Za-z0-9_./-]+'
                     r'\.(?:md|py|sh|js|css|html|json|svg|png)\b)')
    n = 0
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.suffix not in ('.md', '.py', '.sh', '.js'):
            continue
        if _skipped(p) or p.resolve() == SELF:
            continue
        n += 1
        rel = p.relative_to(ROOT)
        for ref in pat.findall(p.read_text(encoding='utf-8', errors='replace')):
            if any(tok in ref for tok in PLACEHOLDER_TOKENS):
                continue
            if not (ROOT / ref).exists():
                problems.append(f'[悬空] {rel} 指向 {ref}，磁盘上没有')
    return n


def check_html_refs(problems: list[str]) -> int:
    """html 里的 link/script/img 本地引用逐条解析（剥掉 script/style 块，里面是注释与模板）。"""
    strip = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.S | re.I)
    ref = re.compile(r'<(?:link|script|img)\b[^>]*?(?:href|src)\s*=\s*"([^"]+)"', re.I)
    n = 0
    for p in html_files():
        n += 1
        body = strip.sub('', p.read_text(encoding='utf-8', errors='replace'))
        for s in ref.findall(body):
            if s.startswith(('http', '//', 'data:', '#', 'mailto:')):
                continue
            if any(tok in s for tok in PLACEHOLDER_TOKENS):
                continue
            if not (p.parent / s.split('?')[0].split('#')[0]).exists():
                problems.append(f'[破图/破链] {p.relative_to(ROOT)} 引用 {s}，解析不到文件')
    return n


def check_names(problems: list[str]) -> int:
    n = 0
    for p in md_files():
        n += 1
        rel = p.relative_to(ROOT)
        text = p.read_text(encoding='utf-8', errors='replace')
        for bad in ('preferred_style', 'preferred_audience'):
            if bad in text:
                problems.append(f'[字段名过期] {rel} 用了 {bad}；正本是 style / audience'
                                f'（见 references/preferences-schema.md）')
        for bad in ('references/styles/', 'presets.md', 'xhs-post', 'references/animations.md'):
            for m in re.finditer(re.escape(bad), text):
                # dimensions-presets.md 是真文件，别误伤
                if bad == 'presets.md' and text[max(0, m.start() - 11):m.end()].endswith('dimensions-presets.md'):
                    continue
                problems.append(f'[幽灵路径] {rel} 提到 {bad}，本 skill 没有这个实体')
    n += 1
    if (ROOT / 'assets/animations/fx-runtime.js').exists():
        problems.append('[空壳复活] assets/animations/fx-runtime.js 又出现了；'
                        '它依赖的 fx/ 目录不在本 skill 内，要么补全要么删')
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or p.suffix not in ('.js', '.html', '.css'):
            continue
        if _skipped(p):
            continue
        if 'fx-runtime' in p.read_text(encoding='utf-8', errors='replace'):
            problems.append(f'[空壳引用] {p.relative_to(ROOT)} 仍在引用 fx-runtime')
    return n


def check_stale_status(problems: list[str]) -> int:
    """状态词只许作为「史料引用」出现，不许作为当前断言。"""
    n = 0
    for p in md_files():
        rel = p.relative_to(ROOT)
        if str(rel) in HISTORY_FILES:
            continue
        n += 1
        for lineno, line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            for phrase in STALE_PHRASES:
                i = line.find(phrase)
                if i < 0:
                    continue
                # 被 「…」 引起来的是历史读数引用，合法
                if line.rfind('「', 0, i) > line.rfind('」', 0, i):
                    continue
                problems.append(f'[状态词] {rel}:{lineno} 把「{phrase}」当当前状态写；'
                                f'状态只认当次退出码，历史读数要带日期并标明是史料')
            vm = re.search(r'现\s*v?\d+\.\d+\.\d+', line)
            if vm:
                problems.append(f'[无日期版本断言] {rel}:{lineno}「{vm.group(0)}」——'
                                f'版本号会随上游变，写成带日期的读数或指向真值源')
    return n



# ── 罗蛇 Rassarpa 字符级红线（2026-11-20 接入）──
# T07 中文不用负字距 / T08 中文不用假斜体。
# 判据只对「容器里装中文」的规则生效：拉丁与数字容器用负字距是正当的（Playfair 大标题、
# 220px 章节号、KPI 数字），一刀切会把它们误判成违规。
CJK_RE = re.compile(r'[\u4e00-\u9fff]')

# T07/T08 用的三个线性判据（2026-11-23）：先切块、再在块内查声明。
# ⛔ 不要退回 `([^{}\n]+)\{([^{}]*<声明>[^{}]*)\}` 那种写法——那是回溯炸弹，
#    century-ave.css 单文件 112 秒，见 check_cjk_type_rules 的 docstring。
BLOCK_RE = re.compile(r'([^{}\n]+)\{([^{}]*)\}')
NEG_LETTER_RE = re.compile(r'letter-spacing:\s*-\s*[\d.]+em')
ITALIC_RE = re.compile(r'font-style:\s*(?:italic|oblique)')


def _container_text(path: str, sel_tail: str) -> str:
    """取某个选择器在配套 HTML 里实际装的字（取不到就返回空串＝不判）。"""
    base = os.path.dirname(path)
    if not os.path.isdir(base):
        return ''
    for fn in sorted(os.listdir(base)):
        if not fn.endswith('.html'):
            continue
        try:
            h = io.open(os.path.join(base, fn), encoding='utf-8').read()
        except Exception:
            continue
        # 类名（.h1 / .hero h1 → h1 或 class="h1"）
        cls = sel_tail.strip().split()[-1].lstrip('.')
        for pat in (r'<[a-z0-9]+[^>]*class="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*>(.*?)</',
                    r'<' + re.escape(cls) + r'[^>]*>(.*?)</'):
            m = re.search(pat, h, re.S)
            if m:
                return re.sub(r'<[^>]+>', '', m.group(1))
    return ''


def check_cjk_type_rules(problems: list[str]) -> int:
    """T07/T08：中文容器的负字距与假斜体。

    ⚠️ 2026-11-23 性能修复：原式 `([^{}\\n]+)\\{([^{}]*<声明>[^{}]*)\\}` 是回溯炸弹。
    外层 `[^{}\\n]+` 在每个起始位置都要试一遍、内层再扫到文件尾，复杂度 O(n²)；
    `century-ave.css`（139KB）单文件实测 112 秒、命中 0 条，整闸常年跑不完等于不跑。
    （惰性量词救不了：`[^{}]*?` 实测同样 >20s 超时。）
    改为「先按块切分、再在块内查声明」，线性，实测毫秒级，结果与原式逐条等价
    （24/24 文件 old==new）。T08 的 font-style 条同一结构，一并改。
    """
    checked = 0
    targets = []
    for pat in ('assets/themes/*.css', 'assets/layouts/*.html',
                'assets/full-decks/*/style.css'):
        targets.extend(sorted(glob.glob(pat)))
    for path in targets:
        if '.bak' in path:
            continue
        try:
            txt = io.open(path, encoding='utf-8').read()
        except Exception:
            continue
        # T07 负字距（先切块，再在块内查声明；等价于原式且线性）
        for m in BLOCK_RE.finditer(txt):
            if not NEG_LETTER_RE.search(m.group(2)):
                continue
            checked += 1
            sel, body = m.group(1).strip().split('\n')[-1].strip(), m.group(2)
            body_text = _container_text(path, sel)
            if body_text and CJK_RE.search(body_text):
                problems.append(
                    f'[罗蛇T07] {path}：`{sel}` 装中文却用负字距（中文不用负字距，'
                    f'会挤掉字怀）')
        # T08 内联 style 里的假斜体（2026-11-20 造错验证抓出的漏网：
        #     big-quote 的 italic 写在 style="..." 里，不在 CSS 规则块内）
        for m in re.finditer(r'<(\w+)([^>]*\bstyle="[^"]*font-style:\s*(?:italic|oblique)[^"]*"[^>]*)>(.*?)</\1>', txt, re.S):
            checked += 1
            body_text = re.sub(r'<[^>]+>', '', m.group(3))
            if CJK_RE.search(body_text):
                problems.append(
                    f'[罗蛇T08] {path}：<{m.group(1)}> 内联 style 装中文却用 italic/oblique'
                    f'（中文字体无真斜体，只会合成倾斜）')

        # T08 假斜体（⛔ 豁免代码注释：.cmt/.comment/.code 内走等宽拉丁字体，
        #     italic 是行业惯例，不属「中文正文假斜体」作用域）
        for m in BLOCK_RE.finditer(txt):
            if not ITALIC_RE.search(m.group(2)):
                continue
            checked += 1
            sel = m.group(1).strip().split('\n')[-1].strip()
            if re.search(r'\.(cmt|comment|code|kw|str)\b', sel):
                continue
            body_text = _container_text(path, sel)
            if body_text and CJK_RE.search(body_text):
                problems.append(
                    f'[罗蛇T08] {path}：`{sel}` 装中文却用 italic/oblique'
                    f'（中文字体无真斜体，只会合成倾斜）')
    return checked



# ── 中西文排版闸（2026-11-20 接入）──
# 三条判据，全部来自实测踩坑：
#  T07 中文不用负字距（--letter-tight / --letter-normal 不许是负值）
#  FONT 中文字体栈必须点名思源黑体，且排在拉丁字体之后
#  AUTO 中西文自动间距（text-autospace）必须在 base 层声明
def check_cjk_typesetting(problems: list[str]) -> int:
    checked = 0
    base = 'assets/base.css'
    if os.path.exists(base):
        txt = io.open(base, encoding='utf-8').read()
        # T07：base 层两个字距 token 不许为负
        for tok in ('--letter-tight', '--letter-normal'):
            m = re.search(re.escape(tok) + r'\s*:\s*(-[\d.]+em)', txt)
            checked += 1
            if m:
                problems.append(
                    f'[中西文T07] {base}：`{tok}` 是负值 {m.group(1)}（中文不用负字距，'
                    f'base 层是 36 个版式的共同底座）')
        # AUTO：中西文自动间距
        checked += 1
        # ⛔ 判的是「声明」不是「字样」：注释里提到 text-autospace 不算数
        if not re.search(r'text-autospace\s*:\s*(normal|auto)', txt):
            problems.append(f'[中西文AUTO] {base}：缺 `text-autospace` 声明（中文与拉丁/数字之间没有四分空）')
        # FONT：base 字体栈要点名思源黑体
        checked += 1
        if 'Source Han Sans SC' not in txt and '思源黑体' not in txt:
            problems.append(f'[中西文FONT] {base}：字体栈没点名思源黑体')

    # 主题层：负 letter-tight 与字体栈顺序
    for pat in ('assets/themes/*.css', 'assets/themes/upstream/*.css'):
        for path in sorted(glob.glob(pat)):
            txt = io.open(path, encoding='utf-8').read()
            m = re.search(r'--letter-tight\s*:\s*(-[\d.]+em)', txt)
            checked += 1
            if m:
                problems.append(
                    f'[中西文T07] {path}：`--letter-tight` 是负值 {m.group(1)}（中文不用负字距）')
            # 字体栈：思源黑体若出现，必须在 'Noto Sans SC' 之前
            for fm in re.finditer(r'--font-(?:sans|display)\s*:\s*([^;\n]+)', txt):
                chain = fm.group(1)
                checked += 1
                if 'Source Han Sans SC' in chain and "'Noto Sans SC'" in chain:
                    if chain.index('Source Han Sans SC') > chain.index("'Noto Sans SC'"):
                        problems.append(
                            f'[中西文FONT] {path}：思源黑体排在 Noto Sans SC 之后，'
                            f'会被伪装成 Noto 名的字体顶替')
    return checked



def check_script_table(problems: list[str]) -> int:
    """脚本表 ↔ scripts/ 双向齐（2026-11-23 评审#08）。
    只写在散文里、表里没有的脚本，等于没人知道它该什么时候跑；
    表里列了却磁盘上没有的，是幽灵命令。"""
    # 2026-11-23 下沉后表在 references/：SKILL.md 与所有 references 一起算「被提到」
    texts = [io.open('SKILL.md', encoding='utf-8').read()]
    for f in sorted(glob.glob('references/*.md')):
        texts.append(io.open(f, encoding='utf-8').read())
    blob = '\n'.join(texts)
    mentioned = set(re.findall(r'(?<![\w/])scripts/([A-Za-z0-9_.-]+\.(?:py|sh))', blob))
    on_disk = {f for f in os.listdir('scripts') if f.endswith(('.py', '.sh'))}
    for f in sorted(on_disk - mentioned):
        problems.append(f'[脚本漏登] scripts/{f} 在磁盘上，但 SKILL.md 的脚本表与正文都没提它'
                        f'（补一行用途，或归档）')
    for f in sorted(mentioned - on_disk):
        problems.append(f'[脚本悬空] SKILL.md 提到 scripts/{f}，磁盘上没有这个文件')
    return len(on_disk | mentioned)

def main() -> int:
    as_json = '--json' in sys.argv
    problems: list[str] = []
    try:
        t = measure()
    except Abort as e:
        print(f'✗ 硬中止：{e}', file=sys.stderr)
        if as_json:
            print(json.dumps({'ok': False, 'aborted': str(e)}, ensure_ascii=False))
        return 2

    checked = 0
    checked += check_claims(t, problems)
    checked += check_rowcounts(t, problems)
    checked += check_skill_ref_list(t, problems)
    checked += check_dangling(problems)
    checked += check_html_refs(problems)
    checked += check_names(problems)
    checked += check_stale_status(problems)
    checked += check_cjk_type_rules(problems)
    checked += check_cjk_typesetting(problems)
    checked += check_script_table(problems)

    if problems:
        for msg in problems:
            print(f'✗ {msg}', file=sys.stderr)
        print(f'✗ 文档对账不过：{len(problems)} 处（共查 {checked} 项）', file=sys.stderr)
    else:
        print(f'✓ 文档对账 {checked} 项全过')
        print('  事实：' + ' / '.join(f'{k}={t[k]}' for k in
              ('themes', 'layouts', 'fulldecks', 'references', 'stylespecs',
               'animclasses', 'anims', 'archetypes', 'presets', 'stylekeys')))
    if as_json:
        print(json.dumps({'ok': not problems, 'checked': checked,
                          'problems': len(problems), 'truth': {
                              k: v for k, v in t.items()
                              if isinstance(v, int)}}, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())