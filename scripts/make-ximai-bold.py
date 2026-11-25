#!/usr/bin/env python3
"""make-ximai-bold.py — 把「字制区喜脉喜欢体」做成万航渡的标题字（可复现）。

用法：
  python3 scripts/make-ximai-bold.py \
      --src "/path/to/字制区喜脉喜欢体.ttf" \
      --width 100 \
      --out assets/fonts/ximai/WanhangXimaiBold-Subset.woff2

做三件事（顺序不可换）：
  1) 裁字：GB2312 一级字（3755）+ ASCII + 常用中文标点，pyftsubset --no-hinting；
  2) 机械加粗：对每个简单字形沿外轮廓等距外扩 width/2（stroke round join 后与原形并集），
     原字 upem=2048，故 width 用 2048 制；+20/1000 em 在 2048 制下是 41，本次实取 100（每边约 2.4%），
     再用 cu2qu 写回二次曲线——不是把字形横向放大的「伪粗」，细起笔仍是细的；
  3) 改名：OFL 保留字名条款要求修改版改名，family 记 Wanhang Ximai，原字名只留在版权行。

⚠️ 只有一档（usWeightClass 700）。@font-face 声明 700–900，标题写 800 也不会合成假粗。

原字来源：字制区「喜脉喜欢体」v1.0（FontQu Smile，SIL OFL 1.1，字体 name 表内附全文），
本机原在外部字体库 `字体/字制区喜脉喜欢体1.00/`。重跑本脚本需要自备该 ttf，路径不写死。
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pathops
from fontTools.pens.basePen import BasePen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

PUNCT = '　、。〃々〈〉《》「」『』【】〔〕〖〗！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～·—…‘’“”％‰℃°'


def charset_path(tmp: Path) -> Path:
    chars = set()
    for b1 in range(0xB0, 0xD8):
        for b2 in range(0xA1, 0xFF):
            try:
                chars.add(bytes([b1, b2]).decode('gb2312'))
            except UnicodeDecodeError:
                pass
    chars.update(chr(i) for i in range(0x20, 0x7F))
    chars.update(PUNCT)
    p = tmp / 'chars.txt'
    p.write_text(''.join(sorted(chars)), encoding='utf-8')
    return p


class PathPen(BasePen):
    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.path = pathops.Path()

    def _moveTo(self, p): self.path.moveTo(*p)

    def _lineTo(self, p): self.path.lineTo(*p)

    def _curveToOne(self, p1, p2, p3): self.path.cubicTo(*p1, *p2, *p3)

    def _qCurveToOne(self, p1, p2): self.path.quadTo(*p1, *p2)

    def _closePath(self): self.path.close()


def embolden(ttf: Path, width: float) -> int:
    f = TTFont(ttf)
    glyf, gs = f['glyf'], f.getGlyphSet()
    done = 0
    skipped = 0
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.isComposite() or not getattr(g, 'numberOfContours', 0):
            continue
        pen = PathPen(gs)
        gs[name].draw(pen)
        outline = pen.path
        if not outline.contours:
            continue
        ring = pathops.Path()
        ring.addPath(outline)
        ring.fillType = pathops.FillType.WINDING
        ring.stroke(width, 0, 1, 4)          # cap=butt, join=round, miter=4
        ring.convertConicsToQuads(0.1)
        outline.fillType = pathops.FillType.WINDING
        try:
            union = pathops.op(outline, ring, pathops.PathOp.UNION)
        except pathops.PathOpsError:
            # 宽描边在笔画交叉处会自交，Lightning 的 union 偶尔失败；
            # 退回「先 simplify 再并」仍然失败就放弃这个字形（保持原形，宁可不变粗）
            try:
                union = pathops.op(outline, pathops.simplify(ring), pathops.PathOp.UNION)
            except pathops.PathOpsError:
                skipped += 1
                continue
        tp = TTGlyphPen(None)
        union.draw(Cu2QuPen(tp, 0.2, reverse_direction=True))
        ng = tp.glyph()
        try:
            ng.recalcBounds(glyf)
        except Exception:
            pass
        glyf[name] = ng
        done += 1
    f.save(ttf)
    if skipped:
        print(f'  note: {skipped} 个字形的并集失败，保留原形', file=sys.stderr)
    return done


def rename(ttf: Path) -> None:
    f = TTFont(ttf)
    name = f['name']
    for nid in (1, 2, 3, 4, 5, 6, 13, 14, 16, 17, 18, 20, 21, 22):
        name.removeNames(nameID=nid)

    def add(nid, s, lang=0x409):
        name.setName(s, nid, 3, 1, lang)

    add(1, 'Wanhang Ximai'); add(2, 'Bold'); add(4, 'Wanhang Ximai Bold')
    add(6, 'WanhangXimai-Bold'); add(3, '1.083;WX;WanhangXimai-Bold')
    add(5, 'Version 1.083; Wanhang derivative 2026-11-21, mechanically emboldened +20/1000 em')
    add(13, 'SIL Open Font License 1.1. Modified version (subset + mechanical emboldening); '
            'the Reserved Font Name of the original (字制区喜脉体 / ZiZhiQuXiMaiTi) is not used. See OFL.txt.')
    add(14, 'https://www.fontqu.com/ (original); derivative by 来雪亭Lesciotia 2026-11-21')
    add(1, '万航渡喜脉体', lang=0x804); add(2, '加粗', lang=0x804); add(4, '万航渡喜脉体 加粗', lang=0x804)

    head = f['head']
    f['OS/2'].usWinAscent = max(f['OS/2'].usWinAscent, head.yMax + 10)
    f['OS/2'].usWinDescent = max(f['OS/2'].usWinDescent, -head.yMin + 10)
    f['OS/2'].usWeightClass = 700
    f['OS/2'].fsSelection = (f['OS/2'].fsSelection & ~0x40) | 0x20
    f['head'].macStyle |= 1
    if 'DSIG' in f:
        del f['DSIG']          # 改字后原数字签名失效，保留会误导
    f.flavor = 'woff2'
    f.save(ttf)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='原字制区喜脉体 otf/ttf')
    ap.add_argument('--out', required=True, help='输出 woff2')
    ap.add_argument('--width', type=float, default=20.0, help='加粗量（stroke 宽度，每边取一半）')
    args = ap.parse_args()

    src = Path(args.src)
    out = Path(args.out)
    if not src.exists():
        print(f'error: 找不到原字 {src}', file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        subset = tmp / 'subset.ttf'
        subprocess.run([
            'pyftsubset', str(src), f'--text-file={charset_path(tmp)}',
            f'--output-file={subset}', '--layout-features=*', '--no-hinting',
        ], check=True)
        n = embolden(subset, args.width)
        rename(subset)
        out.write_bytes(subset.read_bytes())
    print(f'ok: {n} 个字形加粗 → {out} ({out.stat().st_size // 1024} KB)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
