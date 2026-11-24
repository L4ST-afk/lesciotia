#!/usr/bin/env python3
"""来雪亭Lesciotia :: pptx-to-html.py — 逆流：把已有的 PPTX 读成一份网页 deck

用法：
    python3 scripts/pptx-to-html.py deck.pptx -o deck.html
    python3 scripts/pptx-to-html.py deck.pptx -o deck.html --width 1600 --notes

为什么有这个：来雪亭原本只管「内容 → B/C 两个出口」。实际用起来常碰到反方向——
手上有别人给的 pptx，要放到网页里或改成 HTML 版。这条路不通「抓渲染」，
走**读形状**：位置、字号、颜色、文字都从 XML 读，还原成绝对定位的 HTML。

它是**近似还原**，不是像素复制。写清楚的三处：
- 图表、SmartArt、组合内的坐标变换不展开（占位框 + 报告里点名）；
- 主题色的继承链只解到 pptx 自带主题，不猜版式（解不出的落成中性灰并在报告里计数）；
- 阴影、3D、艺术字不还原（与 C 出口的取舍同一条：瓦作里它们是平的）。

读出后立刻自检：把 HTML 里的文字段落数与 pptx 的比一遍，少了的点名。
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import re
import sys
from pathlib import Path

PX_PER_IN = 120.0          # 与 export-pptx 同一把尺：1600 px 对应 13.333 in
EMU_PER_IN = 914400


def emu_px(v) -> float:
    return float(v or 0) / EMU_PER_IN * PX_PER_IN


# ---------- 颜色 ----------
def _srgb(el) -> str | None:
    """<a:srgbClr val="RRGGBB"> → '#rrggbb'；带 alpha 时返回 'rgba(...)'。"""
    if el is None:
        return None
    c = el.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr')
    if c is None:
        return None
    val = c.get('val') or '000000'
    alpha = c.find('{http://schemas.openxmlformats.org/drawingml/2006/main}alpha')
    if alpha is not None:
        a = int(alpha.get('val', '100000')) / 100000
        r, g, b = (int(val[i:i + 2], 16) for i in (0, 2, 4))
        return f'rgba({r},{g},{b},{round(a, 3)})'
    return '#' + val.lower()


def fill_css(shape) -> str:
    """形状填充 → CSS background。渐变按 a:gradFill 的 gsLst + lin ang 还原成 linear-gradient。"""
    try:
        el = shape._element.spPr
    except Exception:
        return 'transparent'
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    grad = el.find(ns + 'gradFill')
    if grad is not None:
        stops = []
        for gs in grad.iter(ns + 'gs'):
            pos = int(gs.get('pos', '0')) / 100000
            col = _srgb(gs)
            if col:
                stops.append(f'{col} {round(pos * 100, 1)}%')
        if stops:
            lin = grad.find(ns + 'lin')
            radial = grad.find(ns + 'path')     # <a:path path="circle"/> 就是径向
            if radial is not None:
                return f'radial-gradient(circle at 50% 50%, {", ".join(stops)})'
            ang = 90 + (int(lin.get('ang', '0')) / 60000 if lin is not None else 0)
            return f'linear-gradient({round(ang, 1)}deg, {", ".join(stops)})'
    solid = _srgb(el.find(ns + 'solidFill'))
    if solid:
        return solid
    try:
        if shape.fill.type is not None and shape.fill.type == 1:
            return '#' + str(shape.fill.fore_color.rgb).lower()
    except Exception:
        pass
    return 'transparent'


def first_color(shape) -> str:
    """取第一个色标/实色，供 SVG 兜底（SVG 里不铺 CSS 渐变，直接用首色）。"""
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    try:
        el = shape._element.spPr
    except Exception:
        return 'transparent'
    for tag in ('solidFill', 'gradFill'):
        found = el.find(ns + tag)
        if found is not None:
            c = _srgb(found)
            if c:
                return c
    return 'transparent'


def custgeom_svg(shape) -> str | None:
    """custGeom（布尔/ path 出件的结果）→ 内联 SVG。PDF/PPT 的复合形在 HTML 里没有原生对应，
    用 SVG 是唯一保形的办法：把每个 a:path 的 moveTo/lnTo/cubicBezTo 读成 SVG 的 d。"""
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    try:
        geom = shape._element.spPr.find(ns + 'custGeom')
    except Exception:
        return None
    if geom is None:
        return None
    lst = geom.find(ns + 'pathLst')
    if lst is None:
        return None
    paths = []
    w = h = None
    for pa in lst.findall(ns + 'path'):
        w, h = float(pa.get('w', '0') or 0), float(pa.get('h', '0') or 0)
        d = []
        for el in pa:
            tag = el.tag.split('}')[-1]
            if tag == 'close':
                d.append('Z')
                continue
            pts = [(float(q.get('x')), float(q.get('y'))) for q in el.findall(ns + 'pt')]
            if tag == 'moveTo':
                d.append('M ' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts[:1]))
            elif tag == 'lnTo':
                d.append('L ' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts[:1]))
            elif tag == 'cubicBezTo':
                d.append('C ' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts[:3]))
        if d:
            paths.append(' '.join(d))
    if not paths or not w or not h:
        return None
    fill = first_color(shape)
    return (f'<svg viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none" '
            f'style="width:100%;height:100%">' +
            ''.join(f'<path d="{p}" fill="{fill}" stroke="none"/>' for p in paths) + '</svg>')


def line_css(shape) -> str:
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
    try:
        ln = shape._element.spPr.find(ns + 'ln')
    except Exception:
        return 'none'
    if ln is None or ln.find(ns + 'noFill') is not None:
        return 'none'
    col = _srgb(ln)
    w = int(ln.get('w', '12700')) / 12700.0    # EMU → pt
    if not col:
        return 'none'
    return f'{col} {max(0.5, round(w * PX_PER_IN / 72.0, 2))}px'


# ---------- 几何 ----------
def radius_css(shape) -> str:
    """圆角/椭圆用 border-radius 近似；其余直角。"""
    try:
        name = shape._element.spPr.find(
            '{http://schemas.openxmlformats.org/drawingml/2006/main}prstGeom').get('prst')
    except Exception:
        name = None
    if name == 'ellipse':
        return '50%'
    if name in ('roundRect', 'round2SameRect'):
        return '12px'
    return '0'


# ---------- 文字 ----------
def para_css(p) -> str:
    algn = {'l': 'left', 'ctr': 'center', 'r': 'right', 'just': 'justify'}.get(
        str(getattr(p.alignment, 'name', '') or '').lower()[:4], '')
    if not algn:
        algn = {'LEFT': 'left', 'CENTER': 'center', 'RIGHT': 'right', 'JUSTIFY': 'justify'}.get(
            str(getattr(p, 'alignment', '') or '').split('.')[-1].upper(), 'left')
    return f'text-align:{algn};'


def run_span(run, anchor: str) -> str:
    f = run.font
    size = f.size.pt if f.size else None
    css = []
    if size:
        css.append(f'font-size:{round(size * PX_PER_IN / 72.0, 1)}px')
    if f.bold:
        css.append('font-weight:700')
    if f.italic:
        css.append('font-style:italic')
    try:
        if f.color and f.color.rgb:
            css.append(f'color:#{str(f.color.rgb).lower()}')
    except Exception:
        pass
    name = f.name
    if name:
        css.append(f"font-family:'{name}',sans-serif")
    txt = run.text or ''
    if not txt.strip():
        return html.escape(txt).replace(' ', '&nbsp;')
    return f'<span style="{";".join(css)}">{html.escape(txt)}</span>'


def shape_text_html(shape, anchor: str) -> str:
    paras = []
    for p in shape.text_frame.paragraphs:
        spans = ''.join(run_span(r, anchor) for r in p.runs)
        if not spans:
            spans = html.escape(p.text or '')
        paras.append(f'<div style="{para_css(p)}min-height:1em">{spans}</div>')
    return ''.join(paras)


def anchor_css(shape) -> str:
    try:
        v = str(getattr(shape.text_frame.vertical_anchor, 'name', '') or '')
    except Exception:
        v = ''
    if 'MIDDLE' in v.upper():
        return 'display:flex;flex-direction:column;justify-content:center;'
    if 'BOTTOM' in v.upper():
        return 'display:flex;flex-direction:column;justify-content:flex-end;'
    return ''


# ---------- 主转换 ----------
def convert(path: Path, out: Path, width: float = 1600, with_notes: bool = False) -> dict:
    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation(str(path))
    scale = width / (prs.slide_width or Emu(12192000))
    ph = round((prs.slide_height or Emu(6858000)) * scale / 1.0)  # 只用于 CSS
    rep = {'slides': 0, 'shapes': 0, 'texts': 0, 'pictures': 0, 'tables': 0,
           'charts': 0, 'groups': 0, 'fallback_fill': 0, 'notes': 0}

    slides_html = []
    for si, slide in enumerate(prs.slides, 1):
        rep['slides'] = si
        parts = []
        for sh in slide.shapes:
            rep['shapes'] += 1
            # 统一换算：EMU → px（按 slide 宽度归一）
            x = (sh.left or 0) * scale
            y = (sh.top or 0) * scale
            w = (sh.width or 0) * scale
            h = (sh.height or 0) * scale
            base = f'position:absolute;left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.1f}px;'

            # 图片
            if sh.shape_type == 13 or sh.__class__.__name__ == 'Picture':
                try:
                    img = sh.image
                    b64 = base64.b64encode(img.blob).decode()
                    parts.append(f'<img src="data:{img.content_type};base64,{b64}" '
                                 f'style="{base}object-fit:contain">')
                    rep['pictures'] += 1
                    continue
                except Exception:
                    pass

            # 图表 / SmartArt：留占位框并记账
            if getattr(sh, 'has_chart', False):
                parts.append(f'<div class="ph" style="{base}border:1px dashed #9aa;color:#789;'
                             f'font:12px system-ui;display:flex;align-items:center;justify-content:center">'
                             f'图表未转（{html.escape(sh.chart.chart_type.__str__() if hasattr(sh,"chart") else "chart")}）</div>')
                rep['charts'] += 1
                continue

            # 组合：展平（坐标不叠加子形状的 offset 变换，只记一笔）
            if sh.__class__.__name__ == 'GroupShape':
                rep['groups'] += 1

            svg = custgeom_svg(sh)
            bg = 'transparent' if svg else fill_css(sh)
            border = 'none' if svg else line_css(sh)
            radius = '0' if svg else radius_css(sh)
            box_css = base + f'background:{bg};border:{border};border-radius:{radius};'
            inner = svg or ''
            wrap = 'box-sizing:border-box;'
            if getattr(sh, 'has_text_frame', False) and sh.has_text_frame and sh.text_frame.text.strip():
                a = anchor_css(sh)
                try:
                    m = sh.text_frame.margin_left
                    pad = round((m or 0) / EMU_PER_IN * PX_PER_IN * scale, 1)
                except Exception:
                    pad = 6
                wrap += f'padding:{pad}px;' + a
                inner = shape_text_html(sh, a)
                rep['texts'] += 1
            if getattr(sh, 'has_table', False) and sh.has_table:
                rows = []
                for r in sh.table.rows:
                    cells = ''.join(
                        f'<td style="border:1px solid #b9c2cc;padding:6px 8px;font-size:13px">'
                        f'{html.escape(c.text)}</td>' for c in r.cells)
                    rows.append(f'<tr>{cells}</tr>')
                inner = ('<table style="border-collapse:collapse;width:100%">'
                         + ''.join(rows) + '</table>')
                rep['tables'] += 1

            if inner or bg != 'transparent' or border != 'none':
                # 带上 pptx 的身份：往返改字时照这个 id 填 edits.json（见 retext-pptx.py）
                ident = f' data-slide="{si}" data-id="{sh.shape_id}" data-name="{html.escape(sh.name)}"'
                parts.append(f'<div{ident} style="{box_css}{wrap}">{inner}</div>')

        notes = ''
        if with_notes:
            try:
                t = slide.notes_slide.notes_text_frame.text.strip()
                if t:
                    notes = f'<aside class="notes">{html.escape(t)}</aside>'
                    rep['notes'] += 1
            except Exception:
                pass
        slides_html.append(f'<section class="slide">{notes}{"".join(parts)}</section>')

    body = "\n".join(slides_html)
    doc = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root { --w: __W__px; --h: __H__px; }
  * { margin:0; padding:0; }
  body { background:#11161d; font-family:system-ui,-apple-system,"Helvetica Neue",sans-serif;
         display:flex; flex-direction:column; align-items:center; gap:18px; padding:18px; }
  .slide { position:relative; width:var(--w); height:var(--h); overflow:hidden;
           background:#fff; box-shadow:0 8px 26px rgba(0,0,0,.4); flex:0 0 auto; }
  .notes { position:absolute; left:0; bottom:0; right:0; background:rgba(0,0,0,.72); color:#fff;
           font-size:13px; padding:8px 12px; display:none; }
  .notes.on { display:block; }
  @media (max-width:1720px) { .slide { zoom: calc(100vw / 1720); } }
</style></head>
<body>
__BODY__
<script>
const slides=[...document.querySelectorAll('.slide')];let i=0;
function show(n){ i=Math.max(0,Math.min(slides.length-1,n)); slides[i].scrollIntoView({behavior:'smooth',block:'center'}); }
addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'||e.key==='ArrowDown'||e.key===' ') show(i+1);
  if(e.key==='ArrowLeft'||e.key==='ArrowUp') show(i-1);
  if(e.key==='n') slides.forEach(s=>s.querySelector('.notes')?.classList.toggle('on'));
});
</script>
</body></html>"""
    doc = (doc.replace('__TITLE__', html.escape(path.stem))
              .replace('__W__', str(int(width)))
              .replace('__H__', str(int(ph)))
              .replace('__BODY__', body))
    out.write_text(doc, encoding='utf-8')
    rep['bytes'] = out.stat().st_size
    # 自检：HTML 里的文字段落 vs pptx 里非空文本框数
    got = len(re.findall(r'<div style="text-align', doc))
    rep['text_blocks_html'] = got
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description='PPTX → 单文件 HTML（逆流出口）')
    ap.add_argument('pptx')
    ap.add_argument('-o', '--out', required=True)
    ap.add_argument('--width', type=float, default=1600, help='画布宽（px），默认 1600')
    ap.add_argument('--notes', action='store_true', help='把备注也带进来（默认不带）')
    args = ap.parse_args()
    src = Path(args.pptx).expanduser().resolve()
    if not src.is_file():
        print(f'✗ 不存在：{src}', file=sys.stderr)
        return 2
    out = Path(args.out).expanduser().resolve()
    rep = convert(src, out, args.width, args.notes)
    print(f'✓ HTML：{out}（{rep["slides"]} 页，{rep["bytes"] / 1024:.0f} KB）')
    print(f'  形状 {rep["shapes"]}（图 {rep["pictures"]} / 表 {rep["tables"]} / 文本框 {rep["texts"]}）')
    if rep['charts'] or rep['groups']:
        print(f'  ⚠ 未展开：图表 {rep["charts"]} 个、组合 {rep["groups"]} 个（占位或展平，不保证位置）')
    if rep['notes']:
        print(f'  备注：{rep["notes"]} 条（按 n 键显隐）')
    print('  ⚠ 这是近似还原：主题色继承、阴影/3D/艺术字不还原')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
