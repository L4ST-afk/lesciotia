#!/usr/bin/env python3
"""gen-theme-slices.py — 从九个主题预览板截出「风格切片」，写进 docs/themes/。

一张切片＝预览板的板头（主题名＋英文＋母题三词）＋色板（主色与副色 hex）＋材质样片，
不含字体授权提示条（那是免责声明，不属于风格）。九张尺寸一致（900×546），README 主页排成 3×3。

判据（都是真实跑过才写下的）：
  ① 截图只认产物文件是否非空——Chrome 写不出文件时也返回 0（见 render-png.sh 判据②）；
  ② 提示条类（`.fb-fontnote` / `.lh-fontnote` / `.py-fontnote`）用 `display:none!important`
     追加在 `</body>` 前；写进 `<head>` 会被后定义的 `display:flex` 盖掉，截出来还在；
  ③ 裁切框是**四边都固定的像素**（380,8)-(1520,700)，与预览板的 1920×1080 视口配套；
     预览板版面一变（加一行板头、换栅格），这里必须跟着改，否则切片会带上半截下一节；
  ④ 缩到 900 宽再存（1140→900，Lanczos），单张 170–330 KB；不缩会把 README 拖成十几 MB。

用法：
    python3 scripts/gen-theme-slices.py            # 全部九张
    python3 scripts/gen-theme-slices.py qiu-r      # 只出一张（调试用）
输出：docs/themes/<slug>.png
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIEWS = ROOT / 'examples' / 'previews'
OUT = ROOT / 'docs' / 'themes'
RENDER = ROOT / 'scripts' / 'render-png.sh'

# 视口与裁切：1920×1080 截图里，正文卡片从 x=380 起、到 x=1520；板头从 y=8 起，
# 材质样片图注 y≈612，留到 700 正好收住图注、不切进下一节。
CROP = (380, 8, 1520, 700)
TARGET_W = 900
HIDE = '.fb-fontnote,.lh-fontnote,.py-fontnote{display:none!important}'


def one(slug: str, tmp: Path) -> Path:
    src = PREVIEWS / f'{slug}-theme-preview.html'
    if not src.is_file():
        raise SystemExit(f'✗ 找不到预览板：{src}')
    text = src.read_text(encoding='utf-8')
    patched = tmp / src.name
    patched.write_text(text.replace('</body>', f'<style>{HIDE}</style></body>'), encoding='utf-8')

    shot_dir = tmp / 'shot'
    shot_dir.mkdir(exist_ok=True)
    subprocess.run(['bash', str(RENDER), str(patched), '1', str(shot_dir)], check=False)
    shot = shot_dir / f'{slug}-theme-preview.png'
    if not shot.is_file() or shot.stat().st_size == 0:
        raise SystemExit(f'✗ 截图没落盘（Chrome 静默失败）：{slug}')

    from PIL import Image
    im = Image.open(shot).convert('RGB').crop(CROP)
    im.thumbnail((TARGET_W, TARGET_W), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f'{slug}.png'
    im.save(dst, optimize=True)
    print(f'  ✓ {dst.relative_to(ROOT)}  {im.size[0]}×{im.size[1]}  {dst.stat().st_size // 1024} KB')
    return dst


def main() -> int:
    slugs = [p.name[:-len('-theme-preview.html')] for p in sorted(PREVIEWS.glob('*-theme-preview.html'))]
    picked = sys.argv[1:] or slugs
    tmp = Path(tempfile.mkdtemp(prefix='slices-'))
    try:
        for slug in picked:
            one(slug, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f'九种瓦作切片：{len(picked)} 张 → docs/themes/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
