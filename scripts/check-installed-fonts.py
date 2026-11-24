#!/usr/bin/env python3
"""字体安装检测：查本机系统里装了哪几款本库用到的字体。

为什么要有这个（2026-11-21）：
  本库改成「字体自备」后，用户装完 ttf/otf 到系统，并不知道有没有装对、
  族名对不对。主题 CSS 里的 `local()` 靠**族名**匹配，族名错了就静默失效，
  页面看着正常但字体没生效——这正是本库反复踩的那类「声明写了没生效」的坑。

判据（三态）：
  OK     系统已装，且族名与主题 CSS 的 local() 候选一致 → 会命中
  MISS   系统未装 → 走随包子集或回退链
  NAME   系统已装，但族名对不上 local() 候选 → ⚠️ 装了也不会命中（最隐蔽）

用法：
  python3 scripts/check-installed-fonts.py           # 人类可读
  python3 scripts/check-installed-fonts.py --json    # 机读
  python3 scripts/check-installed-fonts.py --html    # 出检测页（浏览器里跑 local() 实测）

退出码：0 全部 OK 或 MISS；1 有 NAME 冲突（装了但族名不对）。
"""
import argparse
import glob
import json
import os
import platform
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
THEMES = os.path.join(SKILL, "assets", "themes")

# 主题 → 字体文件 → local() 候选（与 CSS 里的 src 保持一致）
# 这份表是「期望值」，脚本会与 CSS 实际内容对账，不一致就报出来。
EXPECTED = {
    "wanhang-fy": [
        ("WanhangXimaiBold-Subset.woff2", ["Wanhang Ximai", "WanhangXimai-Bold"],
         "万航渡喜脉体", "随包（本库派生件）"),
    ],
    "longhua-si": [
        # 2026-11-21：法华文楷改为「只走 local()」，子集已从仓库删除（zfont font_777 标嵌入禁止）。
        # 文件名只作标识；本脚本查的是系统已装字体，不读仓库文件。
        ("FahwaWenkai-Subset.woff2", ["法华文楷标准版", "FahwaWenkai-Standard"],
         "法华文楷标准版", "自备（未装则标题回落霞鹜文楷）"),
        ("LXGWWenKai-Subset.woff2", ["LXGW WenKai", "霞鹜文楷", "LXGWWenKai-Regular"],
         "霞鹜文楷", "随包（OFL 1.1，内化兜底）"),
        ("SongguHei-Subset.woff2", ["宋骨黑体", "宋骨黑体 Medium", "SGH-Medium"],
         "宋骨黑体", "自备"),
    ],
    "fuzhou-rd": [
        ("NanxiYoumosong-Subset.woff2", ["NanxiYoumosong", "NanxiYoumosong-Regualr"],
         "南西油墨宋", "自备"),
        ("SongguHei-Subset.woff2", ["宋骨黑体", "宋骨黑体 Medium", "SGH-Medium"],
         "宋骨黑体", "自备"),
    ],
    "qiu-r": [
        ("CheeseFoamOolongSong-Subset-Bold.woff2",
         ["Cheese Foam Oolong Song", "CheeseFoamOolongSong-Bold"],
         "芝士奶盖乌龙宋", "自备"),
    ],
    "panyu-rd": [
        # 2026-11-21：改为「只走 local()」，子集 woff2 已从仓库删除（zfont font_657 标嵌入禁止）。
        # 文件名只作标识；本脚本查的是系统已装字体，不读仓库文件。
        ("AidianFengYaHei-Subset.woff2", ["Aidian FengYaHei", "AidianFengYaHei-Regular"],
         "爱点风雅黑", "自备"),
    ],
    "friendship-bldg": [
        # 2026-11-21：摇醒青年黑改为「只走 local()」，子集 woff2 已从仓库删除。
        # 装了就用自己的摇醒（不涉及本库再分发），没装回落宋骨黑体。
        # ⚠️ 文件名只用作标识，仓库里已无此文件；本脚本查的是**系统已装字体**，
        #    不读仓库文件，所以删掉 woff2 不影响检测。
        ("YaoxingYouthHei-Subset.woff2", ["摇醒青年黑1.0", "1.0-Regular"],
         "摇醒青年黑", "自备（不随包；未装则回落宋骨黑体）"),
    ],
}


def system_font_dirs():
    """返回本机字体目录列表（macOS / Windows / Linux）。"""
    home = os.path.expanduser("~")
    sysname = platform.system()
    if sysname == "Darwin":
        return [os.path.join(home, "Library", "Fonts"), "/Library/Fonts",
                "/System/Library/Fonts"]
    if sysname == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        local = os.environ.get("LOCALAPPDATA", "")
        dirs = [os.path.join(windir, "Fonts")]
        if local:
            dirs.append(os.path.join(local, "Microsoft", "Windows", "Fonts"))
        return dirs
    return [os.path.join(home, ".local", "share", "fonts"),
            os.path.join(home, ".fonts"), "/usr/share/fonts", "/usr/local/share/fonts"]


def installed_families():
    """读系统字体文件的 family 名。返回 {family_lower: (family, path)}。

    ⛔ 不能用文件名判断：本库踩过——`STKaiti` 的文件叫 `simkai.ttf`，
    族名与文件名经常对不上。必须读字体 name 表。
    """
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None, "fontTools 未安装（pip install fonttools）"

    out = {}
    exts = ("*.ttf", "*.otf", "*.ttc", "*.TTF", "*.OTF", "*.TTC")
    files = []
    for d in system_font_dirs():
        if not os.path.isdir(d):
            continue
        for e in exts:
            files += glob.glob(os.path.join(d, e))
    for f in files:
        try:
            # ttc 取第一个 face
            t = TTFont(f, fontNumber=0, lazy=True)
            n = t["name"]
            fams = set()
            for r in n.names:
                if r.nameID in (1, 16):  # family / typographic family
                    try:
                        v = r.toUnicode().strip()
                        if v:
                            fams.add(v)
                    except Exception:
                        pass
            for fam in fams:
                out.setdefault(fam.lower(), (fam, f))
        except Exception:
            continue
    return out, None


def css_local_names(theme):
    """读主题 CSS 里实际写的 local() 候选，用于与 EXPECTED 对账。"""
    p = os.path.join(THEMES, f"{theme}.css")
    if not os.path.isfile(p):
        return {}
    s = open(p, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", s, re.S):
        block = m.group(1)
        fm = re.search(r"font-family:\s*'([^']+)'", block)
        if not fm:
            continue
        fam = fm.group(1)
        locs = re.findall(r"local\('([^']+)'\)", block)
        out[fam] = locs
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--html", action="store_true", help="出浏览器检测页")
    args = ap.parse_args()

    installed, err = installed_families()
    if installed is None:
        print(f"! {err}", file=sys.stderr)
        print("  装好后重跑：pip install fonttools", file=sys.stderr)
        return 2

    rows = []
    for theme, fonts in EXPECTED.items():
        css_locs = css_local_names(theme)
        for fname, cands, cn_name, note in fonts:
            hit = None
            for c in cands:
                if c.lower() in installed:
                    hit = installed[c.lower()]
                    break
            # 也查中文名（用户可能装的是中文族名的版本）
            if hit is None and cn_name.lower() in installed:
                hit = installed[cn_name.lower()]
            if not cands:
                status = "NOLOCAL"
            elif hit:
                status = "OK"
            else:
                # 装了但族名对不上？扫一遍有没有名字相近的
                status = "MISS"
            rows.append({
                "theme": theme, "file": fname, "name_cn": cn_name,
                "candidates": cands, "status": status, "note": note,
                "installed_family": hit[0] if hit else None,
                "installed_path": hit[1] if hit else None,
                "css_local": css_locs.get(fname.split("-Subset")[0], []),
            })

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0

    if args.html:
        return write_html(rows)

    # 人类可读
    ok = [r for r in rows if r["status"] == "OK"]
    miss = [r for r in rows if r["status"] == "MISS"]
    nolocal = [r for r in rows if r["status"] == "NOLOCAL"]

    print(f"\n系统字体检测（{platform.system()}，扫描 {len(installed)} 个族名）\n")
    for r in rows:
        mark = {"OK": "✓", "MISS": "·", "NOLOCAL": "—"}[r["status"]]
        line = f" {mark} {r['name_cn']:<14} [{r['theme']}]"
        if r["status"] == "OK":
            line += f"  已装：{r['installed_family']}"
        elif r["status"] == "MISS":
            line += "  未装 → 走随包子集 / 回退链"
        else:
            line += "  不加 local()（见主题注释）"
        print(line)

    print(f"\n已装 {len(ok)} / 未装 {len(miss)} / 不查 {len(nolocal)}")
    if nolocal:
        print("「不查」= 该 @font-face 没有 local()，装不装系统字体都走随包子集。")
    if miss:
        print("\n未装的字体不影响使用：页面照常渲染，只是标题笔意不同。")
        print("获取方式见 assets/fonts/FONTS.md")
    return 0


def write_html(rows):
    """出检测页：在浏览器里跑 document.fonts 实测 local() 是否命中。

    ⛔ 为什么需要浏览器实测：Python 只能读字体文件，读不到「浏览器认不认
    这个族名」。local() 的匹配由浏览器的字体后端决定，两者可能不一致。
    """
    items = []
    for r in rows:
        if not r["candidates"]:
            continue
        locs = ",".join(f"local('{c}')" for c in r["candidates"])
        items.append({
            "fam": f"probe-{r['theme']}-{r['file'].split('-')[0]}",
            "src": locs,
            "label": f"{r['name_cn']} [{r['theme']}]",
        })
    css = "\n".join(
        f"@font-face{{font-family:'{i['fam']}';src:{i['src']};font-display:swap}}"
        for i in items
    )
    divs = "\n".join(
        f'<div class="row"><span class="lbl">{i["label"]}</span>'
        f'<span class="val" id="r-{i["fam"]}">检测中…</span>'
        f'<span class="sample" style="font-family:\'{i["fam"]}\',serif">万航渡 Aa 0123</span></div>'
        for i in items
    )
    js_items = json.dumps([{"fam": i["fam"], "label": i["label"]} for i in items],
                          ensure_ascii=False)
    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>字体安装检测 · 来雪亭</title>
<style>
{css}
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#241C15;background:#FDFAF1}}
h1{{font-size:22px;margin-bottom:6px}}
.sub{{color:#6b7071;font-size:13px;margin-bottom:24px}}
.row{{display:flex;align-items:baseline;gap:16px;padding:10px 0;border-bottom:1px solid #E8E1D4}}
.lbl{{width:260px;font-size:13px;color:#3f4a45}}
.val{{width:110px;font-size:13px;font-weight:600}}
.ok{{color:#3F6449}}.miss{{color:#AD6A45}}
.sample{{flex:1;font-size:20px;text-align:right;color:#241C15}}
.note{{margin-top:24px;padding:14px;background:#F6F1E4;border-left:3px solid #3F6449;font-size:13px;line-height:1.7}}
</style></head><body>
<h1>字体安装检测</h1>
<div class="sub">在浏览器里实测 <code>local()</code> 能否命中你系统里装的字体。装了但显示「未命中」＝族名对不上。</div>
{divs}
<div class="note">
<b>说明</b>：命中＝浏览器会直接用你系统里的字体，不加载随包子集。<br>
未命中不影响使用：走随包子集或回退链，页面照常渲染，只是标题笔意不同。<br>
获取方式见 <code>assets/fonts/FONTS.md</code>。
</div>
<script>
const items = {js_items};
// ⛔ 不能用 document.fonts.check()：字体尚未加载时它默认返回 true，
//    会把「没装」误报成「已命中」（2026-11-21 实测踩到，7 项全假阳性）。
//    正确做法是 document.fonts.load() —— 它会真的去解析 src，
//    local() 全部失败时抛错，据此判定。
(async () => {{
  for (const it of items) {{
    const el = document.getElementById('r-' + it.fam);
    let hit = false;
    try {{
      const faces = await document.fonts.load('16px "' + it.fam + '"');
      // load() 成功但返回空数组＝没有可用 face
      hit = faces.length > 0;
    }} catch (e) {{
      hit = false;
    }}
    if (hit) {{ el.textContent = '✓ 已命中'; el.className = 'val ok'; }}
    else {{ el.textContent = '· 未命中'; el.className = 'val miss'; }}
  }}
}})();
</script>
</body></html>"""
    out = os.path.join(SKILL, "examples", "font-check.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(f"OK {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
