#!/usr/bin/env python3
"""build-deck.py — 把 deck 里对本地 css/js 的引用内联成**单个 HTML 文件**。

用法：
    python3 build-deck.py <src.html> [-o out.html] [--keep-theme-list] [--force] [--json]

做的事：
  1. 本地 <link rel=stylesheet href=...> → <style data-from="...">，逐层内联 @import 的本地 css
  2. 本地 <script src=...> → <script>，保留属性
  3. 本地 <img src=...> → data URL（svg/png/jpg/gif/webp），单文件才真的能「一个文件发出去」
  4. 主题收敛：被内联的主题写回 data-themes（只留这一个），删掉 data-theme-base
     —— 单文件里没有 themes/ 目录，留着它 T 键会去取不存在的 css

判据（脚本自己检查，失败就非 0 退出）：
  - validate：源文件存在、输出目录可写、assets 根存在
  - 写后**回读**输出文件，在回读到的文本上校验：无残留本地 <link>/<script src>、
    剥 <script>/<style> 后存在 class 含 slide 的 <section>（class-token 匹配，与
    render-png.sh 的 count_slides 同源）、无指向不存在本地文件的 <img src>、
    体积 < 8MB —— 不信内存里的字符串，只信落盘后的文件
  - 幂等：输出已存在且没给 --force → 跳过（exit 0），不覆盖；--force 时先把旧件
    复制成同目录 `<name>.bak-<时间戳>`（回滚基线，不落临时目录）
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
import hashlib
import time
from pathlib import Path

LINK_RE = re.compile(r'<link\b[^>]*?rel\s*=\s*"(?:stylesheet|Stylesheet)"[^>]*?>', re.I)
SCRIPT_RE = re.compile(r'<script\b[^>]*?\bsrc\s*=\s*"([^"]+)"[^>]*?>\s*</script>', re.I)
ATTR_RE = re.compile(r'\b([a-zA-Z-]+)\s*=\s*"([^"]*)"')
IMPORT_RE = re.compile(r'@import\s+(?:url\()?["\']([^"\']+)["\']\)?\s*;')

MAX_BYTES = 8 * 1024 * 1024

# 内化字体（2026-11-19）：@font-face 的 src 是相对 CSS 文件的路径。CSS 被内联进
# 单文件后相对路径会按 HTML 位置解析而断链，故打包时把本地字体 url() 转 data URI。
FONT_MIME = {'.ttf': 'font/ttf', '.otf': 'font/otf',
             '.woff': 'font/woff', '.woff2': 'font/woff2'}
FONT_URL_RE = re.compile(r'''url\(\s*(['"]?)([^'")]+)\1\s*\)''', re.I)

SCRIPT_BLOCK_RE = re.compile(r'<script\b[^>]*>.*?</script>', re.S | re.I)
STYLE_BLOCK_RE = re.compile(r'<style\b[^>]*>.*?</style>', re.S | re.I)
SLIDE_RE = re.compile(r'<section\b[^>]*class="[^"]*(?<![A-Za-z0-9_-])slide(?![A-Za-z0-9_-])[^"]*"', re.I)
IMG_RE = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*"([^"]+)"', re.I)
# 块整体优先匹配：script/style 里的内容是 JS/CSS 文本（上游 base.css 注释里就有
# `<img src="…">` 示例），不能当成真图片去解析
IMG_OR_BLOCK_RE = re.compile(
    r'<(script|style)\b[^>]*>.*?</\1>|<img\b[^>]*?\bsrc\s*=\s*"([^"]+)"[^>]*>', re.S | re.I)
IMG_MIME = {'.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp'}


def strip_non_markup(text: str) -> str:
    """script/style 的内容是 JS/CSS 文本，不是标记。上游 base.css 的注释里就有
    `<img src="…">` 示例，不剥掉会被当成破图（2026-11-14 实测假红）。"""
    return STYLE_BLOCK_RE.sub('', SCRIPT_BLOCK_RE.sub('', text))


# ---- 中文半角标点（罗蛇 T03，2026-11-23）-----------------------------------
# 中文句子一律用全角标点；半角逗号/句号/冒号/分号/叹号/问号夹在汉字里是硬失败。
# 只在**紧邻**汉字时报（隔着空格不报，因为「中文 he, she」这种西文句子夹带是正常的）。
# 三条例外都是实测踩过的假阳性：扩展名（报告.pdf）、小数与版本（3.8% / v1.2.19）、
# 代码块（<code>/<pre>/<kbd> 里的示例字符串本来就该带半角）。
CJK_CHAR_RE = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
HALF_PUNCT_RE = re.compile(r'[,.:;!?]')
CODE_BLOCK_RE = re.compile(r'<(code|pre|kbd|samp)\b[^>]*>.*?</\1>', re.S | re.I)
PUNCT_FULL = {',': '，', '.': '。', ':': '：', ';': '；', '!': '！', '?': '？'}


def scan_halfwidth_punct(html: str) -> list[str]:
    """返回「半角标点紧邻汉字」的清单，每条带上下文。只扫文本节点。"""
    body = strip_non_markup(html)
    body = CODE_BLOCK_RE.sub('', body)
    text = re.sub(r'<[^>]+>', '', body)
    issues: list[str] = []
    for m in HALF_PUNCT_RE.finditer(text):
        i, ch = m.start(), m.group(0)
        prev = text[i - 1] if i else ''
        nxt = text[i + 1] if i + 1 < len(text) else ''
        prev_cjk, next_cjk = bool(CJK_CHAR_RE.match(prev)), bool(CJK_CHAR_RE.match(nxt))
        if not (prev_cjk or next_cjk):
            continue
        # 报告.pdf、v1.2.19、3.8%：'.' 后接 ASCII 字母数字，不是句末
        if ch == '.' and re.match(r'[0-9A-Za-z]', nxt):
            continue
        snippet = text[max(0, i - 14):i + 15].replace('\n', ' ').strip()
        issues.append(f'半角「{ch}」紧邻汉字 → 应写「{PUNCT_FULL[ch]}」：…{snippet}…')
    return issues


def attrs(tag: str) -> dict[str, str]:
    return {m.group(1).lower(): m.group(2) for m in ATTR_RE.finditer(tag)}


def is_remote(href: str) -> bool:
    return bool(re.match(r'(?:https?:)?//|data:|#', href.strip(), re.I))


def inline_fonts(css: str, css_dir: Path) -> str:
    """把 CSS 里指向本地字体文件的 url() 转成 data URI；远程/data 原样保留。
       只处理字体扩展名，避免误伤 background:url(...) 的图片（图片走 <img> 通道）。"""
    def repl(m: re.Match) -> str:
        target = m.group(2).strip()
        if not target or is_remote(target):
            return m.group(0)
        if Path(target).suffix.lower() not in FONT_MIME:
            return m.group(0)
        fp = (css_dir / target).resolve()
        if not fp.is_file():
            print(f'! 找不到字体 {target}（原样保留）', file=sys.stderr)
            return m.group(0)
        b64 = base64.b64encode(fp.read_bytes()).decode('ascii')
        mime = FONT_MIME[fp.suffix.lower()]
        return f'url(data:{mime};base64,{b64})'
    return FONT_URL_RE.sub(repl, css)


def inline_images(css: str, css_dir: Path) -> str:
    """把 CSS 里指向本地图片的 url() 转成 data URI；远程/data 原样保留。

    为什么需要（2026-11-22 位图材质进库后才暴露）：`inline_fonts()` 只认字体扩展名，
    CSS 里的 `background:url(../textures/...)` 是被有意放过的。但单文件 deck / 预览页
    是把主题 CSS **内联进页面**的，相对路径的解析基准从「CSS 所在目录」变成「页面所在目录」，
    `../textures/...` 立刻 404——页面照常渲染、纹理静默消失，退出码还是 0。"""
    def repl(m: re.Match) -> str:
        target = m.group(2).strip()
        if not target or is_remote(target):
            return m.group(0)
        mime = IMG_MIME.get(Path(target).suffix.lower())
        if mime is None:
            return m.group(0)
        fp = (css_dir / target).resolve()
        if not fp.is_file():
            print(f'! 找不到图片 {target}（原样保留）', file=sys.stderr)
            return m.group(0)
        b64 = base64.b64encode(fp.read_bytes()).decode('ascii')
        return f'url(data:{mime};base64,{b64})'
    return FONT_URL_RE.sub(repl, css)


def read_css(path: Path) -> str:
    """内联本地 css，并递归内联它 @import 的本地 css（远程 @import 原样保留）；
       同时把本地字体 url() 转 data URI，使单文件里 @font-face 仍生效。"""
    text = path.read_text(encoding='utf-8', errors='replace')
    seen = {path.resolve()}

    def repl(m: re.Match) -> str:
        target = m.group(1).strip()
        if is_remote(target):
            return m.group(0)
        child = (path.parent / target).resolve()
        if not child.exists() or child in seen:
            return m.group(0)
        seen.add(child)
        return read_css(child)

    inlined = IMPORT_RE.sub(repl, text)
    return inline_images(inline_fonts(inlined, path.parent), path.parent)


ASSET_PREFIX_RE = re.compile(r'^\.{0,2}/?assets/')


def resolve_asset(href: str, src: Path, assets_root: Path | None) -> Path:
    """`../assets/base.css` 这类写法按 assets_root 解析，免得 deck 换个目录就断链。"""
    if assets_root and ASSET_PREFIX_RE.match(href):
        return (assets_root / ASSET_PREFIX_RE.sub('', href)).resolve()
    return (src.parent / href).resolve()


def validate(src: Path, out: Path, assets_root: Path | None) -> list[str]:
    """前置校验：不过就退出，不写任何文件。"""
    problems = []
    if not src.is_file():
        problems.append(f'源文件不存在：{src}')
    if not out.parent.is_dir():
        problems.append(f'输出目录不存在：{out.parent}')
    if assets_root is not None and not assets_root.is_dir():
        problems.append(f'assets 根不存在：{assets_root}')
    if src.is_file() and src.stat().st_size == 0:
        problems.append(f'源文件为空：{src}')
    return problems


def verify_on_disk(out: Path, expected_inlined: int) -> list[str]:
    """写后回读：所有断言都在**落盘后的字节**上重算一遍。"""
    problems = []
    if not out.is_file():
        return ['输出文件不存在']
    text = out.read_text(encoding='utf-8', errors='replace')
    left_links = [t for t in LINK_RE.findall(text) if not is_remote(attrs(t).get('href', ''))]
    left_scripts = [s for s in SCRIPT_RE.findall(text) if not is_remote(s)]
    if left_links:
        problems.append(f'仍残留 {len(left_links)} 个本地 <link>')
    if left_scripts:
        problems.append(f'仍残留 {len(left_scripts)} 个本地 <script src>')
    body = strip_non_markup(text)
    if not SLIDE_RE.search(body):
        problems.append('输出里找不到 class 含 slide 的 <section>，不像 deck')
    broken_imgs = [s for s in IMG_RE.findall(body)
                   if not is_remote(s) and not (out.parent / s.split('?')[0].split('#')[0]).exists()]
    if broken_imgs:
        problems.append(f'{len(broken_imgs)} 个 <img src> 指向不存在的本地文件：'
                        + '、'.join(broken_imgs[:3]))
    size = out.stat().st_size
    if size == 0 or size > MAX_BYTES:
        problems.append(f'输出体积异常：{size} bytes')
    if text.count('data-from=') != expected_inlined:
        problems.append(f'内联数与回读不符：{text.count("data-from=")} != {expected_inlined}')
    return problems


def build(src: Path, out: Path, keep_theme_list: bool, assets_root: Path | None,
          allow_punct: bool = False) -> int:
    html = src.read_text(encoding='utf-8', errors='replace')
    # 先查标点再内联：内联之后 CSS/JS 里的字符串也会进正文，扫描面会变脏。
    punct = scan_halfwidth_punct(html)
    if punct:
        head = '⚠️' if allow_punct else '✗'
        for p in punct:
            print(f'{head} {p}', file=sys.stderr)
        if not allow_punct:
            print(f'✗ 中文半角标点 {len(punct)} 处（罗蛇 T03 硬失败）。改用全角，'
                  f'或确实要保留时加 --allow-punct 并说明理由', file=sys.stderr)
            return 1
    inlined: list[str] = []
    theme_name = None

    def link_repl(m: re.Match) -> str:
        nonlocal theme_name
        tag = m.group(0)
        a = attrs(tag)
        href = a.get('href', '').strip()
        if not href or is_remote(href):
            return tag
        target = resolve_asset(href, src, assets_root)
        if not target.exists():
            print(f'! 找不到 {href}（原样保留）', file=sys.stderr)
            return tag
        css = read_css(target)
        extra = ' media="%s"' % a['media'] if 'media' in a else ''
        if a.get('id') == 'theme-link':
            theme_name = Path(href).stem
        inlined.append(href)
        # 记下源文件指纹：check-deck-sync 靠它判断「deck 里的主题 CSS 还是不是最新的」
        raw = target.read_bytes().replace(b'\r\n', b'\n')
        sha = hashlib.sha256(raw).hexdigest()[:16]
        # 保留 id=theme-link：runtime 用它定位主题样式元素，T 键只读不写
        keep_id = f' id="{a["id"]}"' if a.get('id') else ''
        return f'<style{keep_id} data-from="{href}" data-sha256="{sha}"{extra}>\n{css}\n</style>'

    def script_repl(m: re.Match) -> str:
        src_attr = m.group(1).strip()
        if is_remote(src_attr):
            return m.group(0)
        target = resolve_asset(src_attr, src, assets_root)
        if not target.exists():
            print(f'! 找不到 {src_attr}（原样保留）', file=sys.stderr)
            return m.group(0)
        a = attrs(m.group(0))
        keep = ''.join(
            f' {k}="{v}"' for k, v in a.items()
            if k in {'defer', 'async', 'type', 'id'} and not (k == 'type' and v == 'text/javascript')
        )
        js = target.read_text(encoding='utf-8', errors='replace')
        inlined.append(src_attr)
        # 防止 JS 里出现 </script> 提前闭合
        js = js.replace('</script>', '<\\/script>')
        return f'<script{keep} data-from="{src_attr}">\n{js}\n</script>'

    def img_repl(m: re.Match) -> str:
        if m.group(1):  # script/style 块原样保留
            return m.group(0)
        tag = m.group(0)
        src_attr = m.group(2).strip()
        if is_remote(src_attr):
            return tag
        target = resolve_asset(src_attr, src, assets_root)
        mime = IMG_MIME.get(target.suffix.lower())
        if not target.exists() or mime is None:
            print(f'! 找不到 {src_attr}（原样保留）', file=sys.stderr)
            return tag
        b64 = base64.b64encode(target.read_bytes()).decode('ascii')
        inlined.append(src_attr)
        return re.sub(r'\bsrc\s*=\s*"[^"]+"',
                      lambda _: f'data-from="{src_attr}" src="data:{mime};base64,{b64}"',
                      tag, count=1)

    html = LINK_RE.sub(link_repl, html)
    html = SCRIPT_RE.sub(script_repl, html)
    html = IMG_OR_BLOCK_RE.sub(img_repl, html)

    if theme_name:
        if keep_theme_list:
            html = re.sub(r'data-theme-base\s*=\s*"[^"]*"', '', html)
        else:
            html = re.sub(r'data-themes\s*=\s*"[^"]*"', f'data-themes="{theme_name}"', html)
            html = re.sub(r'data-theme-base\s*=\s*"[^"]*"', '', html)

    html = re.sub(r'\n{3,}', '\n\n', html)
    out.write_text(html, encoding='utf-8')

    problems = verify_on_disk(out, len(inlined))
    size = out.stat().st_size if out.is_file() else 0
    for p in inlined:
        print(f'  内联 {p}')
    if problems:
        for p in problems:
            print(f'✗ {p}', file=sys.stderr)
        return 1
    print(f'✓ 单文件：{out}  ({size / 1024:.0f} KB, 内联 {len(inlined)} 个资源)')
    if theme_name:
        print(f'  主题：{theme_name}（已收敛，T 键不再换主题）')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description='把 deck 内联成单文件 HTML')
    ap.add_argument('src', help='源 deck 的 index.html（其中引用 ../assets/*.css|js）')
    ap.add_argument('-o', '--out', help='输出路径（默认 <src stem>-single.html）')
    ap.add_argument('--keep-theme-list', action='store_true',
                    help='保留 data-themes 多主题列表（仅当输出目录旁仍带 themes/ 时用）')
    ap.add_argument('--assets', default=str(Path(__file__).resolve().parent.parent / 'assets'),
                    help='资产根目录：href 以 assets/ 或 ../assets/ 开头时按它解析（默认本 skill 的 assets/）')
    ap.add_argument('--force', action='store_true', help='输出已存在时覆盖（先在同目录留 .bak 基线）')
    ap.add_argument('--json', action='store_true', help='末行输出机器可读摘要')
    ap.add_argument('--allow-punct', action='store_true',
                    help='中文半角标点降级为警告（罗蛇 T03；只有在「这段本来就是要保留的半角」时才用，'
                         '且在交付摘要里说明理由）')
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    out = Path(args.out).expanduser() if args.out else src.with_name(src.stem + '-single.html')
    out = out.resolve()
    assets_root = Path(args.assets).expanduser().resolve() if args.assets else None

    problems = validate(src, out, assets_root)
    if problems:
        for p in problems:
            print(f'✗ {p}', file=sys.stderr)
        return 2

    if out.exists() and not args.force:
        size = out.stat().st_size
        print(f'= 已存在，跳过：{out}（{size / 1024:.0f} KB；要覆盖加 --force）')
        if args.json:
            print(json.dumps({'ok': True, 'skipped': True, 'out': str(out), 'bytes': size},
                             ensure_ascii=False))
        return 0

    if out.exists():
        bak = out.with_name(f'{out.name}.bak-{time.strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(out, bak)
        print(f'  回滚基线：{bak}')

    code = build(src, out, args.keep_theme_list, assets_root, args.allow_punct)
    if args.json:
        print(json.dumps({'ok': code == 0, 'skipped': False, 'out': str(out),
                          'bytes': out.stat().st_size if out.is_file() else 0},
                         ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
