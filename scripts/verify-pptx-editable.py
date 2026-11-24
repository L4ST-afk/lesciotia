#!/usr/bin/env python3
"""verify-pptx-editable.py — 判一份 .pptx 到底可不可编辑（不是"看起来像 pptx"）。

用法：
    python3 verify-pptx-editable.py <deck.pptx> [--json] [--min-text N]
                                    [--allow-fullbleed-picture]

为什么需要这个脚本：A 出口（逐页 PNG 合成）产出的 .pptx 每页就是一张全幅图，
文件名、后缀、页数全部正确，PowerPoint 也能打开——单看"是不是 pptx"完全判不出来。
本脚本读的是**形状层**：每页有没有可改的文本形状、有没有整页铺满的单张图片。

判据（任一不满足即 FAIL）：
- 文件能开、至少 1 页
- 每页文本形状数 ≥ --min-text（默认 1），且文本非空
- 不存在「单张图片铺满整页且该页无任何文本」的页（除非 --allow-fullbleed-picture）

退出码：0 通过 / 1 判失败 / 2 参数或文件问题。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

FULLBLEED_RATIO = 0.9  # 图片面积占页面面积 ≥ 90% 视为"铺满"


def _area(shape) -> float:
    try:
        return float(shape.width or 0) * float(shape.height or 0)
    except (TypeError, ValueError):
        return 0.0


def inspect(path: Path, min_text: int, allow_fullbleed: bool) -> dict:
    prs = Presentation(str(path))
    page_area = float(prs.slide_width) * float(prs.slide_height)
    slides = []
    problems = []
    for idx, slide in enumerate(prs.slides, 1):
        texts = []
        pictures = []
        for sh in slide.shapes:
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pictures.append(_area(sh))
            elif getattr(sh, 'has_text_frame', False):
                if sh.text_frame and sh.text_frame.text.strip():
                    texts.append(sh.text_frame.text.strip())
        fullbleed = bool(pictures) and page_area > 0 and max(pictures) / page_area >= FULLBLEED_RATIO
        slides.append({
            'slide': idx,
            'text_shapes': len(texts),
            'pictures': len(pictures),
            'fullbleed_picture': fullbleed,
            'first_text': (texts[0][:40] if texts else ''),
        })
        if len(texts) < min_text:
            problems.append(f'第 {idx} 页可编辑文本形状 {len(texts)} 个，少于要求的 {min_text} 个')
        if fullbleed and not texts and not allow_fullbleed:
            problems.append(f'第 {idx} 页是整页位图（图片占页 {max(pictures) / page_area:.0%}，无文本）——这是 A 出口的合图件，不是可编辑 pptx')
    if not slides:
        problems.append('这份 pptx 没有任何幻灯片')
    return {'ok': not problems, 'slides': len(slides), 'details': slides, 'problems': problems}


def main() -> int:
    ap = argparse.ArgumentParser(description='判 pptx 是否真可编辑（形状层判据）')
    ap.add_argument('pptx')
    ap.add_argument('--min-text', type=int, default=1, help='每页最少文本形状数（默认 1）')
    ap.add_argument('--allow-fullbleed-picture', action='store_true',
                    help='允许纯图页（仅在明知是 A 出口合图件时用）')
    ap.add_argument('--json', action='store_true', help='末行输出机器可读摘要')
    args = ap.parse_args()

    path = Path(args.pptx).expanduser()
    if not path.is_file():
        print(f'✗ 文件不存在：{path}', file=sys.stderr)
        return 2
    if path.stat().st_size == 0:
        print(f'✗ 文件为空：{path}', file=sys.stderr)
        return 2
    try:
        report = inspect(path, args.min_text, args.allow_fullbleed_picture)
    except Exception as exc:  # 打不开就是打不开，别把异常当结论
        print(f'✗ 打不开这份 pptx：{type(exc).__name__}: {exc}', file=sys.stderr)
        return 2

    for d in report['details']:
        mark = '✗' if d['fullbleed_picture'] and d['text_shapes'] == 0 else '·'
        print(f"  {mark} 第 {d['slide']} 页：文本 {d['text_shapes']} / 图片 {d['pictures']}"
              f"{' / 整页位图' if d['fullbleed_picture'] else ''}"
              f"{'  «' + d['first_text'] + '»' if d['first_text'] else ''}")

    if report['problems']:
        for p in report['problems']:
            print(f'✗ {p}', file=sys.stderr)
        if args.json:
            print(json.dumps(report, ensure_ascii=False))
        return 1

    print(f"✓ 可编辑：{path}（{report['slides']} 页，每页 ≥{args.min_text} 个文本形状，无整页位图）")
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
