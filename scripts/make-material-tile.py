#!/usr/bin/env python3
"""把一张 AI 生成的材质原图做成「灰度无缝 tile」——供主题 CSS 叠在 token 上。

为什么是灰度：颜色必须留在 9 份 CSS 的 `:root`（`check-theme-colors.py` 只认那里）。
位图只给层理与颗粒，色相仍由 token 决定——因此**同一张 tile 可以被多个主题共用**，
亮底用 `multiply`、暗底用 `overlay`（见 profile `dark`）。

三步（都不需要手调参数就能复现）：
  1. 灰度 + 抽掉大块明暗（高半径低通相减），只留材质本身的细结构，再压到极低对比区间；
  2. 位移半幅把接缝移到正中，再用余弦权重把正中十字缝两侧交叉淡化 → 四边连续；
  3. 落成 8bit 灰度 PNG。

profile 只决定「抽多粗的结构、压到多低对比」，算法完全相同：

  marble     白石层理    base 248 amp 7  blur 64   配合 multiply（浅底）
  dark       暗底层理    base 128 amp 42 blur 64   配合 overlay（中值 128 在 overlay 下是恒等，
                                                   所以平白区零漂移、只有脉络起伏——暗底不会起雾）
  grain      颗粒骨料    base 244 amp 9  blur 24   故意留短半径，保住 2–20px 的骨料团
  fiber      纤维纸纹    base 250 amp 5  blur 96
  travertine 石灰华沉积  base 244 amp 10 blur 96   横向纹有方向性，别拿它冒充各向同性纸纹

另有两条「不做无缝」的档：大脉络（Calacatta 式巨脉）本身周期就比面板还大，硬做无缝会把
穿缝的脉揉成软影，所以 vein 不做位移淡化，直接按分位重映射到极窄的灰区间：

  vein       亮脉络  重映射到 200..255   铺在浅底上用 multiply（白底仍是白，颜色留在 :root）
  vein-dark  暗脉络  反相重映射到 0..58   铺在暗底上用 screen（黑底不动，只有亮脉浮起）

另有一档「只给形状、不给颜色」的掩膜（2026-11-22，参照 Portoro 的三层结构）：

  mask       脉络掩膜  RGBA，脉处不透明、板面全透明；CSS 用 background-color:var(--gold)
                      + mask-image 取形状。⛔ 颜色因此永远只在 :root，换色不必重导图，
                      也避免「screen 灰度染不出金色」这个死结。

用法：
  python3 scripts/make-material-tile.py \
      --raw assets/textures-src/grain/grain-raw.png \
      --out assets/textures/grain/grain-gray-512.png --profile grain --size 512

依赖：Pillow + numpy（本库其余脚本坚持标准库，这个绕不开像素运算）。
"""
import argparse
import hashlib
import math
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageFilter
except ImportError:  # pragma: no cover
    sys.exit('缺 Pillow / numpy：pip3 install pillow numpy')

PROFILES = {
    # name: (base, amp, blur, band, 用途备注)
    'marble': (248.0, 7.0, 64, 110, '白石层理，multiply 叠在浅底'),
    'dark': (128.0, 42.0, 64, 110, '暗底层理，中值 128 供 overlay（恒等），暗底不起雾'),
    'grain': (244.0, 9.0, 24, 110, '颗粒骨料，短半径保住骨料团'),
    'fiber': (250.0, 5.0, 96, 110, '纤维纸纹，各向同性细纹'),
    'travertine': (244.0, 10.0, 96, 110, '石灰华横向沉积，方向性材质'),
    'vein': (None, None, 0, 0, '大脉络：不做无缝，重映射 200..255（浅底 multiply）'),
    'vein-dark': (None, None, 0, 0, '大脉络暗底版：反相重映射 0..58（暗底 screen）'),
    'mask': (None, None, 0, 0, '脉络掩膜：alpha=脉形、RGB 全黑；配 token 色走 mask-image'),
}
VEIN_RANGE = {'vein': (200, 255), 'vein-dark': (0, 58)}
MASK_PROFILES = {'mask'}


def build_tile(raw: Path, size: int, base: float, amp: float, blur: int, band: int) -> Image.Image:
    g0 = Image.open(raw).convert('L')
    if g0.size != (size, size):
        g0 = g0.resize((size, size), Image.LANCZOS)
    g = np.asarray(g0, dtype=np.float32)
    # 1) 抽掉大块明暗：原图常有大片灰斑，直接铺会像「脏」而不是「层理」
    low = np.asarray(g0.filter(ImageFilter.GaussianBlur(blur)), dtype=np.float32)
    hp = g - low
    lo, hi = np.percentile(hp, 1), np.percentile(hp, 99)
    hp = np.clip(hp / max(abs(lo), abs(hi), 1e-6), -1, 1)
    a = np.clip(base + hp * amp, 0, 255)

    # 2) 位移 + 余弦交叉淡化
    n = size
    b = np.roll(a, (n // 2, n // 2), axis=(0, 1))
    for d in range(band):
        w = 0.5 * (1 + math.cos(math.pi * d / band))
        l, r = n // 2 - 1 - d, n // 2 + d
        avg = 0.5 * (b[:, l] + b[:, r])
        b[:, l] = (1 - w) * b[:, l] + w * avg
        b[:, r] = (1 - w) * b[:, r] + w * avg
    for d in range(band):
        w = 0.5 * (1 + math.cos(math.pi * d / band))
        t, u = n // 2 - 1 - d, n // 2 + d
        avg = 0.5 * (b[t, :] + b[u, :])
        b[t, :] = (1 - w) * b[t, :] + w * avg
        b[u, :] = (1 - w) * b[u, :] + w * avg
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8), 'L')


def build_vein(raw: Path, size: int, lo: int, hi: int, invert: bool) -> Image.Image:
    """大脉络：只做灰度 + 分位拉伸 + 极窄重映射，不做位移与交叉淡化。
    原因写在头注：巨脉穿过缝会被淡化带揉软，缝没了脉也毁了；这类图按 cover 不重复铺。"""
    g = Image.open(raw).convert('L')
    if g.size != (size, size):
        g = g.resize((size, size), Image.LANCZOS)
    a = np.asarray(g, dtype=np.float32)
    p1, p99 = np.percentile(a, 1), np.percentile(a, 99)
    v = np.clip((a - p1) / max(p99 - p1, 1e-6), 0, 1)
    if invert:
        v = 1 - v
    out = np.clip(lo + v * (hi - lo), 0, 255)
    return Image.fromarray(out.astype(np.uint8), 'L')


def build_mask(raw: Path, size: int, floor: float = 0.28, gamma: float = 1.15) -> Image.Image:
    """脉络掩膜：把原图里「比板面暗」的部分变成长度为不透明度的 alpha。

    为什么不做暗底反相那一套：反相取的是灰度，染出来只能是一层灰白；Portoro 的金脉
    必须由 token 给色。掩膜只保形状，颜色归 :root——这是「颜色不进图」原则最利的落点。
    floor 以下的 alpha 归零：否则整块板面会留一层极淡的雾。"""
    g = Image.open(raw).convert('L')
    if g.size != (size, size):
        g = g.resize((size, size), Image.LANCZOS)
    a = np.asarray(g, dtype=np.float32)
    p1, p50, p99 = np.percentile(a, 1), np.percentile(a, 50), np.percentile(a, 99)
    v = np.clip((a - p1) / max(p99 - p1, 1e-6), 0, 1)          # 0=最暗（脉） 1=板面
    alpha = (1.0 - v) ** gamma                                  # 幂次压掉脉边的灰阶过渡，让脉更「锐」；γ 越大脉越细
    alpha = np.clip((alpha - floor) / max(1.0 - floor, 1e-6), 0, 1)
    rgba = np.zeros((a.shape[0], a.shape[1], 4), dtype=np.uint8)
    rgba[..., 3] = (alpha * 255).round().astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def seam_ratio(im: Image.Image) -> float:
    """跨缝像素差 / 图内典型相邻差。比值 ≈1 就是真无缝：
    跨过接缝与「往旁边挪一个像素」看不出区别。⛔ 别用绝对 seam 值卡高频图——
    颗粒/纸纹的相邻差本来就有 4–7/255，绝对值大不代表有缝。"""
    a = np.asarray(im, dtype=np.float32)
    wrap = max(abs(a[:, -1] - a[:, 0]).mean(), abs(a[-1, :] - a[0, :]).mean())
    typ = max(abs(np.diff(a, axis=1)).mean(), abs(np.diff(a, axis=0)).mean())
    return float(wrap / max(typ, 1e-6))


def seam_score(im: Image.Image) -> float:
    """左右/上下边缘像素差的均值——只做读数，判据看 seam_ratio。"""
    a = np.asarray(im, dtype=np.float32)
    lr = float(np.abs(a[:, 0] - a[:, -1]).mean())
    tb = float(np.abs(a[0, :] - a[-1, :]).mean())
    return max(lr, tb)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True, help='AI 生成的材质原图（任意尺寸，会缩到 --size）')
    ap.add_argument('--out', required=True, help='输出路径（.png；mask 档出 RGBA 掩膜）')
    ap.add_argument('--profile', default='marble', choices=sorted(PROFILES),
                    help='材质档位（默认 marble，与 2026-11-22 首版参数完全一致）')
    ap.add_argument('--size', type=int, default=1024, help='tile 边长，默认 1024；次要面用 512')
    ap.add_argument('--base', type=float, default=None, help='中间调灰度（默认取 profile）')
    ap.add_argument('--amp', type=float, default=None, help='层理幅度（±255，越小越轻）')
    ap.add_argument('--blur', type=int, default=None, help='抽走大块明暗的低通半径')
    ap.add_argument('--band', type=int, default=None, help='十字缝交叉淡化宽度（像素）')
    ap.add_argument('--mask-floor', dest='mask_floor', type=float, default=0.28, help='mask 档：低于此 alpha 归零（去雾），默认 0.28')
    ap.add_argument('--mask-gamma', dest='mask_gamma', type=float, default=1.15, help='mask 档：alpha 幂次，越大脉越细，默认 1.15')
    args = ap.parse_args()

    pbase, pamp, pblur, pband, use = PROFILES[args.profile]
    base = pbase if args.base is None else args.base
    amp = pamp if args.amp is None else args.amp
    blur = pblur if args.blur is None else args.blur
    band = pband if args.band is None else args.band

    raw, out = Path(args.raw).resolve(), Path(args.out).resolve()
    if not raw.is_file():
        print(f'✗ 找不到原图 {raw}', file=sys.stderr)
        return 2
    if args.profile in MASK_PROFILES:
        im = build_mask(raw, args.size, args.mask_floor, args.mask_gamma)
    elif args.profile in VEIN_RANGE:
        lo, hi = VEIN_RANGE[args.profile]
        im = build_vein(raw, args.size, lo, hi, invert=args.profile.endswith('dark'))
    else:
        im = build_tile(raw, args.size, base, amp, blur, band)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)

    stat = np.asarray(im)
    data = out.read_bytes()
    print(f'raw={raw}')
    print(f'out={out}')
    print(f'profile={args.profile}（{use}）base={base} amp={amp} blur={blur} band={band}')
    if args.profile in VEIN_RANGE or args.profile in MASK_PROFILES:
        seam = 'n/a（不做无缝）'
    else:
        seam = f'{seam_score(im):.2f}/255 ratio={seam_ratio(im):.2f}'
    if args.profile in MASK_PROFILES:
        al = stat[..., 3]
        print(f'size={im.size[0]}x{im.size[1]} mode={im.mode} alpha min={al.min()} max={al.max()} '
              f'mean={al.mean():.1f} 不透明占比={(al > 128).mean() * 100:.1f}% seam={seam}')
    else:
        print(f'size={im.size[0]}x{im.size[1]} mode={im.mode} min={stat.min()} max={stat.max()} '
              f'mean={stat.mean():.1f} seam={seam}')
    print(f'bytes={len(data)} sha256={hashlib.sha256(data).hexdigest()[:16]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
