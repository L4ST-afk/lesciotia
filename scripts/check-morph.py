#!/usr/bin/env python3
"""来雪亭Lesciotia :: check-morph.py — morph 的结构判别：配得上吗，配对了吗

用法：
    python3 scripts/check-morph.py deck.pptx
    python3 scripts/check-morph.py deck.pptx --json

为什么要有这个闸：morph 是**唯一**一项本库无法实机核验的能力——播放效果只有真正的
PowerPoint 播放器能给答案，而 `officecli` 的截图是静帧、`validate` 只证 schema。
同类项目里，做 morph 最深的那个 fork（jsamuel1/PptxGenJS 的 auto-animate-morph 分支）
在自己 README 的验收清单里也只把「schema 通过」打了勾，「Verified to animate in PowerPoint」
那一行是空的。**连作者都只能验到结构**，我们也就把能验的验干净，剩下的明说。

能验的三件事：
1. `p159:morph` 必须包在 `mc:AlternateContent` 里，且 `p159` 前缀声明在**那个元素**上
   （写在别处＝`prefix not defined`，PowerPoint 宽容所以不探针发现不了）。
2. `p14:dur` 必须在 schema 范围内（1..2147483647）。
3. **配对**：morph 的补间靠跨页同名对象。这一页声明了 morph，下一张页里至少要有
   一个同名形状；一个都配不上，说明这页的 morph 等于 fade，是「声明了没生效」。

⛔ 本闸不判「动画好不好看」，也不判「播放时是不是真的补间了」。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_P14 = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
NS_P159 = 'http://schemas.microsoft.com/office/powerpoint/2015/09/main'
NS_MC = 'http://schemas.openxmlformats.org/markup-compatibility/2006'


def slide_names(slide) -> list[str]:
    return [sh.name for sh in slide.shapes]


def morph_info(slide):
    """→ (是否 morph, dur 或 None, 报错或 None)"""
    root = slide.element
    alt = root.findall('.//{%s}AlternateContent' % NS_MC)
    for a in alt:
        choice = a.find('{%s}Choice' % NS_MC)
        if choice is None:
            continue
        if choice.get('Requires') != 'p159':
            continue
        if a.get('{%s}Ignorable' % NS_MC) and 'p159' not in a.get('{%s}Ignorable' % NS_MC):
            # Ignorable 没带 p159：Office 会拒绝渲染整段（不是错，是静默丢弃）
            return True, None, 'mc:AlternateContent 的 Ignorable 里没有 p159（会被静默丢弃）'
        # 前缀要么声明在 AlternateContent 上，要么声明在文档根上
        # morph 是 p:transition 的**子元素**，不是 Choice 的直接子元素——这一层结构
        # 一开始读错了，于是每页都报「没有 p159:morph」，而文件其实是对的。
        if choice.find('.//{%s}morph' % NS_P159) is None:
            return True, None, 'mc:Choice 里没有 p159:morph（应在 p:transition 之下）'
        tr = choice.find('.//{%s}transition' % NS_P)
        if tr is None:
            return True, None, 'mc:Choice 里没有 p:transition'
        dur = tr.get('{%s}dur' % NS_P14)
        if dur is None:
            return True, None, 'p:transition 上没有 p14:dur'
        try:
            ms = int(dur)
        except ValueError:
            return True, None, 'p14:dur 不是整数：%r' % dur
        if not (1 <= ms <= 2147483647):
            return True, None, 'p14:dur 超出 schema 范围：%d' % ms
        return True, ms, None
    return False, None, None


def check(path: Path) -> dict:
    from pptx import Presentation
    prs = Presentation(str(path))
    report = {'slides': len(prs.slides._sldIdLst), 'morph_pages': 0,
              'errors': [], 'notes': [], 'pairs': []}
    for idx, slide in enumerate(prs.slides, 1):
        is_morph, ms, err = morph_info(slide)
        if not is_morph:
            continue
        report['morph_pages'] += 1
        if err:
            report['errors'].append('第 %d 页：%s' % (idx, err))
            continue
        # 配对：拿下一张页的同名形状对
        nxt = None
        for j, s2 in enumerate(prs.slides, 1):
            if j == idx + 1:
                nxt = s2
                break
        if nxt is None:
            # 最后一页声明 morph＝这页没东西可补，无害但明确是空转。
            # 不当红：全册默认 morph 时它必然出现，红就成了噪声。
            report['notes'].append('第 %d 页是最后一页，morph 空转（没有下一张可配）' % idx)
            continue
        mine, theirs = slide_names(slide), slide_names(nxt)
        common = sorted(set(mine) & set(theirs))
        report['pairs'].append({'from': idx, 'to': idx + 1, 'dur_ms': ms,
                                'from_shapes': len(mine), 'to_shapes': len(theirs),
                                'paired': common, 'unpaired_from': sorted(set(mine) - set(theirs))})
        if not common:
            report['errors'].append(
                '第 %d 页声明了 morph，与第 %d 页没有一个同名形状 → 实际会退化成 fade'
                % (idx, idx + 1))
    return report


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='morph 的结构判别（不判播放效果）')
    ap.add_argument('pptx')
    ap.add_argument('--json', help='把结论写成 JSON 到这个路径')
    args = ap.parse_args()
    path = Path(args.pptx).expanduser().resolve()
    if not path.is_file():
        print(f'✗ 不存在：{path}', file=sys.stderr)
        return 2
    rep = check(path)
    if rep['morph_pages'] == 0:
        print('  morph：0 页（这份 deck 没声明 morph，不适用）')
    for p in rep['pairs']:
        print('  第 %d→%d 页：配对 %d 个同名形状（%s），未配对 %d 个'
              % (p['from'], p['to'], len(p['paired']), '、'.join(p['paired'][:6]) or '无',
                 len(p['unpaired_from'])))
    for n in rep['notes']:
        print('  · ' + n)
    for e in rep['errors']:
        print('✗ ' + e, file=sys.stderr)
    print('  ⚠ 播放效果未核验：本机没有能播放并回报的工具（officecli 截图是静帧、validate 只证 schema）')
    if args.json:
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding='utf-8')
    return 1 if rep['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
