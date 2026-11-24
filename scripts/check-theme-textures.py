#!/usr/bin/env python3
"""瓦作出图闸：assets/textures/ 与 assets/themes/ 对账（判据级，不是「脚本能起来」）。

为什么需要它：PNG 是派生件，一旦主题 CSS 改了却不出图，A/C 出口拿到的就是旧材质；
而截图退出码永远是 0、图也照样看得见——和预览页漂移同一类静默错。

判据（任一不成立就红）：
  ① 覆盖：每个自建瓦作都有 manifest.json（缺一个就是「这个主题没有出图能力」）
  ② 来源：manifest.source_sha256 == 当前 css 的 sha256（主题改过没重出 ⇒ 红）
  ③ 产物：manifest 列的每张 PNG 存在、是 PNG、宽高与记录一致
  ④ 色值：manifest.palette 里的每个 hex 仍出现在当前 :root（不许图里留着已废的色）
  ⑤ 无孤儿：目录里不在 manifest 的 PNG 报 WARN（不红，但要人看一眼）；
     已登记在 assets/textures-src/registry.json 的**真位图 tile** 豁免（它们不是 CSS 截图，见 theme-to-export.md §位图材质）

用法：
  python3 scripts/check-theme-textures.py [--only qiu-r] [--json]
  --themes-dir / --textures-dir 供自检做负例（指到临时目录，⛔ 不动正本）
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THEMES = os.path.join(ROOT, "assets", "themes")
TEXTURES = os.path.join(ROOT, "assets", "textures")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(p):
    try:
        with open(p, "rb") as f:
            head = f.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def root_palette(css):
    return {v.upper() for v in re.findall(r"--[a-z0-9-]+\s*:\s*(#[0-9A-Fa-f]{3,8})\s*;", css)}


def bitmap_waivers():
    """真位图 tile 的豁免名单：按 theme 目录 → 文件名集合。
    这些图是「CSS 画不出才补的真素材」，不是 CSS 截图；它们由 check-bitmap-assets.py 守，
    在这里报孤儿只会训练人忽略警告。登记表读不到就返回空（退化为旧行为，不算错）。"""
    reg = os.path.join(ROOT, "assets", "textures-src", "registry.json")
    out = {}
    if not os.path.isfile(reg):
        return out
    try:
        data = json.load(open(reg, encoding="utf-8"))
    except Exception:
        return out
    for a in data.get("assets", []):
        d = a.get("derived")
        if not d:
            continue
        theme = os.path.basename(os.path.dirname(d))
        out.setdefault(theme, set()).add(os.path.basename(d))
    return out


def check(themes_dir, tex_dir, only=None):
    problems, warns = [], []
    if not os.path.isdir(themes_dir):
        return None, ["themes 目录不存在：%s" % themes_dir], []
    if not os.path.isdir(tex_dir):
        return None, ["textures 目录不存在：%s（先跑 export-theme-textures.py）" % tex_dir], []

    waivers = bitmap_waivers()
    waived_n = 0
    themes = sorted(f[:-4] for f in os.listdir(themes_dir) if f.endswith(".css"))
    if only:
        themes = [t for t in themes if t == only]
    checked = 0

    for theme in themes:
        css_path = os.path.join(themes_dir, theme + ".css")
        tdir = os.path.join(tex_dir, theme)
        mpath = os.path.join(tdir, "manifest.json")
        checked += 1
        if not os.path.isfile(mpath):
            problems.append("[%s] 缺 manifest.json（该主题没有出图）" % theme)
            continue
        try:
            m = json.load(open(mpath, encoding="utf-8"))
        except Exception as e:
            problems.append("[%s] manifest 读不了：%s" % (theme, e))
            continue

        if m.get("source_sha256") != sha256_file(css_path):
            problems.append("[%s] 源已变、图未重出（source_sha256 不符 ⇒ 重跑 export-theme-textures.py）"
                            % theme)
        css = open(css_path, encoding="utf-8").read()
        pal = {p.upper() for p in m.get("palette", [])}
        if not pal:
            problems.append("[%s] manifest 没有 palette（:root 一个 hex 都没读到）" % theme)
        for hexv in sorted(pal - root_palette(css)):
            problems.append("[%s] manifest 色值 %s 已不在当前 :root（图里留着废色）"
                            % (theme, hexv))

        listed = set()
        for item in m.get("files", []):
            fp = os.path.join(tdir, item.get("file", ""))
            listed.add(item.get("file"))
            size = png_size(fp)
            if size is None:
                problems.append("[%s] %s 不存在或不是 PNG" % (theme, item.get("file")))
            elif size != (item.get("w", -1), item.get("h", -1)):
                problems.append("[%s] %s 尺寸 %s，manifest 记的是 %s"
                                % (theme, item.get("file"), size, (item.get("w"), item.get("h"))))
        if not m.get("files"):
            problems.append("[%s] manifest 里一张图都没有" % theme)

        for f in sorted(os.listdir(tdir)):
            if not f.endswith(".png") or f in listed:
                continue
            if f in waivers.get(theme, set()):
                waived_n += 1
                continue
            warns.append("[%s] 孤儿文件 %s（不在 manifest，手工塞进来的？）" % (theme, f))
        for s in m.get("unknown_material_like", []):
            warns.append("[%s] 疑似材质未进词表：%s" % (theme, s))

    return checked, problems, warns, waived_n


def main():
    ap = argparse.ArgumentParser(add_help=True, description="瓦作出图闸：产物与主题 CSS 对账")
    ap.add_argument("--only", help="只查某个主题")
    ap.add_argument("--themes-dir", default=THEMES)
    ap.add_argument("--textures-dir", default=TEXTURES)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    print("themes_root=%s" % os.path.abspath(args.themes_dir))   # §2.304 显式打印被测根
    print("textures_root=%s" % os.path.abspath(args.textures_dir))
    checked, problems, warns, waived = check(args.themes_dir, args.textures_dir, args.only)
    if checked is None:
        for p in problems:
            print("✗ " + p)
        if args.json:
            print(json.dumps({"ok": False, "checked": 0, "problems": len(problems),
                              "bitmap_waived": 0}, ensure_ascii=False))
        return 2

    if waived:
        print("· 位图 tile 已登记、按豁免跳过孤儿判定：%d 张" % waived)
    for w in warns:
        print("⚠ " + w)
    for p in problems:
        print("✗ " + p)
    if problems:
        print("FAIL 瓦作出图闸：%d 主题、%d 项问题" % (checked, len(problems)))
    else:
        print("PASS 瓦作出图闸：%d 主题、%d 条提醒、位图豁免 %d 张" % (checked, len(warns), waived))
    if args.json:
        print(json.dumps({"ok": not problems, "checked": checked,
                          "problems": len(problems), "warns": len(warns),
                          "bitmap_waived": waived}, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
