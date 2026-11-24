#!/usr/bin/env python3
"""梁架闸：14 族说好了，就别悄悄回涨。

判据（每条都能数）：
  L1 族与文件一一对应：`_families.json` 的 key 集合 == `assets/layouts/*.html` 的 stem 集合
  L2 段与式一一对应：族页每个 `<section data-style>` 的 data-style 集合 == `styles`，
     且段数 == `styles` 长度（v1.2.36 起 `of` 只当「旧名别复活」的针，不再等于段数）
  L3 旧名不再有文件：并掉的 36 式不得以 `<stem>.html` 复活
  L4 旧名不再进文档：文档里不再把旧 stem 当版式名用（会误导下一个读的人）
  L5 离线可跑：族页里的 `<script src>` 不许指 https（CDN 在离线时是空白页）
  L6 vendor 齐：被引用的本地库文件真的在 `assets/vendor/`
  L7 结构类有样式：族页里用到的 class，必须在 base.css / layouts.css / 主题里真有定义
     （这条是补欠账来的：flow / arch / steps / gal / cmp 这些类名一直没样式，
       打开族页就是一列竖排文字，肉眼很难发现，闸能一天扫完）

用法：python3 scripts/check-layouts.py [--json]
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAY = ROOT / 'assets' / 'layouts'
FAM = LAY / '_families.json'
DOCS = [ROOT / 'SKILL.md', ROOT / 'README.md', ROOT / 'SELFTEST.md'] + \
       sorted((ROOT / 'references').glob('*.md'))

problems = []


def bad(msg):
    problems.append(msg)


def main():
    ap = argparse.ArgumentParser(description='梁架闸：族/式/旧名/离线/vendor 五条')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    if not FAM.is_file():
        print('✗ 缺 assets/layouts/_families.json（归并表的唯一正本）')
        return 1
    fam = json.loads(FAM.read_text(encoding='utf-8'))['families']
    files = {p.stem for p in LAY.glob('*.html')}

    if set(fam) != files:
        bad('L1 族与文件不符：缺文件 %s；多文件 %s' % (sorted(set(fam) - files), sorted(files - set(fam))))

    old = set()
    kept = set()
    for k, v in fam.items():
        p = LAY / f'{k}.html'
        if not p.is_file():
            continue
        src0 = p.read_text(encoding='utf-8')
        n = len(re.findall(r'<section\b', src0))
        got = re.findall(r'<section[^>]*data-style="([^"]*)"', src0)
        want = v.get('styles') or []
        if len(got) != n:
            bad('L2 %s 有 %d 段但只有 %d 段写了 data-style（每段都要标）' % (k, n, len(got)))
        elif set(got) != set(want) or len(got) != len(want):
            bad('L2 %s 段上的 data-style 是 %s，归并表 styles 写 %s' % (k, sorted(got), sorted(want)))
        old |= set(v['of'])
        kept |= set(v.get('keep') or [])
        kept |= set(want)
        src = p.read_text(encoding='utf-8')
        for m in re.findall(r'<script[^>]*src="([^"]+)"', src):
            if m.startswith('http'):
                bad('L5 %s 还指着外网 %s（离线打开是空白）' % (k, m))
            elif 'assets/vendor/' in m:
                vf = ROOT / m.split('assets/vendor/', 1)[1].replace('/../', '/')
                vf = (ROOT / 'assets' / 'vendor' / m.split('assets/vendor/', 1)[1])
                if not vf.is_file():
                    bad('L6 %s 引用的 %s 不存在' % (k, vf.name))

    revived = sorted(s for s in old - set(fam) if (LAY / f'{s}.html').exists())
    if revived:
        bad('L3 旧名又长回来了：%s' % revived)

    # 旧名里挑不会被日常用语撞上的那些来查文档
    needles = sorted(s for s in old - set(fam) if ('-' in s or s in {
        'bullets', 'thanks', 'cta', 'timeline', 'roadmap', 'mindmap', 'terminal', 'toc'}))
    for d in DOCS:
        if not d.is_file():
            continue
        text = d.read_text(encoding='utf-8')
        for s in needles:
            if s in kept:
                continue  # 仍作为参数名／旧 stem 对照出现的，不算「当版式名用」
            if '`%s`' % s in text:
                bad('L4 %s 仍把旧名 `%s` 当版式名用（应写族名，对照表在 _families.json）'
                    % (d.relative_to(ROOT), s))

    # L7：族页用到的 class 必须有样式
    css_text = ''.join((ROOT / f).read_text(encoding='utf-8') for f in [
        'assets/base.css', 'assets/layouts.css', 'assets/animations/animations.css'])
    css_text += ''.join(p.read_text(encoding='utf-8') for p in (ROOT / 'assets' / 'themes').rglob('*.css'))
    defined = set(re.findall(r'\.([A-Za-z][\w-]{0,30})', css_text))
    # 语义标记与运行时状态不算「类样式」：tc/center 是排版开关，cta 是页角色
    allow = {'language-javascript', 'language-python', 'language-bash', 'svelte', 'vue', 'cta', 'tc', 'notes'}
    for k in sorted(fam):
        p = LAY / f'{k}.html'
        if not p.is_file():
            continue
        body = p.read_text(encoding='utf-8').split('<body', 1)[-1]
        used = set()
        for m in re.finditer(r'class="([^"]+)"', body):
            used |= set(m.group(1).split())
        miss = sorted(c for c in used if c not in defined and c not in allow)
        if miss:
            bad('L7 %s 用了没样式的类：%s（补 assets/layouts.css 或改用已有类）' % (k, miss))

    summary = {'families': len(fam), 'styles': sum(len(v.get('styles') or v['of']) for v in fam.values()),
               'problems': len(problems), 'verdict': 'pass' if not problems else 'blocked'}
    for x in problems:
        print('✗ ' + x)
    if a.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print('梁架闸：%d 族 / %d 式 —— %s' % (summary['families'], summary['styles'],
                                            '可以交付' if not problems else '不许交付'))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
