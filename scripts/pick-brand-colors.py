#!/usr/bin/env python3
"""配色取色器：把一组成套的强调色按 ΔL* 拉开档位，只动明度、不动色相。

为什么要有这件（2026-11-20 增）：

`check-theme-colors.py` 只判「这组色行不行」，判不出「该怎么改」。四个 B 出口主题手工调色时，
紫与珊瑚的 L* 只差 0.7、三线色挤在 1.0–2.4 级——转灰全并级。手调靠眼睛，眼睛判不出 L*。
这件反过来做：给定已定的色相（品牌就是那几个色，⛔ 不改色相），把明度重新分配到等间距档位，
输出新 hex 与逐对 ΔL*，再交给体检脚本验收。

  python3 scripts/pick-brand-colors.py --colors '#1a7fb8,#8b7ce8,#e0632f' --bg '#eaf7ff'
  python3 scripts/pick-brand-colors.py --colors '#4a7091,#7d5a86,#a34f66' --gap 11 --json

规则：
· 排序按现有 L*，档位顺次不动——谁深谁浅的语义关系保留，⛔ 不许把「轻警示」调成最亮。
· 目标档位围绕这组色的 L* 均值等距展开，间距 = --gap（默认 10），越界夹到 20–90。
· 只改明度：色相与饱和度照原色，⛔ 不顺手改色相（改色相是重新设计，不是取色）。
· 同一色相之间不算暧昧带；不同色相之间 ΔH 落 15–40° 会单独提示。
"""
from __future__ import annotations

import argparse
import colorsys
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "ctc", os.path.join(HERE, "check-theme-colors.py"))
_ctc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ctc)

parse_hex = _ctc.parse_hex
lstar = lambda h: _ctc.lstar(parse_hex(h))
hue = lambda h: _ctc.hue(parse_hex(h))
contrast = lambda a, b: _ctc.contrast(parse_hex(a), parse_hex(b))
hue_delta = lambda a, b: _ctc.hue_delta(hue(a), hue(b))

AMBIG_LO, AMBIG_HI = 15.0, 40.0


def hls(h):
    r, g, b = (x / 255.0 for x in parse_hex(h))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360.0, ss, ll


def at_lstar(h: str, target: float) -> str:
    """同色相同饱和度、明度逼到目标 L*（二分 60 次，够 0.1 级）。"""
    hh, ss, _ = hls(h)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        r, g, b = colorsys.hls_to_rgb(hh / 360.0, mid, ss)
        cand = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
        if lstar(cand) < target:
            lo = mid
        else:
            hi = mid
    return cand


def pick(colors, gap, lo_clamp=20.0, hi_clamp=90.0):
    """排序→等距分配目标 L*→反解 hex。8 位取整会吃掉零点几级，所以留余量并回查。"""
    cols = sorted(colors, key=lambda h: lstar(h))
    n = len(cols)
    mean = sum(lstar(h) for h in cols) / n
    for pad in (0.6, 1.2, 1.8, 2.4):
        targets = []
        for i in range(n):
            t = mean + (i - (n - 1) / 2.0) * (gap + pad)
            targets.append(min(hi_clamp, max(lo_clamp, t)))
        for i in range(1, n):                       # 夹边界后可能并档，从深往浅重拉
            if targets[i] - targets[i - 1] < gap + pad - 0.01:
                targets[i] = min(hi_clamp, targets[i - 1] + gap + pad)
        out = [at_lstar(c, t) for c, t in zip(cols, targets)]
        if min(abs(lstar(out[i]) - lstar(out[j]))
               for i in range(n) for j in range(i + 1, n)) >= gap:
            return cols, out
    return cols, out


def audit_pairs(out, bg):
    rows = []
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            d = abs(lstar(out[i]) - lstar(out[j]))
            dh = hue_delta(out[i], out[j])
            rows.append(dict(a=out[i], b=out[j], dL=round(d, 1), dH=round(dh, 1),
                             ok=d >= 10.0 and not (AMBIG_LO <= dh <= AMBIG_HI)))
    worst = min((r["dL"] for r in rows), default=None)
    bad = [r for r in rows if not r["ok"]]
    return rows, worst, bad


def main():
    ap = argparse.ArgumentParser(description="成套强调色取色：只调明度、不动色相")
    ap.add_argument("--colors", required=True, help="逗号分隔的 hex，如 '#a,#b,#c'")
    ap.add_argument("--gap", type=float, default=10.0, help="相邻档位 ΔL*（默认 10）")
    ap.add_argument("--bg", default="", help="底色；给了就顺带报对底对比与 ΔL*")
    ap.add_argument("--json", action="store_true", help="末行追加机器摘要")
    a = ap.parse_args()

    colors = [c.strip() for c in a.colors.split(",") if c.strip()]
    for c in colors:
        parse_hex(c)                       # 早失败：非法 hex 直接抛
    if len(colors) < 2:
        sys.exit("至少给两个色才能拉档位")

    cols, out = pick(colors, a.gap)
    rows, worst, bad = audit_pairs(out, a.bg)

    print("取色结果（只改明度，色相与饱和度照原色）：\n")
    print("| 原色 | L* | 新色 | L* | 色相 |")
    print("|---|---|---|---|---|")
    for old, new in zip(cols, out):
        print("| %s | %.1f | %s | %.1f | %.0f° |"
              % (old, lstar(old), new, lstar(new), hue(new)))

    print("\n逐对：")
    for r in rows:
        print("  %s ↔ %s：ΔL* %.1f，ΔH %.0f° %s"
              % (r["a"], r["b"], r["dL"], r["dH"], "✅" if r["ok"] else "⚠️"))
    if a.bg:
        print("\n对底 %s：" % a.bg)
        for new in out:
            c = contrast(new, a.bg)
            print("  %s  对比 %.2f:1  ΔL* %.1f %s"
                  % (new, c, abs(lstar(new) - lstar(a.bg)),
                     "" if c >= 3.0 else "⚠️ 做填充/描边需 3:1"))

    if bad:
        print("\n⚠️ 仍有 %d 对不过（ΔL* <10 或落在 15–40° 暧昧带）：调 --gap 或重新定色相"
              % len(bad))
    else:
        print("\n✅ 最小 ΔL* %.1f，全部过线。" % (worst or 0))

    if a.json:
        print(json.dumps(dict(gap=a.gap, colors=out, pairs=rows,
                              min_dL=worst, ok=not bad), ensure_ascii=False))


if __name__ == "__main__":
    main()
