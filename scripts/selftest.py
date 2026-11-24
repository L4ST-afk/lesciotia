#!/usr/bin/env python3
"""离线自检（冒烟级）：语法能过、CLI 能起来。⛔ 不联网、不读凭据、不写业务文件。

⚠️ 边界：这**不是判据级回归**——只证「脚本没坏到起不来」；业务口径仍靠 references/ 的验收项。
"""
import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY = "build-deck.py"


def main():
    ok = True
    for f in sorted(os.listdir(HERE)):
        if f.endswith(".py") and f != "selftest.py":
            try:
                py_compile.compile(os.path.join(HERE, f), doraise=True)
            except Exception as e:
                print("FAIL 编译 %s: %s" % (f, e))
                ok = False
    p = subprocess.run([sys.executable, os.path.join(HERE, ENTRY), "--help"],
                       capture_output=True, text=True, timeout=30)
    out = p.stdout + p.stderr
    if p.returncode != 0 or "usage" not in out.lower():
        print("FAIL %s --help 起不来（rc=%d）：%s" % (ENTRY, p.returncode, out[-300:]))
        ok = False

    # 配色体检闸：能在真实主题目录上跑通并吐出汇总（不写文件、不联网）
    themes = os.path.join(os.path.dirname(HERE), "assets", "themes")
    if os.path.isdir(themes):
        p = subprocess.run([sys.executable, os.path.join(HERE, "check-theme-colors.py"), themes],
                           capture_output=True, text=True, timeout=60)
        if p.returncode != 0 or '"themes"' not in p.stdout:
            print("FAIL check-theme-colors.py 在 %s 上跑不通（rc=%d）：%s"
                  % (themes, p.returncode, (p.stdout + p.stderr)[-300:]))
            ok = False

    # 配色取色器：给三个色相就要吐出一行结论，且不许在只改明度时偷偷改色相
    p = subprocess.run([sys.executable, os.path.join(HERE, "pick-brand-colors.py"),
                        "--colors", "#1a7fb8,#8b7ce8,#e0632f", "--json"],
                       capture_output=True, text=True, timeout=60)
    out = p.stdout + p.stderr
    if p.returncode != 0 or '"min_dL"' not in out:
        print("FAIL pick-brand-colors.py 跑不通（rc=%d）：%s" % (p.returncode, out[-300:]))
        ok = False

    # 暧昧带换轴放行：造一个只在暧昧带里的主题，登记合格依据后必须降级、不登记必须仍 ⚠️
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as td:
        body = (":root { --bg:#ffffff; --text-1:#111111; --accent-2:#0e8c99; --accent-3:#2563a8; }\n")
        for name, head in (("naked", ""),
                           ("waived", "/* amb-ok: accent-2/accent-3 | 面积 12% vs 2% + 图标冗余 + 永不同框 */\n")):
            with open(os.path.join(td, name + ".css"), "w", encoding="utf-8") as fh:
                fh.write(head + body)
        for name, want in (("naked", 0), ("waived", 1)):
            jf = os.path.join(td, name + ".json")
            p = subprocess.run([sys.executable, os.path.join(HERE, "check-theme-colors.py"), td,
                                "--only", name, "--json", jf], capture_output=True, text=True, timeout=30)
            try:
                got = _json.load(open(jf, encoding="utf-8"))["summary"]["amb_waived"]
            except Exception:
                got = None
            if got != want:
                print("FAIL 换轴放行判据（%s）：amb_waived 应为 %s，实得 %s（rc=%d）：%s"
                      % (name, want, got, p.returncode, (p.stdout + p.stderr)[-300:]))
                ok = False

    # 预览页一致性闸：色板/材质/组件类/导览语汇/浮层压卡五类静默漂移。
    # 这是判据级——直接读产物 HTML 对回主题 CSS，不是「脚本能起来」。
    # 没有产物时它自己会 WARN 跳过，不算失败。
    p = subprocess.run([sys.executable, os.path.join(HERE, "check-preview-sync.py")],
                       capture_output=True, text=True, timeout=120)
    out = p.stdout + p.stderr
    if p.returncode != 0:
        print("FAIL check-preview-sync.py 报不一致：\n%s" % out[-1200:])
        ok = False

    # 字体闸（2026-11-21 加）：子集内容 / @font-face 死声明 / 字体 token 死引用 /
    # 标点回落策略。这是判据级——直接读 woff2 的 cmap 与主题 CSS 对账。
    # 踩坑：龙华寺第一版子集把标点一起打了进去，页面看着正常、闸门全绿，
    # 但「标点回落宋体」根本没生效（CSS 回退按字形走）。当时没有任何闸门能发现。
    # ⚠️ 需要 fontTools；没装时脚本自己 WARN 跳过，不算失败。
    p = subprocess.run([sys.executable, os.path.join(HERE, "check-fonts.py")],
                       capture_output=True, text=True, timeout=120)
    out = p.stdout + p.stderr
    if p.returncode != 0:
        print("FAIL check-fonts.py 报字体问题：\n%s" % out[-1200:])
        ok = False

    # 瓦作出图闸（2026-11-21 加）：PNG 是派生件，主题改了不出图时产物照样看得见、
    # 退出码照样 0——与预览页漂移同一类静默错。这里不但要它「跑通」，还要它「能红」：
    # 篡改 source_sha256 / 删一张图 / 撤掉 manifest，三种都必须报红（§2.299 闸存在性自证）。
    p = subprocess.run([sys.executable, os.path.join(HERE, "check-theme-textures.py")],
                       capture_output=True, text=True, timeout=120)
    out = p.stdout + p.stderr
    if p.returncode != 0:
        print("FAIL check-theme-textures.py 报不一致：\n%s" % out[-1200:])
        ok = False
    root_dir = os.path.dirname(HERE)
    tex_dir = os.path.join(root_dir, "assets", "textures")
    th_dir = os.path.join(root_dir, "assets", "themes")
    if os.path.isdir(tex_dir) and os.path.isdir(th_dir):
        import shutil, json as _j
        neg_ran = 0
        for label, mutate in (
            ("改 sha", "sha"),
            ("删图", "drop_png"),
            ("缺 manifest", "drop_manifest"),
        ):
            neg_ran += 1
            with tempfile.TemporaryDirectory() as td:
                # ⚠️ textures 根目录里有 README.md，不能拿 listdir 的第一项当主题目录
                cand = [d for d in sorted(os.listdir(tex_dir))
                        if os.path.isdir(os.path.join(tex_dir, d))]
                t_src = os.path.join(tex_dir, cand[0])
                theme = os.path.basename(t_src)
                os.makedirs(os.path.join(td, "themes"))
                os.makedirs(os.path.join(td, "textures"))
                if os.path.isfile(os.path.join(th_dir, theme + ".css")):
                    shutil.copy(os.path.join(th_dir, theme + ".css"), os.path.join(td, "themes"))
                shutil.copytree(t_src, os.path.join(td, "textures", theme))
                mp = os.path.join(td, "textures", theme, "manifest.json")
                if mutate == "sha":
                    m = _j.load(open(mp, encoding="utf-8"))
                    m["source_sha256"] = "0" * 64
                    _j.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
                elif mutate == "drop_png":
                    m = _j.load(open(mp, encoding="utf-8"))
                    victim = [f for f in m.get("files", []) if f["file"].endswith(".png")][0]["file"]
                    os.remove(os.path.join(td, "textures", theme, victim))
                else:
                    os.remove(mp)
                p = subprocess.run([sys.executable, os.path.join(HERE, "check-theme-textures.py"),
                                    "--themes-dir", os.path.join(td, "themes"),
                                    "--textures-dir", os.path.join(td, "textures")],
                                   capture_output=True, text=True, timeout=60)
                if p.returncode == 0:
                    print("FAIL 瓦作出图闸不会红（负例：%s）" % label)
                    ok = False

        # 负例条数是闸的存在性自证：跑了 0 条也「全绿」，那等于没验（§2.299）
        if neg_ran != 3:
            print("FAIL 瓦作出图闸负例只跑了 %d 条（应为 3）" % neg_ran)
            ok = False

    # 位图资产闸（2026-11-22 加）：灰度材质 tile 一旦进库，就多四类静默错——
    # 图被重出过而登记 sha 没跟上、许可字段空着、单张超体积预算、CSS 引用了没登记的图。
    # 判据只在产物上；这里同样要求它「能红」：改 sha / 删派生件 / 塞未登记源图 / 同图重复登记。
    reg_path = os.path.join(root_dir, "assets", "textures-src", "registry.json")
    p = subprocess.run([sys.executable, os.path.join(HERE, "check-bitmap-assets.py")],
                       capture_output=True, text=True, timeout=60)
    out = p.stdout + p.stderr
    if p.returncode != 0:
        print("FAIL check-bitmap-assets.py 报问题：\n%s" % out[-1200:])
        ok = False
    if os.path.isfile(reg_path):
        import shutil, json as _json
        reg = _json.load(open(reg_path, encoding="utf-8"))
        entries = reg.get("assets") or []

        def stage(td):
            """把登记表、源图、派生件、每个 used_by 指到的主题 CSS、许可文件都摊到临时根。
            少了 CSS 就会让 B7 先把闸弄红，负例于是「无论改什么都红」= 假通过。"""
            for a in entries:
                for rel in (a["source"], a["derived"]):
                    dst = os.path.join(td, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if os.path.isfile(os.path.join(root_dir, rel)):
                        shutil.copy(os.path.join(root_dir, rel), dst)
                for u in (a.get("used_by") or []):
                    css_rel = "assets/themes/%s.css" % u["theme"]
                    dst = os.path.join(td, css_rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    src_css = os.path.join(root_dir, css_rel)
                    if os.path.isfile(src_css):
                        shutil.copy(src_css, dst)
            shutil.copy(reg_path, os.path.join(td, "assets", "textures-src", "registry.json"))
            attr = os.path.join(root_dir, "ATTRIBUTION.md")
            if os.path.isfile(attr):
                shutil.copy(attr, os.path.join(td, "ATTRIBUTION.md"))
            return os.path.join(td, "assets", "textures-src", "registry.json")

        # 基线必须先绿：负例若在「本来就红」的树上跑，等于没验（§2.299）
        with tempfile.TemporaryDirectory() as td:
            treg = stage(td)
            p = subprocess.run([sys.executable, os.path.join(HERE, "check-bitmap-assets.py"),
                                "--root", td, "--registry", treg],
                               capture_output=True, text=True, timeout=60)
            if p.returncode != 0:
                print("FAIL 位图资产闸基线不绿（负例无意义）：\n%s" % (p.stdout + p.stderr)[-900:])
                ok = False

        bmp_neg = 0
        for label, mutate in (
            ("改 sha", "sha"),
            ("删派生件", "drop_derived"),
            ("塞未登记源图", "stray"),
            ("同图重复登记", "dup"),          # v2 家族制的专属退化：按主题复制同一张图
            ("CSS 少一个右括号", "brace"),      # B11：规则在文件里但浏览器整段丢弃
        ):
            bmp_neg += 1
            with tempfile.TemporaryDirectory() as td:
                treg = stage(td)
                if mutate == "sha":
                    m = _json.load(open(treg, encoding="utf-8"))
                    m["assets"][0]["derived_sha256"] = "0" * 16
                    _json.dump(m, open(treg, "w", encoding="utf-8"), ensure_ascii=False)
                elif mutate == "drop_derived":
                    os.remove(os.path.join(td, entries[0]["derived"]))
                elif mutate == "dup":
                    m = _json.load(open(treg, encoding="utf-8"))
                    clone = _json.loads(_json.dumps(m["assets"][0]))
                    clone["id"] = clone["id"] + "-copy"
                    clone["used_by"] = [dict(clone["used_by"][0], theme="qiu-r", sel=".cp-marble")]
                    m["assets"].append(clone)
                    _json.dump(m, open(treg, "w", encoding="utf-8"), ensure_ascii=False)
                    src_css = os.path.join(root_dir, "assets", "themes", "qiu-r.css")
                    if os.path.isfile(src_css):
                        shutil.copy(src_css, os.path.join(td, "assets", "themes", "qiu-r.css"))
                elif mutate == "brace":
                    # 把接线主题 CSS 里某个 `}` 删掉：B7 仍能在文本里找到文件/blend/opacity，
                    # 只有 B11 能发现规则已经解析不出来。
                    css = os.path.join(td, "assets", "themes", "qiu-r.css")
                    body = open(css, encoding="utf-8").read()
                    idx = body.find(".cp-marble::after{")
                    end = body.find("}", idx)
                    open(css, "w", encoding="utf-8").write(body[:end] + body[end + 1:])
                else:
                    stray = os.path.join(td, os.path.dirname(entries[0]["source"]), "stray.png")
                    os.makedirs(os.path.dirname(stray), exist_ok=True)
                    open(stray, "wb").write(b"\x89PNG\r\n\x1a\n")
                p = subprocess.run([sys.executable, os.path.join(HERE, "check-bitmap-assets.py"),
                                    "--root", td, "--registry", treg],
                                   capture_output=True, text=True, timeout=60)
                if p.returncode == 0:
                    print("FAIL 位图资产闸不会红（负例：%s）" % label)
                    ok = False
        if bmp_neg != 5:
            print("FAIL 位图资产闸负例只跑了 %d 条（应为 5）" % bmp_neg)
            ok = False

    # 瓦作翻译闸（2026-11-22 加）：spec 里写了 conic 渐变、union 布尔、未定义 token，
    # 都不会在出件时当场报错——它会产出一份「看着像、细节不对」的 pptx，然后被拿去做
    # 真渲染比对，人眼在错的地方找原因。闸必须在出件之前红。
    # 判据级，且按 §2.299 要求「能红」：四条负例各自点名，跑不满 4 条不算验过。
    wash_sample = os.path.join(root_dir, "examples", "pptx", "wash-sample.json")
    if os.path.isfile(wash_sample):
        p = subprocess.run([sys.executable, os.path.join(HERE, "check-wash.py"), wash_sample],
                           capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            print("FAIL 瓦作翻译闸基线不绿（仓内样例自己过不了闸）：\n%s"
                  % (p.stdout + p.stderr)[-900:])
            ok = False
        base = _json.load(open(wash_sample, encoding="utf-8"))
        wash_neg = 0

        def first_shape(spec, pred):
            for pg in spec.get("slides", []):
                for sh in (pg.get("shapes") or pg.get("wash") or []):
                    if pred(sh):
                        return sh
            return None

        for label, mutate in (
            ("conic 渐变", "conic"),
            ("union 布尔", "union"),
            ("未定义 token", "tok"),
            ("未知 shape", "shape"),
        ):
            wash_neg += 1
            with tempfile.TemporaryDirectory() as td:
                spec = _json.loads(_json.dumps(base))
                if mutate == "conic":
                    sh = first_shape(spec, lambda s: isinstance(s.get("fill"), dict) and "gradient" in s["fill"])
                    if sh is None:
                        print("FAIL 样例里没有渐变形状，conic 负例无从构造")
                        ok = False
                        continue
                    sh["fill"]["gradient"] = "conic-gradient(from 90deg, #000 0%, #fff 100%)"
                elif mutate == "union":
                    sh = first_shape(spec, lambda s: "boolean" in s)
                    if sh is None:
                        print("FAIL 样例里没有布尔形状，union 负例无从构造")
                        ok = False
                        continue
                    sh["boolean"]["op"] = "union"
                elif mutate == "tok":
                    # 追加在末页：不动原样例的版面，只多一个引用不存在的 token
                    spec["slides"][-1].setdefault("shapes", []).append(
                        {"shape": "rect", "box": [0, 0, 100, 100],
                         "fill": {"solid": "--no-such-token"}})
                else:
                    spec["slides"][-1].setdefault("shapes", []).append(
                        {"shape": "star", "box": [0, 0, 100, 100],
                         "fill": {"solid": "#FFFFFF"}})
                bad = os.path.join(td, "spec.json")
                _json.dump(spec, open(bad, "w", encoding="utf-8"), ensure_ascii=False)
                p = subprocess.run([sys.executable, os.path.join(HERE, "check-wash.py"), bad],
                                   capture_output=True, text=True, timeout=60)
                if p.returncode == 0:
                    print("FAIL 瓦作翻译闸不会红（负例：%s）" % label)
                    ok = False
                elif not p.stderr.strip():
                    # 红了但一句话没说 = 不知道哪一页哪个形状，等于没报
                    print("FAIL 瓦作翻译闸报红却无指控（负例：%s）" % label)
                    ok = False
        if wash_neg != 4:
            print("FAIL 瓦作翻译闸负例只跑了 %d 条（应为 4）" % wash_neg)
            ok = False

    # 布尔求值的数值判据（2026-11-23 加）：布尔是本库唯一「算出来」的东西——
    # 算错了 schema 照样通过、真渲染照样出图，只有面积能揭穿它。
    # 两圆之差/交有解析解，就拿来当标尺；自交折线必须当场拒（它的「内部」本身没定义）。
    try:
        import math
        sys.path.insert(0, HERE)
        import wash_bridge as _wb
        r = 200.0
        A = _wb.circle_poly((400, 400), r, 0, 2 * math.pi, 96)[:-1]
        B = _wb.circle_poly((500, 400), r, 0, 2 * math.pi, 96)[:-1]
        # d=100：lens = 2r²acos(d/2r) − (d/2)√(4r²−d²)
        lens = 2 * r**2 * math.acos(100 / (2 * r)) - 50 * math.sqrt(4 * r**2 - 100**2)
        for op, want in (('intersect', lens), ('subtract', math.pi * r**2 - lens)):
            got = sum(abs(_wb.area(c)) for c in _wb.poly_bool(op, A, B))
            if abs(got - want) / want > 0.01:
                print('FAIL 布尔数值（%s）：折线面积 %.0f 与解析解 %.0f 差超 1%%' % (op, got, want))
                ok = False
        bowtie = [(0, 0), (300, 300), (300, 0), (0, 300)]
        if _wb.is_simple(bowtie):
            print('FAIL 自交判定失效：蝴蝶结折线被判成了简单折线')
            ok = False
        try:
            _wb.poly_bool('intersect', bowtie, A)
            print('FAIL 布尔没有拦住自交折线（蝴蝶结形状居然算过去了）')
            ok = False
        except ValueError as e:
            if '自交' not in str(e):
                print('FAIL 自交折线报错不对题（报了「%s」）' % str(e)[:60])
                ok = False
    except ImportError as e:
        print('INFO 跳过布尔数值判据（%s）' % e)

    # 双出口漂移（2026-11-23 加）：spec 里那串声明，HTML 侧必须一模一样地写着。
    # 判据是「归一空白后子串出现」——两边排版不同；但只要有人只改了一边，它就红。
    if os.path.isfile(wash_sample):
        decls = []
        for pg in _json.load(open(wash_sample, encoding="utf-8"))["slides"]:
            for it in (pg.get("shapes") or pg.get("wash") or []):
                f = it.get("fill")
                if isinstance(f, dict):
                    for k in ("gradient", "solid"):
                        if k in f:
                            decls.append(" ".join(str(f[k]).split()))
        if decls:
            with tempfile.TemporaryDirectory() as td:
                def run(keep):
                    h = os.path.join(td, "deck.html")
                    with open(h, "w", encoding="utf-8") as fh:
                        fh.write("<style>\n" + "\n".join(
                            "  background: %s;" % d.replace(", ", ",\n      ") for d in keep) + "\n</style>")
                    return subprocess.run([sys.executable, os.path.join(HERE, "check-wash.py"),
                                           wash_sample, "--html", h],
                                          capture_output=True, text=True, timeout=60)
                if run(decls).returncode != 0:
                    print("FAIL 双出口同源判据基线不绿（HTML 全抄 spec 反倒过不了）")
                    ok = False
                p = run(decls[1:])
                if p.returncode == 0 or not p.stderr.strip():
                    print("FAIL 双出口同源判据不会红（少了一条声明仍判绿）")
                    ok = False

    # morph 结构判别（2026-11-23 加）：morph 是本库唯一无法实机核验的能力，
    # 能验的是「结构对不对、配不配得上」。这里现造两份 deck：同页型相邻 → 必须配对成功；
    # 跨页型相邻 → 一个同名都没有，必须红（否则 morph 只是名字好听，实际退化成 fade）。
    try:
        import tempfile as _tf, json as _j2
        with _tf.TemporaryDirectory() as td:
            def build(pages, out):
                spec = {"slides": pages}
                sp = os.path.join(td, "spec.json")
                with open(sp, "w", encoding="utf-8") as fh:
                    _j2.dump(spec, fh, ensure_ascii=False)
                r = subprocess.run([sys.executable, os.path.join(HERE, "export-pptx.py"), sp,
                                    "-o", out, "--theme", "century-sq", "--allow-prose"],
                                   capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    print("FAIL morph 夹具造不出来：%s" % (r.stderr or r.stdout)[-400:])
                    return False
                return True

            same = [{"type": "bullets", "title": "甲", "items": ["一", "二"], "transition": {"type": "morph"}},
                    {"type": "bullets", "title": "乙", "items": ["三"], "transition": {"type": "morph"}}]
            # 负例必须挂在「还有下一页」的那页上：最后一页的 morph 只会空转（那是注记，不是红）
            mixed = [{"type": "bullets", "title": "甲", "items": ["一"]},
                     {"type": "kpi", "title": "乙", "items": [["9", "件"]], "transition": {"type": "morph"}},
                     {"type": "quote", "text": "丙", "by": "丁"}]
            a = os.path.join(td, "same.pptx")
            b = os.path.join(td, "mixed.pptx")
            if build(same, a):
                r = subprocess.run([sys.executable, os.path.join(HERE, "check-morph.py"), a],
                                   capture_output=True, text=True, timeout=60)
                if r.returncode != 0 or "配对" not in r.stdout:
                    print("FAIL morph 闸对「同页型相邻」判红：%s" % (r.stderr or r.stdout)[-400:])
                    ok = False
            if build(mixed, b):
                r = subprocess.run([sys.executable, os.path.join(HERE, "check-morph.py"), b],
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    print("FAIL morph 闸不会红（跨页型相邻、零同名，仍判绿）")
                    ok = False
    except Exception as e:
        print("INFO 跳过 morph 结构判据（%s）" % e)

    # 曲线布尔（2026-11-23 加）：pathops 装了就必须与解析解对得上；没装则必须**报降级而不是装作会**。
    try:
        sys.path.insert(0, os.path.join(HERE))
        import wash_bridge as wb3
        if wb3.HAS_PATHOPS:
            import math
            r, d = 100.0, 100.0
            lens = 2 * r * r * math.acos(d / (2 * r)) - (d / 2) * math.sqrt(4 * r * r - d * d)
            d1 = 'M 300 200 A 100 100 0 1 1 100 200 A 100 100 0 1 1 300 200 Z'
            d2 = 'M 400 200 A 100 100 0 1 1 200 200 A 100 100 0 1 1 400 200 Z'
            got = wb3.curves_area(wb3.curve_bool('intersect', d1, d2))
            if abs(got - lens) / lens > 0.02:
                print('FAIL 曲线布尔面积对不上解析 lens：%.1f vs %.1f' % (got, lens))
                ok = False
        else:
            print('INFO 未装 skia-pathops：曲线布尔走折线降级（闸只验降级被报出来）')
        # 降级必须由闸/出件说出来：拿一份「要曲线」的 spec，在屏蔽 pathops 的环境里必须红
        stub = os.path.join(tempfile.gettempdir(), 'nopathops-stub')
        os.makedirs(stub, exist_ok=True)
        with open(os.path.join(stub, 'pathops.py'), 'w', encoding='utf-8') as fh:
            fh.write('raise ImportError("stub")\n')
        spec = os.path.join(tempfile.gettempdir(), 'selftest-cbool.json')
        with open(spec, 'w', encoding='utf-8') as fh:
            json.dump({'slides': [{'type': 'wash', 'title': ['曲线'], 'shapes': [
                {'name': 'x', 'shape': 'rect', 'box': [0, 0, 1600, 900], 'fill': {'solid': '#0E1622'}},
                {'name': 'y', 'boolean': {'op': 'intersect',
                  'a': {'path': 'M 300 200 A 100 100 0 1 1 100 200 A 100 100 0 1 1 300 200 Z'},
                  'b': {'path': 'M 400 200 A 100 100 0 1 1 200 200 A 100 100 0 1 1 400 200 Z'}},
                 'fill': {'solid': '#D6A63A'}, 'h': 200, 'at': [100, 100], 'curves': 'require'}]}]},
                      fh, ensure_ascii=False)
        env = dict(os.environ)
        env['PYTHONPATH'] = stub + os.pathsep + env.get('PYTHONPATH', '')
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'export-pptx.py'), spec,
                             '-o', os.path.join(tempfile.gettempdir(), 'selftest-cbool.pptx'),
                             '--theme', 'century-sq', '--force', '--allow-prose'],
                            capture_output=True, text=True, env=env, timeout=120)
        if rr.returncode == 0 or 'skia-pathops' not in (rr.stdout + rr.stderr):
            print('FAIL curves=require 在缺 pathops 时没红：%s' % (rr.stdout + rr.stderr)[-300:])
            ok = False
    except Exception as e:
        print('INFO 跳过曲线布尔判据（%s）' % e)

    # 原生图表页（2026-11-23 加）：C 出口必须真出 chart part，不是贴图；不支持的 kind 必须红。
    try:
        from pptx import Presentation as _Pr
        cspec = os.path.join(tempfile.gettempdir(), 'selftest-chart.json')
        with open(cspec, 'w', encoding='utf-8') as fh:
            json.dump({'theme': 'century-sq', 'slides': [
                {'type': 'cover', 'title': ['图表页', '自检'], 'kicker': 'SELFTEST',
                 'lede': '这一页只是陪跑，好让成稿闸不把整册判成空页。'},
                {'type': 'chart', 'kicker': 'Q4 复盘', 'title': '季度 MRR 趋势',
                 'chart': {'kind': 'bar', 'categories': ['Q1', 'Q2', 'Q3', 'Q4'],
                           'series': [{'name': 'MRR (K)', 'values': [42, 58, 73, 96]},
                                      {'name': '目标', 'values': [40, 60, 80, 100]}]},
                 'note': '来源：财务系统，2026-11'}]}, fh, ensure_ascii=False)
        out = os.path.join(tempfile.gettempdir(), 'selftest-chart.pptx')
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'export-pptx.py'), cspec,
                             '-o', out, '--force', '--allow-prose'],
                            capture_output=True, text=True, timeout=120)
        if rr.returncode != 0:
            print('FAIL 图表页出不来：%s' % (rr.stderr or rr.stdout)[-300:])
            ok = False
        else:
            prs = _Pr(out)
            charts = [sh for sh in prs.slides[1].shapes if sh.has_chart]
            if len(charts) != 1:
                print('FAIL 图表页没有 chart part（PowerPoint 里就不可编辑）：%d 个' % len(charts))
                ok = False
            else:
                ch = charts[0].chart
                n_ser = len(ch.plots[0].series)
                n_cat = len(list(ch.plots[0].categories))
                if n_ser != 2 or n_cat != 4:
                    print('FAIL 图表数据没过来：系列 %d / 类目 %d' % (n_ser, n_cat))
                    ok = False
                else:
                    print('PASS 图表页：原生 chart part、2 系列 4 类目（可编辑，非贴图）')
        # 不支持的 kind 必须说出来，不许塞成柱状图
        bad = os.path.join(tempfile.gettempdir(), 'selftest-chart-bad.json')
        with open(bad, 'w', encoding='utf-8') as fh:
            json.dump({'theme': 'century-sq', 'slides': [
                {'type': 'chart', 'title': '瀑布', 'chart': {'kind': 'waterfall',
                  'categories': ['a'], 'series': [{'name': 'x', 'values': [1]}]}}]},
                fh, ensure_ascii=False)
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'export-pptx.py'), bad,
                             '-o', os.path.join(tempfile.gettempdir(), 'selftest-chart-bad.pptx'),
                             '--force', '--allow-prose'], capture_output=True, text=True, timeout=120)
        if rr.returncode == 0 or 'chart kind' not in (rr.stdout + rr.stderr):
            print('FAIL waterfall 没被拒：%s' % (rr.stdout + rr.stderr)[-200:])
            ok = False
        else:
            print('PASS 图表页：不支持的 kind 被点名拒绝')
    except Exception as e:
        print('INFO 跳过图表页判据（%s）' % e)

    # 逆流：PPTX → HTML（2026-11-23 加）。验的是「页数与文字真的过来了」，不是「长得像」。
    try:
        out_html = os.path.join(tempfile.gettempdir(), 'selftest-pptx2html.html')
        sample = os.path.join(HERE, '..', 'examples', 'pptx', 'wash-sample.pptx')
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'pptx-to-html.py'), sample,
                             '-o', out_html], capture_output=True, text=True, timeout=120)
        if rr.returncode != 0:
            print('FAIL pptx-to-html 跑不起来：%s' % (rr.stderr or rr.stdout)[-300:])
            ok = False
        else:
            doc = open(out_html, encoding='utf-8').read()
            n = doc.count('<section class="slide">')
            if n != 4:
                print('FAIL pptx-to-html 页数不对：%d（应 4）' % n)
                ok = False
            if '两圆相减' not in doc:
                print('FAIL pptx-to-html 丢了文字（找不到「两圆相减」）')
                ok = False
    except Exception as e:
        print('INFO 跳过 pptx→html 判据（%s）' % e)

    # 往返闭环（2026-11-23 加）：只改字的那条路，几何指纹必须一动不动。
    rt_bad = False
    try:
        sample = os.path.join(HERE, '..', 'examples', 'pptx', 'wash-sample.pptx')
        dump = os.path.join(tempfile.gettempdir(), 'selftest-texts.json')
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'retext-pptx.py'), sample,
                             '--dump', dump], capture_output=True, text=True, timeout=120)
        if rr.returncode != 0:
            print('FAIL retext --dump 跑不起来：%s' % (rr.stderr or rr.stdout)[-300:])
            ok = False; rt_bad = True
        else:
            inv = json.load(open(dump, encoding='utf-8'))
            rows = inv['shapes']
            if len(rows) < 8:
                print('FAIL retext 抽到的非空文本框太少：%d' % len(rows))
                ok = False; rt_bad = True
            first = rows[0]
            edits = os.path.join(tempfile.gettempdir(), 'selftest-edits.json')
            with open(edits, 'w', encoding='utf-8') as fh:
                json.dump({'edits': [
                    {'slide': first['slide'], 'id': first['id'], 'text': '往返测试\n第二段'},
                    {'slide': first['slide'], 'notes': '备注也要能落到这一页'}]}, fh, ensure_ascii=False)
            out = os.path.join(tempfile.gettempdir(), 'selftest-retext.pptx')
            rr = subprocess.run([sys.executable, os.path.join(HERE, 'retext-pptx.py'), sample,
                                 '--edits', edits, '-o', out], capture_output=True, text=True, timeout=120)
            if rr.returncode != 0:
                print('FAIL retext --edits 跑不起来：%s' % (rr.stderr or rr.stdout)[-300:])
                ok = False; rt_bad = True
            else:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    'retext_pptx', os.path.join(HERE, 'retext-pptx.py'))
                rt = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rt)
                from pptx import Presentation
                p2 = Presentation(out)
                rows2 = rt.inventory(p2)
                same = [r for r in rows2 if r['id'] == first['id'] and r['slide'] == first['slide']]
                if not same:
                    print('FAIL retext 改完找不到那个形状')
                    ok = False; rt_bad = True
                elif same[0]['geom'] != first['geom']:
                    print('FAIL retext 改字把几何指纹改了：%s → %s' % (first['geom'], same[0]['geom']))
                    ok = False; rt_bad = True
                if p2.slides[first['slide'] - 1].notes_slide.notes_text_frame.text.strip() == '':
                    print('FAIL retext 备注没落进去')
                    ok = False; rt_bad = True
        if not rt_bad:
            print('PASS 往返闭环：只改字、几何指纹未动、备注已落')
    except Exception as e:
        print('INFO 跳过往返闭环判据（%s）' % e)

    # 成稿闸（2026-11-23 加）：套话版必须红，抬密度版必须过；出件口必须真的拒。
    prose_dir = os.path.join(HERE, '..', 'examples', 'prose')
    gate = os.path.join(HERE, 'check-prose.py')
    bad_spec = os.path.join(prose_dir, 'bad-spec.json')
    good_spec = os.path.join(prose_dir, 'good-spec.json')
    if os.path.isdir(prose_dir):
        rr = subprocess.run([sys.executable, gate, bad_spec], capture_output=True, text=True, timeout=60)
        if rr.returncode != 1 or 'P1' not in rr.stdout:
            print('FAIL 成稿闸没拦住套话版（rc=%d）' % rr.returncode)
            ok = False
        rr = subprocess.run([sys.executable, gate, good_spec, '--strict'], capture_output=True, text=True, timeout=60)
        if rr.returncode != 0:
            print('FAIL 成稿闸误伤抬密度版：%s' % rr.stdout.strip()[:200])
            ok = False
        bad_out = os.path.join(tempfile.gettempdir(), 'selftest-prose-blocked.pptx')
        if os.path.exists(bad_out):
            os.remove(bad_out)
        rr = subprocess.run([sys.executable, os.path.join(HERE, 'export-pptx.py'), bad_spec,
                             '-o', bad_out, '--force'], capture_output=True, text=True, timeout=120)
        if rr.returncode == 0 or os.path.exists(bad_out):
            print('FAIL 出件口没被成稿闸拦住（rc=%d，产物%s）' % (rr.returncode, os.path.exists(bad_out)))
            ok = False
        else:
            print('PASS 成稿闸：套话版被拦、抬密度版可出片')

    # 成稿闸吃正本（2026-11-23 加）：pages/NN-*.md 与 spec.json 必须判出同一结果，
    # 且 --emit-spec 派生的 spec 要能被 export-pptx.py 吃。
    # 反例：闸门只认 json 时，workflow Step 5.5 那句「写完就跑闸」是悬空的，
    # 照做的人只能手抄一份 spec——那就成了第二份正本（禅院塔 §2.6）。
    if os.path.isdir(prose_dir):
        pages_dir = os.path.join(tempfile.gettempdir(), 'selftest-pages')
        if os.path.isdir(pages_dir):
            shutil.rmtree(pages_dir)
        os.makedirs(pages_dir)
        # 一页好、一页套话：好页必须过，套话页必须红
        with open(os.path.join(pages_dir, '01-cover.md'), 'w', encoding='utf-8') as f:
            f.write('# 01 · 封面\n\n- **type**: cover\n- **archetype**: pitch\n'
                    '- **title**: 一年 8 倍，不靠补贴\n- **kicker**: Traction\n'
                    '- **lede**: 拦住推广的不是硬件，是数据\n'
                    '- **points**:\n  1. 周活 12K → 96K\n  2. 付费转化 4.7%\n'
                    '- **notes**: 开场先给 8 倍这个数，停一秒再解释凭什么。\n'
                    '- **refs**: [增长看板 2026-10](source-growth.csv)\n')
        with open(os.path.join(pages_dir, '02-bad.md'), 'w', encoding='utf-8') as f:
            f.write('# 02 · 赋能体系\n\n- **type**: bullets\n- **archetype**: pitch\n'
                    '- **title**: 全方位赋能价值体系\n- **kicker**: 抓手\n'
                    '- **points**:\n  1. 通过全链路数智化打通降本增效实现价值最大化\n')
        rr = subprocess.run([sys.executable, gate, pages_dir], capture_output=True, text=True, timeout=60)
        if rr.returncode != 1 or 'P1' not in rr.stdout or '第 2 页' not in rr.stdout:
            print('FAIL 成稿闸读不了 pages/ 正本（rc=%d）：%s'
                  % (rr.returncode, (rr.stdout + rr.stderr).strip()[:200]))
            ok = False
        else:
            # 只留好页，应该能过
            os.remove(os.path.join(pages_dir, '02-bad.md'))
            rr = subprocess.run([sys.executable, gate, pages_dir, '--strict'],
                                capture_output=True, text=True, timeout=60)
            if rr.returncode != 0:
                print('FAIL 成稿闸误伤干净的 pages/：%s' % rr.stdout.strip()[:200])
                ok = False
            else:
                # 派生 spec → export-pptx 必须能读
                emitted = os.path.join(pages_dir, 'deck.json')
                rr = subprocess.run([sys.executable, gate, pages_dir, '--emit-spec', emitted],
                                    capture_output=True, text=True, timeout=60)
                if not os.path.isfile(emitted):
                    print('FAIL --emit-spec 没落盘')
                    ok = False
                else:
                    try:
                        spec = json.load(open(emitted, encoding='utf-8'))
                        s0 = spec['slides'][0]
                        # 字段别名必须真的换过：points→items、refs→source
                        if 'items' not in s0 or 'points' in s0:
                            print('FAIL 派生 spec 没把 points 换成 items：%s' % list(s0))
                            ok = False
                        elif 'source' not in s0 or 'refs' in s0:
                            print('FAIL 派生 spec 没把 refs 换成 source：%s' % list(s0))
                            ok = False
                        else:
                            out = os.path.join(pages_dir, 'out.pptx')
                            rr = subprocess.run([sys.executable, os.path.join(HERE, 'export-pptx.py'),
                                                 emitted, '-o', out, '--force'],
                                                capture_output=True, text=True, timeout=120)
                            if rr.returncode != 0 or not os.path.exists(out):
                                print('FAIL 派生的 spec 出不了件（rc=%d）：%s'
                                      % (rr.returncode, (rr.stderr or rr.stdout).strip()[-200:]))
                                ok = False
                            else:
                                # 回读 PPTX：批 1 四条判据的验收点（2026-11-23）。
                                # ⛔ 只数「出件成功」抓不住标题拆字、讲稿串页——那正是上一轮漏掉的。
                                try:
                                    from pptx import Presentation
                                    prs = Presentation(out)
                                    s1 = prs.slides[0]
                                    paras = []
                                    for sh in s1.shapes:
                                        if not sh.has_text_frame:
                                            continue
                                        for para in sh.text_frame.paragraphs:
                                            t = ''.join(r.text for r in para.runs).strip()
                                            if t:
                                                paras.append(t)
                                    # ① title 是 str 时不得逐字拆：封面标题必须整行出现
                                    if s0['title'] not in paras:
                                        print('FAIL 封面标题被拆了（str 形态没走 _lines）：%s' % paras[:6])
                                        ok = False
                                    # ② notes 必须进备注页，且不得出现在正页
                                    elif s0.get('notes'):
                                        nt = (s1.notes_slide.notes_text_frame.text.strip()
                                              if s1.has_notes_slide else '')
                                        if not nt:
                                            print('FAIL 讲稿没进备注页（notes 被当正页小注了）')
                                            ok = False
                                        elif any(nt[:8] in p for p in paras):
                                            print('FAIL 讲稿泄到正页：%s' % nt[:30])
                                            ok = False
                                        else:
                                            print('PASS 成稿闸吃正本：pages/ 直接判、派生 spec 能出件、'
                                                  '标题不拆字、讲稿进备注页')
                                    else:
                                        print('PASS 成稿闸吃正本：pages/ 直接判、派生 spec 能出件、标题不拆字')
                                except ImportError:
                                    print('PASS 成稿闸吃正本：pages/ 直接判、派生 spec 能出件'
                                          '（缺 python-pptx，跳过标题/备注回读）')
                                except Exception as e:
                                    print('FAIL 回读 PPTX 出错：%s' % e)
                                    ok = False
                    except Exception as e:
                        print('FAIL 派生 spec 读不了：%s' % e)
                        ok = False
        shutil.rmtree(pages_dir, ignore_errors=True)

    # 提示词配方（2026-11-23 加）：五份夹具各自判回自己那一型，五条提示词都出得来。
    rec_dir = os.path.join(HERE, '..', 'examples', 'prose', 'recipes')
    rec = os.path.join(HERE, 'pick-recipe.py')
    if os.path.isdir(rec_dir):
        bad = []
        cases = [('briefing', 'briefing.md'), ('proposal', 'proposal.md'),
                 ('teaching', 'teaching.md'), ('retro', 'retro.md'), ('launch', 'launch.md'),
                 ('proposal', 'en-proposal.md'), ('retro', 'en-retro.md'),
                 ('teaching', 'ja-teaching.md'), ('briefing', 'mixed-zh-first.md')]
        for key, name in cases:
            f = os.path.join(rec_dir, name)
            if not os.path.isfile(f):
                print('FAIL 配方夹具缺 %s.md' % key)
                ok = False
                continue
            r = subprocess.run([sys.executable, rec, '--detect', f, '--json'],
                               capture_output=True, text=True, timeout=60)
            got = (r.stdout or '').strip()
            if r.returncode != 0 or ('"recipe": "%s"' % key) not in got:
                bad.append('%s→%s' % (name, got[-60:]))
            r = subprocess.run([sys.executable, rec, '--show', key],
                               capture_output=True, text=True, timeout=60)
            if r.returncode != 0 or '硬要求' not in r.stdout or '四问' not in r.stdout:
                bad.append('%s 提示词不完整' % key)
        if bad:
            print('FAIL 判型或配方出不来：%s' % '；'.join(bad))
            ok = False
        else:
            print('PASS 提示词配方：五型自判自回、提示词齐（硬要求＋四问）')

    # 梁架闸（2026-11-23 加）：14 族可过；把旧名 files 复活必须红。
    lay_gate = os.path.join(HERE, 'check-layouts.py')
    if os.path.isfile(lay_gate):
        r = subprocess.run([sys.executable, lay_gate], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print('FAIL 梁架闸不过：%s' % (r.stdout.strip()[:300]))
            ok = False
        ghost = os.path.join(os.path.dirname(HERE), 'assets', 'layouts', 'bullets.html')
        try:
            with open(ghost, 'w', encoding='utf-8') as fh:
                fh.write('<!-- ghost -->\n')
            r = subprocess.run([sys.executable, lay_gate], capture_output=True, text=True, timeout=60)
            if r.returncode == 0 or 'L3' not in r.stdout:
                print('FAIL 梁架闸没拦住旧名复活（bullets.html）')
                ok = False
            else:
                print('PASS 梁架闸：17 族可过、旧名复活必红')
        finally:
            if os.path.exists(ghost):
                os.remove(ghost)

    # 装得下闸（2026-11-23 加）：17 族都得装得下；故意做一页字掉出画布的，必须红。
    fit_gate = os.path.join(HERE, 'check-fit.py')
    if os.path.isfile(fit_gate):
        r = subprocess.run([sys.executable, fit_gate], capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            print('FAIL 装得下闸不过：%s' % (r.stdout.strip()[-400:]))
            ok = False
        probe = os.path.join(os.path.dirname(HERE), 'assets', 'layouts', '_fitprobe.html')
        try:
            src = open(os.path.join(os.path.dirname(HERE), 'assets', 'layouts', 'text.html'),
                       encoding='utf-8').read()
            # 把一页内容灌成 40 行，必然溢出
            body = src.split('<div class="deck">', 1)[0] + '<div class="deck"><section class="slide is-active" data-title="Overflow">'
            body += '<p class="kicker">Probe</p><h2 class="h2">装不下的一页</h2>'
            for i in range(40):
                body += '<p>第 %d 行：这一行是为了把画布撑破而写的，正常内容不会这样排。</p>' % i
            body += '</section></div></body></html>'
            with open(probe, 'w', encoding='utf-8') as fh:
                fh.write(body)
            r = subprocess.run([sys.executable, fit_gate, probe], capture_output=True, text=True, timeout=120)
            if r.returncode == 0 or 'F1' not in r.stdout:
                print('FAIL 装得下闸没拦住溢出的页：%s' % r.stdout.strip()[:300])
                ok = False
            else:
                print('PASS 装得下闸：17 族都装得下、溢出页必红')
        finally:
            if os.path.exists(probe):
                os.remove(probe)

    # 结构类闸负例：L7 只查 _families.json 里登记的族，所以往真族页塞一个野类，塞完原样还原。
    if os.path.isfile(os.path.join(HERE, 'check-layouts.py')):
        import shutil as _sh
        victim = os.path.join(os.path.dirname(HERE), 'assets', 'layouts', 'text.html')
        backup = victim + '.l7bak'
        try:
            _sh.copyfile(victim, backup)
            with open(victim, 'a', encoding='utf-8') as fh:
                fh.write('<div class="zzz-nope">没样式的类</div>\n')
            r = subprocess.run([sys.executable, os.path.join(HERE, 'check-layouts.py')],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0 or 'L7' not in r.stdout:
                print('FAIL 梁架闸没拦住没样式的类（L7）：%s' % r.stdout.strip()[:200])
                ok = False
            else:
                print('PASS 梁架闸 L7：没样式的类必红')
        finally:
            if os.path.exists(backup):
                _sh.copyfile(backup, victim)
                os.remove(backup)

    # 符号链接闸（2026-11-20 加）：库内任何符号链接都等于「只在你这台机器上能用」。
    # 实测教训：themes/upstream 曾是链接指向 ../html-ppt-skill/assets/themes，本机跑得通，
    # 单独打包后链接即断，36 个版式全取不到主题，build-deck.py 直接失败。
    root = os.path.dirname(HERE)
    links = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", "node_modules")]
        for name in dirnames + filenames:
            fp = os.path.join(dirpath, name)
            if os.path.islink(fp):
                links.append(os.path.relpath(fp, root))
    if links:
        print("FAIL 库内有符号链接 %d 个（打包分发后会断链）：%s"
              % (len(links), ", ".join(links[:6])))
        ok = False

    print("PASS 冒烟自检" if ok else "FAIL 冒烟自检")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
