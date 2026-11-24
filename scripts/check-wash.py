#!/usr/bin/env python3
"""来雪亭Lesciotia :: check-wash.py — 瓦作翻译闸：这一份 spec 里的染层，翻不翻得动

用法：
    python3 scripts/check-wash.py spec.json              验 spec 的 fill / boolean / path
    python3 scripts/check-wash.py spec.json --theme century-sq
    python3 scripts/check-wash.py                        只报瓦作里的「已知翻不动」清单（不红）

为什么只查 spec 而不查全库 CSS：主题里的 `filter`、`repeating-*`、`mask` 是**装饰**，
C 出口本来就不还原它们（出件时已明说「渐变/纹理不还原」）。把它们按红处理，
闸就会永远红、然后被人关掉——那是闸的失败，不是花的失败。
真正该红的是「这份 spec 要我去翻，而我翻不动」。

判据：
- spec 里 fill 写的渐变，解出 token 之后仍带 `conic-gradient` / `repeating-*` → 红。
- `boolean.op` 只认 `subtract` / `intersect`（两圆）。`union` 红：并集靠同色叠放，不做假布尔。
- `clip-path: polygon()` 不在 path 直译的字母表（只吃 M/L/C/Q/A/Z）→ 红。
- 引用 `:root` 里没有的 token → 红（不允许悄悄用默认值）。

⛔ 这个闸只管「翻不翻得动」。翻得动但不像，是 `--render-check` 的事。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wash_bridge as wb  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
ASSETS = BASE / 'assets'

# 出现即「本库不换算」的写法（用于 INFO 清单与 token 二次检查）
UNSUPPORTED = [
    (r'conic-gradient\(', 'conic-gradient'),
    (r'repeating-(?:linear|radial)-gradient\(', 'repeating-*'),
    (r'background-blend-mode\s*:', 'background-blend-mode'),
    (r'(?<!-webkit-)(?<!-moz-)filter\s*:', 'filter'),
    (r'(?:-webkit-)?mask(?:-image)?\s*:', 'mask'),
    (r'clip-path\s*:\s*polygon\(', 'clip-path: polygon()'),
]


def css_files() -> list[Path]:
    out = [ASSETS / 'base.css']
    out += sorted((ASSETS / 'themes').glob('*.css'))
    out += sorted((ASSETS / 'full-decks').glob('*/style.css'))
    return [p for p in out if p.is_file()]


def css_report() -> list[str]:
    """只报数：这些写法在瓦作里有，但 C 出口不还原它们（出件时已声明）。"""
    hits: dict[str, int] = {}
    for p in css_files():
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith(('/*', '*')):
                continue
            for pat, name in UNSUPPORTED:
                if re.search(pat, line):
                    hits[name] = hits.get(name, 0) + 1
    return [f'{k} × {v}' for k, v in sorted(hits.items())]


def theme_vals(theme: str) -> dict[str, str]:
    css = '\n'.join(p.read_text(encoding='utf-8')
                    for p in (ASSETS / 'base.css', ASSETS / 'themes' / f'{theme}.css') if p.is_file())
    return wb.root_vars(css)


def scan_spec(path: Path, vals: dict[str, str]) -> list[str]:
    red: list[str] = []
    spec = json.loads(path.read_text(encoding='utf-8'))

    def unsupported_in(text: str) -> str | None:
        for pat, name in UNSUPPORTED:
            if re.search(pat, text):
                return name
        return None

    def check_fill(fill, where: str):
        if not isinstance(fill, dict):
            red.append(f'{where} fill 不是对象')
            return
        if 'gradient' in fill:
            try:
                text = wb.resolve(fill['gradient'], vals)
            except ValueError as e:
                red.append(f'{where} 渐变翻不动：{e}')
                return
            bad = unsupported_in(text)
            if bad:
                red.append(f'{where} 用了 {bad}：本次 spec 要翻，但本库不换算（见 SELFTEST 的不换算清单）')
                return
            try:
                wb.parse_gradient(text, vals)
            except ValueError as e:
                red.append(f'{where} 渐变解析失败：{e}')
        elif 'solid' in fill:
            raw = str(fill['solid']).strip()
            name = re.findall(r'--[\w-]+', raw)
            missing = [n for n in name if n not in vals]
            for n in missing:
                red.append(f'{where} 引用了未定义的 token {n}')
            if missing:
                return
            try:
                wb.color(wb.resolve(raw, vals) if 'var(' in raw else
                         (vals[raw] if raw in vals else raw))
            except ValueError as e:
                red.append(f'{where} 颜色翻不动：{e}')
        else:
            red.append(f'{where} fill 只认 gradient / solid')

    for i, page in enumerate(spec.get('slides', []), 1):
        for j, item in enumerate(page.get('shapes') or page.get('wash') or [], 1):
            where = f'第 {i} 页第 {j} 个形状'
            check_fill(item.get('fill'), where)
            if 'boolean' in item:
                b = item['boolean']
                mode = str(item.get('curves', 'auto'))
                if mode not in ('auto', 'polyline', 'require'):
                    red.append(f'{where} curves 只认 auto / polyline / require，收到 {mode!r}')
                elif mode == 'require' and not wb.HAS_PATHOPS:
                    red.append(f'{where} curves=require：本机没装 skia-pathops，这一档拿不到（装或改成 auto）')
                if b.get('op') == 'union':
                    red.append(f'{where} union 不做布尔：同色叠放两张即可')
                elif b.get('op') not in ('subtract', 'intersect'):
                    red.append(f'{where} boolean.op 只认 subtract / intersect，收到 {b.get("op")}')
                # 操作数：{center,r} 走解析解，{path} / {points} 折线走 poly_bool。
                # 「翻不动」的判据不是「有没有实现」，而是**几何本身讲不讲得通**：
                # 自交折线没有内部，布尔算出来也能过 schema，只是看着莫名其妙。
                for k in ('a', 'b'):
                    opd = b.get(k)
                    if not isinstance(opd, dict):
                        red.append(f'{where} boolean 缺 {k}')
                        continue
                    if 'center' in opd and 'r' in opd:
                        continue
                    if 'path' in opd:
                        try:
                            pts = wb._dedupe(wb.svg_path(opd['path'], int(item.get('n', 24)))
                                     )
                        except ValueError as e:
                            red.append(f'{where} boolean.{k}.path 翻不动：{e}')
                            continue
                        if not wb.is_simple(pts):
                            red.append(f'{where} boolean.{k}.path 自交，内部没有定义')
                    elif 'points' in opd:
                        pts = wb._dedupe([(float(p[0]), float(p[1])) for p in opd['points']])
                        if len(pts) < 3:
                            red.append(f'{where} boolean.{k}.points 少于三个点')
                        elif not wb.is_simple(pts):
                            red.append(f'{where} boolean.{k}.points 自交，内部没有定义')
                    else:
                        red.append(f'{where} boolean.{k} 只认 {{center,r}} / {{path}} / {{points}}')
            elif 'path' in item:
                try:
                    wb.svg_path(item['path'], 24)
                except ValueError as e:
                    red.append(f'{where} path 翻不动：{e}')
            elif item.get('shape', 'rect') not in ('rect', 'circle'):
                red.append(f'{where} shape 只认 rect / circle（复杂轮廓用 path / boolean），收到 {item.get("shape")}')
    return red


def html_drift(spec_path: Path, html_path: Path) -> list[str]:
    """双出口同源：spec 里要翻的那串声明，HTML 侧必须**一模一样地写着**。

    这不是渲染一致性的证明（那要两个渲染器），而是**漂移**的证明：
    HTML 改了渐变而 spec 没跟，或反之，B/C 就走成了两份瓦作。
    判据取「归一空白后的子串出现」，因为两边排版不同、换行位置不同。
    只查 fill 的声明，位置与字号由 `head_metrics` 与栅格另行保证。
    """
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    html = ' '.join(html_path.read_text(encoding='utf-8', errors='replace').split())
    red = []
    for i, page in enumerate(spec.get('slides', []), 1):
        for j, item in enumerate(page.get('shapes') or page.get('wash') or [], 1):
            fill = item.get('fill') if isinstance(item.get('fill'), dict) else None
            if not fill:
                continue
            for key in ('gradient', 'solid'):
                if key not in fill:
                    continue
                decl = ' '.join(str(fill[key]).split())
                if decl.startswith('--') and decl not in html:
                    red.append(f'第 {i} 页第 {j} 个形状的 fill.{key}「{decl}」在 HTML 侧没出现'
                               f'（两处不是同一份瓦作，或者这一页 HTML 还没写）')
                elif key == 'gradient' and decl not in html:
                    red.append(f'第 {i} 页第 {j} 个形状的渐变在 HTML 侧找不到同一串：'
                               f'「{decl[:70]}…」（归一空白后仍不匹配＝B/C 已漂移）')
    return red


def main() -> int:
    ap = argparse.ArgumentParser(description='瓦作翻译闸：spec 里翻不动的染层，一律报红')
    ap.add_argument('spec', nargs='?', help='deck spec JSON')
    ap.add_argument('--theme', default='century-sq', help='spec 里 token 的取值依据')
    ap.add_argument('--html', help='同一份落雪的 B 出口 HTML：给了就做「两处声明是否同一串」的漂移比对')
    args = ap.parse_args()

    info = css_report()
    if info:
        print('  INFO 瓦作里的已知不换算写法（装饰用，出件时不还原）：' + '、'.join(info))

    if not args.spec:
        print('  （没给 spec，只报了清单；要判红请传 spec.json）')
        return 0

    spec = Path(args.spec).expanduser().resolve()
    if not spec.is_file():
        print(f'✗ spec 不存在：{spec}', file=sys.stderr)
        return 2
    red = scan_spec(spec, theme_vals(args.theme))
    if args.html:
        hp = Path(args.html).expanduser().resolve()
        if not hp.is_file():
            print(f'✗ HTML 不存在：{hp}', file=sys.stderr)
            return 2
        red += html_drift(spec, hp)
    for r in red:
        print(f'✗ {r}', file=sys.stderr)
    if red:
        return 1
    pages = len(json.loads(spec.read_text(encoding='utf-8'))['slides'])
    if args.html:
        print(f'✓ 瓦作翻译闸：{spec.name} 的染层都能翻，且与 {Path(args.html).name} 同源（{pages} 页）')
    else:
        print(f'✓ 瓦作翻译闸：{spec.name} 的染层都能翻（{pages} 页）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
