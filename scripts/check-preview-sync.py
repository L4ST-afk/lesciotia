#!/usr/bin/env python3
"""预览页一致性闸（判据级）：抓「改了主题、预览页没跟上」这一类静默漂移。

为什么需要它
------------
2026-11-20 那轮返工里，四个主题的预览页同时错了四类，全是静默的——
脚本退出码 0、日志全 OK、页面照常渲染，只是内容在说谎：

  1. 色板标签写旧值。11-20 配色体检改了 :root 的 token，但生成器里的
     色板替换表是硬编码的，12 个色值里 8 个对不上 CSS 真值。
  2. 材质样片用错类。友好大厦 CSS 定义了 10 个 .fb-* 真材质，预览页一个
     都没用，全用世纪广场的通用 .d-*，于是「鎏金塔身」显示拉丝不锈钢、
     「红玻璃星」显示瓷砖格——最核心的四个材质全没画出来。
  3. 组件类只活在生成器里。广兰路主题 CSS 里 0 个 .cp-*，预览页靠内联
     兜底补，而兜底写死了旧色 #e0632f。
  4. 导览面板还是上游主题的语汇。世纪大道是地铁站台，导航却写着
     「广场/餐饮/公园/植被/休憩」，卡片标题还是 Century Sq。

selftest.py 只证「脚本没坏到起不来」，这四类它一个都抓不到。这个闸门
直接读产物 HTML，逐条对回主题 CSS 与模板，任一条不成立就红。

用法
----
    python3 scripts/check-preview-sync.py                 # 查全部已生成的预览页
    python3 scripts/check-preview-sync.py --only century-sq
    python3 scripts/check-preview-sync.py --json out.json

退出码 0 = 全过；1 = 有 FAIL。WARN 不影响退出码，但要人看。
⛔ 不联网、不写业务文件；--json 才写你指定的那个文件。
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
THEMES = os.path.join(ROOT, "assets", "themes")
PREVIEWS = os.path.join(ROOT, "examples", "previews")
TEMPLATE = os.path.join(ROOT, "scripts", "preview-template.html")
TPL = os.path.join(HERE, "preview-template.html")

# 每个主题的色板顺序（与 gen-theme-preview.py 的 PALETTE_SPEC 同源）
PALETTE_SPEC = {
    "guanglan-rd": ["--accent", "--accent-2", "--accent-3", "--good"],
    "century-sq": ["--primary", "--line-2", "--line-4", "--line-6"],
    "century-ave": ["--primary", "--line-2", "--line-4", "--line-6"],
    "friendship-bldg": ["--gold", "--red", "--accent-3", "--mint"],
    "qiu-r": ["--primary", "--line-2", "--line-4", "--line-6"],
    "panyu-rd": ["--primary", "--line-2", "--line-4", "--line-6"],
    "wanhang-fy": ["--primary", "--line-2", "--line-4", "--line-6"],
    "fuzhou-rd": ["--primary", "--vermilion", "--line-2", "--line-6"],
    "longhua-si": ["--sandal", "--tower", "--gold", "--peach"],
}

# 各主题「导览面板」必须出现的自有语汇，以及必须消失的上游语汇。
# 上游语汇来自世纪广场的公园导览，出现在别的主题里就是没换干净。
GUIDE_LEXICON = {
    "century-ave": {
        "must_have": ["站台", "换乘"],
        "must_not": ["植被与休憩", "Century Sq", "公园</span>"],
    },
    "friendship-bldg": {
        "must_have": ["序馆", "鎏金塔"],
        "must_not": ["植被与休憩", "Century Sq"],
    },
    "guanglan-rd": {
        "must_have": ["园区"],
        "must_not": ["Century Sq"],
    },
    "qiu-r": {
        "must_have": ["河道", "图版"],
        "must_not": ["植被与休憩", "Century Sq", "PLAZA"],
    },
    "panyu-rd": {
        "must_have": ["拱", "砖"],
        "must_not": ["植被与休憩", "Century Sq", "PLAZA", "公园</span>"],
    },
    "wanhang-fy": {
        "must_have": ["河岸", "渡口"],
        "must_not": ["植被与休憩", "Century Sq", "PLAZA", "公园</span>", "STUDIO GHIBLI", "吉祥寺"],
    },
    "fuzhou-rd": {
        "must_have": ["报馆", "石印"],
        "must_not": ["植被与休憩", "Century Sq", "PLAZA", "公园</span>", "花生", "PEANUTS"],
    },
    "longhua-si": {
        "must_have": ["塔檐", "香灰"],
        "must_not": ["植被与休憩", "Century Sq", "PLAZA", "公园</span>", "STUDIO GHIBLI"],
    },
}

# 材质样片：主题定义了自己的材质类，预览页就必须用它们，不能退回通用 .d-*
MATERIAL_OWNERS = {
    "friendship-bldg": ["fb-stone", "fb-gold", "fb-terrazzo", "fb-mint",
                        "fb-redglass", "fb-birch", "fb-daylight"],
    "qiu-r": ["qj-brick", "qj-stone", "qj-wave", "qj-grid",
              "cp-tile", "qj-paper", "cp-steel", "qj-deep"],
    "panyu-rd": ["pg-terrazzo", "pg-flute", "pg-terracotta", "pg-travertine",
                 "pg-ochre", "pg-ultra", "pg-sage", "pg-ink"],
    "wanhang-fy": ["wf-wash", "wf-bank", "wf-paper", "wf-river",
                   "wf-quay", "wf-grove", "wf-brick-swatch", "wf-ink"],
    "fuzhou-rd": ["fz-paper", "fz-halftone", "fz-ochre", "fz-news",
                  "fz-misreg", "fz-vermilion", "fz-indigo", "fz-ink"],
    "longhua-si": ["lh-wall", "lh-ash", "lh-granite", "lh-peach",
                   "lh-eave", "lh-patina", "lh-sandal", "lh-ink"],
}

TPL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview-template.html")

GENERIC_MATERIAL = re.compile(r'class="disc d-[a-z]+"')


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def css_tokens(css_text):
    out = {}
    for m in re.finditer(r'^\s*(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\b', css_text, re.M):
        out[m.group(1)] = m.group(2).lower()
    return out


def check_palette(theme, html, tokens, fails, warns):
    """色板图例里写的 hex 必须等于 :root 真值。"""
    spec = PALETTE_SPEC.get(theme)
    if not spec:
        warns.append(f"{theme}: 没有 PALETTE_SPEC，跳过色板核对")
        return
    shown = re.findall(r'<span>(#[0-9A-Fa-f]{6})</span>', html)[:4]
    if len(shown) != len(spec):
        fails.append(f"{theme}: 色板图例只找到 {len(shown)} 个 hex，应为 {len(spec)}")
        return
    for tok, got in zip(spec, shown):
        want = tokens.get(tok)
        if want is None:
            fails.append(f"{theme}: 主题 CSS 里没有 {tok}")
        elif want != got.lower():
            fails.append(f"{theme}: 色板 {tok} 写的是 {got}，CSS 真值是 {want}")

    # 比例条也必须同源（它是色板最显眼的部分）
    bar = re.search(r'<div class="spec-bar">(.*?)</div>', html, re.S)
    if bar:
        bar_hex = [h.lower() for h in re.findall(r'background:(#[0-9a-fA-F]{6})', bar.group(1))]
        for tok, got in zip(spec, bar_hex):
            want = tokens.get(tok)
            if want and want != got:
                fails.append(f"{theme}: 比例条 {tok} 是 {got}，CSS 真值是 {want}")


def check_materials(theme, html, css_text, fails):
    """主题有自己的材质类时，样片不许退回通用 .d-*，且定义必须在模板里。

    2026-11-20：fb-* / qj-* 已从主题 CSS 迁到 scripts/preview-template.html，
    带 [data-theme="X"] 作用域。所以「有定义」要查模板，不是查主题 CSS。
    """
    own = MATERIAL_OWNERS.get(theme)
    if not own:
        return
    tpl = read(TPL_PATH) if os.path.exists(TPL_PATH) else ""
    generic = GENERIC_MATERIAL.findall(html)
    if generic:
        fails.append(f"{theme}: 材质样片仍用通用类 {sorted(set(generic))}，"
                     f"应改用主题自有材质")
    for cls in own:
        if f'class="disc {cls}"' not in html:
            fails.append(f"{theme}: 材质样片缺 .{cls}")
        # 定义必须存在：主题专属类（fb-*/qj-*）住模板带作用域，
        # 跨主题共用类（cp-*）仍住主题 CSS。两处都认。
        in_tpl = f'[data-theme="{theme}"] .{cls}' in tpl
        in_css = f'.{cls}' in css_text
        if not (in_tpl or in_css):
            fails.append(f"{theme}: 材质类 .{cls} 没有定义"
                         f"（主题专属类应住 preview-template.html 带 data-theme 作用域，"
                         f"共用类应住主题 CSS）")


def check_components(theme, css_text, html, fails, warns):
    """预览页用到的 cp-* 组件类，主题 CSS 里必须真的有定义。"""
    used = set(re.findall(r'\b(cp-[a-z0-9-]+)\b', html))
    used = {c for c in used if c not in ("cp-marble",)}  # cp-marble 由主题各自给
    defined = set(re.findall(r'^\.(cp-[a-z0-9-]+)', css_text, re.M))
    missing = sorted(used - defined)
    if missing:
        fails.append(f"{theme}: 预览页用到但主题 CSS 没定义的组件类 {missing}")


def check_guide_lexicon(theme, html, fails):
    """导览面板不许留着上游主题的语汇。"""
    spec = GUIDE_LEXICON.get(theme)
    if not spec:
        return
    # 只看导览面板那一段，避免误伤注释与别处文案
    m = re.search(r'<div class="guide-panel">(.*?)<div class="g-foot">', html, re.S)
    body = m.group(1) if m else html
    for word in spec["must_have"]:
        if word not in body:
            fails.append(f"{theme}: 导览面板缺自有语汇「{word}」")
    for word in spec["must_not"]:
        if word in body:
            fails.append(f"{theme}: 导览面板残留上游语汇「{word}」")


def check_modal_clearance(theme, html, fails, warns):
    """浮层不许压住卡片正文。

    .g-body 卡片自面板内 top 186 起、高 252，即 186–438。
    .g-modal 若 top < 438 且与卡片列水平重叠，就是压正文。
    """
    m = re.search(r'\.g-modal\{[^}]*\}', html, re.S)
    if not m:
        warns.append(f"{theme}: 找不到 .g-modal 规则，跳过浮层压卡检查")
        return
    block = m.group(0)
    top = re.search(r'top:\s*(-?\d+)px', block)
    if not top:
        return
    top = int(top.group(1))
    # 允许骑在卡片底边上（430–438 之间只压 8px 底边，不压文字）
    if top < 430:
        fails.append(f"{theme}: .g-modal top={top}px，落在卡片正文区（186–438），会压字")


def check_template_source(fails, warns):
    """第六类漂移：模板源本身写死的品牌色 hex。

    反例（2026-11-20）：产物靠 sync_palette 覆盖，色板全对，但
    scripts/preview-template.html 里 --primary 还是 #f9d328、--line-6 还是
    #d62768（主题已压到 #721538）。闸门只查产物 ⇒ 全绿。任何绕过
    sync_palette 的路径（手工改模板、新增分支忘了覆盖）都会漏旧色。

    判据（只查「承载品牌色的位置」，不查材质固有色）：
      模板里每个 `--token:#hex` 声明，若该 token 在任一主题 :root 里存在，
      则模板值必须与**至少一个**主题的真值相等。
      材质固有色（大理石/草坪/玻璃的渐变端色）不承载品牌语义，不在检查范围。
    """
    if not os.path.exists(TEMPLATE):
        warns.append("模板源不存在，跳过模板检查")
        return
    tpl = read(TEMPLATE)

    # 主题真值：token 名 → 该 token 在所有主题里出现过的值集合
    truth = {}
    for f in sorted(os.listdir(THEMES)):
        if not f.endswith(".css"):
            continue
        for k, v in css_tokens(read(os.path.join(THEMES, f))).items():
            truth.setdefault(k, set()).add(v.lower())

    if not truth:
        warns.append("读不到任何主题 token，模板检查跳过")
        return

    bad = []
    for m in re.finditer(r'(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})', tpl):
        tok, val = m.group(1), m.group(2).lower()
        if tok not in truth:
            continue          # 模板自有的结构性 token（如 --primary-hi 的默认档）
        if val not in truth[tok]:
            good = " / ".join(sorted(truth[tok]))
            bad.append(f"{tok}: 模板写 {val}，主题真值是 {good}")

    if bad:
        fails.append(f"模板源 {len(bad)} 个品牌色 token 与主题 :root 不符："
                     + "；".join(bad[:6])
                     + ("…" if len(bad) > 6 else "")
                     + "（产物被 sync_palette 救回来了，但模板本身是错的）")


def _div_block(text, start):
    """从某个 <div 的起始位置起，按 <div / </div> 计数取到该 div 闭合，返回整段。"""
    begin = text.rfind("<div", 0, start)
    depth = 0
    i = begin
    for m in re.finditer(r"<div\b|</div>", text[begin:]):
        if m.group(0) == "<div":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return text[begin:begin + m.end()]
        i += 1
    return text[begin:]


def check_corners(fails, warns):
    """第七类：边角要跟瓦作走，不许退回上游默认。

    反例背景（2026-11-24）：预览板一直只展示色板/材质/模度/组件，边角这条从未成判据——
    主题把 --radius 从 20px（广兰路）压到 2px（虬江），但旧检查项全是色值、材质与语汇，
    圆角变了没有任何一处会红，也没人在样本页上看得出差异。

    判据（分两档，源严产物宽）：
      源级（红）：模板里必须有 `data-block="corners"` 样片区；该区内每个 `border-radius`
                 必须引 `var(--radius*)`，⛔ 写死 px／999px／%、⛔ 用别的 token；
                 三档标签 `--radius-sm` / `--radius` / `--radius-lg` 必须齐。
      产物级（黄）：已生成的预览页缺该样片区 ⇒ WARN「待重生成补齐」，不直接判红——
                 九个既有产物要先跑一遍生成器才带得上，判红会挡与边角无关的改动。
    """
    if not os.path.exists(TEMPLATE):
        warns.append("模板源不存在，边角检查跳过")
        return
    tpl = read(TEMPLATE)
    if 'data-block="corners"' not in tpl:
        fails.append("模板源缺边角样片区：组件格里须有 data-block=\"corners\" 的三档圆角样片")
        return
    block = _div_block(tpl, tpl.index('data-block="corners"'))

    bad_radius = [m.group(0).strip() for m in re.finditer(r"border-radius\s*:\s*[^;\"]+", block)
                  if not m.group(0).split(":", 1)[1].strip().startswith("var(--radius")]
    if bad_radius:
        fails.append("边角样片的半径必须读主题 token，发现写死值：" + "；".join(bad_radius[:4]))

    missing = [t for t in ("--radius-sm", "--radius", "--radius-lg") if t not in block]
    if missing:
        fails.append(f"边角样片缺档位标签：{missing}（三档都要标出 token 名，改主题的人才知道动哪一档）")

    # 主题侧：--radius 必须真的定义过，否则样片读的是空值
    if os.path.isdir(THEMES):
        for f in sorted(os.listdir(THEMES)):
            if f.endswith(".css") and not re.search(r"--radius\s*:", read(os.path.join(THEMES, f))):
                fails.append(f"{f[:-4]}: 主题 CSS 没有定义 --radius，边角样片读不到值")

    # 产物侧：只提示，不判红
    if os.path.isdir(PREVIEWS):
        stale = [f for f in sorted(os.listdir(PREVIEWS))
                 if f.endswith(".html") and 'data-block="corners"' not in read(os.path.join(PREVIEWS, f))]
        if stale:
            warns.append(f"{len(stale)} 份预览页还没有边角样片区，重跑 gen-theme-preview.py 补齐：" + "、".join(stale))


def _last_rules(style, needle):
    """线性扫（这些页面单块 <style> 有 4–11MB，正则回溯会卡死）：返回 needle 相关规则的 (selector, body) 列表。"""
    out, i = [], 0
    while True:
        i = style.find(needle, i)
        if i < 0:
            return out
        b = style.find('{', i)
        e = style.find('}', b)
        if b < 0 or e < 0:
            return out
        s0 = max(style.rfind('}', 0, i), style.rfind(';', 0, i)) + 1
        out.append((style[s0:b], style[b + 1:e]))
        i = e


def _resolves(value, defined, depth=0):
    """var(--x, ...) 是否一定能落成可见值：要么不是 var，要么 --x 有定义，要么自带可用兜底。"""
    if depth > 4:
        return False
    if not value or 'none' in value or 'transparent' in value:
        return False
    ok = True
    for m in re.finditer(r'var\(--([a-z0-9-]+)(?:\s*,\s*(.*?))?\)', value):
        name, fallback = m.group(1), m.group(2)
        if name in defined:
            continue
        if fallback and _resolves(fallback, defined, depth + 1):
            continue
        ok = False
    return ok


def check_modscale(theme, html, fails):
    """第八类：模度阶梯的条子读死引用会静默变透明（2026-11-24 排障发现）。

    反例：模板四条用了 --concrete-deep / --steel / --lawn，这三个材料 token 只有世纪广场一系
    定义过；虬江等主题直接读，浏览器把声明整条丢弃 → 条子全空，而页面不报任何错、闸门全绿。
    判据：四档各自的**最终** background 必须能解析（字面色／有定义的 var／带可用兜底的 var）。
    """
    style = html[html.index('<style>'):html.index('</style>')]
    defined = set(re.findall(r'--([a-z0-9-]+)\s*:', style))
    eff = {}
    for sel, body in _last_rules(style, '.mod-scale'):
        m = re.search(r'background\s*:\s*([^;]+)', body)
        if not m:
            continue
        n = re.search(r'nth-child\((\d)\)', sel)
        if n:
            eff[int(n.group(1))] = m.group(1).strip()
        elif re.search(r'\.ms\s+i', sel):
            for k in (1, 2, 3, 4):
                eff.setdefault(k, m.group(1).strip())
    bad = [f"第 {k} 档：{v}" for k, v in eff.items() if not _resolves(v, defined)]
    missing = [k for k in (1, 2, 3, 4) if k not in eff]
    if bad:
        fails.append(f"{theme}: 模度阶梯有解析不了的条子（会静默变透明）——" + "；".join(bad))
    if missing:
        fails.append(f"{theme}: 模度阶梯缺 {missing} 档的 background 声明")


def check_one(theme, fails, warns):
    css_path = os.path.join(THEMES, f"{theme}.css")
    html_path = os.path.join(PREVIEWS, f"{theme}-theme-preview.html")
    if not os.path.exists(css_path):
        warns.append(f"{theme}: 没有主题 CSS，跳过")
        return False
    if not os.path.exists(html_path):
        fails.append(f"{theme}: 缺预览页产物 {os.path.relpath(html_path)}"
                     f" —— 跑 scripts/gen-theme-preview.py {theme} <中文名> <英文名>")
        return False
    css_text = read(css_path)
    html = read(html_path)
    tokens = css_tokens(css_text)

    check_palette(theme, html, tokens, fails, warns)
    check_materials(theme, html, css_text, fails)
    check_components(theme, css_text, html, fails, warns)
    check_guide_lexicon(theme, html, fails)
    check_modal_clearance(theme, html, fails, warns)
    check_modscale(theme, html, fails)
    return True


def discover():
    """应查集合＝自建主题 CSS（非 upstream），⛔ 不看预览目录里有什么。
    2026-11-23 评审#07：原先按产物反向发现，删掉预览页就自动「无此主题」，WARN 跳过即绿。"""
    if not os.path.isdir(THEMES):
        return []
    return sorted(f[:-4] for f in os.listdir(THEMES) if f.endswith('.css'))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", default=None,
                    help="只查这些主题（可重复）")
    ap.add_argument("--json", default=None, help="把明细写到这个文件")
    args = ap.parse_args()

    themes = args.only or discover()
    if not themes:
        print("没有找到任何预览页产物")
        return 1

    report = {"themes": [], "summary": {"checked": 0, "fail": 0, "warn": 0}}
    any_fail = False

    # 模板源检查：与主题无关，跑一次
    tpl_fails, tpl_warns = [], []
    check_template_source(tpl_fails, tpl_warns)
    check_corners(tpl_fails, tpl_warns)
    if tpl_fails:
        any_fail = True
        print("\n=== 模板源 scripts/preview-template.html ===")
        for f in tpl_fails:
            print(f"  FAIL {f}")
        report["template"] = {"fail": tpl_fails, "warn": tpl_warns}
    elif tpl_warns:
        print("\n=== 模板源 scripts/preview-template.html ===")
        for w in tpl_warns:
            print(f"  WARN {w}")
        report["template"] = {"fail": [], "warn": tpl_warns}
        report["summary"]["template_warn"] = len(tpl_warns)
    for theme in themes:
        fails, warns = [], []
        ran = check_one(theme, fails, warns)
        if ran:
            report["summary"]["checked"] += 1
        if fails:
            any_fail = True
            report["summary"]["fail"] += 1
        if warns:
            report["summary"]["warn"] += 1
        report["themes"].append({"theme": theme, "fail": fails, "warn": warns})

        if fails or warns:
            print(f"\n=== {theme} ===")
            for f in fails:
                print(f"  FAIL {f}")
            for w in warns:
                print(f"  WARN {w}")
        elif ran:
            print(f"  OK   {theme}")

    s = report["summary"]
    print(f"\n{'FAIL' if any_fail else 'PASS'} 预览页一致性："
          f"{s['checked']} 个主题，{s['fail']} 个有 FAIL，{s['warn']} 个有 WARN"
          + (f"；模板源另有 {s['template_warn']} 条 WARN（未计入主题数）"
             if s.get("template_warn") else ""))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
