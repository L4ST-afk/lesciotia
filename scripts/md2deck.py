#!/usr/bin/env python3
"""Markdown 入口：一份 `.md` 直接出一册单文件 HTML deck（B 出口）。

这不是"任意 Markdown 无脑转成漂亮幻灯片"——那会违背本库「先选族再排」的边界。
它只做四件事：认结构、配族、落 token、给出可继续手改的 HTML。写完仍然要过
`check-fit.py`，装不下就删字或换族，别指望脚本替你决定。

映射（只有这几条，其余一律当正文）：
  `# 标题`            → cover 族（副标题取紧随的第一段）
  `## 小节`           → 一页；其下 `### 分节` 各自再占一页（章名退成小注）
  正文里有什么就配什么族：
      1 张 `![alt](src)`   → image 族（image-single，图不裁）
      只有 `> 引用`        → quote 族（下一段当署名）
      ≥2 张 `![alt](src)`  → image-set 族（3 张＝image-set / 4-5 张＝image-round / 6 张＝image-card）
      ``` 代码块 ```       → code 族
      `- ` 列表            → text 族（卡片列，默认 data-build 逐条揭示）
      其余                 → text 族（lede 段）
  `---` 之后的 `# 收束`  → end 族（可省，脚本自动补一页）

用法：
  python3 scripts/md2deck.py 讲稿.md -o deck.html [--theme guanglan-rd] [--title "..."]
  python3 scripts/md2deck.py 讲稿.md -o deck.html --no-build   # 关掉逐条揭示
"""
import argparse
import html as H
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
THEME_DIR = ROOT / 'assets' / 'themes'


def esc(s):
    return H.escape(s, quote=False)


def inline(s):
    """行内：`代码`、**粗**、*斜*、[文字](链接) —— 只做这几样，别指望完整 CommonMark。"""
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    return s


def read_nav(body: str):
    """读册级导航条：首部 `<!-- nav: 序 > 现状 > 判断 -->`；`nav-block:` 出色块型。

    返回 (章节名列表, 形式)，没有指令就 (None, 'text')。分隔符认 `>` 与全角「｜」，
    不认逗号——章节名里常有逗号。
    """
    names, form = None, 'text'
    for tag in ('nav', 'nav-block'):
        m = re.search(r'<!--\s*%s:\s*(.*?)\s*-->' % tag, body)
        if m:
            raw = m.group(1)
            names = [x.strip() for x in re.split(r'\s*>\s*|｜', raw) if x.strip()]
            form = 'block' if tag == 'nav-block' else 'text'
            body = body.replace(m.group(0), '', 1)
    return names, form


def split_front(text):
    meta, body = {}, text
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"\'')
        body = text[m.end():]
    return meta, body


def parse_pages(body):
    """按 `## ` 切页；`# ` 只在最前面当封面标题。

    `<!-- sec: 现状 -->` 是本页所属章节，记在 `page['sec']` 里并**从正文删掉**——
    注释混进 blocks() 会被当成一段文字，把 family_of 判歪。
    """
    lines = body.splitlines()
    title, lead, pages, cur = None, [], [], None
    for ln in lines:
        s = ln.rstrip()
        m_sec = re.match(r'\s*<!--\s*sec:\s*(.*?)\s*-->\s*$', s)
        if m_sec:
            if cur is not None:
                cur['sec'] = m_sec.group(1).strip()
            continue
        m_band = re.match(r'\s*<!--\s*band:\s*(.*?)\s*-->\s*$', s)
        if m_band:
            if cur is not None:
                cur['band'] = m_band.group(1).strip()
            continue
        m_dir = re.match(r'\s*<!--\s*(layout|chips):\s*(.*?)\s*-->\s*$', s)
        if m_dir:
            if cur is not None:
                if m_dir.group(1) == 'layout':
                    cur['layout'] = m_dir.group(2).strip().lower()
                else:
                    cur['chips'] = [x.strip() for x in re.split(r'\s*[｜|]\s*', m_dir.group(2)) if x.strip()]
            continue
        if s.startswith('# ') and not s.startswith('## '):
            if title is None and cur is None:
                title = s[2:].strip()
            else:
                cur = {'head': s[2:].strip(), 'body': [], 'layout': None, 'chips': None, 'band': None}
                pages.append(cur)
        elif s.startswith('## '):
            cur = {'head': s[3:].strip(), 'body': [], 'parent': None, 'layout': None, 'chips': None, 'band': None}
            pages.append(cur)
        elif s.startswith('### '):
            parent = cur['parent'] or cur['head'] if cur else None
            if cur is not None and not cur['parent'] and not any(x.strip() for x in cur['body']):
                # `##` 后紧跟 `###`：`##` 只当章名，不单独占一页
                pages.pop()
            cur = {'head': s[4:].strip(), 'body': [], 'parent': parent, 'layout': None, 'chips': None, 'band': None}
            pages.append(cur)
        elif re.match(r'^\s*---\s*$', s):
            continue   # 页间分隔线只是写作习惯，不是正文
        else:
            if cur is None:
                if s.strip():
                    lead.append(s)
            else:
                cur['body'].append(s)
    return title, lead, pages


def blocks(items):
    """把一页正文切成块：para / list / code / img / table。"""
    out, i, n = [], 0, len(items)
    while i < n:
        s = items[i]
        t = s.strip()
        if not t:
            i += 1
            continue
        if t.startswith('```'):
            lang = t[3:].strip() or 'text'
            j, buf = i + 1, []
            while j < n and not items[j].strip().startswith('```'):
                buf.append(items[j])
                j += 1
            out.append(('code', lang, '\n'.join(buf)))
            i = j + 1
            continue
        if t.startswith('>'):
            out.append(('quote', inline(t.lstrip('>').strip())))
            i += 1
            continue
        m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', t)
        if m:
            out.append(('img', m.group(1), m.group(2)))
            i += 1
            continue
        if re.match(r'- ', t):
            buf = []
            while i < n and re.match(r'(?:- |  - )', items[i].strip() or ' '):
                buf.append(inline(items[i].strip()[2:].strip()))
                i += 1
            out.append(('list', buf))
            continue
        if re.match(r'\d+\. ', t):
            buf = []
            while i < n and re.match(r'\d+\. ', items[i].strip() or ' '):
                buf.append(inline(re.sub(r'^\d+\.\s*', '', items[i].strip())))
                i += 1
            out.append(('num', buf))
            continue
        if t.startswith('|'):
            buf = []
            while i < n and items[i].strip().startswith('|'):
                row = [c.strip() for c in items[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:\s]*', c) for c in row):
                    buf.append(row)
                i += 1
            out.append(('table', buf))
            continue
        buf = [t]
        i += 1
        while i < n and items[i].strip() and not re.match(r'(- |\d+\. |```|!\[|\|)', items[i].strip()):
            buf.append(items[i].strip())
            i += 1
        out.append(('para', ' '.join(buf)))
    return out


def family_of(bl):
    kinds = [b[0] for b in bl]
    if kinds in (['quote'], ['quote', 'para'], ['para', 'quote']):
        return 'quote'
    if kinds.count('img') == 1 and 'code' not in kinds and 'table' not in kinds:
        return 'image1'
    if kinds.count('img') >= 2:
        return 'image'
    if 'code' in kinds:
        return 'code'
    if 'table' in kinds and 'list' not in kinds:
        return 'table'
    if kinds.count('num') and sum(len(b[1]) for b in bl if b[0] == 'num') >= 3:
        return 'process'
    return 'text'


def render_text(head, bl, build, kick=''):
    paras = [b for b in bl if b[0] == 'para']
    lists = [b for b in bl if b[0] == 'list']
    nums = [b for b in bl if b[0] == 'num']
    out = []
    out.append('  <p class="kicker">%s</p>' % kick)
    out.append('  <h2 class="h2">%s</h2>' % inline(head))
    if paras:
        out.append('  <p class="lede mb-l">%s</p>' % inline(paras[0][1]))
    for p in paras[1:]:
        out.append('  <p class="dim">%s</p>' % inline(p[1]))
    tag = ' data-build' if build else ''
    if lists:
        items = [x for l in lists for x in l[1]]
        cls = 'grid g2 anim-stagger-list' if len(items) > 3 else 'grid g1 anim-stagger-list'
        out.append('  <div class="%s"%s data-anim-target style="align-items:start;align-content:start;grid-auto-rows:min-content">' % (cls, tag))
        for it in items:
            out.append('    <div class="card card-accent step"><p>%s</p></div>' % it)
        out.append('  </div>')
    if nums:
        items = [x for l in nums for x in l[1]]
        out.append('  <div class="grid g3 anim-stagger-list"%s data-anim-target style="align-items:start;align-content:start;grid-auto-rows:min-content">' % tag)
        for k, it in enumerate(items, 1):
            out.append('    <div class="card step"><p class="eyebrow">%02d</p><p>%s</p></div>' % (k, it))
        out.append('  </div>')
    return '\n'.join(out)


def render_quote(head, bl, kick=''):
    q = [b for b in bl if b[0] == 'quote'][0][1]
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <p class="kicker">%s</p>' % kick]
    out.append('  <div style="max-width:1180px">')
    out.append('    <div class="serif" style="font-size:var(--t-display);line-height:.9;color:var(--accent);opacity:.55">“</div>')
    out.append('    <blockquote class="serif" style="font-size:var(--t-h3);line-height:1.35;margin:-6px 0 22px;font-weight:600">%s</blockquote>' % q)
    if paras:
        out.append('    <p class="dim" style="font-size:var(--t-cap);letter-spacing:.08em">%s</p>' % inline(paras[-1][1]))
    out.append('  </div>')
    return '\n'.join(out)


def render_image_single(head, bl, build, fix=None):
    img = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img'][0]
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <h2 class="h2">%s</h2>' % inline(head)]
    out.append('  <div class="fig anim-fade-up"%s><figure class="img-frame contain"><img src="%s" alt="%s"></figure>' % (' data-anim="fade-up"' if build else '', img[1], esc(img[0])))
    if paras:
        out.append('    <p class="img-cap">%s</p>' % inline(paras[0][1]))
    out.append('  </div>')
    return '\n'.join(out)


def image_style(bl) -> str:
    """图组选式：窄图过半走 phone；否则 1-3 格 bento / 4-5 圆切 / 6 卡列。"""
    imgs = [b for b in bl if b[0] == 'img']
    n = len(imgs)
    narrow = sum(1 for b in imgs if _is_narrow(b[2]))
    if n >= 2 and narrow * 2 >= n:
        return 'image-phone'
    # 4-5 张宽的走 band（c1 主图 2×2、其余填格、图注压 accent 条），与 C 出口的 figures bento 同构
    return 'image-band' if 4 <= n <= 5 else ('image-set' if n <= 3 else 'image-card')


def _is_narrow(path: str) -> bool:
    """宽高比 < 0.9 视为窄图；读不到尺寸就当不窄，宁可走默认版式也不误判。"""
    try:
        from PIL import Image
    except Exception:
        return False
    try:
        f = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
        with Image.open(f) as im:
            return im.width / im.height < 0.9
    except Exception:
        return False


def render_images(head, bl, build, fix=None):
    imgs = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img']
    paras = [b for b in bl if b[0] == 'para']
    n = len(imgs)
    mode = image_style(bl)
    cls = {'image-phone': 'gal phone', 'image-set': 'gal three', 'image-band': 'gg band',
           'image-card': 'gal card'}[mode]
    out = ['  <h2 class="h2">%s</h2>' % inline(head)]
    if paras:
        out.append('  <p class="lede mb-l">%s</p>' % inline(paras[0][1]))
    tag = ' data-build' if build else ''
    if mode == 'image-band':
        out.append('  <div class="%s"%s data-anim-target>' % (cls, tag))
        for i, (alt, src) in enumerate(imgs, 1):
            out.append('    <div class="cell c%d step"><img src="%s" alt="%s"><span>%s</span></div>'
                       % (i, src, esc(alt), esc(alt)))
        out.append('  </div>')
    elif mode == 'image-card':
        out.append('  <div class="%s"%s data-anim-target>' % (cls, tag))
        for alt, src in imgs:
            out.append('    <figure class="step"><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (src, esc(alt), esc(alt)))
        out.append('  </div>')
    elif mode == 'image-round':
        out.append('  <div class="%s"%s>' % (cls, tag))
        for alt, src in imgs:
            out.append('    <figure class="step"><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (src, esc(alt), esc(alt)))
        out.append('  </div>')
    else:
        out.append('  <div class="%s"%s data-anim-target>' % (cls, tag))
        for alt, src in imgs:
            out.append('    <figure class="step"><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (src, esc(alt), esc(alt)))
        out.append('  </div>')
    return '\n'.join(out)


def render_code(head, bl, kick=''):
    code = [b for b in bl if b[0] == 'code'][0]
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <p class="kicker">%s</p>' % kick] if kick else []
    out.append('  <h2 class="h2">%s</h2>' % inline(head))
    if paras:
        out.append('  <p class="lede mb-l">%s</p>' % inline(paras[0][1]))
    out.append('<pre class="card mt-m" style="padding:24px"><code class="language-%s">%s</code></pre>' % (esc(code[1]), esc(code[2])))
    return '\n'.join(out)


def render_process(head, bl, build, kick=''):
    nums = [x for b in bl if b[0] == 'num' for x in b[1]]
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <p class="kicker">%s</p>' % (kick or '步骤 · %d 步' % len(nums))]
    out.append('  <h2 class="h2">%s</h2>' % inline(head))
    if paras:
        out.append('  <p class="lede mb-l">%s</p>' % inline(paras[0][1]))
    tag = ' data-build' if build else ''
    out.append('  <div class="steps anim-stagger-list"%s data-anim-target>' % tag)
    for k, it in enumerate(nums, 1):
        out.append('    <div class="step" style="padding-right:72px"><div class="num">%d</div><p>%s</p></div>' % (k, it))
    out.append('  </div>')
    return '\n'.join(out)


def render_table(head, bl):
    tbl = [b for b in bl if b[0] == 'table'][0][1]
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <h2 class="h2">%s</h2>' % inline(head)]
    if paras:
        out.append('  <p class="lede mb-l">%s</p>' % inline(paras[0][1]))
    out.append('  <div class="split6"><div class="main"><table class="t">')
    head_row, *rows = tbl
    out.append('    <thead><tr>%s</tr></thead>' % ''.join('<th class="num">%s</th>' % inline(c) if re.fullmatch(r'[\d.,%¥+\-]+', c or '') else '<th>%s</th>' % inline(c) for c in head_row))
    out.append('    <tbody>')
    for r in rows:
        out.append('      <tr>%s</tr>' % ''.join('<td class="num">%s</td>' % inline(c) if re.fullmatch(r'[\d.,%¥+\-]+', c or '') else '<td>%s</td>' % inline(c) for c in r))
    out.append('    </tbody>')
    quotes = [b for b in bl if b[0] == 'quote']
    aside = quotes[0][1] if quotes else '<span class="dim">表在左，结论在右：在 md 里写一行 <code>&gt; 结论</code>。</span>'
    out.append('  </table></div><div class="aside"><p class="eyebrow">结论</p><p class="dim">%s</p></div></div>' % aside)
    return '\n'.join(out)



def _card_fields(item: str):
    """列表项按全角「｜」切成卡的字段：第一段是小标题，其余是段落。

    只认全角竖线：半角 `|` 在 md 里是表格语法，别混。
    """
    parts = [x.strip() for x in re.split(r'｜', item) if x.strip()]
    return (parts[0] if parts else ''), parts[1:]


def render_chips(chips):
    if not chips:
        return ''
    spans = ''.join('<span class="chip%s">%s</span>' % (' on' if i == 0 else '', esc(c))
                    for i, c in enumerate(chips))
    return '  <div class="chips">%s<span class="chip more">……</span></div>' % spans


def render_ride(head, bl, build, fix=None, kick=''):
    """图带压卡：1 图当图带、首段当压在图上的结论、列表项当骑压的白卡。"""
    imgs = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img']
    paras = [b for b in bl if b[0] == 'para']
    cards = [x for b in bl if b[0] == 'list' for x in b[1]]
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    out.append('  <div class="ride">')
    out.append('    <div class="rt-img"><img src="%s" alt="%s">' % (imgs[0][1], esc(imgs[0][0])))
    if paras:
        out.append('      <p class="rt-thesis">%s</p>' % inline(paras[0][1]))
    out.append('    </div>')
    out.append('    <div class="rt-cards">')
    for it in cards[:3]:
        parts = [x.strip() for x in re.split(r'｜', it) if x.strip()]
        # 图带卡的小标题给两行：标题｜副标（三字段以上时），其余当正文段
        head2 = parts[0]
        if len(parts) >= 3:
            head2 = parts[0] + '<br>' + parts[1]
            ps = parts[2:]
        else:
            ps = parts[1:]
        body = ''.join('<p>%s</p>' % inline(x) for x in ps)
        out.append('      <div class="rt-card"><b>%s</b>%s</div>' % (inline(head2).replace('&lt;br&gt;', '<br>'), body))
    out.append('    </div>')
    out.append('  </div>')
    return '\n'.join(out)


def render_cols3(head, bl, build, kick='', chips=None):
    """底线三段卡：列表项按「标题｜段一｜段二」切，卡底一道 accent。"""
    cards = [x for b in bl if b[0] == 'list' for x in b[1]]
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    if chips:
        out.append(render_chips(chips))
    out.append('  <div class="cols3">')
    for it in cards[:3]:
        title, ps = _card_fields(it)
        body = ''
        for i, x in enumerate(ps):
            if i:
                body += '<div class="dv"></div>'
            body += '<p>%s</p>' % x
        out.append('    <div class="c3"><span class="k">%s</span>%s</div>' % (inline(title), body))
    out.append('  </div>')
    return '\n'.join(out)


def render_bleed(head, bl, fix=None, kick=''):
    """左文右图出血：文本两段在左，图推到页边。"""
    imgs = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img']
    paras = [b for b in bl if b[0] == 'para']
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    out.append('  <div class="split bleed-img">')
    out.append('    <div class="col-text">')
    for i, p_ in enumerate(paras[:3]):
        out.append('      <p class="lede%s">%s</p>' % ('' if i == 0 else ' dim', inline(p_[1])))
    out.append('    </div>')
    out.append('    <div class="col-img"><figure class="img-frame"><img src="%s" alt="%s"></figure></div>' % (imgs[0][1], esc(imgs[0][0])))
    out.append('  </div>')
    return '\n'.join(out)


def _month_idx(s: str):
    """把 `2026-07` / `2026-07-15` 折成绝对月序（年×12＋月），月粒度已够甘特用。"""
    m = re.search(r'(\d{4})[-/.](\d{1,2})', s or '')
    if not m:
        return None
    return int(m.group(1)) * 12 + int(m.group(2)) - 1


def _pct(s: str) -> int:
    m = re.search(r'(\d{1,3})', s or '')
    return max(0, min(100, int(m.group(1)))) if m else 0


def render_gantt(head, bl, kick=''):
    """甘特二式：日期算刻度，跨年分带，条内嵌完成度，模块之间加一道虚线。"""
    tbl = [b for b in bl if b[0] == 'table']
    if not tbl:
        return render_text(head, bl, False, kick)
    rows = tbl[0][1]
    if rows and ('起' in rows[0] or '开始' in rows[0]):
        rows = rows[1:]
    tasks = []
    for r in rows:
        if len(r) < 4:
            continue
        name, mod, st, en = r[0], r[1], r[2], r[3]
        a, b_ = _month_idx(st), _month_idx(en)
        if a is None or b_ is None or b_ < a:
            continue
        tasks.append({'name': name, 'mod': mod, 'start': a, 'end': b_,
                      'pct': _pct(r[4]) if len(r) > 4 else 0})
    if not tasks:
        return render_text(head, bl, False, kick)
    lo = min(t['start'] for t in tasks)
    hi = max(t['end'] for t in tasks)
    total = hi - lo + 1
    years, months = {}, []
    for k in range(total):
        y, m = divmod(lo + k, 12)
        years.setdefault(y, 0)
        years[y] += 1
        months.append('%02d' % (m + 1))
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    out.append('  <div class="gantt2" style="--cols:%d;--step:%.6f%%">' % (total, 100.0 / total))
    out.append('    <div class="g2-head"><div class="g2-lbl">任务</div><div class="g2-scale">')
    out.append('      <div class="g2-years">%s</div>' % ''.join(
        '<span style="grid-column:span %d">%d</span>' % (n, y) for y, n in years.items()))
    out.append('      <div class="g2-months">%s</div>' % ''.join('<span>%s</span>' % m for m in months))
    out.append('    </div></div>')
    out.append('    <div class="g2-rows">')
    last_mod = None
    for t in tasks:
        modstart = ' is-modstart' if (last_mod is not None and t['mod'] != last_mod) else ''
        last_mod = t['mod']
        left = (t['start'] - lo) / total * 100
        width = (t['end'] - t['start'] + 1) / total * 100
        out.append('      <div class="g2-row%s">' % modstart)
        out.append('        <div class="g2-lbl">%s%s</div>' % (
            inline(t['name']), ('<b class="g2-mod">%s</b>' % inline(t['mod'])) if t['mod'] else ''))
        out.append('        <div class="g2-track"><div class="g2-bar%s" style="left:%.4f%%;width:%.4f%%">'
                   % (' is-done' if t['pct'] >= 100 else '', left, width))
        out.append('          <i class="g2-fill" style="width:%d%%"></i><span class="g2-pct">%d%%</span></div></div>' % (t['pct'], t['pct']))
        out.append('      </div>')
    out.append('    </div>')
    paras = [b[1] for b in bl if b[0] == 'para']
    if paras:
        out.append('    <div class="g2-foot"><b>结论</b><span>%s</span></div>' % inline(paras[-1]))
    out.append('  </div>')
    return '\n'.join(out)


def render_modules(head, bl, fix=None, kick='', chips=None):
    """模块格：卡片分格装载，末格可让给图（图满格、去圆角内缘）。"""
    cards = [x for b in bl if b[0] == 'list' for x in b[1]]
    imgs = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img']
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    if chips:
        out.append(render_chips(chips))
    out.append('  <div class="mod-grid">')
    for it in cards[:4]:
        title, ps = _card_fields(it)
        body = ''.join('<p>%s</p>' % inline(x) for x in ps[:2])
        out.append('    <div class="mod"><p class="k">%s</p>%s</div>' % (inline(title.upper()[:24]), body))
    if imgs:
        out.append('    <figure class="mod tile-img"><img src="%s" alt="%s"></figure>' % (imgs[0][1], esc(imgs[0][0])))
    out.append('  </div>')
    return '\n'.join(x for x in out if x)


def render_arc(head, bl, fix=None, kick='', uid=1):
    """弧形分割：一条 S 弧当分界，图在右（推到页边）、文在左。
    弧线走 objectBoundingBox 的 clipPath，坐标 0–1，跟画布尺寸解耦。"""
    imgs = [(b[1], fix(b[2]) if fix else b[2]) for b in bl if b[0] == 'img']
    paras = [b[1] for b in bl if b[0] == 'para']
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    out.append('  <svg width="0" height="0" style="position:absolute" aria-hidden="true">'
               '<defs><clipPath id="arcClip%d" clipPathUnits="objectBoundingBox">'
               '<path d="M .34,0 C .20,.22 .16,.38 .20,.54 C .24,.70 .16,.86 .10,1 L 1,1 L 1,0 Z"/>'
               '</clipPath></defs></svg>' % uid)
    out.append('  <div class="arc">')
    out.append('    <figure class="arc-img is-clipped" style="--arc-clip:url(#arcClip%d)">'
               '<img src="%s" alt="%s"></figure>' % (uid, imgs[0][1], esc(imgs[0][0])))
    out.append('    <div class="arc-body">')
    for i, p_ in enumerate(paras[:3]):
        out.append('      <p class="%s">%s</p>' % ('lead' if i == 0 else '', inline(p_)))
    out.append('    </div>')
    out.append('  </div>')
    return '\n'.join(out)


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3) * p0 + 3 * (u ** 2) * t * p1 + 3 * u * (t ** 2) * p2 + (t ** 3) * p3


def render_timeline(head, bl, kick=''):
    """弧线时间轴：曲线与圆点算在 SVG 里，卡片按圆点的 x/y 定位，竖杆交替上下。"""
    items = [x for b in bl if b[0] == 'list' for x in b[1]]
    if not items:
        return render_text(head, bl, False, kick)
    out = ['  <p class="kicker">%s</p>' % kick, '  <h2 class="h2">%s</h2>' % inline(head)]
    W, H = 1376, 590
    P = [(0, 285), (330, 245), (1046, 335), (W, 285)]
    d = 'M%d,%d C%d,%d %d,%d %d,%d' % (P[0][0], P[0][1], P[1][0], P[1][1], P[2][0], P[2][1], P[3][0], P[3][1])
    n = len(items[:6])
    out.append('  <div class="tline"><svg class="tl-svg" viewBox="0 0 %d %d" preserveAspectRatio="none">' % (W, H))
    out.append('    <path d="%s"/>' % d)
    dots, cards = [], []
    for i, it in enumerate(items[:6]):
        parts = [x.strip() for x in re.split(r'｜', it) if x.strip()]
        date = parts[0] if parts else ''; title = parts[1] if len(parts) > 1 else ''
        note = parts[2] if len(parts) > 2 else ''
        t = (i + 0.5) / n
        x = _bezier(P[0][0], P[1][0], P[2][0], P[3][0], t)
        y = _bezier(P[0][1], P[1][1], P[2][1], P[3][1], t)
        above = (i % 2 == 0)
        card_h = 200
        top = max(6, y - 46 - card_h) if above else min(H - card_h - 6, y + 46)
        stem_y1, stem_y2 = (y - 18, top + card_h) if above else (y + 18, top)
        dots.append('<circle cx="%.1f" cy="%.1f" r="7"/>' % (x, y))
        dots.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (x, stem_y1, x, stem_y2))
        cards.append('    <div class="tl-card" style="left:%.2f%%;top:%dpx"><p class="d">%s</p>'
                     '<p class="t">%s</p><p class="n">%s</p></div>'
                     % (x / W * 100, top, inline(date), inline(title), inline(note)))
    out.append('    %s' % ''.join(dots))
    out.append('  </svg>')
    out.extend(cards)
    out.append('  </div>')
    return '\n'.join(out)


def claim_band(text):
    return '  <div class="claim-band"><span>%s</span></div>' % inline(text)


def split_item(s: str, limit: int = 19):
    """C 出口的 bullets 正文 32px、单条只有 19 字的位置；长句要拆成「主句 + 小注」。

    在 6–22 字之间找第一个标点断开（优先 `：`，其次 `，。；`），找不到就硬切并加省略号。
    返回 (主句, 小注)，小注可为空。
    """
    s = s.strip()
    if len(s) <= limit:
        return s, ''
    for mark in ('：', '，', '。', '；'):
        cut = s.find(mark, 5)
        if 0 < cut <= 24:
            return s[:cut + 1], s[cut + 1:].strip()
    return s[:limit] + '…', s[limit:].strip()


def nav_markup(nav, form, cur):
    """导航条标记（B 出口）：一章一项，当前页所属那项加 .on。"""
    cls = 'deck-nav is-block' if form == 'block' else 'deck-nav'
    items = ''.join(
        '<span class="nv%s">%s</span>' % (' on' if (cur and n == cur) else '', esc(n))
        for n in nav)
    return '  <nav class="%s" aria-label="章节">%s</nav>' % (cls, items)


def to_spec(pages, meta, title, brand, a_src_dir=None):
    """把 md 的页映射成 C 出口的 spec。**只映射 C 里真有的页型**，其余跳过并明说。

    对照：cover/bullets/quote/table/end 有对应；image 系列与 code 在 C 出口没有等价页型
    （C 的图片只能是版式里的装饰，不是「一图一页」），跳过往 `skipped` 里记，不硬塞。
    """
    out, skipped, notes = [], [], []
    slide = {'type': 'cover', 'title': [title],
             'kicker': meta.get('kicker', ''),
             'lede': '', 'source': meta.get('source', brand),
             'footer': brand}
    out.append(slide)
    for idx, pg in enumerate(pages, 1):
        bl = blocks(pg['body'])
        fam = family_of(bl)
        layout = pg.get('layout')
        head = pg['head']
        foot = f'{brand} · {idx:02d}'
        cards = [x for b in bl if b[0] == 'list' for x in b[1]]
        paras = [b[1] for b in bl if b[0] == 'para']
        imgs = [b for b in bl if b[0] == 'img']
        if layout in ('ride', 'cols3', 'bleed'):
            if layout == 'ride' and imgs and cards:
                titles, caps = [], []
                for it in cards[:5]:
                    t, ps = _card_fields(it)
                    titles.append(t)
                    caps.append(ps[0] if ps else '')
                out.append({'type': 'bullets', 'title': head, 'items': titles,
                            'captions': caps, 'source': meta.get('source', brand), 'footer': foot})
                notes.append((idx, head, '图带压卡：C 侧降级为列表页，图与压卡结构不保留'))
            elif layout == 'cols3' and cards:
                titles, caps = [], []
                for it in cards[:5]:
                    t, ps = _card_fields(it)
                    titles.append(t)
                    caps.append(' '.join(ps)[:96])
                out.append({'type': 'bullets', 'title': head, 'items': titles,
                            'captions': caps, 'source': meta.get('source', brand), 'footer': foot})
                notes.append((idx, head, '底线三段卡：C 侧降级为列表页，卡底 accent 线不保留'))
            elif layout == 'bleed' and imgs:
                src = imgs[0][2]
                if not re.match(r'(https?:|data:|/)', src):
                    src = str((a_src_dir / src).resolve()) if a_src_dir else src
                out.append({'type': 'figure', 'title': head, 'image': src,
                            'caption': re.sub(r'<[^>]+>', '', paras[0]) if paras else imgs[0][1],
                            'source': meta.get('source', brand), 'footer': foot})
                notes.append((idx, head, '左文右图出血：C 侧出单图页，左侧两段正文折进图注'))
            else:
                notes.append((idx, head, 'layout 指令缺图或缺卡片，按普通页处理'))
                layout = None
        if layout == 'gantt':
            tbl = [b for b in bl if b[0] == 'table']
            rows = tbl[0][1] if tbl else []
            if rows and ('起' in rows[0] or '开始' in rows[0]):
                rows = rows[1:]
            rows = [r[:5] for r in rows if len(r) >= 4]
            if rows:
                out.append({'type': 'table', 'title': head, 'cols': ['任务', '模块', '起', '止', '完成'],
                            'rows': [r + [''] * (5 - len(r)) for r in rows],
                            'source': meta.get('source', brand), 'footer': foot})
                notes.append((idx, head, '甘特：C 侧降级为表格（日期与完成度保留，条、跨年分带不保留）'))
            else:
                notes.append((idx, head, '甘特缺日期表，按普通页处理'))
                layout = None
        elif layout == 'modules' and cards:
            titles, caps = [], []
            for it in cards[:5]:
                t, ps = _card_fields(it)
                titles.append(t)
                caps.append(' '.join(ps)[:96])
            out.append({'type': 'bullets', 'title': head, 'items': titles,
                        'captions': caps, 'source': meta.get('source', brand), 'footer': foot})
            notes.append((idx, head, '模块格：C 侧降级为列表页，图格与分格结构不保留'))
        elif layout == 'modules':
            notes.append((idx, head, '模块格缺卡片，按普通页处理'))
            layout = None
        elif layout == 'arc' and imgs:
            src = imgs[0][2]
            if not re.match(r'(https?:|data:|/)', src):
                src = str((a_src_dir / src).resolve()) if a_src_dir else src
            out.append({'type': 'figure', 'title': head, 'image': src,
                        'caption': re.sub(r'<[^>]+>', '', paras[0]) if paras else imgs[0][1],
                        'source': meta.get('source', brand), 'footer': foot})
            notes.append((idx, head, '弧形分割：C 侧出单图页，S 弧与左侧正文折进图注'))
        elif layout == 'timeline-arc' and cards:
            items, caps = [], []
            for it in cards[:6]:
                parts = [x.strip() for x in re.split(r'｜', it) if x.strip()]
                items.append(' '.join(parts[:2]))
                caps.append(parts[2] if len(parts) > 2 else '')
            out.append({'type': 'bullets', 'title': head, 'items': items,
                        'captions': caps, 'source': meta.get('source', brand), 'footer': foot})
            notes.append((idx, head, '弧线时间轴：C 侧降级为列表页，曲线与上下交替不保留'))
        elif layout == 'timeline-arc':
            notes.append((idx, head, '弧线时间轴缺里程碑，按普通页处理'))
            layout = None
        if layout in ('ride', 'cols3', 'bleed', 'gantt', 'modules', 'arc', 'timeline-arc'):
            pass
        elif fam == 'quote':
            q = [b for b in bl if b[0] == 'quote'][0][1]
            paras = [b for b in bl if b[0] == 'para']
            out.append({'type': 'quote', 'title': head, 'text': q,
                        'size': 44 if len(q) > 24 else 56,
                        'by': ('— ' + paras[-1][1].lstrip('—').strip()) if paras else '',
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'table':
            tbl = [b for b in bl if b[0] == 'table'][0][1]
            cols, rows = tbl[0], [t for t in tbl[1:]]
            out.append({'type': 'table', 'title': head, 'cols': cols, 'rows': rows,
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'text':
            lists = [x for b in bl if b[0] in ('list', 'num') for x in b[1]]
            paras = [b[1] for b in bl if b[0] == 'para']
            items = [re.sub(r'<[^>]+>', '', x) for x in lists] or [re.sub(r'<[^>]+>', '', p_) for p_ in paras[:3]]
            if not items:
                skipped.append((idx, head, '空页'))
                continue
            pairs = [split_item(x) for x in items[:5]]
            out.append({'type': 'bullets', 'title': head, 'items': [p_[0] for p_ in pairs],
                        'captions': [p_[1] for p_ in pairs],
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'process':
            nums = [re.sub(r'<[^>]+>', '', x) for b in bl if b[0] == 'num' for x in b[1]]
            pairs = [split_item(x, 15) for x in nums[:5]]
            out.append({'type': 'bullets', 'title': head,
                        'items': [f'{k}. {pairs[k - 1][0]}' for k in range(1, len(pairs) + 1)],
                        'captions': [p_[1] for p_ in pairs],
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'image':
            imgs = [b for b in bl if b[0] == 'img']
            paras = [b[1] for b in bl if b[0] == 'para']
            if any(b[2].lower().endswith('.svg') for b in imgs):
                skipped.append((idx, head, '图组里有 SVG：C 出口只认位图，换 PNG 或留在 B 出口'))
                continue
            items = []
            for alt, src in [(b[1], b[2]) for b in imgs][:5]:
                if re.match(r'(https?:|data:)', src):
                    skipped.append((idx, head, '图组里有网络图：C 出口要本地文件'))
                    items = []
                    break
                if not src.startswith('/'):
                    src = str((a_src_dir / src).resolve()) if a_src_dir else src
                items.append({'image': src, 'caption': alt})
            if not items:
                continue
            out.append({'type': 'figures', 'title': head, 'items': items,
                        'lede': (re.sub(r'<[^>]+>', '', paras[0]) if paras else ''),
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'image1':
            img = [b for b in bl if b[0] == 'img'][0]
            paras = [b[1] for b in bl if b[0] == 'para']
            src = img[2]
            if src.lower().endswith('.svg'):
                skipped.append((idx, head, '图是 SVG：C 出口只认位图（PNG/JPG），换图或留在 B 出口'))
                continue
            if not re.match(r'(https?:|data:|/)', src):
                src = str((a_src_dir / src).resolve()) if a_src_dir else src
            out.append({'type': 'figure', 'title': head, 'image': src,
                        'caption': (re.sub(r'<[^>]+>', '', paras[0]) if paras else img[1]),
                        'source': meta.get('source', brand), 'footer': foot})
        elif fam == 'code':
            blk = [b for b in bl if b[0] == 'code'][0]
            paras = [b[1] for b in bl if b[0] == 'para']
            out.append({'type': 'code', 'title': head, 'lang': blk[1],
                        'lines': blk[2].splitlines(),
                        'note': re.sub(r'<[^>]+>', '', paras[0]) if paras else '',
                        'source': meta.get('source', brand), 'footer': foot})
        else:
            skipped.append((idx, head, '未映射'))
        if pg.get('sec') and out and out[-1].get('type') != 'cover':
            out[-1]['sec'] = pg['sec']
    out.append({'type': 'end', 'title': '谢谢', 'lede': meta.get('outro', '讲完这一册，剩下的交给现场。'),
                'source': meta.get('source', brand), 'footer': brand})
    return {'slides': out, 'skipped': skipped, 'notes': notes}


def emit_pptx(a, build_steps: bool) -> int:
    """同一份 md 再出一件原生 PPTX：先映射成 spec，再调 export-pptx.py。"""
    import json, subprocess, tempfile
    meta, body = split_front(a.src.read_text(encoding='utf-8'))
    nav, nav_form = read_nav(body)
    body = re.sub(r'<!--\s*nav(?:-block)?:\s*.*?-->', '', body, count=1, flags=re.S)
    title, _lead, pages = parse_pages(body)
    title = a.title or meta.get('title') or title or a.src.stem
    theme = meta.get('theme') or a.theme or 'guanglan-rd'
    brand = meta.get('brand', '来雪亭')
    spec = to_spec(pages, meta, title, brand, a.src.parent.resolve())
    tmp = pathlib.Path(tempfile.mkdtemp()) / 'spec.json'
    payload = {'slides': spec['slides']}
    if nav:
        payload['nav'] = nav
        payload['nav_form'] = nav_form
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    for idx, head, why in spec['skipped']:
        print(f'  · 跳过第 {idx} 页「{head}」：{why}')
    for idx, head, why in spec.get('notes', []):
        print(f'  · 降级第 {idx} 页「{head}」：{why}')
    cmd = [sys.executable, str(ROOT / 'scripts' / 'export-pptx.py'), str(tmp),
           '-o', str(a.pptx), '--theme', theme, '--allow-prose', '--force']
    # md 是这册的正源：成稿闸的「字数够不够 / 单条太长」判据是给手写 spec 用的，
    # 从 md 映射出来的页一律放行（跳过的页已逐条列出，不会悄悄丢内容）。
    if a.pptx_animate or build_steps:
        cmd.append('--animate')
    return subprocess.call(cmd)


def build(src_path, out, theme, title_override, build_steps):
    src = src_path
    meta, body = split_front(src.read_text(encoding='utf-8'))
    nav, nav_form = read_nav(body)
    body = re.sub(r'<!--\s*nav(?:-block)?:\s*.*?-->', '', body, count=1, flags=re.S)
    title, lead, pages = parse_pages(body)
    title = title_override or meta.get('title') or title or src.stem
    theme = meta.get('theme') or theme
    if theme and not (THEME_DIR / (theme + '.css')).is_file():
        cand = sorted(p.stem for p in THEME_DIR.glob('*.css'))
        print('✗ 主题 %s 不存在；可用：%s' % (theme, ', '.join(cand)), file=sys.stderr)
        return 1
    theme = theme or 'guanglan-rd'
    out_dir = out.parent.resolve()

    def link(p):
        return pathlib.PurePosixPath(os.path.relpath(p, out_dir)).as_posix()

    def fix_image(src):
        """md 里的图片按 md 文件位置算，落到 deck 里要改成相对 deck 的路径。"""
        if re.match(r'(https?:|data:|file:|/)', src):
            return src
        return link((src_path.parent / src).resolve())

    A = ROOT / 'assets'
    head = ['<!DOCTYPE html>', '<html lang="zh-CN">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>%s</title>' % esc(title),
            '<link rel="stylesheet" href="%s">' % link(A / 'fonts.css'),
            '<link rel="stylesheet" href="%s">' % link(A / 'base.css'),
            '<link rel="stylesheet" href="%s">' % link(A / 'animations' / 'animations.css'),
            '<link rel="stylesheet" href="%s">' % link(A / 'layouts.css'),
            '<link rel="stylesheet" id="theme-link" href="%s">' % link(A / 'themes' / (theme + '.css')),
            '</head>', '<body>', '<div class="deck">', '']

    total_guess = len(pages) + 2
    sec = []
    sec.append('  <section data-style="cover" class="slide is-active" data-title="封面">')
    sec.append('    <p class="kicker">%s</p>' % inline(meta.get('kicker', 'Markdown · 直接成册')))
    sec.append('    <h1 class="h1 mt-s">%s</h1>' % inline(title))
    if lead:
        sec.append('    <p class="lede mt-m">%s</p>' % inline(' '.join(lead)))
    sec.append('    <div class="deck-footer"><span>%s</span><span class="slide-number" data-current="1" data-total="%d"></span></div>' % (esc(meta.get('brand', '来雪亭')), total_guess))
    sec.append('  </section>')

    for idx, pg in enumerate(pages, 1):
        bl = blocks(pg['body'])
        fam = family_of(bl)
        kick = pg.get('parent') or ('第 %02d 页' % idx)
        layout = pg.get('layout')
        has_img = any(b[0] == 'img' for b in bl)
        if layout == 'ride' and has_img:
            inner = render_ride(pg['head'], bl, build_steps, fix_image, kick)
            fam = 'ride'
        elif layout == 'cols3':
            inner = render_cols3(pg['head'], bl, build_steps, kick, pg.get('chips'))
            fam = 'cols3'
        elif layout == 'bleed' and has_img:
            inner = render_bleed(pg['head'], bl, fix_image, kick)
            fam = 'bleed'
        elif layout == 'gantt':
            inner = render_gantt(pg['head'], bl, kick)
            fam = 'gantt'
        elif layout == 'modules':
            inner = render_modules(pg['head'], bl, fix_image, kick, pg.get('chips'))
            fam = 'modules'
        elif layout == 'arc' and has_img:
            inner = render_arc(pg['head'], bl, fix_image, kick, len(sec))
            fam = 'arc'
        elif layout == 'timeline-arc':
            inner = render_timeline(pg['head'], bl, kick)
            fam = 'tline'
        elif fam == 'quote':
            inner = render_quote(pg['head'], bl, kick)
        elif fam == 'image1':
            inner = render_image_single(pg['head'], bl, build_steps, fix_image)
        elif fam == 'text':
            inner = render_text(pg['head'], bl, build_steps, kick)
        elif fam == 'image':
            inner = render_images(pg['head'], bl, build_steps, fix_image)
        elif fam == 'process':
            inner = render_process(pg['head'], bl, build_steps, kick)
        elif fam == 'code':
            inner = render_code(pg['head'], bl, kick if pg.get('parent') else '')
        else:
            inner = render_table(pg['head'], bl)
        style = {'quote': 'quote', 'image1': 'image-single', 'text': 'text', 'process': 'process-steps', 'image': image_style(bl), 'code': 'code', 'table': 'split', 'ride': 'image-band', 'cols3': 'text', 'bleed': 'image-split',
                             'gantt': 'process-gantt', 'modules': 'text',
                             'arc': 'image-split', 'tline': 'process-timeline'}[fam]
        has_band = bool(pg.get('band'))
        sec.append('  <section data-style="%s" class="slide%s" data-title="%s">'
                   % (style, ' has-band' if has_band else '', esc(pg['head'])))
        sec.append(nav_markup(nav, nav_form, pg.get('sec'))) if nav and pg.get('sec') else None
        sec.append(inner)
        if has_band:
            sec.append(claim_band(pg['band']))
        sec.append('  </section>')

    sec.append('  <section data-style="end" class="slide center tc" data-title="收束">')
    sec.append('    <div><h1 class="h1" style="font-size:var(--t-display);line-height:1"><span class="gradient-text">谢谢</span></h1>')
    sec.append('    <p class="lede" style="margin:18px auto 0">%s</p></div>' % inline(meta.get('outro', '讲完这一册，剩下的交给现场。')))
    sec.append('    <div class="deck-footer"><span>%s</span><span class="slide-number" data-current="%d" data-total="%d"></span></div>' % (esc(meta.get('brand', '来雪亭')), total_guess, total_guess))
    sec.append('  </section>')

    foot = ['</div>', '<script src="%s"></script>' % link(A / 'runtime.js'), '</body>', '</html>', '']
    out.write_text('\n'.join(head) + '\n' + '\n'.join(sec) + '\n' + '\n'.join(foot), encoding='utf-8')
    print('✓ %s → %s（%d 页，主题 %s，%s）' % (src.name, out, total_guess, theme,
                                             '逐条揭示开' if build_steps else '逐条揭示关'))
    return 0


def main():
    ap = argparse.ArgumentParser(description='Markdown → 单文件 HTML deck（B 出口）')
    ap.add_argument('src', type=pathlib.Path)
    ap.add_argument('-o', '--out', type=pathlib.Path, required=True)
    ap.add_argument('--theme', default=None, help='主题 slug，见 assets/themes/*.css')
    ap.add_argument('--title', default=None)
    ap.add_argument('--no-build', action='store_true', help='不加 data-build（不做逐条揭示）')
    ap.add_argument('--inline', action='store_true', help='直接出单文件（css/js/图全内联，走 build-deck.py）')
    ap.add_argument('--pptx', type=pathlib.Path, default=None,
                    help='同一份 md 再出一件原生 PPTX（走 export-pptx.py；图/代码页没有对应页型，会跳过并列出）')
    ap.add_argument('--pptx-animate', action='store_true',
                    help='PPTX 逐组淡入（默认跟随 --no-build 的反面）')
    a = ap.parse_args()
    if not a.src.is_file():
        print('✗ 找不到 %s' % a.src, file=sys.stderr)
        return 1

    if a.inline:
        import subprocess, tempfile
        tmp = pathlib.Path(tempfile.mkdtemp()) / 'deck.html'
        rc = build(a.src, tmp, a.theme, a.title, not a.no_build)
        if rc:
            return rc
        rc = subprocess.call([sys.executable, str(ROOT / 'scripts' / 'build-deck.py'),
                              str(tmp), '-o', str(a.out), '--force'])
    else:
        rc = build(a.src, a.out, a.theme, a.title, not a.no_build)
    if rc:
        return rc
    if a.pptx:
        return emit_pptx(a, not a.no_build)
    return 0


if __name__ == '__main__':
    sys.exit(main())
