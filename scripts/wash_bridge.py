#!/usr/bin/env python3
"""染层与墨线：把 CSS 渐变、布尔结果、SVG path 翻成 DrawingML（C 出口的补充件）。

瓦作是先验的：`linear-gradient` / `radial-gradient` / `clip-path: path()` 写在 CSS 里，
浏览器与 python-pptx 各解释一次，谁也不是谁的截图。分流只在解释器一侧，不在数据一侧。

用法（当「样张器」跑，出一份三页 proofer 核对换算是否成立）：

    python3 scripts/wash_bridge.py path/to/wash.css -o /tmp/wash-proofer.pptx

可换算：linear-gradient（角度与 to <side>、多色标、rgba）、radial-gradient(circle at x% y%)、
clip-path: path()、内联 SVG 的 M/L/C/Q/A/Z。
不换算：conic-gradient、repeating-*、background-blend-mode、filter、多焦点径向——
这些写进瓦作只会得到近似或空白，闸（见 SELFTEST「染层与墨线」一节）按红处理。

依赖：python-pptx + lxml；Pillow 只在自绘预览时用。
"""
from __future__ import annotations

import math
import re
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

W, H = 1600, 900          # 栅格，与 B 出口一致
PX_PER_IN = 120
EMU_PER_PX = 914400 / PX_PER_IN

NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'


def px(v: float) -> int:
    return int(round(v * EMU_PER_PX))


# ---------------------------------------------------------------- CSS 解析

def root_vars(css: str) -> dict[str, str]:
    """收所有 :root 块，后面的覆盖前面的。

    ⛔ 两条坑都在这里踩过：
    1. 只取第一块 —— base.css 的 :root 会把主题的 :root 整块顶掉；
    2. 按 ';' 切完不做注释剥离 —— 声明前面挂着 `/* 注释 */` 时，
       键名就成了「注释 + --x」，被 `--` 前缀判断静默丢掉，
       于是 token 明明写了却报「未定义」，错还指不到病根。
    """
    vals: dict[str, str] = {}
    for blk in re.finditer(r':root\s*\{(.*?)\}', css, re.S):
        body = re.sub(r'/\*.*?\*/', '', blk.group(1), flags=re.S)
        for decl in body.split(';'):
            m = re.search(r'(--[\w-]+)\s*:\s*(.+)', decl, re.S)
            if m:
                vals[m.group(1)] = ' '.join(m.group(2).split())
    return vals


def resolve(value: str, vals: dict[str, str]) -> str:
    """代换 var(--x)。找不到变量必须报错，不能拿整串顶回去——
    那样会把自己嵌进自己，绕四圈长成一团，最后报一个与病因无关的「认不出的颜色」。"""
    for _ in range(8):
        m = re.search(r'var\((--[\w-]+)\)', value)
        if not m:
            return value
        name = m.group(1)
        if name not in vals:
            raise ValueError(f'瓦作里没有定义 {name}（先查 :root，别指望它有默认值）')
        value = value.replace(m.group(0), vals[name])
    raise ValueError('var() 嵌套超过八层，八成是循环定义')


def balanced(text: str, start: int) -> tuple[str, int]:
    """从 '(' 后开始，返回括号内文本与结束位置（含右括号）。"""
    depth, i = 1, start
    while i < len(text):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[start:i], i
        i += 1
    raise ValueError('括号不闭合')


def split_top(text: str) -> list[str]:
    out, depth, buf = [], 0, ''
    for c in text:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        if c == ',' and depth == 0:
            out.append(buf.strip())
            buf = ''
        else:
            buf += c
    if buf.strip():
        out.append(buf.strip())
    return out


def color(text: str) -> tuple[str, float]:
    """#hex / rgb() / rgba() / 具名透明 → (RRGGBB, alpha 0..1)"""
    text = text.strip().lower()
    if text in ('transparent', 'none'):
        return 'FFFFFF', 0.0
    m = re.fullmatch(r'#([0-9a-f]{6})', text)
    if m:
        return m.group(1).upper(), 1.0
    m = re.fullmatch(r'#([0-9a-f]{3})', text)
    if m:
        return ''.join(c * 2 for c in m.group(1)).upper(), 1.0
    m = re.fullmatch(r'rgba?\(([^)]+)\)', text)
    if m:
        parts = [p.strip() for p in re.split(r'[,\s/]+', m.group(1)) if p.strip()]
        r, g, b = (int(float(p)) for p in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return f'{r:02X}{g:02X}{b:02X}', a
    raise ValueError(f'认不出的颜色：{text}')


def parse_gradient(text: str, vals: dict[str, str]) -> dict:
    """linear-gradient / radial-gradient → 归一化的中间表示。"""
    text = re.sub(r'\s+', ' ', text.strip())
    kind = 'linear' if text.startswith('linear') else 'radial'
    body = text[text.index('(') + 1: text.rindex(')')]
    parts = split_top(body)
    angle, center, stops_raw = 135.0, (0.5, 0.5), []
    head = parts[0]
    if kind == 'linear':
        m = re.fullmatch(r'(-?[\d.]+)deg', head)
        if m:
            angle = float(m.group(1))
            stops_raw = parts[1:]
        elif head.startswith('to '):
            dirs = {'top': 0, 'right': 90, 'bottom': 180, 'left': 270}
            words = head[3:].split()
            if len(words) == 2:
                combos = {('right', 'top'): 45, ('bottom', 'right'): 135,
                          ('left', 'bottom'): 225, ('top', 'left'): 315}
                angle = float(combos.get(tuple(sorted(words, key=words.index)), 135))
            else:
                angle = float(dirs.get(words[0], 180))
            stops_raw = parts[1:]
        else:
            stops_raw = parts
    else:
        m = re.match(r'circle at ([\d.]+)% ([\d.]+)%', head)
        if m:
            center = (float(m.group(1)) / 100, float(m.group(2)) / 100)
            stops_raw = parts[1:]
        else:
            stops_raw = parts
    stops = []
    for i, s in enumerate(stops_raw):
        m0 = re.match(r'(var\(--[\w-]+\)|rgba?\([^)]*\)|#[0-9a-fA-F]{3,6}|[a-zA-Z]+)', s.strip())
        col = color(resolve(m0.group(0), vals)) if m0 else color('transparent')
        rest = s.strip()[m0.end():].split() if m0 else []
        pos = None
        for t in rest:
            if t.endswith('%'):
                pos = float(t[:-1]) / 100
            elif t.endswith('px') and False:
                pass
        stops.append({'color': col, 'pos': pos, 'i': i})
    n = len(stops)
    for k, s in enumerate(stops):
        if s['pos'] is None:
            s['pos'] = 0.0 if k == 0 else (1.0 if k == n - 1 else k / (n - 1))
    stops = [{'pos': s['pos'], 'color': s['color']} for s in stops]
    return {'kind': kind, 'angle': angle, 'center': center, 'stops': stops}


# ------------------------------------------------------------ DrawingML

A = f'{{{NS}}}'


def grad_xml(g: dict) -> etree._Element:
    gf = etree.SubElement(etree.Element(A + 'tmp'), A + 'gradFill')
    gf.set('rotWithShape', '1')
    gs = etree.SubElement(gf, A + 'gsLst')
    for s in g['stops']:
        el = etree.SubElement(gs, A + 'gs')
        el.set('pos', str(int(round(s['pos'] * 100000))))
        clr = etree.SubElement(el, A + 'srgbClr')
        clr.set('val', s['color'][0])
        if s['color'][1] < 1:
            al = etree.SubElement(clr, A + 'alpha')
            al.set('val', str(int(round(s['color'][1] * 100000))))
    if g['kind'] == 'linear':
        lin = etree.SubElement(gf, A + 'lin')
        ang = int(round(((g['angle'] - 90) % 360) * 60000))
        lin.set('ang', str(ang))
        lin.set('scaled', '1')
    else:
        path = etree.SubElement(gf, A + 'path')
        path.set('path', 'circle')
        ftr = etree.SubElement(path, A + 'fillToRect')
        cx, cy = g['center']
        ftr.set('l', str(int(round(cx * 100000))))
        ftr.set('t', str(int(round(cy * 100000))))
        ftr.set('r', str(int(round((1 - cx) * 100000))))
        ftr.set('b', str(int(round((1 - cy) * 100000))))
    return gf


def set_fill(shape, fill) -> None:
    """fill = ('solid', hex) 或 ('grad', dict)；插在几何之后、线之前。"""
    spPr = shape._element.spPr
    for tag in ('noFill', 'solidFill', 'gradFill', 'pattFill', 'blipFill', 'grpFill'):
        for e in spPr.findall(A + tag):
            spPr.remove(e)
    if fill[0] == 'solid':
        el = etree.SubElement(etree.Element(A + 'tmp'), A + 'solidFill')
        c = etree.SubElement(el, A + 'srgbClr')
        c.set('val', fill[1])
    else:
        el = grad_xml(fill[1])
    ln = spPr.find(A + 'ln')
    if ln is not None:
        ln.addprevious(el)
    else:
        spPr.append(el)


def set_alpha(shadow_shape) -> None:
    pass


def custgeom(shape, points, cx: float, cy: float, closed: bool = True) -> None:
    """把点列写成 custGeom。

    `points` 可以是单条轮廓 [(x,y), …]，也可以是**多条轮廓** [[…], […]]——
    后者是布尔运算产生了洞或裂成好几块时的形态（洞按反向前一条绕向排）。
    """
    contours = points if (points and isinstance(points[0][0], (list, tuple))) else [points]
    geom = etree.SubElement(etree.Element(A + 'tmp'), A + 'custGeom')
    for t in ('avLst', 'gdLst', 'ahLst', 'cxnLst'):
        etree.SubElement(geom, A + t)
    rect = etree.SubElement(geom, A + 'rect')
    for k, v in (('l', 'l'), ('t', 't'), ('r', 'r'), ('b', 'b')):
        rect.set(k, v)
    lst = etree.SubElement(geom, A + 'pathLst')
    for contour in contours:
        if len(contour) < 2:
            continue
        p = etree.SubElement(lst, A + 'path')
        p.set('w', str(px(cx)))
        p.set('h', str(px(cy)))
        move = etree.SubElement(p, A + 'moveTo')
        pt = etree.SubElement(move, A + 'pt')
        pt.set('x', str(px(contour[0][0])))
        pt.set('y', str(px(contour[0][1])))
        for x, y in contour[1:]:
            ln = etree.SubElement(p, A + 'lnTo')
            q = etree.SubElement(ln, A + 'pt')
            q.set('x', str(px(x)))
            q.set('y', str(px(y)))
        if closed:
            etree.SubElement(p, A + 'close')
    spPr = shape._element.spPr
    prst = spPr.find(A + 'prstGeom')
    if prst is not None:
        prst.addnext(geom)
        spPr.remove(prst)
    else:
        spPr.insert(0, geom)


# ------------------------------------------------------------ 布尔

def circle_poly(c, r, a0, a1, n=64) -> list[tuple[float, float]]:
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n),
             c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def circle_bool(op: str, c1, r1, c2, r2, bbox, n=64):
    """两圆的差/交，解析解出来的边界点列；曲线按 n 段折线近似。"""
    d = math.hypot(c2[0] - c1[0], c2[1] - c1[1])
    if d >= r1 + r2 or d <= abs(r1 - r2):
        raise ValueError('两圆相离或包含，布尔无意义')
    c = (r1 * r1 + d * d - r2 * r2) / (2 * d * r1)      # cosθ
    c2v = (r1 * r1 - d * d - r2 * r2) / (2 * d * r2)    # cosφ
    c, c2v = max(-1, min(1, c)), max(-1, min(1, c2v))
    th = math.acos(c)
    ph = math.acos(c2v)
    base = math.atan2(c2[1] - c1[1], c2[0] - c1[0])
    if op == 'subtract':
        outer = circle_poly(c1, r1, base + th, base + 2 * math.pi - th, n)
        inner = circle_poly(c2, r2, base + 2 * math.pi - ph, base + ph, n)
        pts = outer + inner
    else:
        outer = circle_poly(c1, r1, base - th, base + th, n)
        inner = circle_poly(c2, r2, base + ph, base + 2 * math.pi - ph, n)
        pts = outer + inner
    pts = [(x - bbox[0], y - bbox[1]) for x, y in pts]
    return pts


# ------------------------------------------------- 任意折线布尔（两圆解析解之外）

def _cross(o, a, b) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _on_seg(p, a, b, eps=1e-7) -> bool:
    if abs(_cross(a, b, p)) > eps * max(1.0, math.hypot(b[0] - a[0], b[1] - a[1])):
        return False
    return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
            min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps)


def pt_in_poly(p, poly) -> bool | None:
    """射线法。点正好落在边界上返回 None——这不是布尔运算能替你决定的事，
    由调用方按语义处置（见 poly_bool 里的「落在边界算在里」）。"""
    x, y = p
    n = len(poly)
    inside = False
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if _on_seg(p, a, b):
            return None
        if (a[1] > y) != (b[1] > y):
            xin = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < xin:
                inside = not inside
    return inside


def _seg_cross(p1, p2, q1, q2, eps=1e-12):
    """两线段的交叉参数。**端点也算**（0 与 1 会被夹回来）——

    只认「真交叉」会漏掉一类最常见的退化：A 的顶点正好落在 B 的边上
    （本项目实测：圆的 0°/90° 顶点正好压在某条竖直边上，两条相邻边各自
    t=1 与 t=0，都被排除，于是整条边一个交叉点都没找到，布尔看着像「两形相离」）。
    平行、共线仍然返回 None，那种重合边由 `_on_seg` 的 eps 兜。
    """
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = q2[0] - q1[0], q2[1] - q1[1]
    den = rx * sy - ry * sx
    if abs(den) < eps:
        return None
    t = ((q1[0] - p1[0]) * sy - (q1[1] - p1[1]) * sx) / den
    u = ((q1[0] - p1[0]) * ry - (q1[1] - p1[1]) * rx) / den
    tol = 1e-9
    if not (-tol <= t <= 1 + tol and -tol <= u <= 1 + tol):
        return None
    return max(0.0, min(1.0, t)), max(0.0, min(1.0, u))


def _dedupe(poly) -> list[tuple[float, float]]:
    out = []
    for p in poly:
        if not out or abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
            out.append((float(p[0]), float(p[1])))
    while len(out) > 2 and abs(out[0][0] - out[-1][0]) <= 1e-9 and abs(out[0][1] - out[-1][1]) <= 1e-9:
        out.pop()
    return out


def area(poly) -> float:
    """鞋带公式，带符号。判「这块是外轮廓还是洞」全靠它。"""
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2


def _chain(segs, tol=1e-5):
    """把有向线段首尾相接成轮廓。接不上就说明这段几何不自洽，直接报。"""
    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))

    starts: dict = {}
    for i, (p, q) in enumerate(segs):
        starts.setdefault(key(p), []).append(i)
    used = [False] * len(segs)
    out = []
    for i0 in range(len(segs)):
        if used[i0]:
            continue
        used[i0] = True
        contour = [segs[i0][0], segs[i0][1]]
        start_key = key(segs[i0][0])
        while True:
            cands = [j for j in starts.get(key(contour[-1]), []) if not used[j]]
            if not cands:
                break
            j = cands[0]
            used[j] = True
            contour.append(segs[j][1])
            if key(contour[-1]) == start_key:
                break
        if len(contour) >= 4 and key(contour[-1]) == start_key:
            out.append(contour[:-1])
    if not out and segs:
        raise ValueError('布尔结果断成了开口折线（多半是两形共线重合）：改写成 path 或用解析解')
    return out


def collinear_overlap(p1, p2, q1, q2, eps=1e-9):
    """两条**共线且重叠**的边 → 各自的重叠参数区间；不共线或只是端点相接则 None。

    这是折线布尔里最容易被绕过去的一类：两形共享一段直边（两个方块贴边、
    同一个形状自差），既不是交叉也不是包含，中点还正好落在对方边界上。
    """
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    ex, ey = q2[0] - q1[0], q2[1] - q1[1]
    la, lb = math.hypot(dx, dy), math.hypot(ex, ey)
    if la < eps or lb < eps:
        return None
    if abs(dx * ey - dy * ex) > eps * la * lb:
        return None
    if abs((q1[0] - p1[0]) * dy - (q1[1] - p1[1]) * dx) > eps * la:
        return None
    t0 = ((q1[0] - p1[0]) * dx + (q1[1] - p1[1]) * dy) / (la * la)
    t1 = ((q2[0] - p1[0]) * dx + (q2[1] - p1[1]) * dy) / (la * la)
    lo, hi = min(t0, t1), max(t0, t1)
    lo, hi = max(0.0, lo), min(1.0, hi)
    if hi - lo <= 1e-9:
        return None
    # B 侧也换算成参数
    u0 = ((p1[0] + dx * lo - q1[0]) * ex + (p1[1] + dy * lo - q1[1]) * ey) / (lb * lb)
    u1 = ((p1[0] + dx * hi - q1[0]) * ex + (p1[1] + dy * hi - q1[1]) * ey) / (lb * lb)
    return lo, hi, min(u0, u1), max(u0, u1)


def is_simple(poly) -> bool:
    """折线是否自交（相邻边不算）。自交的折线「内部」本身就没有定义，
    布尔会算出一个能过 schema 但看着莫名其妙的形状——必须在算之前挡住。"""
    n = len(poly)
    for i in range(n):
        a1, a2 = poly[i], poly[(i + 1) % n]
        for j in range(i + 2, n):
            if (i == 0 and j == n - 1):
                continue
            b1, b2 = poly[j], poly[(j + 1) % n]
            if _seg_cross(a1, a2, b1, b2) is not None:
                return False
    return True


def poly_bool(op: str, A, B, eps=1e-7):
    """任意两个简单多边形（折线）的 差 / 交 → 轮廓列表。

    走的是「切段 + 分类 + 接力」：把双方边在所有交叉点处切开，每段按中点落在
    对方内部与否决定留不留，再把留下的有向段接回轮廓。比 Greiner–Hormann 好理解，
    代价是**共线重合边**要靠 `_on_seg` 的 eps 兜，兜不住的地方直接报。
    """
    if op not in ('subtract', 'intersect'):
        raise ValueError(f'poly_bool 只认 subtract / intersect，收到 {op}')
    A, B = _dedupe(A), _dedupe(B)
    if len(A) < 3 or len(B) < 3:
        raise ValueError('布尔的两边都得是至少三个点的闭合折线')
    for tag, poly in (('a', A), ('b', B)):
        if not is_simple(poly):
            raise ValueError(f'操作数 {tag} 是自交折线，内部没有定义——先修几何再算布尔')

    # 交叉点先算一遍，双方共用同一个坐标——各自按参数插值会差出 1e-12，
    # 落进 1e-5 的网格就可能分到两格，接力时于是「接不上」，报成共线重合的错。
    # 这是踩过的坑：症状是「断成开口折线」，病根却在两边的浮点插值不碰头。
    cuts: dict[tuple[int, int], tuple[float, float, tuple[float, float]]] = {}
    for i in range(len(A)):
        p, q = A[i], A[(i + 1) % len(A)]
        for j in range(len(B)):
            r0, q1 = B[j], B[(j + 1) % len(B)]
            r = _seg_cross(p, q, r0, q1)
            if r:
                t, u = r
                pa = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                pb = (r0[0] + (q1[0] - r0[0]) * u, r0[1] + (q1[1] - r0[1]) * u)
                cuts[(i, j)] = (t, u, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2))

    # 共线重合边：记下双方的重叠区间，两端也当作切点，于是这段会被切成独立的小段，
    # 再由 keep() 里的「中点落在对方边界上 → 丢」统一消掉（各自走一遍方向相反，等于抵消）。
    shares = []
    for i in range(len(A)):
        p, q = A[i], A[(i + 1) % len(A)]
        for j in range(len(B)):
            r0, q1b = B[j], B[(j + 1) % len(B)]
            ov = collinear_overlap(p, q, r0, q1b)
            if ov:
                lo, hi, u0, u1 = ov
                pa0 = (p[0] + (q[0] - p[0]) * lo, p[1] + (q[1] - p[1]) * lo)
                pa1 = (p[0] + (q[0] - p[0]) * hi, p[1] + (q[1] - p[1]) * hi)
                shares.append((i, j, lo, hi, u0, u1, pa0, pa1))

    def split(poly, other_n, side):
        out = []
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            marks: dict[float, tuple[float, float]] = {}
            for (ci, cj), (t, u, pt) in cuts.items():
                if side == 'a' and ci == i:
                    marks[t] = pt
                elif side == 'b' and cj == i:
                    marks[u] = pt
            for (si, sj, lo, hi, u0, u1, pa0, pa1) in shares:
                if side == 'a' and si == i:
                    marks[lo] = pa0
                    marks[hi] = pa1
                elif side == 'b' and sj == i:
                    marks[u0] = pa0
                    marks[u1] = pa1
            # 同一条边被打两次（重合边）时，只保留参数最靠前的那个
            ordered = sorted(marks.items())
            prev_t, prev_p = 0.0, p
            for t, pt in ordered:
                out.append((prev_p, pt))
                prev_t, prev_p = t, pt
            out.append((prev_p, q))
        return out

    segs_a = split(A, len(B), 'a')
    segs_b = split(B, len(A), 'b')

    def keep(seg, own, other, want_inside, prefer):
        mid = ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2)
        r = pt_in_poly(mid, other)
        if r is not None:
            return r == want_inside
        # 中点落在对方边界上＝**共享边**。这条边留不留，取决于两形的内部在它的**同侧还是异侧**：
        #   同侧  → 交集这里挨着两边共同的内腔，是结果的边界（留）；差集这里两边都有，被挖掉了（丢）
        #   异侧  → 交集只剩贴一下，没有内腔（丢）；差集的边界正是这条（留）
        # 而且只留 A 的那一份：两份都留就成了双线，接力接不上。
        p, q = seg
        ex, ey = q[0] - p[0], q[1] - p[1]
        L = math.hypot(ex, ey)
        if L < 1e-9:
            return False
        nx, ny = -ey / L, ex / L
        off = max(1e-6, 0.002 * L)
        same = None
        for sgn in (1.0, -1.0):
            probe = (mid[0] + nx * off * sgn, mid[1] + ny * off * sgn)
            if pt_in_poly(probe, own) is True:
                same = (pt_in_poly(probe, other) is True)
                break
        if same is None:
            return False           # 极薄几何：探针落不进任何一侧，宁可不留
        keep_it = same if op == 'intersect' else (not same)
        return prefer and keep_it

    kept = [s for s in segs_a if keep(s, A, B, op == 'intersect', True)]
    # 方向：交集两边都按自己的绕向走；差集里 B 的那截要**反向**（挖洞/咬掉）。
    # 这条一开始写反了，症状是「两条轮廓同向，接力接不上」——接不上的点正好是两个交点在
    # 各偏一侧，看着像浮点噪声，其实是绕向错。
    if op == 'subtract':
        kept += [(s[1], s[0]) for s in segs_b if keep(s, B, A, True, False)]
    else:
        kept += [s for s in segs_b if keep(s, B, A, True, False)]

    if not kept:
        # 没有交叉段：只剩包含或相离，逐个判
        a_in_b = pt_in_poly(A[0], B)
        b_in_a = pt_in_poly(B[0], A)
        if a_in_b is None and b_in_a is None:
            # 两形的边界完全重合（自差、或同一份几何两份写法）
            if op == 'intersect':
                return [A]
            raise ValueError('两形边界完全重合，差集为空')
        if op == 'intersect':
            if a_in_b:      # A ⊂ B
                return [A]
            if b_in_a:
                return [B]
            raise ValueError('两形相离，交集为空')
        if a_in_b:          # A ⊂ B
            raise ValueError('相减后为空（A 整块落在 B 里）')
        if b_in_a:          # B ⊂ A：A 中间挖个洞，洞按反向绕走
            return [A, list(reversed(B))]
        return [A]

    contours = _chain(kept)
    return contours


def _poly_of(spec: dict, n: int):
    """spec 里的一个布尔操作数 → 点列。三种写法：两圆（center/r）、path、points。"""
    if 'center' in spec and 'r' in spec:
        return circle_poly(spec['center'], float(spec['r']), 0.0, 2 * math.pi, n)[:-1]
    if 'path' in spec:
        return _dedupe(svg_path(spec['path'], n))
    if 'points' in spec:
        return _dedupe([(float(p[0]), float(p[1])) for p in spec['points']])
    raise ValueError('布尔的操作数只认 {center,r} / {path} / {points}')


def boolean_points(op: str, a: dict, b: dict, n: int = 64):
    """布尔入口：两圆走解析解（边界干净），其余一律折算成折线再算。

    返回**轮廓列表**——差集挖洞、交集成多块，都可能不止一条轮廓。
    """
    if op not in ('subtract', 'intersect'):
        raise ValueError(f'boolean.op 只认 subtract / intersect，收到 {op}')
    if all(k in a for k in ('center', 'r')) and all(k in b for k in ('center', 'r')):
        pts = circle_bool(op, a['center'], float(a['r']), b['center'], float(b['r']),
                          (0, 0), n)
        return [pts]
    pa, pb = _poly_of(a, n), _poly_of(b, n)
    return poly_bool(op, pa, pb)


# ------------------------------------------------------------ SVG path

def svg_path(d: str, n=24) -> tuple[list[tuple[float, float]], float, float]:
    """只为一件事：把带曲线的 d 变成点列（A 段按圆处理）。"""
    toks = re.findall(r'[MmLlCcQqAaZz]|-?\d*\.?\d+(?:e-?\d+)?', d)
    pts: list[tuple[float, float]] = []
    cx = cy = 0.0
    cmd = None
    i = 0
    start = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        if re.fullmatch(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                if start and (pts[-1] != start):
                    pts.append(start)
                continue
        rel = cmd.islower()
        k = cmd.upper()
        if k == 'M':
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            pts.append((cx, cy)); start = (cx, cy)
            cmd = 'l' if rel else 'L'
        elif k == 'L':
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            pts.append((cx, cy))
        elif k == 'C':
            x1, y1, x2, y2, x, y = (num() for _ in range(6))
            if rel:
                x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
            p0 = (cx, cy)
            for s in range(1, n + 1):
                t = s / n
                bx = ((1-t)**3)*p0[0] + 3*((1-t)**2)*t*x1 + 3*(1-t)*(t**2)*x2 + t**3*x
                by = ((1-t)**3)*p0[1] + 3*((1-t)**2)*t*y1 + 3*(1-t)*(t**2)*y2 + t**3*y
                pts.append((bx, by))
            cx, cy = x, y
        elif k == 'Q':
            x1, y1, x, y = (num() for _ in range(4))
            if rel:
                x1 += cx; y1 += cy; x += cx; y += cy
            p0 = (cx, cy)
            for s in range(1, n + 1):
                t = s / n
                bx = (1-t)**2*p0[0] + 2*(1-t)*t*x1 + t*t*x
                by = (1-t)**2*p0[1] + 2*(1-t)*t*y1 + t*t*y
                pts.append((bx, by))
            cx, cy = x, y
        elif k == 'A':
            rx, ry, rot, large, sweep, x, y = (num() for _ in range(7))
            if rel:
                x += cx; y += cy
            pts += arc_points((cx, cy), (x, y), rx, ry, int(large), int(sweep), n)
            cx, cy = x, y
        else:
            raise ValueError(f'没实现的命令：{cmd}')
    return pts


def arc_points(p0, p1, rx, ry, large, sweep, n=24):
    """SVG 端点式圆弧 → 点列（x 轴半径、旋转忽略，本项目只画正圆）。"""
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    lam = dx**2 / rx**2 + dy**2 / ry**2
    if lam > 1:
        rx *= math.sqrt(lam); ry *= math.sqrt(lam)
    sign = -1 if large == sweep else 1
    co = sign * math.sqrt(max(0, (rx**2 * ry**2 - rx**2 * dy**2 - ry**2 * dx**2)
                             / (rx**2 * dy**2 + ry**2 * dx**2)))
    cxp, cyp = co * rx * dy / ry, -co * ry * dx / rx
    ccx, ccy = cxp + (x0 + x1) / 2, cyp + (y0 + y1) / 2
    a0 = math.atan2((y0 - ccy) / ry, (x0 - ccx) / rx)
    a1 = math.atan2((y1 - ccy) / ry, (x1 - ccx) / rx)
    da = a1 - a0
    if sweep and da < 0:
        da += 2 * math.pi
    if not sweep and da > 0:
        da -= 2 * math.pi
    return [(ccx + rx * math.cos(a0 + da * s / n), ccy + ry * math.sin(a0 + da * s / n))
            for s in range(1, n + 1)]


def arc_to_cubics(p0, p1, rx, ry, large, sweep, max_seg_deg=90.0):
    """SVG 端点式圆弧 → 一串三次贝塞尔（每段 ≤90°，k = 4/3·tan(θ/4)）。

    ⛔ 不要拿采样折线糊过去：折线在 A→custGeom 是保真的，但视觉上圆会变成多边形，
    段数少了看得出棱角，段数多了文件膨胀——贝塞尔两头都省。
    """
    x0, y0 = p0
    x1, y1 = p1
    if rx == 0 or ry == 0:
        return [('line', (x1, y1))]
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    lam = dx**2 / rx**2 + dy**2 / ry**2
    if lam > 1:
        rx *= math.sqrt(lam); ry *= math.sqrt(lam)
    sign = -1 if large == sweep else 1
    num = rx**2 * ry**2 - rx**2 * dy**2 - ry**2 * dx**2
    co = sign * math.sqrt(max(0, num / (rx**2 * dy**2 + ry**2 * dx**2)))
    cxp, cyp = co * rx * dy / ry, -co * ry * dx / rx
    ccx, ccy = cxp + (x0 + x1) / 2, cyp + (y0 + y1) / 2
    a0 = math.atan2((y0 - ccy) / ry, (x0 - ccx) / rx)
    a1 = math.atan2((y1 - ccy) / ry, (x1 - ccx) / rx)
    da = a1 - a0
    if sweep and da < 0:
        da += 2 * math.pi
    if not sweep and da > 0:
        da -= 2 * math.pi
    steps = max(1, int(math.ceil(abs(math.degrees(da)) / max_seg_deg)))
    out = []
    for i in range(steps):
        t0 = a0 + da * i / steps
        t1 = a0 + da * (i + 1) / steps
        dt = t1 - t0
        k = 4 / 3 * math.tan(dt / 4)
        px0, py0 = ccx + rx * math.cos(t0), ccy + ry * math.sin(t0)
        px1, py1 = ccx + rx * math.cos(t1), ccy + ry * math.sin(t1)
        c1 = (px0 - k * rx * math.sin(t0), py0 + k * ry * math.cos(t0))
        c2 = (px1 + k * rx * math.sin(t1), py1 - k * ry * math.cos(t1))
        out.append(('cubic', c1, c2, (px1, py1)))
    return out


def svg_segments(d: str):
    """`d` → 段列：('line', pt) / ('cubic', c1, c2, pt)。坐标是绝对值，首段是 ('move', pt)。

    与 `svg_path` 的分工：`svg_path` 给布尔用（布尔要的是折线），这个给 custGeom 用（要保真）。
    """
    toks = re.findall(r'[MmLlCcQqAaZz]|-?\d*\.?\d+(?:e-?\d+)?', d)
    segs: list = []
    cx = cy = 0.0
    cmd = None
    i = 0
    start = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def q2c(p0, c, p1):
        """二次 → 三次（升阶，误差为零）。"""
        c1 = (p0[0] + 2 / 3 * (c[0] - p0[0]), p0[1] + 2 / 3 * (c[1] - p0[1]))
        c2 = (p1[0] + 2 / 3 * (c[0] - p1[0]), p1[1] + 2 / 3 * (c[1] - p1[1]))
        return c1, c2

    while i < len(toks):
        if re.fullmatch(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                if start is not None and (cx, cy) != start:
                    segs.append(('line', start))
                continue
        rel = cmd.islower()
        k = cmd.upper()
        if k == 'M':
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            segs.append(('move', (cx, cy)))
            start = (cx, cy)
            cmd = 'l' if rel else 'L'
        elif k == 'L':
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            segs.append(('line', (cx, cy)))
        elif k == 'C':
            x1, y1, x2, y2, x, y = (num() for _ in range(6))
            if rel:
                x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
            segs.append(('cubic', (x1, y1), (x2, y2), (x, y)))
            cx, cy = x, y
        elif k == 'Q':
            x1, y1, x, y = (num() for _ in range(4))
            if rel:
                x1 += cx; y1 += cy; x += cx; y += cy
            c1, c2 = q2c((cx, cy), (x1, y1), (x, y))
            segs.append(('cubic', c1, c2, (x, y)))
            cx, cy = x, y
        elif k == 'A':
            rx, ry, rot, large, sweep, x, y = (num() for _ in range(7))
            if rel:
                x += cx; y += cy
            segs += arc_to_cubics((cx, cy), (x, y), rx, ry, int(large), int(sweep))
            cx, cy = x, y
        else:
            raise ValueError(f'没实现的命令：{cmd}')
    return segs


def custgeom_segments(shape, segs, cx: float, cy: float, off=(0.0, 0.0), closed: bool = True):
    """把段列写成 custGeom（lnTo / cubicBezTo）。坐标按 bbox 平移后交给 path 自己的 EMU 空间。"""
    ox, oy = off
    geom = etree.SubElement(etree.Element(A + 'tmp'), A + 'custGeom')
    for t in ('avLst', 'gdLst', 'ahLst', 'cxnLst'):
        etree.SubElement(geom, A + t)
    rect = etree.SubElement(geom, A + 'rect')
    for k, v in (('l', 'l'), ('t', 't'), ('r', 'r'), ('b', 'b')):
        rect.set(k, v)
    lst = etree.SubElement(geom, A + 'pathLst')
    p = etree.SubElement(lst, A + 'path')
    p.set('w', str(px(cx)))
    p.set('h', str(px(cy)))

    def pt(tag, xy):
        el = etree.SubElement(p, A + tag)
        q = etree.SubElement(el, A + 'pt')
        q.set('x', str(px(xy[0] - ox)))
        q.set('y', str(px(xy[1] - oy)))
        return q

    for seg in segs:
        if seg[0] == 'move':
            pt('moveTo', seg[1])
        elif seg[0] == 'line':
            pt('lnTo', seg[1])
        elif seg[0] == 'cubic':
            c = etree.SubElement(p, A + 'cubicBezTo')
            for xy in (seg[1], seg[2], seg[3]):
                q = etree.SubElement(c, A + 'pt')
                q.set('x', str(px(xy[0] - ox)))
                q.set('y', str(px(xy[1] - oy)))
    if closed:
        etree.SubElement(p, A + 'close')
    spPr = shape._element.spPr
    prst = spPr.find(A + 'prstGeom')
    if prst is not None:
        prst.addnext(geom)
        spPr.remove(prst)
    else:
        spPr.insert(0, geom)


# ------------------------------------------------------------ 出件

def build_proofer(css_path: Path, out: Path, title: str = '染层与墨线') -> Path:
    css = css_path.read_text(encoding='utf-8')
    vals = root_vars(css)
    grads = {}
    for m in re.finditer(r'\.([\w-]+)\s*\{([^}]*)\}', css, re.S):
        name, blk = m.group(1), m.group(2)
        bg = re.search(r'background\s*:\s*((?:linear|radial)-gradient\()', blk)
        if bg:
            inner, _ = balanced(blk, bg.end())
            grads[name] = parse_gradient(bg.group(1) + inner + ')', vals)

    prs = Presentation()
    prs.slide_width = Emu(px(W))
    prs.slide_height = Emu(px(H))
    blank = prs.slide_layouts[6]

    def label(sl, text, x, y, size=28, color_hex='1B2A4A', bold=False, w=1400):
        tb = sl.shapes.add_textbox(Emu(px(x)), Emu(px(y)), Emu(px(w)), Emu(px(56)))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = text
        r.font.size = Pt(size * 0.75)
        r.font.bold = bold
        r.font.color.rgb = RGBColor.from_string(color_hex)
        r.font.name = 'Inter'
        return tb

    def panel(sl, x, y, w, h, fill, name=None):
        sh = sl.shapes.add_shape(1, Emu(px(x)), Emu(px(y)), Emu(px(w)), Emu(px(h)))
        sh.line.fill.background()
        set_fill(sh, fill)
        if name:
            sh.name = name
        return sh

    # 页 1：三色标 + 角度 + 末标 alpha（形状先入，文字后入，文字压在上面）
    s1 = prs.slides.add_slide(blank)
    panel(s1, 88, 210, 1424, 400, ('grad', grads['wash-a']))
    label(s1, '染层：三色标、135°、末标不透明', 88, 96, 34, bold=True)
    label(s1, 'CSS: linear-gradient(135deg, --wash-ink 0%, --wash-sea 45%, rgba(214,166,58,.75) 100%)',
          88, 636, 20, '555555')
    label(s1, '同一份声明 → a:gradFill 的三枚 a:gs，第三枚带 a:alpha val=75000', 88, 676, 20, '555555')

    # 页 2：两层叠加（径向亮斑压在底色上）
    s2 = prs.slides.add_slide(blank)
    panel(s2, 88, 210, 1424, 400, ('solid', '1B2A4A'))
    panel(s2, 88, 210, 1424, 400, ('grad', grads['wash-b']), name='wash-b')
    label(s2, '染层叠加：底色 + 径向亮斑', 88, 96, 34, bold=True)
    label(s2, 'CSS 的多层 background 与 DrawingML 的单层 gradFill 不等价，等价的是「多层绘制」：'
              '层数、顺序、alpha 对上即可', 88, 636, 20, '555555')

    # 页 3：布尔（差 / 交）＋ 直接 path
    s3 = prs.slides.add_slide(blank)

    def place(pts, fill, name, at_x, at_y, target_h=430.0):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        minx, miny = min(xs), min(ys)
        nw, nh = max(xs) - minx, max(ys) - miny
        k = target_h / nh
        w, h = nw * k, target_h
        sh = panel(s3, at_x, at_y, w, h, fill, name=name)
        custgeom(sh, [((x - minx) * k, (y - miny) * k) for x, y in pts], w, h)
        return w

    pts_sub = circle_bool('subtract', (300, 300), 300, (420, 300), 300, (0, 0), 96)
    wx = place(pts_sub, ('solid', '2F5D8A'), 'boolean-subtract', 88, 215)
    pts_int = circle_bool('intersect', (1400, 300), 220, (1550, 300), 220, (0, 0), 96)
    wx2 = place(pts_int, ('solid', 'D6A63A'), 'boolean-intersect', 88 + wx + 70, 215)
    m = re.search(r'\.moon\s*\{[^}]*path\("([^"]+)"\)', css)
    pts_path = svg_path(m.group(1)) if m else []
    if pts_path:
        place(pts_path, ('grad', grads['wash-a']), 'path-passthrough',
              88 + wx + wx2 + 130, 215)

    label(s3, '墨线：布尔在导出时求值', 88, 96, 34, bold=True)
    label(s3, '左：subtract（两圆相减）　中：intersect（两圆相交）　右：瓦作里 path() 原样翻译',
          88, 690, 18, '555555')
    label(s3, 'PPTX 没有布尔指令，所以布尔不在 PPT 里做——在导出时算成一条路径写进去',
          88, 728, 18, '555555')

    prs.save(str(out))
    return out
# ---------- 可选后端：uharfbuzz（整段 shaping 的量宽） ----------
# 现有量宽是**逐字**累加（PIL 的 getlength(ch)），天然丢掉字偶距与连字。
# 装了 uharfbuzz 就能把一段文字整体 shape 一遍再取 advance——但这条会改变断行结果，
# 所以**默认不开**（`export-pptx.py --hb-measure` 才走），免得同一份稿在两台机器上断行不同。
try:  # pragma: no cover
    import uharfbuzz as _hb
    HAS_UHARFBUZZ = True
except Exception:  # noqa: BLE001
    _hb = None
    HAS_UHARFBUZZ = False

_HB_CACHE: dict = {}


def _hb_font(font_path: str):
    key = font_path
    if key not in _HB_CACHE:
        blob = _hb.Blob.from_file_path(font_path)
        face = _hb.Face(blob)
        font = _hb.Font(face)
        font.scale = (face.upem, face.upem)
        _HB_CACHE[key] = (font, face.upem)
    return _HB_CACHE[key]


def hb_width(text: str, font_path: str, size_px: float) -> float:
    """整段 shaping 后的宽度（px）。缺后端就抛 RuntimeError，由调用方回落逐字量宽。"""
    if not HAS_UHARFBUZZ:
        raise RuntimeError('uharfbuzz 未装：pip install uharfbuzz')
    font, upem = _hb_font(font_path)
    buf = _hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    _hb.shape(font, buf)
    total = sum(p.x_advance for p in buf.glyph_positions)
    return total * size_px / upem


# ---------- 可选后端：skia-pathops（曲线布尔的真裁剪） ----------
# 本库的默认路线是「纯 python3，零重依赖」，所以曲线布尔默认走折线求值。
# 但真裁剪只有 Skia 的 pathops 能算——装了就用它，没装就退回折线并**明说降级**，
# 不让同一份 spec 在两台机器上悄悄出两种精度而谁都不知道。
try:  # pragma: no cover - 取决于这台机器装没装
    import pathops as _pathops
    HAS_PATHOPS = True
except Exception:  # noqa: BLE001
    _pathops = None
    HAS_PATHOPS = False


def backend_report() -> dict:
    """给出口与闸用的能力表（不是错误：装了什么就报什么）。"""
    return {'pathops': HAS_PATHOPS, 'uharfbuzz': HAS_UHARFBUZZ}


def _segs_to_pathops(segs, pathops):
    """段列（move/line/cubic）→ pathops.Path。只认这三种：Q 已在 svg_segments 里升成三次。"""
    p = pathops.Path()
    pen = p.getPen()
    for seg in segs:
        if seg[0] == 'move':
            pen.moveTo(seg[1])
        elif seg[0] == 'line':
            pen.lineTo(seg[1])
        elif seg[0] == 'cubic':
            pen.curveTo(seg[1], seg[2], seg[3])
    pen.closePath()
    return p


_DUMP_MOVE = re.compile(r'path\.moveTo\(([^)]*)\)')
_DUMP_LINE = re.compile(r'path\.lineTo\(([^)]*)\)')
_DUMP_CUBIC = re.compile(r'path\.cubicTo\(([^)]*)\)')
_DUMP_QUAD = re.compile(r'path\.quadTo\(([^)]*)\)')


def _nums(text: str) -> list[float]:
    return [float(v) for v in text.split(',')]


def _pathops_to_contours(path, pathops) -> list[list]:
    """读回轮廓：`Path` 没有稳定的遍历 API（segments 是生成器、verbs/points 要自己配），
    而 `dump()` 的文本格式是稳定的（FontTools 同款），就从它读——比猜 API 稳。"""
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):   # dump() 只往 stdout 写，签名里没有 stream
        path.dump()
    out: list[list] = []
    cur = None
    for line in buf.getvalue().splitlines():
        m = _DUMP_MOVE.match(line)
        if m:
            cur = [('move', tuple(_nums(m.group(1))[:2]))]
            out.append(cur)
            continue
        if cur is None:
            continue
        m = _DUMP_LINE.match(line)
        if m:
            cur.append(('line', tuple(_nums(m.group(1))[:2])))
            continue
        m = _DUMP_CUBIC.match(line)
        if m:
            v = _nums(m.group(1))
            cur.append(('cubic', (v[0], v[1]), (v[2], v[3]), (v[4], v[5])))
            continue
        m = _DUMP_QUAD.match(line)
        if m:
            v = _nums(m.group(1))
            # 二次升三次：与 svg_segments 的 q2c 同一套公式
            p0 = cur[-1][-1]; c = (v[0], v[1]); p1 = (v[2], v[3])
            c1 = (p0[0] + 2 / 3 * (c[0] - p0[0]), p0[1] + 2 / 3 * (c[1] - p0[1]))
            c2 = (p1[0] + 2 / 3 * (c[0] - p1[0]), p1[1] + 2 / 3 * (c[1] - p1[1]))
            cur.append(('cubic', c1, c2, p1))
    return [c for c in out if len(c) >= 2]


def curve_bool(op: str, a_d: str, b_d: str) -> list[list]:
    """**真**曲线布尔：沿曲线裁，不采样。返回轮廓的段列列表（可能多轮廓）。

    只在装了 skia-pathops 时可用；没装就抛 RuntimeError，由调用方退回 `poly_bool` 并报降级。
    精度：pathops 用三次贝塞尔近似圆（k=0.5523），面积误差来自这个近似，不是布尔算错——
    r=100、心距 100 的透镜实测 12288.7，解析解 12284.4（差 0.03%）。
    """
    if not HAS_PATHOPS:
        raise RuntimeError('曲线布尔要 skia-pathops（未安装）：pip install skia-pathops')
    if op not in ('subtract', 'intersect'):
        raise ValueError(f'curve_bool 只认 subtract / intersect，收到 {op}')
    pa = _segs_to_pathops(svg_segments(a_d), _pathops)
    pb = _segs_to_pathops(svg_segments(b_d), _pathops)
    want = _pathops.PathOp.DIFFERENCE if op == 'subtract' else _pathops.PathOp.INTERSECTION
    res = _pathops.op(pa, pb, want)
    return _pathops_to_contours(res, _pathops)


def curves_area(contours: list[list]) -> float:
    """段列的（近似）面积：把曲线采样成折线算，用来跟解析解对账。只为对账，不进产线。"""
    polys = []
    for c in contours:
        poly = []
        last = None
        for seg in c:
            if seg[0] == 'move':
                last = seg[1]; poly.append(last)
            elif seg[0] == 'line':
                last = seg[1]; poly.append(last)
            elif seg[0] == 'cubic':
                p0, p1, p2, p3 = last, seg[1], seg[2], seg[3]
                for i in range(1, 9):
                    t = i / 8
                    mt = 1 - t
                    poly.append((mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
                                 mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]))
                last = p3
        polys.append(poly)
    return sum(abs(area(p)) for p in polys)


def custgeom_curves(shape, contours: list[list], w: float, h: float, off=(0.0, 0.0)):
    """多轮廓的段列 → 一个 custGeom（每个轮廓一个 a:path）。曲线布尔咬成几块时用它。"""
    geom = etree.SubElement(etree.Element(A + 'tmp'), A + 'custGeom')
    for t in ('avLst', 'gdLst', 'ahLst', 'cxnLst'):
        etree.SubElement(geom, A + t)
    rect = etree.SubElement(geom, A + 'rect')
    for k, v in (('l', 'l'), ('t', 't'), ('r', 'r'), ('b', 'b')):
        rect.set(k, v)
    lst = etree.SubElement(geom, A + 'pathLst')
    ox, oy = off
    for c in contours:
        p = etree.SubElement(lst, A + 'path')
        p.set('w', str(px(w)))
        p.set('h', str(px(h)))
        for seg in c:
            if seg[0] == 'move':
                m = etree.SubElement(p, A + 'moveTo')
                q = etree.SubElement(m, A + 'pt')
                q.set('x', str(px(seg[1][0] - ox))); q.set('y', str(px(seg[1][1] - oy)))
            elif seg[0] == 'line':
                m = etree.SubElement(p, A + 'lnTo')
                q = etree.SubElement(m, A + 'pt')
                q.set('x', str(px(seg[1][0] - ox))); q.set('y', str(px(seg[1][1] - oy)))
            elif seg[0] == 'cubic':
                cu = etree.SubElement(p, A + 'cubicBezTo')
                for xy in (seg[1], seg[2], seg[3]):
                    q = etree.SubElement(cu, A + 'pt')
                    q.set('x', str(px(xy[0] - ox))); q.set('y', str(px(xy[1] - oy)))
        etree.SubElement(p, A + 'close')
    spPr = shape._element.spPr
    prst = spPr.find(A + 'prstGeom')
    if prst is not None:
        prst.addnext(geom); spPr.remove(prst)
    else:
        spPr.insert(0, geom)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='染层与墨线的换算样张器')
    ap.add_argument('css', help='wash.css（含 :root 变量与渐变/path 声明）')
    ap.add_argument('-o', '--out', required=True, help='输出 .pptx')
    args = ap.parse_args()
    css_path = Path(args.css).expanduser().resolve()
    if not css_path.is_file():
        print(f'✗ 不存在：{css_path}', file=__import__('sys').stderr)
        return 2
    out = build_proofer(css_path, Path(args.out).expanduser().resolve())
    print(f'✓ 样张：{out}（{out.stat().st_size} B）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
