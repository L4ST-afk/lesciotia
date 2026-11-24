#!/usr/bin/env python3
"""deck 与主题的一致性闸：交付的单文件 deck 里内联的主题 CSS 还新不新。

为什么要有（2026-11-22）：主题 CSS 一改，deck 不会自己变；此前只靠"记得重打包"，
实际出过用 11:18 旧产物截图的事故。本闸只认产物字节：
  1. 源 deck（库内 examples/decks/…）必须存在，且 <link id="theme-link"> 指到登记的主题；
  2. 交付文件里每个 <style data-from data-sha256> 的指纹，必须等于源文件当前指纹——
     不等就是"主题已改、deck 未重打包"，判失败并给出要跑的命令；
  3. 交付文件里不许残留本地 <link>/<script src>（内联没做干净）；
  4. 页数与登记值一致。

边界：交付文件不在本机时记 WARN 而不是 FAIL（可能换机器/换了输出目录），
但源与服务端登记表仍然要自洽。
"""
import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / 'assets' / 'decks.json'
STYLE_BLOCK = re.compile(r'<style\b([^>]*)>(.*?)</style>', re.S | re.I)
ATTR = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"')
LINK = re.compile(r'<link\b[^>]*?rel\s*=\s*"(?:stylesheet|Stylesheet)"[^>]*?>', re.I)
SCRIPT = re.compile(r'<script\b[^>]*?\bsrc\s*=\s*"([^"]+)"[^>]*>', re.I)
SLIDE = re.compile(r'<section\b[^>]*\bclass\s*=\s*"[^"]*\bslide\b', re.I)
NONMARKUP = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.S | re.I)
THEME_LINK = re.compile(r'<link\b[^>]*id\s*=\s*"theme-link"[^>]*href\s*=\s*"([^"]+)"', re.I)


def sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:16]


def attrs(tag_attrs: str) -> dict:
    return {m.group(1).lower(): m.group(2) for m in ATTR.finditer(tag_attrs)}


def main() -> int:
    if not REG.is_file():
        print(f'FAIL 登记表不存在：{REG.relative_to(ROOT)}')
        return 1
    data = json.loads(REG.read_text(encoding='utf-8'))
    decks = data.get('decks') or []
    if not decks:
        print('FAIL 登记表里没有 deck')
        return 1

    fails, warns, infos, checked = [], [], [], 0

    for d in decks:
        name = d.get('name') or d.get('src')
        src = ROOT / d['src']
        theme = d.get('theme')
        if not src.is_file():
            fails.append(f'{name}: 源 deck 不在库里（{d["src"]}）')
            continue
        src_text = src.read_text(encoding='utf-8', errors='replace')
        # 页数：源级也要数（2026-11-23 评审#02：原先 source 分支提前 continue，pages 从未校验）
        pages = len(SLIDE.findall(NONMARKUP.sub('', src_text)))
        if d.get('pages') and pages != d['pages']:
            fails.append(f'{name}: 源页数 {pages} ≠ 登记 {d["pages"]}')
        m = THEME_LINK.search(src_text)
        if not m:
            fails.append(f'{name}: 源里没有 id="theme-link" 的样式引用')
            continue
        href = m.group(1)
        if theme and Path(href).stem != theme:
            fails.append(f'{name}: 源引用主题 {Path(href).stem}，登记的是 {theme}')
        theme_file = (src.parent / href).resolve()
        if not theme_file.is_file():
            fails.append(f'{name}: 源里的主题文件不存在：{href}')
            continue

        if d.get('mode') == 'source' and not d.get('built'):
            infos.append(f'{name}: 源级登记、页数已校验（模板不预生成交付件，主题切换改 index.html 的 theme-link）')
            continue

        built = Path(d.get('built', '')).expanduser() if d.get('built') else None
        if built is None or not built.is_file():
            # 2026-11-23 评审#03：登记了 built 却找不到，直接判红——WARN 会让覆盖静默归零
            fails.append(f'{name}: 登记的交付文件不存在（{d.get("built")}）'
                         f' —— 要么重打包：scripts/build-deck.py {d["src"]} -o "<路径>" --force，'
                         f'要么把 built 改成库内相对路径 / 显式标 mode:"source"')
            continue

        checked += 1
        text = built.read_text(encoding='utf-8', errors='replace')
        # 2026-11-23 评审#05：指纹要逐块校，⛔ 只对主题块会让 base/fonts/animations 漏检
        seen_theme = False
        for a, body in STYLE_BLOCK.findall(text):
            at = attrs(a)
            df = at.get('data-from')
            if at.get('id') == 'theme-link' or (df or '').endswith(theme_file.name):
                seen_theme = True
            if not df:
                continue
            srcf = (src.parent / df).resolve()
            if not srcf.is_file():
                fails.append(f'{name}: 内联块 {df} 对应的源不存在（源已删或路径漂移）')
                continue
            sh = at.get('data-sha256')
            if not sh:
                fails.append(f'{name}: 内联块 {df} 缺 data-sha256（旧版 build-deck 打的，需重打包）')
            elif sh != sha16(srcf):
                fails.append(f'{name}: {df} 已改、deck 未重打包（deck {sh} ≠ 源 {sha16(srcf)}）'
                             f' —— 跑 scripts/build-deck.py {d["src"]} -o "{d["built"]}" --force')
        if not seen_theme:
            fails.append(f'{name}: 交付文件里找不到内联的主题样式块')

        # ⛔ 先剥掉 <style>/<script> 的内容再数弹：CSS 注释里就能出现「<section class="slide」的字样
        body = NONMARKUP.sub('', text)
        left_links = [t for t in LINK.findall(body) if '://' not in t and not t.startswith('data:')]
        if left_links:
            fails.append(f'{name}: 交付文件残留 {len(left_links)} 个本地 <link>（内联没做干净）')
        left_scripts = [s for s in SCRIPT.findall(body) if '://' not in s]
        if left_scripts:
            fails.append(f'{name}: 交付文件残留 {len(left_scripts)} 个本地 <script src>')
        pages = len(SLIDE.findall(body))
        if d.get('pages') and pages != d['pages']:
            fails.append(f'{name}: 页数 {pages} ≠ 登记 {d["pages"]}')

    # 2026-11-23 评审#10：未登记的 deck 源＝无人守——扫两类目录，缺登记直接红
    reg = {(ROOT / d['src']).resolve() for d in decks if d.get('src')}
    for pat in ('examples/decks/*/index.html', 'assets/full-decks/*/index.html'):
        for p in sorted(ROOT.glob(pat)):
            if p.resolve() not in reg:
                fails.append(f'未登记的 deck 源：{p.relative_to(ROOT)}'
                             f' —— 在 assets/decks.json 登记（或删掉源），否则主题漂移无人守')

    for i in infos:
        print(f'INFO {i}')
    for w in warns:
        print(f'WARN {w}')
    for f in fails:
        print(f'FAIL {f}')
    if fails:
        print(f'FAIL deck 与主题不一致：{len(fails)} 条问题（比对了 {checked} 份产物）')
        return 1
    note = f'、{len(infos)} 份源级登记' if infos else ''
    print(f'PASS deck 与主题一致：{len(decks)} 份登记、{checked} 份产物已比对{note}、0 条问题')
    return 0


if __name__ == '__main__':
    sys.exit(main())
