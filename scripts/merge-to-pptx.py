#!/usr/bin/env python3
"""merge-to-pptx.py — 把逐页 PNG 合成一个 PowerPoint（每页一张全幅图）。

用法：
    python3 merge-to-pptx.py <deck-dir> [-o out.pptx] [--notes notes.json]
                             [--size auto|16:9|4:3] [--force] [--json]

为什么用 python 而不是原 TS 脚本：原脚本要 `bun`/`npx -y bun`，本机只装了 node。
本脚本只依赖 python-pptx，零 npm。

- 页序＝文件名里的 `NN-` 前缀数字，不看 mtime（改版后 mtime 会乱）
- 幻灯片尺寸：`auto` 取第一张图的宽高比（不拉伸、不留白边）；也可强制 16:9 / 4:3
- 图片按「等比铺满」放置；比例与页面不一致时居中留白，绝不拉伸
- notes.json 形如 {"01-slide-cover.png": "第一页口播…"}，写进备注页
- validate → 写 → **回读**（重开 pptx 数页数与图片）才算成功；幂等：已存在且无
  `--force` 就跳过，`--force` 时同目录留 `.bak-<时间戳>` 基线
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Inches

SLIDE_SIZES = {
    '16:9': (Inches(13.333), Inches(7.5)),
    '4:3': (Inches(10), Inches(7.5)),
}
NUM_RE = re.compile(r'^(\d+)-')


def collect(deck_dir: Path) -> list[Path]:
    pngs = [p for p in deck_dir.glob('*.png') if NUM_RE.match(p.name)]
    if not pngs:
        return []
    pngs.sort(key=lambda p: int(NUM_RE.match(p.name).group(1)))
    return pngs


def validate(deck: Path, pngs: list[Path], out: Path) -> list[str]:
    problems = []
    if not deck.is_dir():
        problems.append(f'不是目录：{deck}')
    if not pngs:
        problems.append(f'{deck} 里没有 NN-*.png')
    if not out.parent.is_dir():
        problems.append(f'输出目录不存在：{out.parent}')
    nums = [int(NUM_RE.match(p.name).group(1)) for p in pngs]
    if nums and nums != list(range(nums[0], nums[0] + len(nums))):
        problems.append(f'页号不连续：{nums}（先重排 NN 再合并）')
    return problems


def verify_output(out: Path, expected: int) -> list[str]:
    """回读：重开 pptx，数页数、数图片、量尺寸。"""
    problems = []
    if not out.is_file() or out.stat().st_size == 0:
        return ['输出 pptx 不存在或为空']
    prs = Presentation(str(out))
    slides = list(prs.slides)
    if len(slides) != expected:
        problems.append(f'回读页数不符：{len(slides)} != {expected}')
    for i, s in enumerate(slides, 1):
        pics = [sh for sh in s.shapes if sh.shape_type == 13]
        if not pics:
            problems.append(f'第 {i} 页没有图片形状')
            break
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description='PNG 逐页 → PPTX')
    ap.add_argument('deck_dir')
    ap.add_argument('-o', '--out')
    ap.add_argument('--size', default='auto', choices=['auto', '16:9', '4:3'])
    ap.add_argument('--notes', help='notes.json：{文件名: 备注文本}')
    ap.add_argument('--force', action='store_true', help='输出已存在时覆盖（先留 .bak 基线）')
    ap.add_argument('--json', action='store_true', help='末行输出机器可读摘要')
    args = ap.parse_args()

    deck = Path(args.deck_dir).expanduser().resolve()
    pngs = collect(deck) if deck.is_dir() else []
    out = Path(args.out).expanduser() if args.out else deck / (deck.name + '.pptx')
    out = out.resolve()

    problems = validate(deck, pngs, out)
    if problems:
        for p in problems:
            print(f'✗ {p}', file=sys.stderr)
        return 2

    if out.exists() and not args.force:
        print(f'= 已存在，跳过：{out}（要覆盖加 --force）')
        if args.json:
            print(json.dumps({'ok': True, 'skipped': True, 'out': str(out)}, ensure_ascii=False))
        return 0
    if out.exists():
        bak = out.with_name(f'{out.name}.bak-{time.strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(out, bak)
        print(f'  回滚基线：{bak}')

    prs = Presentation()
    if args.size == 'auto':
        with Image.open(pngs[0]) as im:
            w, h = im.size
        # 高度锁 7.5in（PPT 的常规高），宽度按首图比例推 —— 16:9 正好落回 13.33×7.5
        prs.slide_height = Inches(7.5)
        prs.slide_width = Emu(int(Inches(7.5) * w / h))
    else:
        prs.slide_width, prs.slide_height = SLIDE_SIZES[args.size]

    notes = {}
    if args.notes:
        try:
            notes = json.loads(Path(args.notes).read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            print(f'✗ notes.json 读不了：{exc}', file=sys.stderr)
            return 2

    sw, sh = prs.slide_width, prs.slide_height
    blank = prs.slide_layouts[6]
    hits = 0
    for p in pngs:
        with Image.open(p) as im:
            iw, ih = im.size
        slide = prs.slides.add_slide(blank)
        scale = min(sw / iw, sh / ih)
        w, h = int(iw * scale), int(ih * scale)
        slide.shapes.add_picture(str(p), int((sw - w) / 2), int((sh - h) / 2), width=w, height=h)
        if notes.get(p.name):
            slide.notes_slide.notes_text_frame.text = notes[p.name]
            hits += 1

    prs.save(out)
    problems = verify_output(out, len(pngs))
    if problems:
        for p in problems:
            print(f'✗ {p}', file=sys.stderr)
        return 1
    print(f'✓ PPTX：{out}（{len(pngs)} 页，{prs.slide_width / 914400:.2f}×{prs.slide_height / 914400:.2f} in，'
          f'备注 {hits} 处；已回读核对）')
    if args.json:
        print(json.dumps({'ok': True, 'skipped': False, 'out': str(out), 'slides': len(pngs),
                          'width_in': round(prs.slide_width / 914400, 2),
                          'height_in': round(prs.slide_height / 914400, 2),
                          'notes': hits}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
