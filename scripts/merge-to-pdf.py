#!/usr/bin/env python3
"""merge-to-pdf.py — 把逐页 PNG 合成一个 PDF（每页一张整幅图）。

用法：
    python3 merge-to-pdf.py <deck-dir> [-o out.pdf] [--dpi 150] [--force] [--json]

- 页序＝文件名 `NN-` 前缀数字，不看 mtime
- 先转 RGB 再落盘：带 alpha 的 PNG 直接进 PDF 会被某些阅读器渲染成黑底
- --dpi 只影响 PDF 页面物理尺寸的换算（像素尺寸不变），打印时按这个值缩放
- validate → 写 → **回读**：本机没有 pypdf/fitz，故按原始字节数 `/Type /Page` 对象
  与 `startxref`，两者都对才算成功；幂等：已存在且无 `--force` 就跳过
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

NUM_RE = re.compile(r'^(\d+)-')


def collect(deck: Path) -> list[Path]:
    pngs = [p for p in deck.glob('*.png') if NUM_RE.match(p.name)]
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
    """回读：数 PDF 里的页对象，并确认有 startxref。

    ⚠️ 不能直接数 `/Type /Page`：页树节点是 `/Type /Pages`，会被一起数进去而多报一页
    （2026-11-10 实测：5 页 PDF 首版判成 6 页）。必须减去 `/Pages` 节点。
    """
    problems = []
    if not out.is_file() or out.stat().st_size == 0:
        return ['输出 PDF 不存在或为空']
    data = out.read_bytes()
    pages = ((data.count(b'/Type /Page') - data.count(b'/Type /Pages'))
             + (data.count(b'/Type/Page') - data.count(b'/Type/Pages')))
    if pages != expected:
        problems.append(f'回读页数不符：{pages} != {expected}')
    if b'startxref' not in data[-2048:]:
        problems.append('PDF 尾部缺 startxref（文件可能被截断）')
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description='PNG 逐页 → PDF')
    ap.add_argument('deck_dir')
    ap.add_argument('-o', '--out')
    ap.add_argument('--dpi', type=int, default=150)
    ap.add_argument('--force', action='store_true', help='输出已存在时覆盖（先留 .bak 基线）')
    ap.add_argument('--json', action='store_true', help='末行输出机器可读摘要')
    args = ap.parse_args()

    deck = Path(args.deck_dir).expanduser().resolve()
    pngs = collect(deck) if deck.is_dir() else []
    out = Path(args.out).expanduser() if args.out else deck / (deck.name + '.pdf')
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

    pages = []
    for p in pngs:
        with Image.open(p) as im:
            pages.append(im.convert('RGB'))
    if len({p.size for p in pages}) > 1:
        print('! 页面尺寸不一致，PDF 会按各自尺寸混排', file=sys.stderr)

    pages[0].save(out, 'PDF', resolution=args.dpi, save_all=True, append_images=pages[1:])
    problems = verify_output(out, len(pages))
    if problems:
        for p in problems:
            print(f'✗ {p}', file=sys.stderr)
        return 1
    print(f'✓ PDF：{out}（{len(pages)} 页，{args.dpi} dpi；已回读核对）')
    if args.json:
        print(json.dumps({'ok': True, 'skipped': False, 'out': str(out),
                          'pages': len(pages), 'dpi': args.dpi,
                          'bytes': out.stat().st_size}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
