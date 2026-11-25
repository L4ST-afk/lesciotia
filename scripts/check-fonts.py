#!/usr/bin/env python3
"""字体闸门：查内化字体的子集内容与声明一致性。

为什么要有这个脚本（2026-11-21 踩坑）：
  龙华寺换法华文楷时，要求「汉字用楷书、标点回落系统宋体」。第一版子集把
  `，。；：！“”‘’《》〈〉「」` 一起打了进去 —— 页面看起来完全正常，闸门全绿，
  但标点根本没回落到宋体。根因：CSS 的字体回退是**按字形**的，字体里有这个
  字形，浏览器就不会回退。光改 font-family 回退链无效，必须从子集里删掉。

  这个错误没有任何既有闸门能发现：selftest 只编译脚本，check-preview-sync 只
  对账色值，check-theme-colors 只看对比度。字体子集内容是盲区。

判据（四条）：
  F1  子集里必须有汉字。空子集或纯拉丁子集一律红。
  F2  `--ff-title` 等字体族在主题 CSS 里必须能解析到已声明的 @font-face 或系统字体。
  F3  @font-face 声明了但本主题无任何选择器引用 → 死声明（白加载体积）。
  F4  主题 CSS 里出现 `font-family:'X'` 而 X 既无 @font-face 也无系统字体兜底 → 红。

用法：
  python3 scripts/check-fonts.py [--only THEME] [--json]

退出码：0 全绿；1 有 FAIL。
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
THEMES = os.path.join(SKILL, "assets", "themes")
FONTS = os.path.join(SKILL, "assets", "fonts")

# 系统字体白名单：这些不要求在 assets/fonts 里有文件
SYSTEM_FONTS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "STZhongsong", "华文中宋", "Songti SC", "STSong", "SimSun", "宋体",
    "Source Han Serif SC", "思源宋体", "Noto Serif CJK SC", "Noto Serif SC",
    "Source Han Sans SC", "思源黑体", "Noto Sans CJK SC", "PingFang SC",
    "Heiti SC", "SimHei", "黑体",
    "Kaiti SC", "STKaiti", "楷体", "LXGW WenKai", "霞鹜文楷",
    "SF Mono", "Menlo", "Consolas", "Roboto Mono",
    "Georgia", "Times New Roman", "Helvetica", "Arial",
    # ⛔ 内化字体的中文别名不要放这里：F5 要靠「不在白名单」才走别名解析，
    #    放进白名单就永远解不到 @font-face 的 src，只能报「找不到文件」。
    #    （2026-11-21 踩过：法华文楷在白名单里，F5 一直 WARN）
    # 各主题回退链里实际出现的商业/系统字体（本机已装，非内化）
    "Bodoni 72", "Bodoni 72 Oldstyle", "Didot", "Playfair Display",
    "Optima", "Futura", "Gill Sans", "Baskerville", "Hoefler Text",
    "PingFang TC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑",
    "Noto Sans SC", "Noto Serif TC", "Source Han Serif TC",
}

PUNCT_PROBE = "，。、；：？！“”‘’（）《》〈〉【】—…·「」『』～×／"


FONTS_MANIFEST = os.path.join(FONTS, "FONTS.md")


def self_supplied_paths():
    """读 FONTS.md 的「放置路径」列，返回登记为「自备」的相对路径集合。

    为什么需要这个（2026-11-21）：本库改成不随包分发第三方字体，缺字体是
    **预期状态**，不是错误。F1 若仍按「文件必须存在」判红，用户 clone 下来
    一字未动就先红一片，闸门失去意义。判据改成：文件存在 → 查子集内容；
    文件不存在 → 查 FONTS.md 有没有登记；登记过就放行（WARN 提示自备）。
    """
    if not os.path.isfile(FONTS_MANIFEST):
        return set()
    out = set()
    try:
        with io.open(FONTS_MANIFEST, encoding="utf-8") as fh:
            for line in fh:
                # 表格行：| 主题 | 字体 | `路径` | 大小 | 授权 | 获取 |
                m = re.search(r"`(assets/fonts/[^`]+\.(?:woff2|ttf|otf))`", line)
                if m:
                    out.add(os.path.normpath(m.group(1)))
    except OSError:
        pass
    return out


try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None


def load_cmap(path):
    """读 woff2/ttf 的 cmap。fontTools 缺失时由 main() 直接判红，
    ⛔ 不再让 F1 降级成 WARN（2026-11-23 评审#06：软跳过＝闸门可被环境绕过）。"""
    if TTFont is None:
        return None
    try:
        return TTFont(path).getBestCmap()
    except Exception:
        return None


_SYS_INDEX = None


def system_family_index():
    """本机系统字体族名小写集合（懒加载，只算一次）。"""
    global _SYS_INDEX
    if _SYS_INDEX is not None:
        return _SYS_INDEX
    import platform
    home = os.path.expanduser("~")
    if platform.system() == "Darwin":
        dirs = [os.path.join(home, "Library", "Fonts"), "/Library/Fonts"]
    elif platform.system() == "Windows":
        dirs = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")]
    else:
        dirs = [os.path.join(home, ".local", "share", "fonts"), "/usr/share/fonts"]
    out = set()
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        _SYS_INDEX = out
        return out
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for e in ("*.ttf", "*.otf", "*.ttc", "*.TTF", "*.OTF", "*.TTC"):
            for f in glob.glob(os.path.join(d, e)):
                try:
                    t = TTFont(f, fontNumber=0, lazy=True)
                    for r in t["name"].names:
                        if r.nameID in (1, 16):
                            try:
                                out.add(r.toUnicode().strip().lower())
                            except Exception:
                                pass
                except Exception:
                    continue
    _SYS_INDEX = out
    return out


def subset_name_table(path):
    """读字体 name 表里的 family / typo family / PostScript 名，返回集合。"""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    try:
        t = TTFont(path, lazy=True)
        out = set()
        for r in t["name"].names:
            if r.nameID in (1, 4, 6, 16):
                try:
                    v = r.toUnicode().strip()
                    if v:
                        out.add(v)
                except Exception:
                    pass
        return out
    except Exception:
        return None


def declared_faces(css):
    """返回 {family: (path, weight)} —— CSS 里 @font-face 声明的族。"""
    out = {}
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, re.S):
        block = m.group(1)
        fam = re.search(r"font-family\s*:\s*['\"]?([^'\";]+)", block)
        src = re.search(r"url\(['\"]?([^'\")]+)", block)
        if fam:
            out[fam.group(1).strip()] = src.group(1) if src else None
    return out


def used_families(css):
    """返回 CSS 里被「引用」的族名。

    ⚠️ 必须先把 @font-face 块整段挖掉再找 font-family —— 否则 @font-face 里的
    font-family 会被当成「引用」，F3（死声明）永远不触发，F4 还会把中文别名
    全报成未知族（2026-11-21 首版就是这么误报 13 条的）。
    """
    stripped = re.sub(r"@font-face\s*\{.*?\}", "", css, flags=re.S)
    used = set()
    # ⚠️ 必须同时扫 --ff-* 和 --font-*：主题里两种写法都有。
    # 友好大厦把族名直接写在 --font-display 里（不是 --ff-title），
    # 只扫 --ff-* 会把它误判成「@font-face 死声明」（2026-11-21 首版误报）。
    pats = [r"font-family\s*:\s*([^;}]+)",
            r"--ff-[a-z]+\s*:\s*([^;}]+)",
            r"--font-[a-z]+\s*:\s*([^;}]+)"]
    for pat in pats:
        for m in re.finditer(pat, stripped):
            for part in m.group(1).split(","):
                name = part.strip().strip("'\"").strip().rstrip(")")
                if name and not name.startswith("var("):
                    used.add(name)
    return used


SYS_DIRS = [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts",
            "/System/Library/Fonts", "/System/Library/Fonts/Supplemental"]


def _sys_dirs():
    return list(SYS_DIRS)


# 族名 → 文件名关键字。macOS 上族名与文件名经常对不上：
#   STKaiti → simkai.ttf、STSong → songti.ttc、STZhongsong → STZhongsong.ttf
# 不做映射就只能「查不到」，而查不到会被当成通过（首版就是这么漏掉楷体的）。
FAMILY_FILE_HINTS = {
    "stkaiti": ["simkai", "kaiti"],
    "stsong": ["songti", "stsong"],
    "stzhongsong": ["zhongsong"],
    "songtisc": ["songti"],
    "kaitisc": ["kaiti"],
    "stsongti": ["songti"],
    "lxgwwenkai": ["wenkai"],
    "pingfangsc": ["pingfang"],
    "heitisc": ["heiti"],
}


def system_font_punct(family):
    """查本机系统字体里 family 是否含全角标点。

    返回 (bad, found)：
      bad   —— 命中的标点列表（空＝不含标点）
      found —— 是否在本机找到了这个字体的文件
    ⚠️ 必须区分「不含标点」和「没找到文件」。首版把两者都返回 []，
       于是楷体 STKaiti（本机文件名是 simkai.ttf，名字对不上）被静默放行，
       变异测试里插进回退链也不报红（2026-11-21 实测漏网）。
    """
    key = re.sub(r"[^a-z0-9]", "", family.lower())
    if not key:
        return [], False
    keys = FAMILY_FILE_HINTS.get(key, [key])
    for d in _sys_dirs():
        if not os.path.isdir(d):
            continue
        for f in glob.glob(os.path.join(d, "*")):
            base = re.sub(r"[^a-z0-9]", "", os.path.basename(f).lower())
            if not any(k in base for k in keys):
                continue
            cmap = load_cmap(f)
            if cmap is None:
                continue
            bad = [c for c in PUNCT_PROBE if ord(c) in cmap]
            return bad, True
    return [], False


def global_font_aliases():
    """assets/fonts.css 是全局字体层：每个 deck 都 <link> 它，@font-face 写在那一份里是对的。
    F4 只看本主题 CSS，会把它误判成「本主题没声明」——所以全局声明的族名要算进白名单。"""
    fonts_css = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts.css")
    if not os.path.isfile(fonts_css):
        return set()
    css = open(fonts_css, encoding="utf-8").read()
    out = set()
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, re.S):
        for fm in re.finditer(r"font-family\s*:\s*([^;}]+)", m.group(1)):
            for part in fm.group(1).split(","):
                nm = part.strip().strip("'\"").strip()
                if nm:
                    out.add(nm)
    return out


GLOBAL_ALIASES = global_font_aliases()


def check_theme(name, css_path, font_files):
    fails, warns = [], []
    css = open(css_path, encoding="utf-8").read()

    faces = declared_faces(css)
    used = used_families(css)

    # 别名集合：@font-face 块里 font-family 出现过的所有名字。
    # 内化字体常写成 font-family:'FahwaWenkai','法华文楷'（同一族的英文名+中文名），
    # 中文名不是独立族，不该报 F4。
    aliases = set()
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, re.S):
        for fm in re.finditer(r"font-family\s*:\s*([^;}]+)", m.group(1)):
            for part in fm.group(1).split(","):
                nm = part.strip().strip("'\"").strip()
                if nm:
                    aliases.add(nm)
    aliases |= GLOBAL_ALIASES

    # F4：只查「内化字体有没有正确声明」。
    # ⛔ 不报回退链里的系统/商业字体（Lato、Segoe UI、华文黑体…）——那些本来就
    #    该由系统提供，报出来只是噪音（2026-11-21 首版一次报了 26 条）。
    # 判据：族名能在 assets/fonts/ 里找到同名文件，却没在本主题 @font-face 里声明 → 红。
    for fam in sorted(used):
        if fam in faces or fam in SYSTEM_FONTS or fam in aliases:
            continue
        # 族名与某个内化字体文件同名（忽略大小写与连字符）→ 说明是本库字体但没声明
        norm = re.sub(r"[^a-z0-9]", "", fam.lower())
        hit = [f for f in font_files if norm and norm in re.sub(r"[^a-z0-9]", "", f.lower())]
        if hit:
            fails.append(f"F4 引用了内化字体 {fam!r} 但本主题没有对应 @font-face（会静默回落系统字体）")

    # F3：@font-face 声明了但没人引用
    for fam, src in faces.items():
        if fam not in used:
            size = ""
            if src:
                p = os.path.normpath(os.path.join(os.path.dirname(css_path), src))
                if os.path.isfile(p):
                    size = f"，{os.path.getsize(p) / 1024 / 1024:.2f} MB"
            fails.append(f"F3 @font-face 声明了 {fam!r} 但本主题无选择器引用（白加载{size}）")

    self_supplied = self_supplied_paths()

    # F1：每个被引用的内化字体，子集里必须有汉字
    #     文件不存在时查 FONTS.md：登记为「自备」→ 放行（WARN），否则红。
    for fam, src in faces.items():
        if not src:
            continue
        p = os.path.normpath(os.path.join(os.path.dirname(css_path), src))
        if not os.path.isfile(p):
            rel = os.path.relpath(p, SKILL).replace(os.sep, "/")
            if os.path.normpath(rel) in self_supplied:
                warns.append(
                    f"F1 {fam!r} 字体未随包（自备）：{rel} —— 缺字时回落系统字体，见 assets/fonts/FONTS.md"
                )
            else:
                fails.append(
                    f"F1 @font-face {fam!r} 指向的文件不存在且未在 FONTS.md 登记：{rel}"
                )
            continue
        cmap = load_cmap(p)
        if cmap is None:
            warns.append(f"F1 无法读取 {os.path.basename(p)}（fontTools 未装？）")
            continue
        han = sum(1 for c in cmap if "\u4e00" <= chr(c) <= "\u9fff")
        if han == 0:
            fails.append(f"F1 {os.path.basename(p)} 子集里 0 个汉字")
        punct = [c for c in PUNCT_PROBE if ord(c) in cmap]

    # ── F5：标点回落策略 ──────────────────────────────────────────────
    # 主题用 `@font-policy han-only` 声明「标题字体只承载汉字，标点回落系统宋体」。
    #
    # 判据不是「链里不许有含标点的字体」——宋体本身就含标点，它就是落点。
    # 真正要守的是**顺序**：CSS 回退按字形走，谁先有标点字形谁截走。
    # 所以链里第一个含全角标点的字体，必须就是标点目标（宋体系）。
    # 若中间插进霞鹜文楷 / 楷体这类「含标点但不是目标」的字体，标点就落错了。
    policy = re.search(r"@font-policy\s+([a-z-]+)", css)
    if policy and policy.group(1) == "han-only":
        chain = None
        for var in ("--ff-title", "--font-display"):
            m = re.search(re.escape(var) + r"\s*:\s*([^;}]+)", css)
            if m:
                chain = [x.strip().strip("'\"").strip()
                         for x in m.group(1).split(",")]
                break
        if chain:
            # 标点目标：宋体系（含标点，且是我们要的落点）
            TARGET = {"Source Han Serif SC", "思源宋体", "Noto Serif CJK SC",
                      "Noto Serif SC", "STZhongsong", "华文中宋", "Songti SC",
                      "STSong", "SimSun", "宋体"}
            first_punct = None
            prev_declared = None   # 链里上一个能解析到 @font-face 的族
            for fam in chain:
                if fam in ("serif", "sans-serif", "monospace", "system-ui"):
                    continue
                src = faces.get(fam)
                if src:
                    prev_declared = src
                elif prev_declared and fam not in SYSTEM_FONTS:
                    # 中文别名紧跟英文族名（'FahwaWenkai','法华文楷'），
                    # 同一款字，直接沿用前一个的 src。
                    src = prev_declared
                bad = []
                found = True
                if src:
                    fp = os.path.normpath(os.path.join(os.path.dirname(css_path), src))
                    cmap = load_cmap(fp) if os.path.isfile(fp) else None
                    if cmap is not None:
                        bad = [c for c in PUNCT_PROBE if ord(c) in cmap]
                else:
                    bad, found = system_font_punct(fam)
                    if not found:
                        # 查不到文件 ≠ 不含标点。宁可报 WARN 让人确认，也不静默放行。
                        warns.append(
                            f"F5 回退链里的 {fam!r} 在本机找不到字体文件，"
                            f"无法判定它是否含全角标点（⛔ 不等于通过）")
                if bad:
                    first_punct = (fam, bad)
                    break
            if first_punct:
                fam, bad = first_punct
                if fam not in TARGET:
                    fails.append(
                        f"F5 标点回落策略下，回退链里 {fam!r} 排在宋体之前且含 "
                        f"{len(bad)} 个全角标点（{''.join(bad[:8])}），会把标点截走；"
                        f"⛔ 该字体必须从链里删掉，标点才能落到宋体")
            else:
                fails.append(
                    "F5 标点回落策略下，回退链里找不到任何含全角标点的字体，"
                    "标点将落到浏览器默认字体（不可控）")

    # ── F7：local() 族名可解析 ────────────────────────────────────────
    # `src:local('X'),url(...)` 里 X 写错时，浏览器**静默跳过 local()**，
    # 直接加载 url —— 页面看着正常，但「用户装了系统字体就用系统的」这条
    # 承诺失效了，而且没有任何报错。这类错和 F6 同源：声明写了没生效。
    #
    # 判据：每个 local() 的族名，必须能在**子集文件的 name 表**里找到
    # （family / typographic family / PostScript 名任一），或在本机系统字体里
    # 存在。两者都找不到 → 红（说明这个名字是凭空写的）。
    # ⚠️ 本机没装该字体不算错（那是用户环境差异），只查「名字本身有没有依据」。
    for fam, src in faces.items():
        if not src:
            continue
        p = os.path.normpath(os.path.join(os.path.dirname(css_path), src))
        if not os.path.isfile(p):
            continue
        block = None
        for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, re.S):
            if re.search(r"font-family\s*:\s*['\"]?" + re.escape(fam) + r"['\"]?\s*;", m.group(1)):
                block = m.group(1)
                break
        if not block:
            continue
        locs = re.findall(r"local\(\s*['\"]([^'\"]+)['\"]\s*\)", block)
        if not locs:
            continue
        known = subset_name_table(p)
        if known is None:
            warns.append(f"F7 无法读取 {os.path.basename(p)} 的 name 表，跳过 local() 校验")
            continue
        for name in locs:
            if name in known:
                continue
            if name.lower() in system_family_index():
                continue
            fails.append(
                f"F7 local('{name}') 在子集 {os.path.basename(p)} 的 name 表里找不到，"
                f"本机也没装这个族名 —— local() 会被静默跳过，"
                f"可用名：{', '.join(sorted(known)[:4])}"
            )

    # ── F8：han-only 策略下，带 local() 的 @font-face 必须声明 unicode-range ──
    # 这是 F5 的补丁，也是 2026-11-21 差点踩的坑。
    # `@font-policy han-only` 要求标点回落系统宋体。子集剔掉了标点，所以
    # 走 url() 时没问题。但一旦加了 local('完整版族名')，用户装了完整版 ttf
    # （**含全角标点**）后浏览器会优先命中它 —— 标点被楷体截走，策略直接破。
    # 唯一的解法是 unicode-range：让浏览器按码位决定用不用这款字体，
    # 把全角标点（U+3000-303F、U+FF00-FFEF、U+2014、U+00B7 等）挡在区间外。
    # 判据：han-only 主题里，任何带 local() 的 @font-face 必须同时有 unicode-range。
    # ⚠️ 只查**标题字体**：策略原文是「标题字体只承载汉字/拉丁」。正文黑体
    # （--ff-body）用自己的标点是正常的，不在 han-only 管辖范围内 —— 判据写宽
    # 会把 SongguHei 这种正文误判成红。
    han_only = bool(re.search(r"@font-policy\s+han-only", css))
    if han_only:
        title_fam = None
        tm = re.search(r"--ff-title\s*:\s*['\"]?([^'\",]+)", css)
        if tm:
            title_fam = tm.group(1).strip()
        if not title_fam:
            warns.append("F8 主题声明了 han-only 但读不到 --ff-title 的首位字体，跳过")
        else:
            for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, re.S):
                block = m.group(1)
                fm = re.search(r"font-family\s*:\s*['\"]?([^'\";]+)", block)
                if not fm or fm.group(1).strip() != title_fam:
                    continue
                if not re.search(r"local\(", block):
                    continue
                if re.search(r"unicode-range\s*:", block):
                    continue
                fails.append(
                    f"F8 han-only 主题的标题字体 '{title_fam}' 用了 local() 但没声明 "
                    f"unicode-range —— 用户装了完整版字体后标点会被该字体截走，"
                    f"违反 han-only 策略")

    # ── F6：字体 token 死引用 ──────────────────────────────────────────
    # `font-family:var(--font-body)` 而主题里从没定义 --font-body 时，
    # 浏览器**静默丢弃**整条声明，字体走继承 —— 既不报错也不回落，
    # 页面看着「有点像但不是」。万航渡的 .g-card h3 就这么错了很久
    # （2026-11-21 才发现：九个主题都没有 --font-body，只有 --font-sans）。
    defined = set(re.findall(r"(--font-[a-z-]+)\s*:", css))
    defined |= set(re.findall(r"(--ff-[a-z-]+)\s*:", css))
    # 2026-11-23 评审#01：defined 同时收了 --ff-*，正则却只认 --font-*，写 var(--ff-xxx) 会漏报
    for m in re.finditer(r"font-family\s*:\s*var\((--(?:font|ff)-[a-z0-9-]+)\)", css):
        tok = m.group(1)
        if tok not in defined:
            fails.append(
                f"F6 font-family 引用了未定义的 {tok}（本主题只有 "
                f"{', '.join(sorted(defined)) or '无'}），声明会被浏览器丢弃，字体走继承")

    return {"theme": name, "fails": fails, "warns": warns,
            "faces": {k: v for k, v in faces.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="只查一个主题（不含 .css）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if TTFont is None:
        print("FAIL 字体闸门：缺 fontTools（F1 子集汉字/标点判据无法执行）"
              "—— 装 python3 -m pip install --user fonttools，⛔ 本闸不接受软跳过")
        return 2

    font_files = [os.path.basename(p) for p in glob.glob(os.path.join(FONTS, "*", "*"))]

    if args.only:
        paths = [os.path.join(THEMES, args.only + ".css")]
    else:
        # 只查自建主题，不查 upstream
        paths = sorted(p for p in glob.glob(os.path.join(THEMES, "*.css")))

    results = []
    for p in paths:
        if not os.path.isfile(p):
            print(f"! 找不到 {p}", file=sys.stderr)
            continue
        results.append(check_theme(os.path.basename(p)[:-4], p, font_files))

    total_fail = sum(len(r["fails"]) for r in results)
    total_warn = sum(len(r["warns"]) for r in results)

    if args.json:
        print(json.dumps({"themes": len(results), "fail": total_fail,
                          "warn": total_warn, "results": results},
                         ensure_ascii=False, indent=1))
    else:
        for r in results:
            mark = "FAIL" if r["fails"] else ("WARN" if r["warns"] else " OK ")
            print(f"[{mark}] {r['theme']}")
            for f in r["fails"]:
                print(f"       ✗ {f}")
            for w in r["warns"]:
                print(f"       ! {w}")
        print()
        print(f"字体闸门：{len(results)} 个主题，FAIL {total_fail}，WARN {total_warn}")

    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
