#!/usr/bin/env python3
"""实测每个接线处「位图到底有没有出现」，而不是只看 CSS 里写没写。

为什么需要这个：闸（B7）只核「文件名/选择器/blend/opacity 四要素在不在文件里」。
2026-11-22 实测踩到两次假绿——
  ① 拼接时少一个 `}`，整段位图规则被浏览器当成上一条规则的无效声明丢掉，
     四要素全在文件里，页面上一个字都没有；
  ② 就算层真的画出来了，tile 对比太低（amp=9），A/B 的 |Δ| 只有 1–3/255，
     接线正确但肉眼等于没接。
两条都不是文本能查出来的，只能渲染出来量像素。

做法：对 registry 里每个 used_by 生成一张 A/B 图（A = `<sel>--flat` 纯 CSS，
B = 默认态），headless Chrome 截图，量两个指标：
  · 高频增量  Δhf = hf(B) - hf(A)（灰度级）—— 颗粒/纸纹这类高频材质看这个（≥0.35 算看见）
  · 低通差    |blur(A) - blur(B)| 均值    —— 大脉络/暗底这类低频材质看这个（≥3.5 算看见）
⛔ 不用 hf(B)/hf(A) 比值：A 完全平坦时它会被除零放成天文数字（实测出现过 847750.01）。
两者任一达标即判「可见」。判据是产物（PNG 像素），不是退出码。

用法：
  python3 scripts/probe-texture-visibility.py            # 全部 used_by
  python3 scripts/probe-texture-visibility.py --only qiu-r
  python3 scripts/probe-texture-visibility.py --keep     # 保留 A/B 图在 --out 下

依赖：Pillow + numpy + 本机 Chrome（截图）。慢：每处约 3–6 秒。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageFilter
except ImportError:  # pragma: no cover
    sys.exit('缺 Pillow / numpy：pip3 install pillow numpy')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

BOX_W, BOX_H, GAP = 300, 200, 20
SCALE = 2

CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
]


def chrome() -> str:
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    found = shutil.which('google-chrome') or shutil.which('chromium')
    if not found:
        sys.exit('找不到 Chrome / Chromium，无法截图')
    return found


PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{css}">
<style>
 html,body{{margin:0;background:#101010}}
 .wrap{{display:flex;gap:{gap}px;padding:10px}}
 .b{{width:{w}px;height:{h}px;overflow:hidden}}
</style></head><body>
<div class="wrap"><div class="b {sel} {sel}--flat"></div><div class="b {sel}"></div></div>
</body></html>'''


def hf(a: np.ndarray) -> float:
    """高频能量：原图减去半径 2 的高斯模糊，取绝对值的均值。"""
    im = Image.fromarray(a.astype(np.uint8))
    return float(np.abs(a - np.asarray(im.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)).mean())


def lowpass_delta(a: np.ndarray, b: np.ndarray) -> float:
    """低通差：缩到 1/4 再比，避开高频图案的亚像素错位。"""
    box = lambda x: np.asarray(Image.fromarray(x.astype(np.uint8)).resize((75, 50), Image.BOX), dtype=np.float32)
    return float(np.abs(box(a) - box(b)).mean())


def measure(png: Path) -> dict:
    a = np.asarray(Image.open(png).convert('L'), dtype=np.float32)
    # 盒子位置由上面的模板决定：padding 10 + 第一盒 300 → 第二盒左边缘 330
    A = a[20:20 + BOX_H * SCALE, 20:20 + BOX_W * SCALE]
    B = a[20:20 + BOX_H * SCALE, (10 + BOX_W + GAP) * SCALE:(10 + BOX_W + GAP) * SCALE + BOX_W * SCALE]
    ha, hb = hf(A), hf(B)
    return dict(hf_a=ha, hf_b=hb, dhf=hb - ha, lp=lowpass_delta(A, B),
                mean_a=float(A.mean()), mean_b=float(B.mean()),
                # A 完全平坦时比值会变成天文数字（除零放大），这种情况只报绝对增量
                gain=(hb / ha) if ha >= 0.5 else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=str(ROOT))
    ap.add_argument('--registry', default=None, help='默认 <root>/assets/textures-src/registry.json')
    ap.add_argument('--only', default=None, help='只测某主题')
    ap.add_argument('--out', default=None, help='A/B 图输出目录（默认临时目录）')
    ap.add_argument('--keep', action='store_true', help='保留截图')
    ap.add_argument('--dhf-min', type=float, default=0.35,
                    help='高频绝对增量下限（灰度级）：Δhf = hf(B) - hf(A)')
    ap.add_argument('--lp-min', type=float, default=3.5, help='低通差下限（灰度级）')
    args = ap.parse_args()

    root = Path(args.root)
    reg_path = Path(args.registry) if args.registry else root / 'assets/textures-src/registry.json'
    reg = json.load(open(reg_path, encoding='utf-8'))
    exe = chrome()
    out = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix='texprobe-'))
    out.mkdir(parents=True, exist_ok=True)

    cases = []
    for a in reg['assets']:
        if a.get('stage') != 'wired':
            continue
        for u in a.get('used_by') or []:
            if args.only and u['theme'] != args.only:
                continue
            cases.append((a['id'], u['theme'], u['sel']))

    print(f'chrome={exe}\n用例 {len(cases)} 处\n')
    bad = 0
    rows = []
    for i, (aid, theme, sel) in enumerate(cases, 1):
        css = root / 'assets/themes' / ('%s.css' % theme)
        html = out / ('%s-%s.html' % (theme, sel.lstrip('.')))
        html.write_text(PAGE.format(css=css, gap=GAP, w=BOX_W, h=BOX_H, sel=sel.lstrip('.')), encoding='utf-8')
        png = html.with_suffix('.png')
        prof = Path(tempfile.mkdtemp(prefix='crx-'))
        subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-first-run',
                        '--user-data-dir=%s' % prof, '--hide-scrollbars',
                        '--force-device-scale-factor=%d' % SCALE,
                        '--window-size=%d,%d' % ((BOX_W * 2 + GAP + 20), BOX_H + 20),
                        '--screenshot=%s' % png, 'file://%s' % html],
                       capture_output=True, text=True, timeout=90)
        shutil.rmtree(prof, ignore_errors=True)
        if not png.exists() or png.stat().st_size < 1000:
            print('✗ %s %s 截图没产出（Chrome 静默失败）' % (theme, sel))
            bad += 1
            continue
        m = measure(png)
        visible = m['dhf'] >= args.dhf_min or m['lp'] >= args.lp_min
        rows.append((aid, theme, sel, m, visible))
        flag = '✓' if visible else '✗'
        gain = '—' if m['gain'] is None else '%4.2f' % m['gain']
        print('%s %-16s %-14s %-16s 高频增益=%5s Δhf=%5.2f 低通Δ=%5.2f  Δ均值=%5.1f'
              % (flag, theme, sel, aid, gain, m['dhf'], m['lp'], abs(m['mean_b'] - m['mean_a'])))
        if not visible:
            bad += 1

    if not args.keep and not args.out:
        shutil.rmtree(out, ignore_errors=True)
    print()
    if bad:
        print('FAIL 可见性实测：%d / %d 处接上看不见（阈值 Δhf≥%.2f 或 低通Δ≥%.1f 灰度级）'
              % (bad, len(cases), args.dhf_min, args.lp_min))
        return 1
    print('PASS 可见性实测：%d 处全部可见（阈值 Δhf≥%.2f 或 低通Δ≥%.1f 灰度级）'
          % (len(cases), args.dhf_min, args.lp_min))
    return 0


if __name__ == '__main__':
    sys.exit(main())
