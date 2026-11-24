#!/usr/bin/env python3
"""瓦作出图：把 assets/themes/<theme>.css 里的材质渲染成 PNG，供 A/C 出口取用。

为什么有这一步：瓦作（主题）原先只服务 B 出口（网页 deck）。A 出口是逐页 AI 生图、
C 出口交给外部引擎，两侧都不读 CSS，所以主题的材质在 PPT 侧等于不存在。
本脚本把 CSS 里的材质类与内联 SVG 纹理渲染成 PNG，作为 A 的 style 参考图、C 的底纹贴图。

铁则：**不新增第二份色值**。PNG 是派生件（build output），manifest 里记 source_sha256；
主题一改、图没重出，check-theme-textures.py 立刻红。⛔ 不许手改 PNG 或手写 palette。

用法：
  python3 scripts/export-theme-textures.py                 # 全部自建瓦作
  python3 scripts/export-theme-textures.py --only qiu-r    # 单个主题
  python3 scripts/export-theme-textures.py --list          # 只列出会导出什么
  --force 覆盖已存在（默认幂等：源未变且产物齐全就跳过）
  --json  末行输出一行机器摘要
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THEMES = os.path.join(ROOT, "assets", "themes")
OUT = os.path.join(ROOT, "assets", "textures")

CHROME_CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

# 材质词表：只有这些语义名算「材质」。新增材质必须加进这里，否则会出现在 WARN 里，
# 而不是被静默漏掉（禅院塔 §2.261：枚举写死成员，漏一整片时输出全绿）。
MATERIAL_WORDS = (
    "marble", "steel", "tile", "lawn", "terrazzo", "stone", "brick", "grain",
    "speck", "fiber", "ripple", "ash", "eave", "censer", "gold", "granite",
    "arch", "flute", "fluted", "ink", "ochre", "paper", "water", "glass",
)

TILE = 320           # 单张材质样片边长
BOARD_COLS = 3
BOARD_CELL = 360
BOARD_HEAD = 96
BOARD_PAD = 24


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(p):
    """读 IHDR 拿宽高（标准库，不引 Pillow）。非 PNG 返回 None。"""
    try:
        with open(p, "rb") as f:
            head = f.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def theme_files(only=None):
    out = []
    for f in sorted(os.listdir(THEMES)):
        if not f.endswith(".css"):
            continue
        if only and os.path.splitext(f)[0] != only:
            continue
        out.append(os.path.join(THEMES, f))
    return out


def material_classes(css):
    """挑出语义材质类。形态：`.cp-marble` / `.fb-stone` / `.glass`，且块内有 background。"""
    hits = []
    for word in MATERIAL_WORDS:
        pat = re.compile(r"\.([a-z]{1,3}-)?" + re.escape(word) + r"\b")
        for m in pat.finditer(css):
            brace = css.find("{", m.end())
            if brace < 0:
                continue
            header = css[m.end():brace]
            if "\n" in header or len(header) > 60:
                continue
            block = css[brace:css.find("}", brace)]
            if "background" in block:
                hits.append(m.group(0))
                break
    return sorted(set(hits))


def unknown_material_like(css, known):
    """报告「像材质但没进词表」的选择器，避免新增材质被静默漏掉。"""
    suspects = set()
    for m in re.finditer(r"\.([a-z]{1,3}-[a-z]{3,})\s*\{", css):
        sel = "." + m.group(1)
        if sel in known:
            continue
        brace = m.end() - 1
        block = css[brace:css.find("}", brace)]
        if "background-image" in block and "gradient" not in block:
            suspects.add(sel)
    return sorted(suspects)


def svg_tokens(css):
    """取内联 SVG 纹理 token：--qj-fiber:url("data:image/svg+xml,...")。返回 [(token, w, h)]。"""
    out = []
    # ⚠️ 不能写成 [^)"']*：data URI 内部就有单引号（xmlns='http://…'），那样会截断到第一个引号，
    # 后面 width/height 全读不到，于是所有 token 都退回 200×200 默认值（2026-11-21 实测踩到）。
    for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*url\(\s*(?:\"|')?(data:image/svg\+xml[^)]*)\)", css):
        token = m.group(1)
        uri = m.group(2).rstrip("\"' ")
        raw = uri.split(",", 1)[1] if "," in uri else ""
        raw = (raw.replace("%3C", "<").replace("%3E", ">").replace("%23", "#")
                  .replace("%20", " ").replace("%2C", ","))
        wm = re.search(r"width\s*=\s*['\"]?(\d+)", raw)
        hm = re.search(r"height\s*=\s*['\"]?(\d+)", raw)
        vb = re.search(r"viewBox\s*=\s*['\"]?\s*\d+\s+\d+\s+(\d+)\s+(\d+)", raw)
        w = int(wm.group(1)) if wm else (int(vb.group(1)) if vb else 200)
        h = int(hm.group(1)) if hm else (int(vb.group(2)) if vb else 200)
        out.append((token, w, h))
    return out


def bg_token(css):
    """主题底色：材质样片要落在它自己的纸上，落在 #fff 上会把低 α 纹理看错。"""
    m = re.search(r"--bg\s*:\s*(#[0-9A-Fa-f]{3,8})", css)
    return m.group(1) if m else "#ffffff"


def palette(css):
    """只读 :root 里的 hex。⛔ 不产生第二份色值：这是 build 记录，闸会回查当前 :root。"""
    vals = re.findall(r"--[a-z0-9-]+\s*:\s*(#[0-9A-Fa-f]{3,8})\s*;", css)
    return sorted({v.upper() for v in vals})


def prepare_css(src, workdir, name):
    """离线化：剥 @import 外链、把 ../fonts 改成绝对 file://，免得截图时联网。"""
    text = open(src, encoding="utf-8").read()
    text = re.sub(r"@import\s+url\(\s*['\"]https?://[^)]*\)\s*;", "", text)
    fonts_abs = os.path.join(ROOT, "assets", "fonts").replace("\\", "/")
    text = text.replace("url('../fonts/", "url('file://%s/" % fonts_abs)
    text = text.replace('url("../fonts/', 'url("file://%s/' % fonts_abs)

    # 主题里的位图（如 .cp-marble::after 的 ../textures/…）也要改绝对：截图页在临时目录，
    # 相对路径会按截图页解析成 404 —— 图静默不出现，样片只画出 CSS 那几道斜光（2026-11-22 实测）。
    css_dir = os.path.dirname(os.path.abspath(src)).replace("\\", "/")

    def _abs_url(m):
        target = m.group(2).strip()
        if not target or target.startswith(("http", "data:", "#", "file:")):
            return m.group(0)
        fp = os.path.normpath(os.path.join(css_dir, target)).replace("\\", "/")
        if not os.path.isfile(fp):
            return m.group(0)
        return "url('file://%s')" % fp

    text = re.sub(r"url\(\s*(['\"]?)([^'\")\n]+)\1\s*\)", _abs_url, text)

    dst = os.path.join(workdir, name + ".css")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    return dst


def shot(chrome, html_body, w, h, out_png, workdir, tag):
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>%s"
        "<style>html,body{margin:0;padding:0;background:#ffffff;overflow:hidden}"
        "%s</style></head><body>%s</body></html>"
    ) % (html_body[0], html_body[1], html_body[2])
    src = os.path.join(workdir, "shot-%s.html" % tag)
    with open(src, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [
        chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--default-background-color=00000000",
        "--window-size=%d,%d" % (w, h), "--screenshot=%s" % out_png,
        "file://" + src,
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return png_size(out_png) == (w, h)


def build_theme(path, chrome, workdir, force=False):
    theme = os.path.splitext(os.path.basename(path))[0]
    css = open(path, encoding="utf-8").read()
    src_sha = sha256_file(path)
    tdir = os.path.join(OUT, theme)
    mpath = os.path.join(tdir, "manifest.json")

    mats = material_classes(css)
    texs = svg_tokens(css)
    theme_bg = bg_token(css)
    suspects = unknown_material_like(css, set(mats))
    if not mats:
        return {"theme": theme, "ok": False, "error": "没有可导出的材质类（先查词表）", "files": []}

    # 幂等：源未变 + 产物齐全 + 尺寸对 → 跳过
    if not force and os.path.isfile(mpath):
        try:
            old = json.load(open(mpath, encoding="utf-8"))
        except Exception:
            old = {}
        if old.get("source_sha256") == src_sha:
            good = True
            for item in old.get("files", []):
                fp = os.path.join(tdir, item["file"])
                if not os.path.isfile(fp) or png_size(fp) != (item["w"], item["h"]):
                    good = False
                    break
            if good:
                return {"theme": theme, "ok": True, "skipped": True, "files": old["files"],
                        "palette": old.get("palette", []), "warn": suspects}

    os.makedirs(tdir, exist_ok=True)
    local_css = prepare_css(path, workdir, theme)
    link = "<link rel='stylesheet' href='file://%s'>" % local_css
    files = []
    problems = []

    for cls in mats:
        name = "mat-%s.png" % cls.lstrip(".")
        out_png = os.path.join(tdir, name)
        body = (link, "html,body{background:%s}.probe{width:%dpx;height:%dpx}" % (theme_bg, TILE, TILE),
                "<div class='probe %s'></div>" % cls.lstrip("."))
        if not shot(chrome, body, TILE, TILE, out_png, workdir, theme + "-" + name):
            problems.append("%s 截图失败（产物不是 %dx%d）" % (cls, TILE, TILE))
            continue
        files.append({"file": name, "kind": "material-class", "class": cls.lstrip("."),
                      "w": TILE, "h": TILE, "sha256": sha256_file(out_png)})

    for token, tw, th in texs:
        name = "tex-%s.png" % token
        out_png = os.path.join(tdir, name)
        w, h = tw * 2, th * 2   # 铺两名样，肉眼能看出平铺节奏；tile 原尺寸记在 manifest
        body = (link, "html,body{background:%s}.probe{width:%dpx;height:%dpx;"
                "background-image:var(--%s);background-size:%dpx %dpx;background-repeat:repeat}"
                % (theme_bg, w, h, token, tw, th),
                "<div class='probe'></div>")
        if not shot(chrome, body, w, h, out_png, workdir, theme + "-" + name):
            problems.append("--%s 截图失败（产物不是 %dx%d）" % (token, w, h))
            continue
        files.append({"file": name, "kind": "svg-token", "token": token, "tile_w": tw,
                      "tile_h": th, "w": w, "h": h, "sha256": sha256_file(out_png)})

    # 材质板：一张图看全该主题材质，A 出口直接当 style 参考图
    if files:
        rows = (len(files) + BOARD_COLS - 1) // BOARD_COLS
        bw = BOARD_COLS * BOARD_CELL + BOARD_PAD * 2
        bh = BOARD_HEAD + rows * (BOARD_CELL + 44) + BOARD_PAD
        cells = []
        for i, item in enumerate(files):
            r, c = divmod(i, BOARD_COLS)
            x = BOARD_PAD + c * BOARD_CELL
            y = BOARD_HEAD + r * (BOARD_CELL + 44)
            label = item.get("class") or ("--" + item["token"])
            if item["kind"] == "svg-token":
                cell_css = "background-image:var(--%s);background-size:%dpx %dpx" % (
                    item["token"], item["tile_w"], item["tile_h"])
            else:
                cell_css = ""
            cells.append(
                "<div style='position:absolute;left:%dpx;top:%dpx;width:%dpx;height:%dpx;"
                "background-color:%s;border:1px solid rgba(0,0,0,.12)'>"
                "<div style='width:100%%;height:100%%;%s' class='%s'></div></div>"
                "<div style='position:absolute;left:%dpx;top:%dpx;font:12px/1.4 -apple-system,"
                "sans-serif;color:#333'>%s</div>"
                % (x, y, BOARD_CELL - 2, BOARD_CELL - 2, theme_bg, cell_css,
                   item.get("class", "") if item["kind"] == "material-class" else "",
                   x, y + BOARD_CELL + 2, label))
        head = ("<div style='position:absolute;left:%dpx;top:28px;font:600 26px/1.2 "
                "-apple-system,sans-serif;color:#111'>%s</div>"
                "<div style='position:absolute;left:%dpx;top:62px;font:13px/1.2 "
                "-apple-system,sans-serif;color:#666'>瓦作出图 · %d 项材质 · 生成于 %s</div>"
                % (BOARD_PAD, theme, BOARD_PAD, len(files),
                   datetime.now().strftime("%Y-%m-%d")))
        board_png = os.path.join(tdir, "board.png")
        body = (link, "", "<div style='position:relative;width:%dpx;height:%dpx'>%s%s</div>"
                % (bw, bh, head, "".join(cells)))
        if shot(chrome, body, bw, bh, board_png, workdir, theme + "-board"):
            files.append({"file": "board.png", "kind": "board", "w": bw, "h": bh,
                          "sha256": sha256_file(board_png)})
        else:
            problems.append("board.png 截图失败（产物不是 %dx%d）" % (bw, bh))

    manifest = {
        "theme": theme,
        "source": "../themes/%s.css" % theme,
        "source_sha256": src_sha,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "renderer": "chrome-headless",
        "palette": palette(css),
        "files": files,
        "unknown_material_like": suspects,
    }
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return {"theme": theme, "ok": not problems, "skipped": False, "files": files,
            "palette": manifest["palette"], "warn": suspects, "problems": problems}


def main():
    ap = argparse.ArgumentParser(add_help=True, description="瓦作出图：主题 CSS → PNG 材质与材质板")
    ap.add_argument("--only", help="只导出某个主题（如 qiu-r）")
    ap.add_argument("--list", action="store_true", help="只列出会导出什么，不渲染")
    ap.add_argument("--force", action="store_true", help="覆盖已有产物")
    ap.add_argument("--out", default=OUT, help="输出目录（默认 assets/textures）")
    ap.add_argument("--json", action="store_true", help="末行输出机器摘要")
    args = ap.parse_args()

    print("root=%s" % ROOT)          # 禅院塔 §2.304：被测根显式打印
    print("themes=%s" % THEMES)
    print("out=%s" % args.out)
    globals()["OUT"] = args.out

    files = theme_files(args.only)
    if not files:
        print("error: 找不到主题（%s）" % (args.only or "全部"), file=sys.stderr)
        return 2

    if args.list:
        for p in files:
            css = open(p, encoding="utf-8").read()
            mats = material_classes(css)
            texs = svg_tokens(css)
            print("%-16s 材质 %d：%s｜纹理 %d：%s"
                  % (os.path.splitext(os.path.basename(p))[0], len(mats),
                     ",".join(c.lstrip(".") for c in mats) or "-", len(texs),
                     ",".join(t[0] for t in texs) or "-"))
        return 0

    chrome = find_chrome()
    if not chrome:
        print("error: 找不到 Chrome/Chromium（可用 CHROME_BIN 指定）", file=sys.stderr)
        return 2
    print("chrome=%s" % chrome)

    workdir = tempfile.mkdtemp(prefix="lescio-tex-")
    results = []
    try:
        for p in files:
            r = build_theme(p, chrome, workdir, force=args.force)
            results.append(r)
            if r.get("ok") and r.get("skipped"):
                print("= %-16s 跳过（源未变，产物齐全）" % r["theme"])
            elif r.get("ok"):
                print("✓ %-16s %d 项 → %s/"
                      % (r["theme"], len(r["files"]), os.path.basename(args.out)))
            else:
                print("✗ %-16s %s" % (r["theme"], r.get("error") or "; ".join(r.get("problems", []))))
            for s in r.get("warn", []):
                print("  ⚠ 未进词表的疑似材质：%s（加进 MATERIAL_WORDS 再导）" % s)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)   # 收尾：临时件清掉（§2.336）

    bad = [r for r in results if not r.get("ok")]
    total = sum(len(r.get("files", [])) for r in results)
    print("共 %d 主题 / %d 张图%s" % (len(results), total,
                                     "，失败 %d" % len(bad) if bad else ""))
    if args.json:
        print(json.dumps({"ok": not bad, "themes": len(results), "images": total,
                          "failed": [r["theme"] for r in bad],
                          "textures_dir": args.out}, ensure_ascii=False))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
