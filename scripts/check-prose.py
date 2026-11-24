#!/usr/bin/env python3
"""成稿闸：判一份 spec 的文字「够不够到能出片的密度」。

来雪亭不生成文字——文字是在对话里写的，写的人（模型）比脚本会写。脚本只当判官：
把「像模像样」拆成九条能数出来的判据，红一条就不许出片。

用法：
    python3 scripts/check-prose.py deck.json            # 逐页查，红则 exit 1
    python3 scripts/check-prose.py deck.json --strict   # 警告也当红
    python3 scripts/check-prose.py deck.json --json     # 机器可读摘要
    python3 scripts/check-prose.py pages/               # 直接吃正本（目录或单个 NN-*.md）
    python3 scripts/check-prose.py pages/ --emit-spec deck.json   # 派生 spec 给 export-pptx

两种入参吃的是同一套九条判据：`pages/NN-{slug}.md`（正本，markdown）与 spec.json
（派生件）。字段名不同但语义相同，映射见 FIELD_ALIAS。

判据（原文与理由见 references/prose-gate.md）：
    P1 套话        —— 词表命中即红：赋能 / 闭环 / 抓手 / 一站式 …
    P2 标题空转    —— 标题里 ≥2 个抽象词且无数字、无专名、无动词
    P3 首句复述    —— lede 与标题的二字重叠 ≥50%：等于没说第二遍
    P4 单条超长    —— bullet ≥20 字，或句读 >1 个（32px 正文在栏内约 17 字/行，20 字已是两行）
    P5 数字无出处  —— 正文有数字，这页却没声明 source / figures
    P6 术语无注    —— 连续大写字母首现，后面没跟（中文）
    P7 一页多主张  —— 因此 / 所以 / 这意味着 / 总之 出现 ≥2 次
    P8 页面太薄或糊—— 正文 <30 字（空页），或 >260 字（糊；32px 下约 5 行起就开始挤）
    P9 问叹滥用    —— ？＋！ 的个数超过页数
"""
import argparse
import json
import re
import sys
from pathlib import Path

BAN = [
    '赋能', '闭环', '抓手', '一站式', '全方位', '多维度', '全链路', '深度融合',
    '护城河', '生态位', '数智化', '顶层设计', '颗粒度', '组合拳', '势能', '发力',
    '引爆', '颠覆', '重新定义', '降本增效', '打通', '落地生花', '价值最大化',
]
# 抽象词：只有这些词组成的标题，读者拿不到任何具体东西
ABSTRACT = [
    '价值', '能力', '体系', '机制', '路径', '范式', '生态', '格局', '维度', '层级',
    '协同', '底座', '引擎', '矩阵', '方法论', '战略', '抓手', '闭环', '效能', '势能',
]
VERB = [
    '减', '算', '裁', '改', '出', '挣', '省', '降', '升', '断', '拆', '拼', '接', '换',
    '放', '收', '走', '跑', '读', '写', '量', '验', '校', '开', '关', '立', '砍', '挪',
    '撬', '焊', '钉', '织', '酿', '切', '削', '磨', '烧', '铸', '查', '记', '比', '选',
]
SENT_LEADS = ['因此', '所以', '这意味着', '总之', '可见', '换句话说']
# 计量单位与自解释缩写：它们本来就该这么写，不必括注
UNITS = {'GB', 'MB', 'KB', 'TB', 'MS', 'PX', 'PT', 'DPI', 'PDF', 'PPTX', 'HTML', 'JSON'}
# 这些页型本来就该稀（一个数、一句收尾），不拿「太薄」判它们
SPARSE = {'kpi', 'end', 'quote'}

# 必填槽位（references/page-record.md「必填的最小集」）：空着的槽，这页就不成立。
# ⛔ 以前这里一条必填校验都没有，而文档写着「缺必填 P8 会红」——那是句假话：
#    缺 title 会用 H1 兜底，缺 points 只要 title+lede 满 30 字 P8 就不响。
#    「有牙」不能写成希望，得写成代码（2026-11-23 三席评审）。
# 按页型分：封面/收尾/引用页没有要点是**对的**，一刀切会把好稿判红。
REQUIRED = {
    'title': ('type', 'title'),                    # 所有页型
    'body': ('type', 'title', 'items'),            # 要论据的页型
}
# 这些页型只靠一个数/一句话成立，不要求 items（与 SPARSE 同源，但语义不同：
# SPARSE 管「太薄」不报，这里管「缺 items 不报」）
NO_ITEMS = {'cover', 'end', 'quote', 'wash', 'section'}

# ── pages/NN.md → spec 同构 ────────────────────────────────────────────
# 正本是 markdown（references/page-record.md），闸门必须直接吃它：
# 禅院塔 §2.6「一份正本 + 指针」——同一句话出现在两个文件里，其中一个是错的定时炸弹。
# 这里只做「读」，不改 pages 的格式；spec.json 由 --emit-spec 机器生成，⛔ 不手改。

# 同一样东西两个名：pages 叫 points / refs，spec 叫 items / source。
# ⛔ 改这张表就是改契约（§2.18）：export-pptx.py 吃的是 items / source。
FIELD_ALIAS = {'points': 'items', 'refs': 'source'}

PAGE_HEAD_RE = re.compile(r'^#\s+(\d+)\s*·\s*(.+?)\s*$')
PAGE_FIELD_RE = re.compile(r'^-[ \t]*\*\*([a-z_]+)\*\*:[ \t]*(.*)$')
PAGE_ITEM_RE = re.compile(r'^[ \t]+(?:\d+\.|[-*])[ \t]+(.+?)[ \t]*$')


def parse_page_md(text):
    """把一份 `pages/NN-{slug}.md` 解析成 spec 的一页（dict）。

    认两种写法：单行字段 `- **type**: data`，和多行块（字段行后面跟缩进的
    `1.` / `-` 列表，points 就是这种）。标题优先取 `**title**`，没有就退回
    H1 的 `# 03 · 标题`。
    """
    d, head_title, cur = {}, None, None
    for line in text.splitlines():
        m = PAGE_HEAD_RE.match(line)
        if m:
            head_title, cur = m.group(2), None
            continue
        m = PAGE_FIELD_RE.match(line)
        if m:
            key = FIELD_ALIAS.get(m.group(1), m.group(1))
            val = m.group(2).strip()
            if val:
                d[key], cur = val, None
            else:
                d.setdefault(key, [])
                cur = key
            continue
        if cur:
            m = PAGE_ITEM_RE.match(line)
            if m:
                d[cur].append(m.group(1))
            elif line.strip():
                # 非列表的续行：并进上一条，别静默丢字
                if d[cur]:
                    d[cur][-1] += line.strip()
                else:
                    d[cur].append(line.strip())
            else:
                cur = None
    if 'title' not in d and head_title:
        d['title'] = head_title
    if 'items' in d and not isinstance(d['items'], list):
        d['items'] = [d['items']]
    return d


def load_pages(path):
    """读 pages/ 目录（或单个 .md），返回 (spec 同构的 deck, 文件名列表)。"""
    p = Path(path)
    files = sorted(p.glob('[0-9][0-9]-*.md')) if p.is_dir() else [p]
    if p.is_dir() and not files:
        files = sorted(p.glob('*.md'))
    slides = []
    for f in files:
        d = parse_page_md(f.read_text(encoding='utf-8'))
        if d:
            slides.append(d)
    return {'slides': slides}, [f.name for f in files]


red, warn = [], []


def R(code, page, field, msg, text=''):
    red.append((code, page, field, msg, text))


def W(code, page, field, msg, text=''):
    warn.append((code, page, field, msg, text))


def bigrams(s):
    s = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s or '')
    return {s[i:i + 2] for i in range(len(s) - 1)} - {'' }


def page_text(d):
    """正文＝能读的句子（不含 kicker / footer / notes 小注）。"""
    parts = []
    t = d.get('title')
    parts += t if isinstance(t, list) else ([t] if t else [])
    for k in ('lede', 'subtitle', 'body'):
        if d.get(k):
            parts.append(str(d[k]))
    for it in d.get('items') or []:
        if isinstance(it, str):
            parts.append(it)
        elif isinstance(it, (list, tuple)):
            parts += [str(c) for c in it]
    for side in ('left', 'right'):
        for it in ((d.get(side) or {}).get('items') or []):
            parts.append(str(it))
    if d.get('quote'):
        parts.append(str(d['quote']))
    for row in d.get('rows') or []:
        parts += [str(c) for c in row]
    return [p for p in parts if p]


def check_page(d, no):
    # P0 必填槽位：先查「这页成不成立」，再查「文字写得好不好」。
    # 按页型取集：封面/收尾/引用页没有要点是对的，一刀切会把好稿判红。
    slot = 'title' if d.get('type') in NO_ITEMS else 'body'
    for f in REQUIRED[slot]:
        v = d.get(f)
        if isinstance(v, (list, tuple)):
            empty = not [x for x in v if str(x).strip()]
        else:
            empty = not (v or '').strip() if isinstance(v, str) else v is None
        if empty:
            R('P0', no, f, '缺必填字段「%s」：这页不成立（page-record.md 必填的最小集）' % f)

    title = d.get('title')
    title_s = ''.join(title) if isinstance(title, list) else (title or '')
    lede = d.get('lede') or ''

    for field, txt in [('kicker', d.get('kicker') or ''), ('title', title_s), ('lede', lede)] + \
            [('items[%d]' % i, str(it)) for i, it in enumerate(d.get('items') or [])]:
        for w in BAN:
            if w in txt:
                R('P1', no, field, '套话「%s」——换成它指的实事' % w, txt)

    if title_s.strip():
        ab = sum(1 for w in ABSTRACT if w in title_s)
        if ab >= 2 and not re.search(r'\d', title_s) and not re.search(r'[A-Za-z]{2,}|「|」|《', title_s) \
                and not [v for v in VERB if v in title_s]:
            R('P2', no, 'title', '标题里 %d 个抽象词、没有对象也没有动作' % ab, title_s)

    if title_s.strip() and lede.strip():
        a, b = bigrams(title_s), bigrams(lede)
        if a and len(a & b) / len(a) >= 0.5 and len(b) <= len(a) + 2:
            R('P3', no, 'lede', 'lede 复述标题（二字重叠 %d/%d），等于说第二遍'
              % (len(a & b), len(a)), lede)

    for i, it in enumerate(d.get('items') or []):
        it_s = str(it[0]) if isinstance(it, (list, tuple)) else str(it)
        if d.get('type') == 'kpi':
            continue
        if len(it_s) >= 20:
            R('P4', no, 'items[%d]' % i, '单条 %d 字（上限 19），32px 正文在栏内装不下两行' % len(it_s), it_s)
        elif it_s.count('，') > 1 or it_s.count('；') > 1:
            R('P4', no, 'items[%d]' % i, '一条里有 %d 个句读：拆成两条' % (it_s.count('，') + it_s.count('；')), it_s)

    text = page_text(d)
    joined = ' '.join(text)
    if re.search(r'\d', joined) and not (d.get('source') or d.get('figures')):
        W('P5', no, '-', '有数字但没声明 source / figures——这数字谁给的', joined[:40])

    seen = set()
    for m in re.finditer(r'[A-Z]{2,}', joined):
        tok = m.group(0)
        if tok in seen or tok in UNITS:
            continue
        seen.add(tok)
        if not re.match(r'[（(]', joined[m.end():m.end() + 1] or ''):
            W('P6', no, '-', '术语「%s」首现没有（中文）括注' % tok, joined[max(0, m.start() - 8):m.end() + 8])

    leads = sum(joined.count(w) for w in SENT_LEADS)
    if leads >= 2:
        W('P7', no, '-', '%d 个结论句——一页只许一个主张' % leads)

    n = sum(len(t) for t in text)
    if n < 30 and d.get('type') not in SPARSE:
        R('P8', no, '-', '正文只有 %d 字：这一页没有东西可看' % n)
    elif n > 260:
        R('P8', no, '-', '正文 %d 字（上限 260）：删到一屏能读完' % n)


def main():
    ap = argparse.ArgumentParser(description='成稿闸：九条判据查文字密度')
    ap.add_argument('spec', help='deck spec JSON，或 pages/ 目录（或单个 NN-*.md）')
    ap.add_argument('--strict', action='store_true', help='警告也当红')
    ap.add_argument('--json', action='store_true', help='输出机器可读摘要')
    ap.add_argument('--suggest', action='store_true',
                    help='末尾加一行判型：这稿该按哪一型写（调 pick-recipe.py）')
    ap.add_argument('--emit-spec', metavar='PATH',
                    help='把 pages/ 解析成 spec.json 写到 PATH（派生件，供 export-pptx.py；⛔ 别手改）')
    a = ap.parse_args()

    src = Path(a.spec)
    if src.is_dir() or src.suffix.lower() == '.md':
        try:
            deck, names = load_pages(src)
        except Exception as e:
            print('✗ 读不了 pages：%s' % e)
            return 2
        if not deck['slides']:
            print('✗ %s 里没有可解析的 NN-*.md' % src)
            return 2
    else:
        try:
            deck = json.load(open(src, encoding='utf-8'))
        except Exception as e:
            print('✗ 读不了 spec：%s' % e)
            return 2
        names = None
    slides = deck.get('slides') or deck.get('pages') or []
    if not slides:
        print('✗ spec 里一页都没有')
        return 2

    if a.emit_spec:
        out = Path(a.emit_spec)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({'slides': slides}, ensure_ascii=False, indent=2) + '\n',
                       encoding='utf-8')
        print('已派生 spec：%s（%d 页，来自 %s）'
              % (out, len(slides), 'pages/' if names else src.name), file=sys.stderr)

    for i, d in enumerate(slides, 1):
        check_page(d, i)

    # P9：问号加叹号的总数超过页数 ⇒ 一份陈述里这些符号会互相抵消。
    # ⛔ 旧写法 `sum('？' in pg + '?' in pg + ... for pg in ...)` 是**链式比较**，不是计数：
    #    `a in b + c in d` 解析成 `(a in (b+c)) and ((b+c) in d)`，后者几乎恒为 False，
    #    所以这条判据从写下来那天起就恒为 0、一直静默通过（2026-11-23 三席评审共识）。
    q = sum(sum(pg.count(ch) for ch in '？?！!') for pg in
            [' '.join(page_text(x)) for x in slides])
    if q > len(slides):
        W('P9', 0, '-', '问号加叹号 %d 个（超过页数 %d）：一份陈述里这些符号会互相抵消' % (q, len(slides)))

    for code, page, field, msg, txt in red:
        print('✗ %s 第 %s 页 %s：%s' % (code, page, field, msg))
    for code, page, field, msg, txt in warn:
        print('⚠ %s 第 %s 页 %s：%s' % (code, page, field, msg))

    bad = len(red) + (len(warn) if a.strict else 0)
    summary = {'pages': len(slides), 'red': len(red), 'warn': len(warn),
               'codes': sorted({c for c, *_ in red} | ({c for c, *_ in warn} if a.strict else set())),
               'verdict': 'blocked' if bad else 'pass'}
    if a.suggest and not a.json:
        try:
            import importlib.util
            path = __import__('pathlib').Path(__file__).with_name('pick-recipe.py')
            spec_ = importlib.util.spec_from_file_location('pick_recipe', path)
            mod = importlib.util.module_from_spec(spec_)
            spec_.loader.exec_module(mod)
            text = mod.collect_text({'slides': slides})
            ranked, _ = mod.detect(text)
            top, second = ranked[0], ranked[1]
            name = mod.RECIPES[top[0]]['name']
            if top[1] - second[1] <= 2 and top[1] > 0:
                print('体裁判型：两型都对（%s %d / %s %d）——分段写'
                      % (name, top[1], mod.RECIPES[second[0]]['name'], second[1]))
            else:
                print('体裁判型：%s（%d 分）——python3 scripts/pick-recipe.py --show %s'
                      % (name, top[1], top[0]))
        except Exception as e:
            print('（判型跳过：%s）' % e)
    if a.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(('成稿闸：%d 页，红 %d / 警告 %d —— ' % (len(slides), len(red), len(warn))) +
              ('不许出片' if bad else '可以出片'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
