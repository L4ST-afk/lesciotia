#!/usr/bin/env python3
"""B 出口主题配色体检闸 —— 读 :root 的 hex token，算可核对的四项

判据形态取自 Lovart「配色法则」skill 的 D2(层级) D3(明度骨架) D5(对比度) D6(色相关系)，
落成本地可复算的规则：WCAG 对比度、CIE L* 间距、色相暧昧带、主色-底明度差。
判据理由与取舍见 references/theme-preview.md「配色体检」一节。
不联网、不调外部服务，只读 assets/themes/*.css 里的 :root。

用法：python3 scripts/check-theme-colors.py assets/themes [--md out.md] [--json out.json]
"""
import json, os, re, argparse, sys

def parse_hex(s):
    s = s.strip().lstrip('#')
    if len(s) in (3, 4):
        s = ''.join(c * 2 for c in s[:3])
    if len(s) == 8:
        s = s[:6]
    if len(s) != 6 or not re.fullmatch(r'[0-9a-fA-F]{6}', s):
        return None
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def rel_lum(rgb):
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    y1, y2 = rel_lum(a), rel_lum(b)
    hi, lo = max(y1, y2), min(y1, y2)
    return (hi + 0.05) / (lo + 0.05)

def lstar(rgb):
    y = rel_lum(rgb)
    f = y ** (1 / 3) if y > 0.008856 else 7.787 * y + 16 / 116
    return 116 * f - 16

def hue(rgb):
    r, g, b = (x / 255.0 for x in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return None
    if mx == r:
        return 60 * (((g - b) / d) % 6)
    if mx == g:
        return 60 * ((b - r) / d + 2)
    return 60 * ((r - g) / d + 4)

def hue_delta(h1, h2):
    if h1 is None or h2 is None:
        return None
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)

def chroma(rgb):
    r, g, b = (x / 255.0 for x in rgb)
    return max(r, g, b) - min(r, g, b)

def _srgb_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def oklch_chroma(rgb):
    """sRGB → OKLab 的彩度（a,b 模长）。渐变中段掉不掉饱和，只有这个量看得准；
    max-min 的 .chroma() 对深色会低估（深棕在 RGB 里 chroma 大、肉眼却不艳）。"""
    r, g, b = (_srgb_lin(x / 255.0) for x in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return (a * a + bb * bb) ** 0.5

GRAD_RE = re.compile(r'--grad\s*:\s*linear-gradient\((.+?)\)\s*;', re.S)
GRAD_DROP = 0.25      # 中段彩度相对两端掉 25% 以上 → 肉眼读作灰带
GRAD_DH = 60          # 两端色相差 60° 以上才谈得上「绕色环」

def audit_grad(path):
    """--grad 掉饱和 / 明度回折。判据来自「渐变实验室」（mudong-gradient）那条：
    端点色相远时按 RGB 直连会穿过色环低饱和区，中间一段发灰；解法是绕色相弧，
    色标之间留够中间点，别只给两端。"""
    src = open(path, encoding='utf-8').read()
    m = GRAD_RE.search(src)
    if not m:
        return None
    body = m.group(1)
    if re.search(r'\bin\s+ok(?:lch|lab|hsv|hsl)', body):
        return dict(interp='ok', drops=0, flag=None)
    hexes = re.findall(r'#[0-9a-fA-F]{6}', body)
    if len(hexes) < 2:
        return None
    rgbs = [parse_hex(h) for h in hexes]
    stops = []
    for i in range(len(rgbs) - 1):
        stops += [tuple(round(rgbs[i][k] + (rgbs[i + 1][k] - rgbs[i][k]) * t / 8) for k in range(3))
                  for t in range(8)]
    stops.append(rgbs[-1])
    cs = [oklch_chroma(x) for x in stops]
    ends = min(oklch_chroma(rgbs[0]), oklch_chroma(rgbs[-1]))
    drop = 1 - min(cs) / ends if ends > 0.02 else 0
    dh = hue_delta(hue(rgbs[0]), hue(rgbs[-1]))
    ls = [lstar(x) for x in stops]
    back = max(ls[i] - ls[i + 1] for i in range(len(ls) - 1))
    flag = None
    if dh is not None and dh >= GRAD_DH and drop >= GRAD_DROP:
        flag = ('D', '渐变中段掉饱和：%d 个色标、两端 ΔH %.0f°，路径彩度掉 %.0f%%（%.3f→%.3f）。'
                '按 RGB 直连穿过了色环低饱和区；补 2–3 个中间色标（沿色相弧、保彩度）或改 `in oklch`。' % (
                    len(rgbs), dh, drop * 100, ends, min(cs)))
    elif back > 3:
        flag = ('M', '渐变明度回折：沿路径 L* 反向跳 %.1f 级（应单调）。中间色标的明度按两端线性插值，'
                '别让某一段亮暗倒过来。' % back)
    return dict(interp='srgb', drops=round(drop, 3), cfgs=len(rgbs), dh=None if dh is None else round(dh, 1),
                monoback=round(back, 1), flag=flag)

VAR_RE = re.compile(r'--([a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\b')
ROOT_RE = re.compile(r':root\s*\{(.*?)\}', re.S)
GROUNDS = ('bg', 'surface')
BRAND_RE = re.compile(r'^(primary|accent|accent-\d|line-\d+)$')

# 降级路径：功能色（状态色）场景下 15–40° 不可满足（红橙天生 20–40°），只能换轴。
# 写法（主题 css 任意注释里一行）：
#   /* amb-ok: accent-2/accent-3 | 面积 12% vs 2% + 图标冗余 + 永不同框 */
# 认哪几条轴、要几轴同时成立，就是这条判据可证伪的部分。
WAIVER_RE = re.compile(r'amb-ok\s*[:：]\s*([a-z0-9_-]+)\s*[/／]\s*([a-z0-9_-]+)\s*[|｜=＝]\s*(.+)')
AXIS_WORDS = {'area': ('面积', '占比', '大小'),
              'shape': ('形状', '图标', '纹样', '图形'),
              'position': ('位置', '不同框', '同框', '不同屏', '不相邻')}
AXES_MIN = 2
BASIS_MIN = 20

# BLK 的降级路径（2026-11-23 补）：主色压底 <3:1 时，三律给的第二种解法是加 1px 描边而不是换主色。
# 但闸只读 :root 的 hex，看不见 `box-shadow: inset 0 0 0 1px var(--accent-edge)`，于是永远只能报 W。
# 写法（主题 css 任意注释里一行）：
#   /* blk-ok: primary | 五处实心块（.gg .cell.c7 / .ring .hub / .mm .n.root）均带 1px --accent-edge 描边 */
# 闸据此把 BLK 降为 BLKOK，并把「描边对主色的实际对比度」算出来一并报出——依据不合格仍报 W。
BLKWAIVER_RE = re.compile(r'blk-ok\s*[:：]\s*([a-z0-9_-]+)\s*[|｜=＝]\s*(.+)')
EDGE_WORDS = ('描边', 'edge', '边线', '轮廓')
EDGE_MIN_CONTRAST = 1.2


def waiver_axes(basis):
    return sum(1 for words in AXIS_WORDS.values() if any(w in basis for w in words))


def load_waivers(path):
    """读主题 css 里的 amb-ok 行，返回 {(tokA, tokB) 排序元组: 依据}。"""
    src = open(path, encoding='utf-8').read()
    out = {}
    for a, b, basis in WAIVER_RE.findall(src):
        while '*/' in basis:                 # 注释收尾符不该算进依据
            basis = basis[:basis.rindex('*/')]
        out[tuple(sorted((a.lower(), b.lower())))] = basis.strip()
    return out


def load_blk_waivers(path):
    """读主题 css 里的 blk-ok 行，返回 {token: 依据}（token 已去前导 --）。"""
    src = open(path, encoding='utf-8').read()
    out = {}
    for tok, basis in BLKWAIVER_RE.findall(src):
        while '*/' in basis:
            basis = basis[:basis.rindex('*/')]
        out[tok.lower()] = basis.strip()
    return out


def edge_contrast(accent, text1, alpha=0.30):
    """--accent-edge = color-mix(in srgb, text-1 30%, transparent) 压在 accent 上的合成色。

    按 sRGB 通道做 0.3/0.7 混合，回主色与页面底的对比度——1px 线不该要求 3:1，
    只要求「看得见」：≥1.2 视为立住边界。缺 text-1 时返回 None（无法证明）。
    """
    if not text1:
        return None
    edge = tuple(int(round(alpha * t + (1 - alpha) * a)) for t, a in zip(text1, accent))
    return round(contrast(edge, accent), 2)


def load_theme(path):
    src = open(path, encoding='utf-8').read()
    m = ROOT_RE.search(src)
    body = m.group(1) if m else src
    out = {}
    for name, hexv in VAR_RE.findall(body):
        rgb = parse_hex(hexv)
        if rgb and name not in out:
            out[name] = (hexv, rgb)
    return out

def audit(path):
    v = load_theme(path)
    grounds = [(n, v[n][0], v[n][1]) for n in GROUNDS if n in v]
    seen = set()
    brand = []
    for n in v:
        if BRAND_RE.match(n) and v[n][0].lower() not in seen:
            seen.add(v[n][0].lower())
            brand.append((n, v[n][0], v[n][1]))
    issues = []

    # 文字三档 vs 页面底/卡片底
    for tok, sev, label in (('text-1', 'F', '正文'), ('text-2', 'W', '辅助字'), ('text-3', 'I', '次级标注')):
        if tok not in v or not grounds:
            continue
        worst = min(((contrast(v[tok][1], g[2]), g[0], g[1]) for g in grounds), key=lambda x: x[0])
        if worst[0] < 4.5:
            issues.append(dict(code='T', sev=sev, token=tok, value=v[tok][0],
                               ratio=round(worst[0], 2), ground=worst[1], ground_hex=worst[2],
                               msg='--%s %s 压 --%s %s 只有 %.2f:1（%s 需 4.5）' % (
                                   tok, v[tok][0], worst[1], worst[2], worst[0], label)))

    # accent-ink 压在主色填充上（主按钮上的字）
    if 'accent-ink' in v:
        ink = v['accent-ink']
        main = v.get('primary') or v.get('accent')
        if main:
            r = contrast(ink[1], main[1])
            if r < 4.5:
                issues.append(dict(code='INK', sev='F' if r < 3 else 'W', ratio=round(r, 2),
                                   msg='--accent-ink %s 压主色 %s 只有 %.2f:1（主按钮/主色块上的字需要 4.5）' % (
                                       ink[0], main[0], r)))
                issues[-1]['main'] = True
            else:
                issues.append(dict(code='INK', sev='OK', ratio=round(r, 2),
                                   msg='--accent-ink %s 压主色 %s = %.2f:1' % (ink[0], main[0], r)))
        weak = []
        for n in ('accent-2', 'accent-3'):
            if n in v and contrast(ink[1], v[n][1]) < 4.5:
                weak.append('--%s %s(%.2f:1)' % (n, v[n][0], contrast(ink[1], v[n][1])))
        if weak:
            issues.append(dict(code='INK2', sev='I',
                               msg='次色填充上沿用 accent-ink 不达标，建议这几块换白字：%s' % '、'.join(weak)))

    # 填充底上的字（2026-11-20 补）：任何品牌色 token 都可能被拿去当实心填充
    # （主按钮、标签胶囊、进度条、选中态）。闸门原先只查 accent-ink 压主色，
    # 漏掉了「次色做底 + 纸白字」这类——万航渡（当时名吉祥寺）的 .pill-accent 用 --sky-lo 天青
    # 做底配纸白字，只有 2.99:1，体检却报 clean。这里按「纸白字」口径补一遍：
    # 凡是品牌色 token，若它比主色更暗（会被当实心块用），其上的纸白字须 ≥4.5。
    # ⛔ 不判「浅色做底配墨字」——那是合法用法，字色会跟着换。
    paper_ink = v.get('accent-ink') or v.get('bg')
    if paper_ink:
        weak_fill = []
        for n, hexv, rgb in brand:
            if n.lower() in ('accent-ink', 'bg', 'bg-soft', 'surface', 'surface-2'):
                continue
            # 只查「深色填充 + 浅字」这一种组合：填充色明显暗于字色
            if rel_lum(rgb) >= rel_lum(paper_ink[1]):
                continue
            r = contrast(paper_ink[1], rgb)
            if r < 4.5:
                weak_fill.append((n, hexv, round(r, 2)))
        if weak_fill:
            # ⚠️ 这是「线索」不是「结论」：静态查 token 不知道这块色到底有没有字。
            # 实测口径见 references/palette-check.md「填充底上的字」——用浏览器量
            # 每个带文字元素的实际对比度才算证据。这里只提示可能踩坑的 token。
            issues.append(dict(code='FILL', sev='I',
                               items=weak_fill,
                               msg='线索：这些品牌色若拿去做实心填充，纸白字不达标（需 4.5）：%s。'
                                   '若该色只做面/条/描边（无文字）可忽略；'
                                   '若承载文字，要么压深该色，要么改用墨字' %
                                   '、'.join('--%s %s(%.2f:1)' % (n, h, r) for n, h, r in weak_fill)))

    # 主色压底：色块边界/大色块能否被看见
    brand_main = v.get('primary') or v.get('accent')
    if brand_main and grounds:
        worst = min(((contrast(brand_main[1], g[2]), g[0], g[1]) for g in grounds), key=lambda x: x[0])
        if worst[0] < 3.0:
            main_tok = 'primary' if v.get('primary') else 'accent'
            blk_basis = load_blk_waivers(path).get(main_tok)
            edge = edge_contrast(brand_main[1], v['text-1'][1] if 'text-1' in v else None)
            if blk_basis and len(blk_basis) >= BASIS_MIN and any(w in blk_basis.lower() for w in EDGE_WORDS):
                if edge is not None and edge >= EDGE_MIN_CONTRAST:
                    issues.append(dict(code='BLKOK', sev='OK', ratio=round(worst[0], 2), edge=edge,
                                       msg='主色 %s 压 --%s %s 仅 %.2f:1，已用 1px 描边立边界'
                                           '（合成后对主色 %.2f:1，依据「%s」）' % (
                                               brand_main[0], worst[1], worst[2], worst[0], edge, blk_basis)))
                else:
                    issues.append(dict(code='BLKJ', sev='W', ratio=round(worst[0], 2), edge=edge,
                                       msg='主色 %s 压 --%s 仅 %.2f:1，描边豁免依据在、但描边本身不够'
                                           '（对主色 %s:1 < %.1f:1）——加粗到 2px 或把 --accent-edge 的 alpha 提到 45%%' % (
                                               brand_main[0], worst[2], worst[0], edge, EDGE_MIN_CONTRAST)))
            elif blk_basis:
                issues.append(dict(code='BLKJ', sev='W', ratio=round(worst[0], 2),
                                   msg='主色 %s 压 --%s 仅 %.2f:1，登记了 blk-ok 但依据不合格'
                                       '（须 ≥%d 字并写明描边/edge）：「%s」' % (
                                           brand_main[0], worst[2], worst[0], BASIS_MIN, blk_basis)))
            else:
                issues.append(dict(code='BLK', sev='W', ratio=round(worst[0], 2),
                                   msg='主色 %s 压 --%s %s 仅 %.2f:1（色块/描边需 3:1）' % (
                                       brand_main[0], worst[1], worst[2], worst[0])))

    # 品牌色两两：暧昧带 / 灰阶分不开
    ambig, close = [], []
    for i in range(len(brand)):
        for j in range(i + 1, len(brand)):
            a, b = brand[i], brand[j]
            dl = abs(lstar(a[2]) - lstar(b[2]))
            dh = hue_delta(hue(a[2]), hue(b[2]))
            if dh is not None and 15 <= dh <= 40 and dl < 15:
                ambig.append((a[0], a[1], b[0], b[1], round(dh, 1), round(dl, 1)))
            if dl < 10 and chroma(a[2]) > 0.08 and chroma(b[2]) > 0.08:
                close.append((a[0], a[1], b[0], b[1], round(dl, 1)))
    kept, waived, used = [], [], set()
    if ambig:
        waivers = load_waivers(path)
        for it in ambig:
            key = tuple(sorted((it[0].lower(), it[2].lower())))
            basis = waivers.get(key)
            if basis is None:
                kept.append(it)
                continue
            used.add(key)
            if len(basis) < BASIS_MIN or waiver_axes(basis) < AXES_MIN:
                issues.append(dict(code='AMBJ', sev='W', items=[it], basis=basis,
                                   msg='暧昧带登记了豁免但依据不合格（须 ≥%d 字、且至少 %d 轴：'
                                       '面积／形状／位置）：`--%s` ↔ `--%s` 依据「%s」' % (
                                           BASIS_MIN, AXES_MIN, it[0], it[2], basis)))
            else:
                waived.append((it, basis))
        if kept:
            issues.append(dict(code='AMB', sev='W', items=kept,
                               msg='暧昧带（ΔH 15–40° 且 ΔL*<15）：%d 对' % len(kept)))
        for it, basis in waived:
            issues.append(dict(code='AMBOK', sev='OK', items=[it], basis=basis,
                               msg='暧昧带换轴放行：`--%s` ↔ `--%s` ΔH %s°，依据「%s」' % (
                                   it[0], it[2], it[4], basis)))
        for key in waivers:
            if key not in used:
                issues.append(dict(code='WAM', sev='I',
                                   msg='失效豁免（这对已不在暧昧带或 token 已改名）：`--%s` ↔ `--%s`'
                                       % key))
    if close:
        issues.append(dict(code='LST', sev='W', items=close,
                           msg='灰阶分不开（ΔL*<10）：%d 对' % len(close)))

    # 主色与底同明度
    if brand_main and grounds:
        worst = min(((abs(lstar(brand_main[1]) - lstar(g[2])), g[0], g[1]) for g in grounds), key=lambda x: x[0])
        if worst[0] < 12:
            issues.append(dict(code='DL', sev='W', ratio=round(worst[0], 1),
                               msg='主色 %s(L*%.1f) 与 --%s %s(L*%.1f) 只差 ΔL*%.1f' % (
                                   brand_main[0], lstar(brand_main[1]), worst[1], worst[2],
                                   lstar(parse_hex(worst[2])), worst[0])))

    if len(brand) > 4:
        issues.append(dict(code='CNT', sev='I',
                           msg='品牌/编码色 %d 个：--%s' % (len(brand), ', --'.join(b[0] for b in brand))))

    # --grad 掉饱和 / 明度回折（2026-11-23）
    g = audit_grad(path)
    grad = None
    if g:
        grad = g
        if g.get('flag'):
            code, msg = g['flag']
            issues.append(dict(code=code, sev='W' if code == 'D' else 'I', msg=msg))
        else:
            issues.append(dict(code='GRADOK', sev='OK',
                               msg='--grad 过渡正常：%d 个色标、彩度最低掉 %.0f%%%s' % (
                                   g.get('cfgs', 0), (g.get('drops') or 0) * 100,
                                   '、按 oklch 插值' if g.get('interp') == 'ok' else '')))

    t1 = None
    if 'text-1' in v and grounds:
        t1 = round(min(contrast(v['text-1'][1], g[2]) for g in grounds), 2)

    return dict(file=os.path.basename(path), tokens=len(v), brand=len(brand), t1=t1, issues=issues, grad=grad,
                fail=sum(1 for i in issues if i['sev'] == 'F'),
                warn=sum(1 for i in issues if i['sev'] == 'W'),
                amb=len(kept),
                amb_waived=len(waived),
                amb_stale=sum(1 for i in issues if i['code'] == 'WAM'))

CODE_TITLE = {
    'T': '文字对比度不足 4.5:1',
    'INK': '主色上的字对比度不足',
    'BLK': '主色色块对底不足 3:1',
    'BLKOK': '主色压底<3:1，已用 1px 描边立边界',
    'BLKJ': '描边豁免依据不合格',
    'AMB': '色相暧昧带（ΔH 15–40° 且 ΔL*<15）',
    'AMBJ': '暧昧带豁免依据不合格',
    'WAM': '失效豁免',
    'LST': '灰阶分不开（ΔL*<10）',
    'DL': '主色与底同明度（ΔL*<12）',
    'CNT': '品牌/编码色超过 4 个',
}

def render_md(rows, agg):
    o = ['# 来雪亭 · B 出口主题配色体检（%d 个主题）\n' % agg['themes'],
         '判据来自 Lovart「配色法则」skill 的 D2/D3/D5/D6，改成四条能离线复算的规则：'
         'WCAG 对比度、CIE L* 间距、色相暧昧带、主色与底的明度差。只读 `:root` 里的 hex token，不依赖任何外部服务。\n',
         '严重度：❌ 正文对比度不达标（无障碍硬伤）｜⚠️ 层级或可辨性问题｜ℹ️ 提示\n',
         '## 总览\n', '| 项 | 数 |', '|---|---|',
         '| 主题总数 | %d |' % agg['themes'],
         '| 正文对比度硬伤（❌） | %d |' % agg['with_fail'],
         '| 有 ⚠️ 级问题 | %d |' % agg['with_warn'],
         '| 全清 | %d |' % agg['clean'],
         '| 换轴放行（暧昧对，已登记依据） | %d 对 |' % agg.get('amb_waived', 0),
         '| 描边放行（BLK → BLKOK） | %d 个主题 |' % agg.get('blkok', 0),
         '| 失效豁免 | %d 条 |' % agg.get('amb_stale', 0)]
    for k in sorted(agg['by_code']):
        o.append('| %s %s | %d 个主题 |' % (k, CODE_TITLE.get(k, ''), agg['by_code'][k]))
    # 三个最该动的地方：0 个时不写修法，只报实情
    by = lambda code: [r['file'][:-4] for r in rows if any(i['code'] == code and i['sev'] in ('F', 'W') for i in r['issues'])]
    blk, lst, amb = by('BLK'), by('LST'), by('AMB')
    o += ['\n## 三个最该动的地方\n',
          '- **主色压底不足 3:1（%d 个）**：%s%s' % (
              len(blk), '、'.join(blk) or '无',
              '。这些主题的主色全靠 `--accent-ink` 写字才立得住，一旦色块与底直接相邻（标签、色带、圆点）就糊在底上。' if blk else '。这四个主题的主色色块都能与底分立。'),
          '- **灰阶撞车（%d 个）**：%s%s' % (
              len(lst), '、'.join(lst) or '无',
              '。转灰、黑白打印、色弱场景下这些色对会合并成一个色阶。' if lst else '。无色对 ΔL* 挤在 10 以内。'),
          '- **暧昧带（%d 个）**：%s%s' % (
              len(amb), '、'.join(amb) or '无',
              '。ΔH 落在 15–40°，既不像同族也不像对比，看起来像“配色没调完”。' if amb else '。没有色对卡在 15–40° 这个既不同族也不对比的地段。')]
    o += ['\n## 逐主题\n',
          '| 主题 | 正文最小对比 | 主色上文字 | 主色对底 | 主色↔底 ΔL* | 暧昧带 | 灰阶撞车 | 判定 |',
          '|---|---|---|---|---|---|---|---|']
    for r in rows:
        d = {i['code']: i for i in r['issues']}
        v = '❌' if r['fail'] else ('⚠️' if r['warn'] else '✅')
        o.append('| %s | %s | %s | %s | %s | %s | %d | %s |' % (
            r['file'][:-4],
            ('%.2f' % r['t1']) if r['t1'] else '—',
            d['INK']['ratio'] if 'INK' in d else '—',
            (d['BLKOK']['ratio'] if 'BLKOK' in d else d['BLK']['ratio']) if ('BLK' in d or 'BLKOK' in d) else '3+',
            d['DL']['ratio'] if 'DL' in d else '12+',
            (str(len(d['AMB']['items'])) + ('(%d换轴)' % len(d['AMBOK']['items']) if 'AMBOK' in d else '')) if 'AMB' in d else ('0(%d换轴)' % len(d['AMBOK']['items']) if 'AMBOK' in d else '0'),
            len(d['LST']['items']) if 'LST' in d else 0, v))
    o.append('\n## 明细\n')
    for r in rows:
        real = [i for i in r['issues'] if i['sev'] in ('F', 'W')]
        if not real:
            continue
        o.append('### %s\n' % r['file'][:-4])
        for i in real:
            mark = '❌' if i['sev'] == 'F' else '⚠️'
            o.append('- %s %s' % (mark, i['msg']))
            for it in i.get('items', []):
                if i['code'] in ('AMB', 'AMBJ'):
                    o.append('    - `--%s` %s ↔ `--%s` %s：ΔH %s°、ΔL* %s' % it)
                else:
                    o.append('    - `--%s` %s ↔ `--%s` %s：ΔL* %s' % it)
        o.append('')
    okrows = [(r['file'][:-4], i) for r in rows for i in r['issues'] if i['code'] in ('AMBOK', 'BLKOK')]
    if okrows:
        o.append('\n## 放行（已登记依据：暧昧换轴 / 描边立边界）\n')
        for slug, i in okrows:
            o.append('- **%s**：%s' % (slug, i['msg']))
        o.append('')
    stale = [(r['file'][:-4], i['msg']) for r in rows for i in r['issues'] if i['code'] == 'WAM']
    if stale:
        o.append('\n## 失效豁免（该删）\n')
        for slug, msg in stale:
            o.append('- **%s**：%s' % (slug, msg))
        o.append('')
    o += ['\n## 怎么修\n',
          '- **INK（主色上的字）**：主色是浅色时 `--accent-ink` 必须是深墨（`#222` 级），主色是深色时必须是白；'
          '一档 token 服务不了两类主色，就按 `--accent-ink` 与 `--accent-ink-invert` 拆两档。',
          '- **BLK（主色色块对底 <3:1）**：不要靠提高饱和度救，改「加一圈 1px 描边 / 加 8% 的深色投影」，'
          '色块边界就地被看见，且不动主色本身。描边做成了，就在主题 css 注释里登记一行：'
          '`/* blk-ok: primary | 五处实心块均带 1px --accent-edge 描边 */`，闸会把 BLK 降为 BLKOK，'
          '并把合成后「描边对主色」的对比度一并算出来（≥1.2 才算立住；依据不够或描边太弱报 BLKJ）。',
          '- **DL（主色与底同明度）**：只在主色大面积铺底的版面上是问题；若主色只做小面积标记，可降级忽略，'
          '但要在主题头部注释里写明「本主题主色不作大面积底色」。',
          '- **AMB（暧昧带）**：两色 ΔH 15–40° 时，人眼既不判为「同一色族」也不判为「对比色」，'
          '修法是把其中一个推到 ΔH ≥60°（变成明确对比）或 ≤10°（变成同族深浅），比调明度有效。',
          '- **功能色换轴放行（AMBOK／AMBJ／WAM）**：状态色（信息/警示/成功）语义是抢来的，'
          '警示红橙与暖主色天生只差 20–40°，这一带**靠色相解决不了**。改在主题 css 注释里登记一行：'
          '`/* amb-ok: accent-2/accent-3 | 面积 12% vs 2% + 图标冗余 + 永不同框 */`。'
          '依据须 ≥20 字且盖住面积／形状／位置三轴中至少两轴（单轴不算，单轴救不了这条带）；'
          '登记后这对降级为放行并在表里标「换轴」，⛔ 不静默消失；登记了却没对上任何暧昧对 ⇒ 报失效豁免，删掉它。',
          '- **LST（灰阶撞车）**：两色转灰后 ΔL* <10，纹样/色弱/黑白打印时层级塌陷。'
          '给其中之一加一条独立的编码冗余（形状、位置、图标），不要只靠颜色。',
          '- **T（正文对比度）**：低于 4.5:1 即为无障碍硬伤，必须压深 `--text-1`。']
    return '\n'.join(o)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir'); ap.add_argument('--json'); ap.add_argument('--md')
    ap.add_argument('--only', help='只查这几个主题（逗号分隔 slug，如 guanglan-rd,century-sq）')
    a = ap.parse_args()
    files = sorted(f for f in os.listdir(a.dir) if f.endswith('.css') and '.bak' not in f and 'bak-' not in f)
    if a.only:
        want = {s.strip() for s in a.only.split(',') if s.strip()}
        files = [f for f in files if f[:-4] in want]
    rows = [audit(os.path.join(a.dir, f)) for f in files]
    rows.sort(key=lambda r: (-r['fail'], -r['warn'], r['file']))
    agg = dict(themes=len(rows),
               with_fail=sum(1 for r in rows if r['fail']),
               with_warn=sum(1 for r in rows if r['warn']),
               clean=sum(1 for r in rows if not r['fail'] and not r['warn']), by_code={},
               amb_waived=sum(r['amb_waived'] for r in rows),
               blkok=sum(1 for r in rows for i in r['issues'] if i['code'] == 'BLKOK'),
               amb_stale=sum(r['amb_stale'] for r in rows))
    for r in rows:
        for i in r['issues']:
            if i['sev'] in ('F', 'W'):
                agg['by_code'][i['code']] = agg['by_code'].get(i['code'], 0) + 1
    if a.json:
        json.dump(dict(summary=agg, rows=rows), open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(agg, ensure_ascii=False, indent=1))
    if a.md:
        open(a.md, 'w', encoding='utf-8').write(render_md(rows, agg))
    # 2026-11-23 评审#04：原先只打印不退出，对比度硬伤也 exit 0
    return 1 if agg["with_fail"] else 0

if __name__ == '__main__':
    sys.exit(main())
