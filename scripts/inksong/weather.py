#!/usr/bin/env python3
"""
墨点做旧引擎 —— 把 OFL 宋体字形处理成铅印 / 油墨斑驳质感。

流程（每字）：
  1. 原字形 → 高分辨率位图（抗锯齿）
  2. 形态学侵蚀（erode）→ 笔画边缘被"啃"掉一圈，模拟油墨未完全覆盖
  3. 墨点 → 墨迹内部随机挖白洞（漏印 / 墨点）
  4. 轻微膨胀（dilate）回补 → 避免笔画被削得过细
  5. potrace 描回矢量（三次贝塞尔）
  6. 三次 → 二次贝塞尔（Cu2Qu），写入 glyf

为什么重建 TTF 而不是改原 CFF：
  思源宋是 CID-keyed CFF，charstring 惰性反编译，setBytecode 后再 save
  会在 recalcFontBBox 阶段炸（program is None）。重建 glyf 完全绕开这个坑，
  而且 woff2 压缩后体积更小。

用法：
  python weather.py --src base.otf --dst out.ttf --preset light
  python weather.py --src base.otf --dst t.ttf --chars "永龍書" --preset medium
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

# ── 预设：侵蚀半径 / 墨点密度 / 墨点半径区间 / 回补半径 / 柔化 ──────────
# 单位：像素（在 --size 渲染尺寸下）。size 越大，这些值要按比例放大。



# 数值按 size=512 标定。512 是必须的：256 下 Regular 的细横只有 8~12px，
# 侵蚀 3px 就吃掉大半，得到的是「碎掉」而不是「斑驳」。
# ⚠️ 改 --size 时 erode / band / *_scale 要按 size/512 等比缩放。
# ⚠️ 标定原则（2026-11-21 重做）：**先加粗、再啃**。
#
# 旧版只有 erode（减墨），结果墨量掉到思源宋 Regular 的 60%——
# 14px 下看着就是一款「细宋」，不是「有墨点的宋」。做旧的观感该来自
# 边缘毛边与内部漏印，**不是整体变细**。所以现在每档先 thicken 补墨
# （把笔画撑到比原字略厚），再用 erode/edge_bite 啃回去，净墨量 ≈ 原字或略厚。
#
# 参数语义：
#   thicken    先加粗半径（px）。这是「油墨铺开」的那一步。
#   erode      再侵蚀半径（px）。与 thicken 相抵后决定净字重。
#   band       边缘带宽度（px）
#   edge_bite  边缘带被啃掉的比例 0~1 —— 毛边主要来源
#   edge_scale 边缘噪声斑块大小（px）
#   inner_leak 内部被漏印掉的比例 0~1
#   inner_scale 内部斑块大小（px）
#   splash     外溅墨点个数 —— 撒在字形轮廓**外面**，这是「油墨宋」的关键
#   splash_r   外溅墨点半径（px）
#   splash_reach 外溅墨点离轮廓的最大距离（px）
#   dilate     最后回补膨胀半径（px）
#   blur       柔化半径（px）
# 标定基准（2026-11-22 实测，单字「永」512px）
#
# ⚠️ 四条踩过的坑，写在这里免得重犯：
#
# 坑一：只看墨量会标错。把墨量调到 118% 就以为对了，96px 一看还是「细而脏」。
#       墨量是结果，不是原因。
#
# 坑二：inner_scale 必须远小于笔画宽度。旧版 inner_scale=32 而笔画才 34px，
#       噪声斑块和笔画一样宽，挖出来的是大洞不是麻点——「墨」字直接认不出。
#
# 坑三：**笔画内部要实心**。这是最后才想明白的一条。南西放大看是「实心粗笔画
#       + 轮廓外零星墨点」；我前几版一直靠 inner_leak 在笔画内部挖洞，挖出来的
#       是「脏」，不是「油墨」。现在 inner_leak 压到 0.02~0.06，只做轻微不匀。
#
# 坑四：南西不是思源宋压出来的。实测南西字面宽度只有思源宋的 0.78 倍、
#       高度 0.96 倍——它是另一套窄体设计。想靠位图变形逐像素逼近南西走不通
#       （试过横向压缩 0.78，宋体的横竖对比直接压变形）。
#       墨点宋的目标不是「等于南西」，是「看起来是有墨点的宋体」+ 授权干净。
#
# 参考数据（单字「永」512px）：
#   指标          思源宋   南西油墨宋
#   墨量          43163    51755（120%）
#   字面 bbox     478x467  367x452
#   孤立块数      2        103（54 个 1-4px / 47 个 5-16px，中位距离 15px）
#
# ⛔ thicken 必须大于 erode，否则净墨量低于原字，14px 下就是细宋。
# ⛔ inner_leak 别超过 0.10：超过就是在笔画里挖洞，观感是脏不是油墨。
# ⛔ splash_r 别用 2 以上：半径一大墨点会和笔画粘连，孤立块数反而下降。
# ⛔ splash_reach 别超过 10：reach=12 时墨点被推到 40px 外，近处反而没有墨点。
PRESETS = {
    # 极轻：只在笔画边缘留一点毛边，正文完全可读
    "hairline": dict(thicken=2, erode=0, band=3, edge_bite=0.14, edge_scale=5,
                     inner_leak=0.02, inner_scale=5,
                     splash=90, splash_r=1, splash_reach=8,
                     dilate=0, blur=0.6),
    # 轻：看得出油墨感，14px 仍可读 —— Regular 字重推荐
    "light":    dict(thicken=3, erode=0, band=5, edge_bite=0.22, edge_scale=6,
                     inner_leak=0.03, inner_scale=6,
                     splash=160, splash_r=1, splash_reach=11,
                     dilate=0, blur=0.7),
    # 中：明显斑驳，适合标题 20px+
    "medium":   dict(thicken=5, erode=1, band=7, edge_bite=0.26, edge_scale=7,
                     inner_leak=0.05, inner_scale=7,
                     splash=220, splash_r=1, splash_reach=11,
                     dilate=0, blur=0.8),
    # 重：接近扛重族 Heavy 的观感，只能当大标题
    "heavy":    dict(thicken=8, erode=2, band=9, edge_bite=0.28, edge_scale=9,
                     inner_leak=0.06, inner_scale=8,
                     splash=300, splash_r=1, splash_reach=12,
                     dilate=0, blur=1.0),
}


def render_glyph(font_path, ch, size, index=0):
    """
    把单个字符渲染成 L 模式位图（白底黑字），返回 (img, ink_bbox)。

    ink_bbox 是实际墨迹的 (left, top, right, bottom) 像素框。做旧后轮廓要
    映射回字体坐标，靠这个框做线性标定 —— 不依赖 PIL 的 anchor 语义，
    也不依赖 hhea/OS2 的 ascent 口径，避免坐标系翻错。
    """
    font = ImageFont.truetype(font_path, size, index=index)
    img = Image.new("L", (size * 2, size * 2), 255)
    d = ImageDraw.Draw(img)
    d.text((size * 0.5, size * 0.5), ch, font=font, fill=0, anchor="lt")
    # ⚠️ 坑：img.getbbox() 会把抗锯齿的浅灰边也算进去，实测能扩到整个画布
    #    (0,0,1024,1024)，导致后面 bbox 标定完全失效。必须按阈值算。
    a = np.array(img)
    ys, xs = np.nonzero(a < 128)
    if len(xs) == 0:
        return img, None          # 字形为空（字不在字体里），调用方跳过
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return img, bbox


def morph(ink, radius, mode):
    """
    形态学侵蚀 / 膨胀。入参出参都是 bool 数组（True = 有墨）。

    ⚠️ 坑：PIL 的 MinFilter 作用在「白底黑字」上是在**扩黑**（取邻域最小值，
       黑=0 会扩散），方向正好相反。所以这里统一在「墨=255」的掩膜上做：
         erode  → MinFilter（取最小，墨收缩）
         dilate → MaxFilter（取最大，墨扩张）
    """
    if radius <= 0:
        return ink
    k = radius * 2 + 1
    m = np.where(ink, 255, 0).astype(np.uint8)
    f = ImageFilter.MinFilter(k) if mode == "erode" else ImageFilter.MaxFilter(k)
    return np.array(Image.fromarray(m).filter(f)) > 127


def splash(ink, count, radius, reach, rng, cluster=0.55):
    """
    外溅墨点：在字形轮廓**外面**撒孤立墨点，模拟油墨飞溅。

    ⚠️ 这是南西油墨宋和普通「做旧宋」最大的差别。实测单字「永」512px：
         思源宋 Regular   连通块 3    孤立块 2
         南西油墨宋       连通块 104  孤立块 103   ← 墨点溅到笔画外面
         旧版墨点宋       连通块 6    孤立块 5     ← 只在内部啃，外面干净
    没有这一步，做旧出来的字只是「边缘毛糙的宋体」，不是「油墨宋」。

    参数：
      count    墨点个数（按字形面积归一化后的基准数）
      radius   墨点半径（px）
      reach    墨点离轮廓的最大距离（px）
      cluster  成团比例：油墨飞溅不是均匀撒芝麻，是几处溅开、其余零星。
               0 = 全均匀撒；1 = 全成团。
    """
    if count <= 0:
        return ink
    h, w = ink.shape
    # 轮廓外环：dilate(reach) 减去原字形 = 可撒墨点的环带
    outer = morph(ink, reach, "dilate")
    ring = outer & ~ink
    ys, xs = np.nonzero(ring)
    if len(xs) == 0:
        return ink

    out = ink.copy()
    n_cluster = int(count * cluster)
    n_scatter = count - n_cluster

    def stamp(py, px, r):
        y0, y1 = max(0, py - r), min(h, py + r + 1)
        x0, x1 = max(0, px - r), min(w, px + r + 1)
        if y0 >= y1 or x0 >= x1:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        out[y0:y1, x0:x1] |= ((yy - py) ** 2 + (xx - px) ** 2) <= r * r

    # 成团：先随机选几个「溅落中心」，再在中心附近撒
    if n_cluster > 0:
        n_centers = max(1, n_cluster // 6)
        for k in rng.integers(0, len(xs), n_centers):
            cy, cx = int(ys[k]), int(xs[k])
            for _ in range(int(rng.integers(4, 9))):
                py = cy + int(rng.integers(-reach, reach + 1))
                px = cx + int(rng.integers(-reach, reach + 1))
                if not (0 <= py < h and 0 <= px < w) or ink[py, px]:
                    continue
                stamp(py, px, max(1, int(radius * rng.uniform(0.6, 1.6))))

    # 零星：在环带上均匀撒
    if n_scatter > 0:
        for k in rng.integers(0, len(xs), n_scatter):
            stamp(int(ys[k]), int(xs[k]), max(1, int(radius * rng.uniform(0.5, 1.2))))

    return out


def edge_band(ink, width):
    """取笔画的边缘带（离边界 width 像素以内的墨）。"""
    if width <= 0:
        return np.zeros_like(ink)
    inner = morph(ink, width, "erode")
    return ink & ~inner


def noise_field(h, w, scale, rng):
    """
    低频噪声场，值域 0..1。scale 越大斑块越大。

    ⚠️ 为什么不用「逐个画椭圆」：每字要撒几百到几千个圆，PIL 的 ellipse
       是 Python 层循环，3755 字跑下来要几十分钟。噪声场是纯 numpy +
       一次 resize，快两个数量级，而且天然成片（更像油墨，不像撒芝麻）。
    """
    sh = max(2, h // scale)
    sw = max(2, w // scale)
    small = rng.random((sh, sw)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC)
    return np.array(img).astype(np.float32) / 255.0


def weather_bitmap(img, preset, rng):
    """
    对位图施加做旧效果，返回 L 模式数组（白底黑字）。

    真实油墨的斑驳有两个来源，分开建模：
      1. 边缘啃蚀 —— 笔画轮廓被啃出不规则缺口（erode + 边缘带噪声）
      2. 内部漏印 —— 实心区出现成片浅斑（低频噪声，不是均匀芝麻点）

    参数语义（都是「比例」，好调）：
      thicken    先加粗半径（px）—— 油墨铺开那一步，⛔ 别设 0
      erode      基础侵蚀半径（px，按 size 标定）
      band       边缘带宽度（px）
      edge_bite  边缘带被啃掉的比例 0~1
      edge_scale 边缘噪声斑块大小（px）
      inner_leak 内部被漏印掉的比例 0~1
      inner_scale 内部斑块大小（px）
      splash     外溅墨点个数（撒在轮廓外面）
      splash_r   外溅墨点半径（px）
      splash_reach 外溅墨点离轮廓最大距离（px）
      dilate     回补膨胀半径（px）
      blur       柔化半径（px）
    """
    arr = np.array(img)
    h, w = arr.shape
    ink = arr < 128  # True = 有墨

    # 0) 先加粗：模拟油墨铺开，把笔画撑到比原字略厚。
    #    这一步是「做旧不等于变细」的关键——没有它，后面的侵蚀只会让字越做越瘦。
    if preset.get("thicken", 0) > 0:
        ink = morph(ink, preset["thicken"], "dilate")

    # 1) 基础侵蚀：把加粗出来的部分啃回去，净字重由 thicken - erode 决定
    if preset["erode"] > 0:
        ink = morph(ink, preset["erode"], "erode")

    # 2) 边缘啃蚀：边缘带上按噪声挖，得到不规则毛边
    band = edge_band(ink, preset["band"])
    if band.any() and preset["edge_bite"] > 0:
        n = noise_field(h, w, preset["edge_scale"], rng)
        # 噪声均匀分布 → P(n > 1-f) ≈ f，所以阈值 = 1 - 比例
        ink = ink & ~(band & (n > 1.0 - preset["edge_bite"]))

    # 3) 内部漏印：低频噪声成片挖
    if preset["inner_leak"] > 0:
        n2 = noise_field(h, w, preset["inner_scale"], rng)
        ink = ink & ~(ink & (n2 > 1.0 - preset["inner_leak"]))

    # 4) 回补：膨胀一点，防止笔画被削太细
    if preset["dilate"] > 0:
        ink = morph(ink, preset["dilate"], "dilate")

    # 4.5) 外溅墨点：撒在轮廓外面。⛔ 必须放在 blur 之前，
    #      否则柔化会把小墨点糊掉；也必须在 thicken/erode 之后，
    #      因为环带要按最终轮廓算。
    if preset.get("splash", 0) > 0:
        ink = splash(ink, preset["splash"], preset.get("splash_r", 1),
                     preset.get("splash_reach", 6), rng)

    # 5) 轻微柔化 → 边缘不那么"刀切"，再二值化
    if preset["blur"] > 0:
        soft = Image.fromarray(np.where(ink, 0, 255).astype(np.uint8))
        soft = soft.filter(ImageFilter.GaussianBlur(preset["blur"]))
        ink = np.array(soft) < 128

    return np.where(ink, 0, 255).astype(np.uint8)


def trace_to_path(arr, tmpdir, name):
    """位图 → potrace → SVG path 字符串（三次贝塞尔）。"""
    bmp = Path(tmpdir) / f"{name}.pbm"
    svg = Path(tmpdir) / f"{name}.svg"
    Image.fromarray(arr).convert("1").save(bmp)
    subprocess.run(
        ["potrace", "-s", "-o", str(svg), "--flat", "-u", "10",
         "--turdsize", "2", "--alphamax", "1.0", str(bmp)],
        check=True, capture_output=True,
    )
    m = re.search(r'<path d="([^"]+)"', svg.read_text())
    return m.group(1) if m else None


def svg_path_to_pen(d, pen, size, upem, ink_bbox, font_bbox):
    """
    potrace 的 SVG path → fontTools pen。

    坐标链：
      potrace path 坐标 = 1/10 像素，y 向上（因为 SVG 里 g 有 scale(0.1,-0.1)
      且 translate(0, canvas_h)，path 里的 y 已经翻转过：path_y 越大 = 越靠上）
      → 除以 10 得到「y 向上的画布像素」
      → 用墨迹 bbox 线性映射到字体坐标的墨迹 bounds

    ⚠️ 坑：path 坐标已经翻转过一次，这里**不能再翻**。之前写成
       (size - y*0.1 - oy) 就是多翻了一次，结果整个字上下颠倒。
    """
    tokens = re.findall(r"[MmLlHhVvCcQqZz]|-?\d*\.?\d+", d)
    bl, bt, br, bb = ink_bbox
    fx0, fy0, fx1, fy1 = font_bbox

    # 画布像素（y 向上）：path_y/10 直接就是它
    # 墨迹在「y 向上画布」里的范围：底 = canvas_h - bb，顶 = canvas_h - bt
    canvas_h = size * 2
    bx0, bx1 = bl, br
    by0, by1 = canvas_h - bb, canvas_h - bt
    bw = max(1.0, bx1 - bx0)
    bh = max(1.0, by1 - by0)
    fw = max(1.0, fx1 - fx0)
    fh = max(1.0, fy1 - fy0)

    def tx(x, y):
        # potrace 的 path 坐标已经是 0.1px 单位、y 向上（SVG 里那个
        # scale(0.1,-0.1) 是给渲染器用的，path 数据本身已经翻好）
        px = x * 0.1
        py = y * 0.1
        return (fx0 + (px - bx0) / bw * fw,
                fy0 + (py - by0) / bh * fh)

    i = 0
    cx = cy = 0.0
    start = (0.0, 0.0)
    cmd = None
    while i < len(tokens):
        t = tokens[i]
        if re.match(r"[MmLlHhVvCcQqZz]", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                pen.closePath()
                cx, cy = start
            continue
        need = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4}[cmd.upper()]
        nums = []
        while i < len(tokens) and not re.match(r"[MmLlHhVvCcQqZz]", tokens[i]):
            nums.append(float(tokens[i]))
            i += 1
        for k in range(0, len(nums) - need + 1, need):
            seg = nums[k:k + need]
            rel = cmd.islower()
            c = cmd.upper()
            if c == "M":
                x, y = (cx + seg[0], cy + seg[1]) if rel else (seg[0], seg[1])
                pen.moveTo(tx(x, y))
                start = (x, y)
                cx, cy = x, y
                cmd = "l" if rel else "L"   # 后续隐式 lineto
            elif c == "L":
                x, y = (cx + seg[0], cy + seg[1]) if rel else (seg[0], seg[1])
                pen.lineTo(tx(x, y))
                cx, cy = x, y
            elif c == "H":
                x = cx + seg[0] if rel else seg[0]
                pen.lineTo(tx(x, cy))
                cx = x
            elif c == "V":
                y = cy + seg[0] if rel else seg[0]
                pen.lineTo(tx(cx, y))
                cy = y
            elif c == "C":
                if rel:
                    p1 = (cx + seg[0], cy + seg[1])
                    p2 = (cx + seg[2], cy + seg[3])
                    p3 = (cx + seg[4], cy + seg[5])
                else:
                    p1, p2, p3 = (seg[0], seg[1]), (seg[2], seg[3]), (seg[4], seg[5])
                pen.curveTo(tx(*p1), tx(*p2), tx(*p3))
                cx, cy = p3
            elif c == "Q":
                if rel:
                    p1 = (cx + seg[0], cy + seg[1])
                    p2 = (cx + seg[2], cy + seg[3])
                else:
                    p1, p2 = (seg[0], seg[1]), (seg[2], seg[3])
                pen.qCurveTo(tx(*p1), tx(*p2))
                cx, cy = p2


# ── 并行 worker（模块级，才能被 multiprocessing pickle）──────────────
_W = {}


def _init_worker(src_path, preset_name, size, seed):
    _W["src"] = src_path
    _W["preset"] = PRESETS[preset_name]
    _W["size"] = size
    _W["seed"] = seed
    _W["td"] = tempfile.mkdtemp()
    # 每个 worker 自己开一份字体句柄，算原字形 bbox 用
    f = TTFont(src_path)
    _W["cmap"] = f.getBestCmap()
    _W["glyphset"] = f.getGlyphSet()


def _glyph_font_bbox(glyphset, gname):
    """原字形在字体坐标里的墨迹 bounds。"""
    bp = BoundsPen(glyphset)
    glyphset[gname].draw(bp)
    return bp.bounds


def _weather_one(args):
    """处理单个码位，返回 (cp, path_d 或 None, 错误信息)。"""
    cp, idx = args
    ch = chr(cp)
    size = _W["size"]
    try:
        gname = _W["cmap"][cp]
        fb = _glyph_font_bbox(_W["glyphset"], gname)
        if fb is None:
            return (cp, None, None)      # 空字形，跳过
        rng = np.random.default_rng(_W["seed"] + cp)
        img, ink_bbox = render_glyph(_W["src"], ch, size)
        if ink_bbox is None:
            return (cp, None, None)
        arr = weather_bitmap(img, _W["preset"], rng)
        d = trace_to_path(arr, _W["td"], f"g{idx}")
        return (cp, (d, ink_bbox, fb), None)
    except Exception as e:
        return (cp, None, f"{ch}:{e}")


def build_font(src_path, dst_path, preset, size, seed, only_chars=None, jobs=1):
    src = TTFont(src_path)
    cmap = src.getBestCmap()
    upem = src["head"].unitsPerEm
    hmtx = src["hmtx"]

    # 目标字符集
    if only_chars:
        targets = [c for c in only_chars if ord(c) in cmap]
    else:
        targets = [chr(cp) for cp in cmap if 0x4E00 <= cp <= 0x9FFF]

    # 保留原字体的全部码位（含拉丁/标点），但只对 targets 做旧
    all_cps = sorted(cmap.keys())
    print(f"总码位 {len(all_cps)} | 做旧 {len(targets)} 字 | preset={preset} | size={size}", flush=True)

    # 字形名映射：每个码位一个独立字形名
    glyph_order = [".notdef"]
    cmap_out = {}
    for cp in all_cps:
        gname = f"u{cp:04X}"
        cmap_out[cp] = gname
        if gname not in glyph_order:
            glyph_order.append(gname)

    glyphs = {}
    metrics = {}

    # .notdef 空字形
    pen = TTGlyphPen(None)
    glyphs[".notdef"] = pen.glyph()
    metrics[".notdef"] = (upem, 0)

    target_set = {ord(c) for c in targets}
    offset = (size * 0.5, size * 0.5)

    # ── 并行做旧 ────────────────────────────────────────────────
    todo = [(cp, i) for i, cp in enumerate(all_cps) if cp in target_set]
    print(f"待做旧 {len(todo)} 字 | jobs={jobs}", flush=True)

    results = {}
    failed = []
    if jobs > 1:
        import multiprocessing as mp
        with mp.Pool(jobs, initializer=_init_worker,
                     initargs=(src_path, preset, size, seed)) as pool:
            for n, (cp, d, err) in enumerate(
                    pool.imap_unordered(_weather_one, todo, chunksize=16), 1):
                results[cp] = d
                if err:
                    failed.append(err)
                if n % 500 == 0:
                    print(f"  {n}/{len(todo)} ...", flush=True)
    else:
        with tempfile.TemporaryDirectory() as td:
            gs = src.getGlyphSet()
            for n, (cp, idx) in enumerate(todo, 1):
                ch = chr(cp)
                rng = np.random.default_rng(seed + cp)
                try:
                    fb = _glyph_font_bbox(gs, cmap[cp])
                    img, ink_bbox = render_glyph(src_path, ch, size)
                    arr = weather_bitmap(img, preset, rng)
                    d = trace_to_path(arr, td, f"g{idx}")
                    results[cp] = (d, ink_bbox, fb) if (d and ink_bbox and fb) else None
                except Exception as e:
                    results[cp] = None
                    failed.append(f"{ch}:{e}")
                if n % 250 == 0:
                    print(f"  {n}/{len(todo)} ...", flush=True)

    # ── 组装字形 ────────────────────────────────────────────────
    done = 0
    for cp in all_cps:
        gname = cmap_out[cp]
        src_gname = cmap[cp]
        adv, lsb = hmtx[src_gname]
        res = results.get(cp)

        if res:
            d, ink_bbox, fb = res
            try:
                pen = TTGlyphPen(None)
                qpen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
                svg_path_to_pen(d, qpen, size, upem, ink_bbox, fb)
                glyphs[gname] = pen.glyph()
                metrics[gname] = (adv, lsb)
                done += 1
                continue
            except Exception as e:
                failed.append(f"{chr(cp)}:{e}")

        # 不做旧 / 做旧失败：复制原轮廓
        pen = TTGlyphPen(None)
        qpen = Cu2QuPen(pen, max_err=1.0, reverse_direction=True)
        src.getGlyphSet()[src_gname].draw(qpen)
        glyphs[gname] = pen.glyph()
        metrics[gname] = (adv, lsb)

    print(f"做旧完成 {done} | 失败 {len(failed)}")
    if failed[:8]:
        print("失败样例:", failed[:8])

    # ── 组装 TTF ────────────────────────────────────────────────
    fb = FontBuilder(upem, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap_out)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)

    os2_src = src["OS/2"]
    name_src = src["name"]
    fb.setupHorizontalHeader(
        ascent=src["hhea"].ascent,
        descent=src["hhea"].descent,
        lineGap=src["hhea"].lineGap,
    )
    fb.setupNameTable({
        "familyName": "InkSong",
        "styleName": "Regular",
        "uniqueFontIdentifier": "InkSong-Regular;2026;Lesciotia",
        "fullName": "InkSong Regular",
        "psName": "InkSong-Regular",
        "version": "Version 1.000",
        "copyright": (
            "Derived from Source Han Serif SC Regular, Copyright 2017 Adobe "
            "(http://www.adobe.com/), with Reserved Font Name 'Source'. "
            "Weathering modifications by Lesciotia, 2026. "
            "Licensed under SIL Open Font License 1.1."
        ),
        "licenseDescription": (
            "This Font Software is licensed under the SIL Open Font License, "
            "Version 1.1. This license is available with a FAQ at: "
            "https://openfontlicense.org"
        ),
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=os2_src.sTypoAscender,
        sTypoDescender=os2_src.sTypoDescender,
        sTypoLineGap=os2_src.sTypoLineGap,
        usWinAscent=os2_src.usWinAscent,
        usWinDescent=os2_src.usWinDescent,
        sxHeight=getattr(os2_src, "sxHeight", 0),
        sCapHeight=getattr(os2_src, "sCapHeight", 0),
        usWeightClass=400,
        usWidthClass=5,
        fsType=0,
        panose=os2_src.panose.__dict__ if hasattr(os2_src, "panose") else None,
    )
    fb.setupPost()
    fb.save(dst_path)
    print("已保存", dst_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--chars", default=None, help="只做旧这些字（调试用）")
    ap.add_argument("--preset", default="light", choices=list(PRESETS))
    ap.add_argument("--size", type=int, default=256, help="栅格化尺寸")
    ap.add_argument("--seed", type=int, default=20261121)
    ap.add_argument("--jobs", type=int, default=1, help="并行进程数")
    args = ap.parse_args()

    build_font(
        args.src, args.dst, args.preset, args.size, args.seed,
        only_chars=args.chars, jobs=args.jobs,
    )


if __name__ == "__main__":
    main()
