#!/usr/bin/env python3
"""来雪亭Lesciotia :: export-pptx.py — 用同一份瓦作（主题 token）出**原生可编辑** PPTX

用法：
    python3 scripts/export-pptx.py spec.json -o out.pptx [--theme century-sq] [--json]
    python3 scripts/export-pptx.py spec.json -o out.pptx --force --bundle-fonts

判据是**产物本身**：写完回读 pptx，逐页数形状与字符，任何一页像截图就红。
⛔ 不看退出码、不看日志里的 ✓。

为什么要有这支脚本（而不是借外部的 SVG→PPTX 管道）：
B 出口的梁架在浏览器里执行，C 出口若另起一套 SVG 作者层，两边就变成两套渲染器，
只剩「配色一样」。这里反过来做——**只读主题 token 与一套栅格**，用 python-pptx
直接摆原生文本框与形状。代价是拿不到渐变叠加、布尔合并、动效；换来的是文字可双击改、
零外部引擎、且和 HTML 侧共用同一份瓦作真源。

三处是向同类工程学来的（不是自己的发明）：
1. 三槽字体 a:latin / a:ea / a:cs —— 只写一槽会让「3.8%」落到中文字面。
2. 随包字体 + 真粗体面 —— 声明栈里的 Playfair/Inter 走 Google CDN，收件人机器上没有；
   随包一份 ttf 并允许「拷出去让人装」，字形才不靠运气。
3. 断行锁定 —— 收件人缺字体时用同宽更宽的字面替代，换行点会重排；把按 HTML 侧字体
   量出来的断行写死成段，版面就不随机器漂。

依赖：python-pptx（本库唯一的非标准库，缺了按退出码 2 报，⛔ 不许静默降级成截图）。
可选：fontTools（读随包字体的族名）、Pillow（量字宽，锁断行）；缺了降级但仍出件，摘要里写明。
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    from lxml import etree
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import nsdecls, qn
    from pptx.util import Inches, Pt
except ImportError:  # pragma: no cover - 环境问题，不是判据问题
    print('✗ 缺 python-pptx：pip install python-pptx。'
          '⛔ 不许改成「截图塞 pptx」兜底——那不是可编辑件', file=sys.stderr)
    raise SystemExit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wash_bridge as wb  # noqa: E402  同一目录的换算件：渐变求值、布尔求值、path 直译

BASE = Path(__file__).resolve().parent.parent
ASSETS = BASE / 'assets'
THEMES = BASE / 'assets' / 'themes'
FONT_DIR = BASE / 'assets' / 'fonts'

# 画布坐标系：1600×900 px 与 HTML 侧同尺寸，1 in = 120 px，于是版式参数可以照抄 CSS。
CANVAS_W, CANVAS_H = 1600, 900
PX_PER_IN = 120.0
LEFT, CW = 88, 1424  # 版心：左边界与内容宽（与 CSS 的 80/96 padding 取中）

# 字体角色 → 候选栈（按「主题字体 → 本机 → 同类骨架」降级）。
# 字体真源在 `assets/base.css` 的 --font-serif / --font-sans 声明栈里，本脚本**不抄第二份**：
# 先在声明栈里挑本机装得上的，全落空才用下面这组兜底（顺序按「同类骨架」，不是偏好）。
FONT_FALLBACK = {
    'serif': ['Source Han Serif SC', '思源宋体', 'Songti SC', 'STSong', 'SimSun'],
    'sans': ['Source Han Sans SC', '思源黑体', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei'],
    'latin-serif': ['Georgia', 'Times New Roman'],
    'latin-sans': ['Helvetica Neue', 'Arial'],
}
FALLBACK_NOTE = 'PPTX 不带字体，本机缺哪款就退到下一档'


def px(v: float) -> Inches:
    return Inches(v / PX_PER_IN)


def read_tokens(theme: str) -> dict[str, str]:
    """取主题 `:root` 里的颜色瓦作：`--k:#hex`，以及 `--k:var(--other)` 这类别名，逐层解到底。

    ⛔ 别只抓 `#hex`：世纪广场的 --accent 写成 var(--primary)，只抓字面会把「强调色」
    读成兜底黑，时间线的点、分隔线全变墨色——预览里一眼看得出，产物里也真黑。
    渐变/纹理不取（PPT 侧不还原）。
    """
    css = (THEMES / f'{theme}.css').read_text(encoding='utf-8')
    if ':root{' not in css:
        raise SystemExit(f'主题 {theme} 里找不到 :root')
    block = css[css.index(':root{'):]
    block = block[:block.index('\n}')]
    raw = dict(re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', block))

    def resolve(key: str, depth: int = 0) -> str | None:
        if depth > 6 or key not in raw:
            return None
        val = raw[key].strip()
        m = re.fullmatch(r'(#[0-9a-fA-F]{3,8})', val)
        if m:
            return m.group(1)
        m = re.fullmatch(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+)\s*)?\)', val)
        if m:  # --border 是 rgba(34,34,34,.14)，PPT 没有带 alpha 的纯色：按底色合成成实色
            r, g, b = (int(m.group(i)) for i in (1, 2, 3))
            a = float(m.group(4)) if m.group(4) else 1.0
            base = resolve('--bg', depth + 1) or '#ffffff'
            br, bg_, bb = (int(base.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            mix = lambda c, d: int(round(c * a + d * (1 - a)))
            return '#%02X%02X%02X' % (mix(r, br), mix(g, bg_), mix(b, bb))
        m = re.fullmatch(r'var\(\s*(--[\w-]+)\s*\)', val)
        if m:
            return resolve(m.group(1), depth + 1)
        return None

    return {k: v for k in raw if (v := resolve(k))}


def head_metrics(theme: str, deck_css: Path | None = None) -> tuple[str, float]:
    """标题走衬线还是黑体、多大字号——从 CSS 读，不让 spec 逐页抄一遍。

    顺序：base.css 兜底 → 主题覆盖 → 整册模板（--deck-css）覆盖。
    只认 `h2{...}` / `.h2{...}` 里显式的 font-family 与 font-size；找不到就守 54px / sans
    （与 base.css 的 .h2 一致，别在这里发明一套数）。
    """
    role, size = 'sans', 54.0
    sources = [BASE / 'assets' / 'base.css', THEMES / f'{theme}.css']
    if deck_css:
        sources.append(deck_css)
    for src in sources:
        if not src.is_file():
            continue
        css = src.read_text(encoding='utf-8')
        for m in re.finditer(r'(?:^|[,}\s])(?:[.#\w-]*\.)?h2\s*\{([^}]*)\}', css, re.M):
            blk = m.group(1)
            fm = re.search(r'font-family\s*:\s*([^;}]+)', blk)
            if fm:
                val = fm.group(1).lower()
                role = 'serif' if ('serif' in val and 'sans-serif' not in val) else 'sans'
            sz = re.search(r'font-size\s*:\s*([\d.]+)px', blk)
            if sz:
                size = float(sz.group(1))
    return role, size


def installed_families() -> set[str] | None:
    """查本机字体族。没有 fontconfig 就返回 None——**未知不等于已装**，摘要里要写清楚。"""
    exe = shutil.which('fc-list')
    if not exe:
        return None
    try:
        out = subprocess.run([exe, ':family'], capture_output=True, text=True, timeout=20).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    fams = set()
    for line in out.splitlines():
        for part in line.split(','):
            if part.strip():
                fams.add(part.strip())
    return fams


def font_file(family: str) -> str | None:
    """族名 → 本机字体文件。量字宽要用真文件，不能拿「大概 1em」估。"""
    exe = shutil.which('fc-match')
    if not exe:
        return None
    try:
        out = subprocess.run([exe, '-f', '%{file}', family], capture_output=True, text=True, timeout=15)
        path = out.stdout.strip()
        return path if path and Path(path).is_file() else None
    except (subprocess.SubprocessError, OSError):
        return None


VARIANT_SUFFIX = re.compile(r'\s+(vf|regular|bold|italic|light|medium|heavy|black|semibold)\b.*$', re.I)


def _core(name: str) -> str:
    """去掉 VF/Bold 这类变体后缀再比：本机的 `Source Han Serif SC VF` 与声明里的
    `Source Han Serif SC` 是同一族，⛔ 不能按整串比，否则「装了」被读成「没装」。"""
    return VARIANT_SUFFIX.sub('', name.strip()).strip().lower()


def declared_families() -> tuple[list[str], list[str]]:
    """从 base.css 取 --font-serif / --font-sans 声明栈里的族名（跳过 var() 与通用族）。"""
    css = (BASE / 'assets' / 'base.css').read_text(encoding='utf-8')
    out = []
    for token in ('--font-serif', '--font-sans'):
        m = re.search(rf'{token}\s*:\s*([^;]+);', css)
        fams = re.findall(r"'([^']+)'", m.group(1)) if m else []
        out.append([f for f in fams if f.lower() not in {'serif', 'sans-serif', 'monospace'}])
    return out[0], out[1]


CJK_FAMILY = re.compile(r'source han|noto (serif|sans)\s*(sc|cjk)|songti|stsong|simsun|pingfang|yahei|hiragino|思源|宋体|黑体|楷体|苹方', re.I)


def is_cjk_family(name: str) -> bool:
    return bool(CJK_FAMILY.search(name))


def bundled_fonts() -> dict[str, dict]:
    """随包字体：CSS 族名 → {regular/bold 文件 + 文件里的真实族名}。

    真源是 `assets/fonts.css` 的 @font-face，不扫目录：一个文件被谁声明、给哪个角色用，
    只有那儿说了算。Google 的静态实例常把族名写歪（Space Grotesk 的 400 实例内部叫
    「Space Grotesk Light」），所以 CSS 名与文件内部名分开存：HTML 认前者，PPT 认后者。
    """
    out: dict[str, dict] = {}
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return out
    css = (BASE / 'assets' / 'fonts.css').read_text(encoding='utf-8')
    for m in re.finditer(r'@font-face\s*\{(.*?)\}', css, re.S):
        blk = m.group(1)
        fam = re.search(r"font-family\s*:\s*'([^']+)'", blk)
        src = re.search(r"url\('([^']+)'\)", blk)
        wr = re.search(r'font-weight\s*:\s*(\d+)', blk)
        if not (fam and src):
            continue
        path = (BASE / 'assets' / src.group(1)).resolve()
        if path.suffix.lower() != '.ttf' or not path.is_file():
            continue
        try:
            f = TTFont(str(path), fontNumber=0, lazy=True)
            inner = f['name'].getDebugName(1) or path.stem
            f.close()
        except Exception:  # 坏文件不该拖垮出件
            continue
        slot = 'bold' if (int(wr.group(1)) if wr else 400) >= 600 else 'regular'
        entry = out.setdefault(fam.group(1), {'names': {}})
        entry[slot] = str(path)
        entry['names'][slot] = inner
    return out


def resolve_font(role: str, have: set[str] | None, declared: list[str],
                 bundled: dict[str, dict[str, Path]]) -> dict:
    """返回 {family, path, bold_path, state}。state ∈ 首选 / 随包 / 降级 / 未验证。

    ⚠ 中/西不能混着一个栈走：声明栈里 `Playfair Display` 后面紧跟 `Source Han Serif SC`，
    若只按顺序取第一个装得上的，本机没装 Playfair 就会拿中文衬线去排「3.8%」，
    数字的骨架立刻变味。所以先按 is_cjk_family 把栈劈成中文一半、西文一半，各取各的。
    """
    want_cjk = role in ('serif', 'sans')
    pool = [f for f in declared if is_cjk_family(f) == want_cjk]
    if not pool:  # 主题只声明了中文族时，西文也要有个能落地的
        pool = list(FONT_FALLBACK[role])
    cands = pool + FONT_FALLBACK[role]
    cores = {_core(f) for f in have} if have else set()

    for i, name in enumerate(cands):
        # 随包字体优先：它就是 HTML 侧真正用的那副字面，量出来的断行才对得上
        for fam, faces in bundled.items():
            if _core(fam) == _core(name):
                names = faces.get('names', {})
                return {'family': names.get('regular') or names.get('bold') or fam,
                        'path': faces.get('regular') or faces.get('bold'),
                        'bold_path': faces.get('bold') if (names.get('bold'), faces.get('bold')) else None,
                        'state': '首选' if i == 0 else '随包'}
        if have is None:
            return {'family': name, 'path': font_file(name), 'bold_path': None, 'state': '未验证'}
        if _core(name) in cores:
            return {'family': name, 'path': font_file(name), 'bold_path': None,
                    'state': '首选' if i == 0 else '降级'}
    name = cands[-1]
    return {'family': name, 'path': font_file(name), 'bold_path': None,
            'state': '未验证' if have is None else '降级'}


# ---------- 断行锁定 ----------
CJK_CHAR = re.compile(r'[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef\u3000-\u303f]')
NO_LINE_START = set('，。、；：？！）】」』》〉”’…·%、,.;:?!)]}')
NO_LINE_END = set('（【「『《〈“‘([{')

_MEASURE: dict[tuple[str, int], object] = {}


def _face(path: str, size: int):
    key = (path, size)
    if key not in _MEASURE:
        from PIL import ImageFont
        _MEASURE[key] = ImageFont.truetype(path, size)
    return _MEASURE[key]


HB_MEASURE = False   # --hb-measure 才开：整段 shaping 会改断行结果，默认沿用逐字


def _lines(v) -> list:
    """标题类字段的两种形态收在一处：手写 spec 给 list（一行一段），
    pages/NN.md 派生出来是 str（`- **title**: 一年 8 倍`）。

    ⛔ 别在渲染函数里直接 `for line in d['title']`——对 str 会**逐字符**迭代，
    封面标题被拆成一字一段竖排（2026-11-23 三席评审共识 #B）。
    """
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if str(x).strip()]
    return [ln for ln in str(v).splitlines() if ln.strip()]


def text_width(txt: str, size_px: float, latin: str | None, ea: str | None) -> float | None:
    """按**真字体文件**量宽：CJK 走中文面，其余走拉丁面。缺文件就返回 None（不锁）。

    装了 uharfbuzz 且开了 `--hb-measure` 时，整段 shape 一遍取 advance（带字偶距与连字）；
    否则逐字累加——两者在长句上会有 1–3% 的差，足以改变断行点，所以默认不开。
    """
    if not (latin or ea):
        return None
    if HB_MEASURE and wb.HAS_UHARFBUZZ:
        try:
            if ea and any(CJK_CHAR.match(ch) for ch in txt):
                w = 0.0
                chunk = ''
                for ch in txt:
                    if CJK_CHAR.match(ch):
                        if chunk:
                            w += wb.hb_width(chunk, latin or ea, size_px); chunk = ''
                        w += wb.hb_width(ch, ea, size_px)
                    else:
                        chunk += ch
                if chunk:
                    w += wb.hb_width(chunk, latin or ea, size_px)
                return w
            return wb.hb_width(txt, latin or ea, size_px)
        except Exception:
            pass
    try:
        import PIL.ImageFont  # noqa: F401
    except ImportError:
        return None
    size = int(round(size_px))
    w = 0.0
    for ch in txt:
        path = ea if (CJK_CHAR.match(ch) and ea) else (latin or ea)
        if not path:
            return None
        try:
            w += _face(path, size).getlength(ch)
        except Exception:
            return None
    return w


def wrap_text(txt: str, width: float, size_px: float, latin: str | None, ea: str | None) -> list[str] | None:
    """贪心断行，把 HTML 侧的换行点写成硬段。拉丁按词断，中文按字断，禁头标点不落下行。"""
    if '\n' in txt:
        return txt.split('\n')
    probe = text_width(txt, size_px, latin, ea)
    if probe is None:
        return None
    if probe <= width:
        return [txt]

    # 切段：连续的 ASCII 字母数字算一个词，其余逐字
    segs = re.findall(r'[A-Za-z0-9%$@#&+\-_/.]+(?:\s|$)|.', txt)
    lines, cur = [], ''
    for seg in segs:
        cand = cur + seg
        w = text_width(cand, size_px, latin, ea)
        if w is None:
            return None
        if w <= width or not cur:
            cur = cand
            continue
        if seg and seg[0] in NO_LINE_START:  # 标点悬挂：宁可超一点，不把「。」甩到行首
            cur = cand
            continue
        while cur and cur[-1] in NO_LINE_END:  # 开引号不留在行尾
            seg = cur[-1] + seg
            cur = cur[:-1]
        lines.append(cur.rstrip())
        cur = seg.lstrip() if seg.strip() else ''
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def set_font(run, latin: str, ea: str, size_px: float, bold: bool = False, color: RGBColor | None = None) -> None:
    """三槽一起写：`run.font.name` 只治拉丁，中文走 `a:ea`，复杂文种走 `a:cs`。

    ⛔ 只写 ea 会让「3.8%」这类数字落到中文字面，行高与基线都会歪。
    """
    f = run.font
    f.size = Pt(size_px * 0.75)  # 1600px 画布 → pt
    f.bold = bold
    if color is not None:
        f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag, face in (('a:latin', latin), ('a:ea', ea), ('a:cs', latin)):
        node = rpr.find(qn(tag))
        if node is None:
            node = rpr.makeelement(qn(tag), {})
            rpr.append(node)
        node.set('typeface', face)
    f.name = latin  # 兼容不读 rPr 的查看器


class Deck:
    def __init__(self, tokens: dict[str, str], fonts: dict[str, dict], lock: bool = True,
                 head: tuple[str, float] = ('sans', 54.0), transition: dict | None = None,
                 wash_css: list[Path] | None = None):
        self.t = tokens
        self.head_role, self.head_size = head
        # 标题压下来多少，内容就让多少：68px 标题配 224px 起的卡片会顶到色条
        self.head_bottom = 128 + self.head_size * 1.42
        self.fonts = fonts
        self.lock = lock
        self.prs = Presentation()
        self.stripped_placeholders = strip_stray_placeholders(self.prs)
        self.prs.slide_width = px(CANVAS_W)
        self.prs.slide_height = px(CANVAS_H)
        self.blank = self.prs.slide_layouts[6]
        self.expected = 0
        self.locked_runs = 0
        # 量宽「试过几次、败了几次」。断行这件事有三种状态，别混成一个 0：
        # ① 量了、折了（locked_runs > 0）② 量了、都单行（无需锁定，完全正常）
        # ③ 压根没量成（缺字体文件 / 缺 Pillow）——只有这一种才是「收件人会重排」的风险。
        self.runs_measured = 0
        self.measure_fail = 0
        self.tr_default = transition or {}
        self.transitions = 0
        self.timed = 0
        self.timed_shapes = 0
        self.timed_clicks = 0
        # ：root 的真源就是这几份 CSS：base → 主题 → 整册模板，后面的覆盖前面的
        self.wash_vals = wb.root_vars('\n'.join(
            p.read_text(encoding='utf-8') for p in (wash_css or []) if p.is_file()))
        self.pending_wash = None
        self.wash_shapes = 0
        self.wash_curve_bool = 0      # 走 skia-pathops 真裁剪的布尔个数
        self.wash_degraded: list[str] = []   # 想要曲线布尔但本机没装的账
        self._wash_n = 0

    # --- 瓦作取值 ---
    def c(self, key: str, default: str = '#000000') -> RGBColor:
        """token 名优先；给了 `#RRGGBB` 就直接当颜色——否则「深底白字」会静默落成黑字。"""
        v = self.t.get(key)
        if v is None:
            v = key if isinstance(key, str) and key.startswith('#') else default
        v = v.lstrip('#')
        if len(v) == 3:
            v = ''.join(ch * 2 for ch in v)
        return RGBColor.from_string(v[:6].upper())

    # --- 基础件 ---
    def slide(self):
        s = self.prs.slides.add_slide(self.blank)
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = self.c('--bg', '#ffffff')
        self.expected += 1
        self._wash_n = 0
        if self.pending_wash:
            before = self.wash_shapes
            self.wash_layer(s, self.pending_wash)
            self._wash_n = self.wash_shapes - before
            self.pending_wash = None
        return s

    def role_names(self, s, kind: str) -> int:
        """把 python-pptx 的默认名（`TextBox 3`、`Rectangle 7`）改成**按角色稳定**的名字。

        为什么非改不可：morph 的补间靠「跨页同名对象」，而 python-pptx 是每页独立计数命名的——
        第 1 页的 `TextBox 3` 与第 2 页的 `TextBox 3` 根本是两个角色。按 `页型-序号` 写死之后，
        同页型相邻的两页，同名即同角色，morph 才有意义。洗层形状单独前缀，不挤占内容序号。
        """
        n = wash_i = content_i = 0
        for i, sh in enumerate(s.shapes):
            if not DEFAULT_SHAPE_NAME.match(sh.name):
                continue          # spec 里给了名字的（moon / lens / field）一律不动
            if i < self._wash_n:
                sh.name = f'{kind}-bg{wash_i}'
                wash_i += 1
            else:
                sh.name = f'{kind}-s{content_i}'
                content_i += 1
            n += 1
        return n

    def apply_transition(self, s, d):
        """把这一页的切换写进 <p:sld>：位置在 clrMapOvr 之后——序列校验的，写别处就红。
        返回 True 表示写了元素；'none' 是不写（继承母版即为无切换），不是「写个空壳」。"""
        tr = dict(self.tr_default)
        tr.update(d.get('transition') or {})
        err = check_transition(tr)
        if err:
            raise ValueError(err)
        if tr.get('type', 'fade') == 'none':
            return False
        el = build_transition(tr)
        sld = s.element
        anchor = sld.find(qn('p:clrMapOvr'))
        if anchor is not None:
            anchor.addnext(el)
        else:
            sld.append(el)
        self.transitions += 1
        return True

    def apply_timing(self, s, d, default_on: bool, dur_ms: int = 400):
        """给这一页写 p:timing：每个内容形状一次点击淡入。染层底色不参与。"""
        on = d.get('animate') if isinstance(d.get('animate'), bool) else default_on
        if not on:
            return 0
        spids = []
        for i, sh in enumerate(s.shapes):
            if i < self._wash_n:
                continue
            if '-bg' in sh.name:
                continue
            spids.append(sh.shape_id)
        if len(spids) < 2:
            # 只有一块内容时「逐块揭示」等于没揭示，不写这棵树
            return 0
        cap = int(d.get('animate_groups') or d.get('groups') or 4)
        cap = max(1, min(cap, len(spids)))
        groups = [spids[j::cap] for j in range(cap)] if len(spids) > cap else [[sp] for sp in spids]
        el = build_timing(groups, d.get('animate_ms') or dur_ms)
        s.element.append(el)
        self.timed += 1
        self.timed_shapes += len(spids)
        self.timed_clicks += len(groups)
        return len(spids)

    # --- 染层：渐变与布尔在这一层求值，画在内容之下 ---
    def wash_fill(self, spec: dict):
        """{'gradient': 'linear-gradient(…)'} 或 {'solid': '--accent' | '#1B2A4A', 'alpha': 0.4}"""
        if 'gradient' in spec:
            # 先把 var(--x) 解成真值再解析：parse_gradient 只负责结构，不负责代换
            return ('grad', wb.parse_gradient(wb.resolve(spec['gradient'], self.wash_vals),
                                              self.wash_vals))
        if 'solid' in spec:
            raw = spec['solid'].strip()
            # 裸 token（--bg）与 var(--bg) 两种写法都收；都不认识就报，别当透明
            if raw.startswith('--'):
                if raw not in self.wash_vals:
                    raise ValueError(f'瓦作里没有定义 {raw}（先查 :root，别指望它有默认值）')
                raw = self.wash_vals[raw]
            else:
                raw = wb.resolve(raw, self.wash_vals)
            return ('solid', wb.color(raw)[0], spec.get('alpha'))
        raise ValueError('fill 只认 {"gradient": …} 或 {"solid": …}')

    def wash_place(self, s, pts, fill, item):
        """把点列放成一条 custGeom 形状；缩放按目标高度，位置按 at。

        `pts` 可以是单轮廓，也可以是**多条轮廓**（布尔挖洞、咬成好几块时的形态）。
        """
        contours = pts if (pts and isinstance(pts[0][0], (list, tuple))) else [pts]
        allp = [p for c in contours for p in c]
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        minx, miny = min(xs), min(ys)
        nw, nh = (max(xs) - minx) or 1, (max(ys) - miny) or 1
        h = float(item.get('h', nh))
        k = h / nh
        at_x, at_y = item.get('at', [0, 0])
        sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(at_x), px(at_y), px(nw * k), px(h))
        self._strip_style(sh)
        sh.line.fill.background()
        self._set_wash_fill(sh, fill)
        wb.custgeom(sh, [[((x - minx) * k, (y - miny) * k) for x, y in c] for c in contours],
                    nw * k, h)
        if item.get('name'):
            sh.name = item['name']
        self.wash_shapes += 1
        return sh

    def wash_bezier(self, s, segs, fill, item):
        """曲线保真版：`path()` 的 A/C/Q 段换算成 `cubicBezTo`，不再采样成折线。

        为什么不再采样：本库的 A→custGeom 是「原样翻译」，采样折线只能近似——
        段少看得出棱角，段多文件膨胀。贝塞尔一处就把圆画圆了。
        布尔结果仍然只能折线（曲线对曲线的真裁剪要给 pathops，见 SELFTEST 的账）。
        """
        allp = [seg[1] for seg in segs if seg[0] == 'move'] + \
               [p for seg in segs if seg[0] in ('line', 'cubic') for p in seg[1:]] 
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        minx, miny = min(xs), min(ys)
        nw, nh = (max(xs) - minx) or 1, (max(ys) - miny) or 1
        h = float(item.get('h', nh))
        k = h / nh
        at_x, at_y = item.get('at', [0, 0])
        sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(at_x), px(at_y), px(nw * k), px(h))
        self._strip_style(sh)
        sh.line.fill.background()
        self._set_wash_fill(sh, fill)
        # 控制点也要跟着缩放与平移：先按 k 缩、再整体减 bbox 原点
        scaled = []
        for seg in segs:
            if seg[0] == 'move':
                scaled.append(('move', ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k)))
            elif seg[0] == 'line':
                scaled.append(('line', ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k)))
            elif seg[0] == 'cubic':
                scaled.append(('cubic',
                               ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k),
                               ((seg[2][0] - minx) * k, (seg[2][1] - miny) * k),
                               ((seg[3][0] - minx) * k, (seg[3][1] - miny) * k)))
        wb.custgeom_segments(sh, scaled, nw * k, h, off=(0, 0))
        if item.get('name'):
            sh.name = item['name']
        self.wash_shapes += 1
        return sh

    def wash_curves(self, s, contours, fill, item):
        """曲线布尔的出件：每个轮廓一个 `a:path`，段里带 `cubicBezTo`。

        与 `wash_bezier` 的差别只在「可能有多个轮廓」——差集把形咬成两块时，
        两块都得写进同一个 custGeom，否则第二块会丢。
        """
        allp = []
        for c in contours:
            for seg in c:
                allp.append(seg[1])
                if seg[0] == 'cubic':
                    allp.append(seg[2]); allp.append(seg[3])
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        minx, miny = min(xs), min(ys)
        nw, nh = (max(xs) - minx) or 1, (max(ys) - miny) or 1
        h = float(item.get('h', nh))
        k = h / nh
        at_x, at_y = item.get('at', [0, 0])
        sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(at_x), px(at_y), px(nw * k), px(h))
        self._strip_style(sh)
        sh.line.fill.background()
        self._set_wash_fill(sh, fill)
        scaled = []
        for c in contours:
            sc = []
            for seg in c:
                if seg[0] == 'move':
                    sc.append(('move', ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k)))
                elif seg[0] == 'line':
                    sc.append(('line', ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k)))
                elif seg[0] == 'cubic':
                    sc.append(('cubic', ((seg[1][0] - minx) * k, (seg[1][1] - miny) * k),
                               ((seg[2][0] - minx) * k, (seg[2][1] - miny) * k),
                               ((seg[3][0] - minx) * k, (seg[3][1] - miny) * k)))
            scaled.append(sc)
        wb.custgeom_curves(sh, scaled, nw * k, h, off=(0, 0))
        if item.get('name'):
            sh.name = item['name']
        self.wash_shapes += 1
        self.wash_curve_bool += 1
        return sh

    @staticmethod
    def _strip_style(sh) -> None:
        """删掉 <p:style>：它按主题的 effectRef 挂投影与描边，而瓦作里这些形状是平的。
        留着就等于「悄悄多了一层投影」——同源翻译里最不该有的那种偏差。"""
        st = sh._element.find(qn('p:style'))
        if st is not None:
            sh._element.remove(st)

    def _set_wash_fill(self, sh, fill) -> None:
        if fill[0] == 'solid':
            wb.set_fill(sh, ('solid', fill[1]))
            if fill[2] is not None and float(fill[2]) < 1:
                for c in sh._element.spPr.iter(qn('a:srgbClr')):
                    a = parse_xml(f'<a:alpha {nsdecls("a")} val="{int(float(fill[2]) * 100000)}"/>')
                    c.append(a)
        else:
            wb.set_fill(sh, ('grad', fill[1]))

    def wash_layer(self, s, shapes: list) -> None:
        for item in shapes:
            fill = self.wash_fill(item.get('fill') or {'solid': '--bg'})
            if 'boolean' in item:
                b = item['boolean']
                op = b['op']
                if op == 'union':
                    raise ValueError('并集不做布尔：同色叠放两张即可（wash 的 union 只认叠放写法）')
                if op not in ('subtract', 'intersect'):
                    raise ValueError(f'boolean.op 只认 subtract / intersect，收到 {op}')
                # 操作数三种写法：两圆 {center,r}（走解析解，边界最干净）、{path}、{points}。
                # 只要有一边不是圆，就折算成折线走 poly_bool——PPT 里没有布尔指令，
                # 求值只能发生在这里（导出的那一刻），写进去的是算完的轮廓。
                #
                # 可选后端：两边都是 {path} 且本机装了 skia-pathops，就走**真曲线裁剪**，
                # 沿曲线切、结果带三次贝塞尔。没装则退回折线，并把降级记进报告——
                # 「装了什么出什么精度」必须写出来，否则同 spec 两台机器出两种精度。
                mode = str(item.get('curves', 'auto'))
                if mode not in ('auto', 'polyline', 'require'):
                    raise ValueError(f'curves 只认 auto / polyline / require，收到 {mode!r}')
                if mode != 'polyline' and 'path' in b['a'] and 'path' in b['b']:
                    if wb.HAS_PATHOPS:
                        self.wash_curves(s, wb.curve_bool(op, b['a']['path'], b['b']['path']), fill, item)
                        continue
                    if mode == 'require':
                        raise ValueError('curves=require：spec 要真曲线裁剪，但本机没装 skia-pathops（pip install skia-pathops）')
                    self.wash_degraded.append(f'第 {len(s.shapes)} 个染层形状的布尔降级为折线（缺 skia-pathops）')
                pts = wb.boolean_points(op, b['a'], b['b'], int(item.get('n', 64)))
                self.wash_place(s, pts, fill, item)
            elif 'path' in item:
                if item.get('curve', 'bezier') == 'polyline':
                    self.wash_place(s, wb.svg_path(item['path'], int(item.get('n', 24))), fill, item)
                else:
                    self.wash_bezier(s, wb.svg_segments(item['path']), fill, item)
            else:
                kind = item.get('shape', 'rect')
                if kind == 'rect':
                    box = item['box']
                    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(box[0]), px(box[1]), px(box[2]), px(box[3]))
                elif kind == 'circle':
                    c, r = item['center'], item['r']
                    sh = s.shapes.add_shape(MSO_SHAPE.OVAL, px(c[0] - r), px(c[1] - r), px(2 * r), px(2 * r))
                else:
                    raise ValueError(f'wash 的 shape 只认 rect / circle（复杂轮廓用 path 或 boolean），收到 {kind}')
                self._strip_style(sh)
                sh.line.fill.background()
                self._set_wash_fill(sh, fill)
                if item.get('name'):
                    sh.name = item['name']
                self.wash_shapes += 1

    def font_for(self, role: str, bold: bool) -> dict:
        """{latin, ea, bold, latin_path, ea_path}。有真 Bold 字面就按 bold 开关走，量宽也用 Bold 面。"""
        lan = self.fonts['latin-serif' if role == 'serif' else 'latin-sans']
        cjk = self.fonts['serif' if role == 'serif' else 'sans']
        return {
            'latin': lan['family'],
            'ea': cjk['family'],
            'bold': bool(bold),
            'latin_path': (lan.get('bold_path') or lan.get('path')) if bold else lan.get('path'),
            'ea_path': cjk.get('path'),
        }

    def text(self, s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
        """runs = [(文本, 角色, 字号px, 字重, 色token), …]，每个 run 一段。
        断行锁定时，一个 run 会展开成多段硬回车，且关掉自动换行——否则 PowerPoint 会二次折行。"""
        box = s.shapes.add_textbox(px(x), px(y), px(w), px(h))
        tf = box.text_frame
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        first = True
        any_locked = False
        for txt, role, size, bold, color_key in runs:
            ff = self.font_for(role, bold)
            lines = wrap_text(txt, w, size, ff['latin_path'], ff['ea_path']) if self.lock else None
            if self.lock:
                if lines is None:
                    self.measure_fail += 1
                else:
                    self.runs_measured += 1
            if lines and len(lines) > 1:
                any_locked = True
            for line in (lines or [txt]):
                p = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                p.alignment = align
                if spacing:
                    p.line_spacing = spacing
                r = p.add_run()
                r.text = line
                set_font(r, ff['latin'], ff['ea'], size, ff['bold'], self.c(color_key))
        tf.word_wrap = not any_locked
        if any_locked:
            self.locked_runs += 1
        return box

    def bar(self, s, x, y, w, h, color_key, fill=True):
        sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
        if fill:
            sh.fill.solid()
            sh.fill.fore_color.rgb = self.c(color_key)
        else:
            sh.fill.background()
        sh.line.fill.background()
        sh.shadow.inherit = False
        return sh

    def panel(self, s, x, y, w, h, fill_key='--surface', border_key='--border'):
        sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x), px(y), px(w), px(h))
        sh.adjustments[0] = min(18 / max(w, 1), 0.5)
        sh.fill.solid()
        sh.fill.fore_color.rgb = self.c(fill_key)
        sh.line.color.rgb = self.c(border_key)
        sh.line.width = Pt(0.75)
        _soft_shadow(sh)
        return sh

    def dot(self, s, cx, cy, d, color_key='--accent'):
        sh = s.shapes.add_shape(MSO_SHAPE.OVAL, px(cx - d / 2), px(cy - d / 2), px(d), px(d))
        sh.fill.solid()
        sh.fill.fore_color.rgb = self.c(color_key)
        sh.line.color.rgb = self.c('--bg')
        sh.line.width = Pt(2)
        sh.shadow.inherit = False
        return sh

    def footer(self, s, left: str, idx: int, total: int):
        if left:
            self.text(s, LEFT, 790, 700, 26, [(left, 'sans', 14, False, '--text-3')])
        self.text(s, 1440, 790, 80, 26, [(f'{idx} / {total}', 'sans', 14, False, '--text-3')])

    def head(self, s, d, size=None, role=None):
        """页标题：kicker 在上，标题在下——四个内容页型共用，别各写一份。
        base.css 里 .h2 是 54px / --font-display（默认 sans）；.kicker 是 14px --accent。
        主题若把 h2 改成衬线（course-module 那样），spec 里传 role='serif' 即可。"""
        size = size or self.head_size
        role = role or d.get('title_role') or self.head_role
        if d.get('kicker'):
            self.text(s, LEFT, 86, 900, 26, [(d['kicker'], 'sans', 14, True, '--accent')])
        lines = _lines(d['title'])
        self.text(s, LEFT, 128, 1240, 80,
                  [(lines[0] if lines else '', role, size, True, '--text-1')], spacing=1.1)

    # --- 页型 ---
    def cover(self, d, page_no, total):
        s = self.slide()
        self.bar(s, LEFT, 118, 22, 3, '--primary')
        self.text(s, LEFT + 30, 108, 700, 24, [(d.get('kicker', ''), 'sans', 12, True, '--text-2')])
        self.text(s, LEFT, 236, 940, 250,
                  [(line, 'serif', d.get('title_size', 72), True, '--text-1') for line in _lines(d['title'])])
        if d.get('lede'):
            self.text(s, LEFT, 520, 640, 120, [(d['lede'], 'sans', 20, False, '--text-2')])
        self.footer(s, d.get('footer', ''), page_no, total)

    def wash(self, d, page_no, total):
        """整页染层：渐变底、布尔轮廓、path 轮廓都行；文字压在上面。
        这一页的意义是「瓦作里的渐变/布尔能在 C 出口出现」，不是又一个内容页型。"""
        s = self.slide()
        color = d.get('color', '--text-1')
        if d.get('kicker'):
            self.bar(s, LEFT, 118, 22, 3, '--primary')
            self.text(s, LEFT + 30, 108, 1100, 24, [(d['kicker'], 'sans', 12, True, color)])
        if d.get('title'):
            self.text(s, LEFT, d.get('title_y', 236), 1240, 260,
                      [(line, 'serif', d.get('title_size', 72), True, color) for line in _lines(d['title'])])
        if d.get('lede'):
            self.text(s, LEFT, d.get('lede_y', 520), 1000, 120,
                      [(d['lede'], 'sans', 20, False, color)])
        self.footer(s, d.get('footer', ''), page_no, total)

    def bullets(self, d, page_no, total):
        s = self.slide()
        self.text(s, LEFT, 90, 1000, 60,
                  [((_lines(d['title']) or [''])[0], 'serif', 44, True, '--text-1')])
        caps = d.get('captions') or []
        for i, item in enumerate(d['items']):
            y = 240 + i * 116
            self.bar(s, LEFT, y + 6, 3, 34, '--primary')
            self.text(s, LEFT + 28, y, 1000, 40, [(item, 'sans', 24, False, '--text-1')])
            # 正页小注是 `captions`（与 items 一一对应）。
            # ⛔ 不是 `notes`：notes 是讲稿，只进备注页，见 page-record.md 硬约束 6。
            if i < len(caps) and caps[i]:
                self.text(s, LEFT + 28, y + 44, 1000, 30,
                          [(str(caps[i]), 'sans', 15, False, '--text-3')])
        self.footer(s, d.get('footer', ''), page_no, total)

    def kpi(self, d, page_no, total):
        s = self.slide()
        self.text(s, LEFT, 80, 1000, 60, [(d['title'], 'serif', 44, True, '--text-1')])
        cols = len(d['items'])
        cw = (CW - (cols - 1) * 40) / cols
        for i, (num, label) in enumerate(d['items']):
            x = LEFT + i * (cw + 40)
            self.bar(s, x, 240, cw, 3, '--primary')
            self.text(s, x, 262, cw, 96, [(num, 'sans', 64, True, '--accent')])
            self.text(s, x, 362, cw, 34, [(label, 'sans', 18, False, '--text-2')])
        self.footer(s, d.get('footer', ''), page_no, total)

    def comparison(self, d, page_no, total):
        """两栏对照（layouts/comparison.html）：1fr 90px 1fr，gap 28，卡顶 3px 色条。"""
        s = self.slide()
        self.head(s, d)
        gap, mid = 28, 90
        top = max(224.0, self.head_bottom + 20)
        card_w = (CW - mid - gap * 2) / 2
        n_items = max(len((d.get('left') or {}).get('items') or []),
                      len((d.get('right') or {}).get('items') or []), 1)
        h = 92 + n_items * 34 + 30  # 卡片贴内容长，不撑满版心——撑满就是四成留白
        for side, x, border, marker in (
            (d.get('left'), LEFT, '--bad', 'marker_bad'),
            (d.get('right'), LEFT + card_w + gap + mid + gap, '--good', 'marker_good'),
        ):
            if not side:
                continue
            self.panel(s, x, top, card_w, h, side.get('fill', '--surface'))
            self.bar(s, x, top, card_w, 3, border)
            self.text(s, x + 30, top + 28, card_w - 60, 40, [(side.get('title', ''), 'serif', 24, True, '--text-1')])
            for i, item in enumerate(side.get('items', [])):
                self.text(s, x + 30, top + 92 + i * 34, card_w - 60, 32, [(f'· {item}', 'sans', 15, False, '--text-2')])
        if d.get('mid'):
            self.text(s, LEFT + card_w + gap, top + h / 2 - 34, mid, 80, [(d['mid'], 'serif', 52, True, '--text-3')], align=PP_ALIGN.CENTER)
        self.footer(s, d.get('footer', ''), page_no, total)

    def timeline(self, d, page_no, total):
        """横向时间线（layouts/timeline.html）：贯线 + 圆点 + 年份/标题/说明。"""
        s = self.slide()
        self.head(s, d)
        items = d['items']
        n = max(len(items), 1)
        gap = 22
        cw = (CW - (n - 1) * gap) / n
        dy = max(0.0, self.head_bottom + 20 - 262)
        line_y = dot_cy = 316 + dy
        self.bar(s, LEFT, line_y, CW, 2, '--border')
        for i, it in enumerate(items):
            x = LEFT + i * (cw + gap)
            self.text(s, x, 262 + dy, cw, 24, [(it.get('year', ''), 'sans', 13, True, '--text-3')], align=PP_ALIGN.CENTER)
            self.dot(s, x + cw / 2, dot_cy, 22, '--accent')
            self.text(s, x, 356 + dy, cw, 32, [(it.get('title', ''), 'serif', 18, True, '--text-1')], align=PP_ALIGN.CENTER)
            if it.get('desc'):
                self.text(s, x, 396 + dy, cw, 80, [(it['desc'], 'sans', 13, False, '--text-2')], align=PP_ALIGN.CENTER, spacing=1.5)
        self.footer(s, d.get('footer', ''), page_no, total)

    def _series_color(self, i: int, n: int) -> RGBColor:
        """系列配色：单 accent 主题里没有八个色。第 1 条用 accent，其余向背景色分级淡化——
        明度即数据，不新增色值（⛔ 别在这里写死第二份调色板）。"""
        accent = self.c('--accent')
        bg = self.c('--bg')
        if n <= 1 or i == 0:
            return accent
        t = min(0.72, 0.22 * i)  # 逐条向底色淡出
        return RGBColor(*[int(round(a + (b - a) * t)) for a, b in zip(accent, bg)])

    def chart(self, d, page_no, total):
        """原生图表页（layouts/charts.html 的 C 出口）：python-pptx add_chart →
        在 PowerPoint 里可编辑（改数据、换系列、改配色），不是贴图。
        spec：{"type":"chart","title":…,"chart":{"kind":"bar|line|pie|radar",
        "categories":[…],"series":[{"name":…,"values":[…]}]}}"""
        s_ = self.slide()
        self.head(s_, d)
        spec = d.get('chart') or {}
        kind = str(spec.get('kind') or 'bar').lower()
        cats = list(spec.get('categories') or [])
        series = list(spec.get('series') or [])
        if not cats or not series:
            raise ValueError('chart 页缺数据：要 categories 与 series')
        if len(cats) != len(series[0].get('values') or []):
            raise ValueError('chart 页 categories %d 个、第一系列 %d 个值，对不上'
                             % (len(cats), len(series[0].get('values') or [])))
        kinds = {
            'bar': XL_CHART_TYPE.COLUMN_CLUSTERED,
            'column': XL_CHART_TYPE.COLUMN_CLUSTERED,
            'bar-h': XL_CHART_TYPE.BAR_CLUSTERED,
            'line': XL_CHART_TYPE.LINE_MARKERS,
            'pie': XL_CHART_TYPE.PIE,
            'doughnut': XL_CHART_TYPE.DOUGHNUT,
            'radar': XL_CHART_TYPE.RADAR,
        }
        if kind not in kinds:
            raise ValueError('chart kind 只认 %s（瀑布/哑铃/点阵是 B 出口专有：C 里没有原生等价，'
                             '别硬塞成柱状图）' % '/'.join(sorted(kinds)))
        cd = CategoryChartData()
        cd.categories = cats
        for i, ser in enumerate(series, 1):
            cd.add_series(str(ser.get('name') or f'系列 {i}'), [float(v) for v in ser['values']])
        top = max(232.0, self.head_bottom + 20)
        h = 690 - top
        gf = s_.shapes.add_chart(kinds[kind], px(LEFT), px(top), px(CW), px(h), cd)
        ch = gf.chart
        ch.has_title = False  # 标题由 head() 写，图表自带标题会重复
        ch.font.size = Pt(13)
        try:
            ch.font.name = self.font_for('sans', False)['latin']
        except Exception:
            pass
        n = len(series)
        ch.has_legend = n > 1
        if ch.has_legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        plot = ch.plots[0]
        # 系列配色（饼图按点配色，柱/线按系列配色）
        if kind in ('pie', 'doughnut'):
            pts = list(plot.series[0].points)
            for i, pt in enumerate(pts):
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = self._series_color(i, len(pts))
                pt.format.line.color.rgb = self.c('--bg')
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.show_percentage = True
            dl.show_value = False
            dl.position = XL_LABEL_POSITION.BEST_FIT
        else:
            for i, ser in enumerate(plot.series):
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = self._series_color(i, n)
                try:
                    ser.format.line.color.rgb = self._series_color(i, n)
                except Exception:
                    pass
        if d.get('note'):
            self.text(s_, LEFT, 706, 900, 24, [(d['note'], 'sans', 13, False, '--text-3')])
        self.footer(s_, d.get('footer', ''), page_no, total)

    def table(self, d, page_no, total):
        """原生表格（layouts/table.html）：表头小字、行间 1px 分隔线，单元格可改。"""
        s = self.slide()
        self.head(s, d)
        cols, rows = d['cols'], d['rows']
        nrow, ncol = len(rows) + 1, len(cols)
        top, row_h, head_h = max(218.0, self.head_bottom + 16), 56, 46
        shape = s.shapes.add_table(nrow, ncol, px(LEFT), px(top), px(CW), px(head_h + row_h * len(rows)))
        tbl = shape.table
        tbl.first_row = True
        widths = d.get('col_widths') or [None] * ncol
        if all(widths):
            for i, wv in enumerate(widths):
                tbl.columns[i].width = px(wv * CW / sum(widths))
        else:
            for i in range(ncol):
                tbl.columns[i].width = px(CW / ncol)
        for r in range(nrow):
            tbl.rows[r].height = px(head_h if r == 0 else row_h)
            for c in range(ncol):
                cell = tbl.cell(r, c)
                cell.margin_left = cell.margin_right = px(14)
                cell.margin_top = cell.margin_bottom = px(6)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.fill.solid()
                cell.fill.fore_color.rgb = self.c('--bg')
                _cell_bottom(cell, self.t.get('--border', '#dddddd'))
                txt = cols[c] if r == 0 else str(rows[r - 1][c])
                num = r > 0 and c >= (d.get('num_from', ncol))
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.RIGHT if num else PP_ALIGN.LEFT
                run = p.add_run()
                run.text = txt
                bold = r > 0 and bool(d.get('first_col_bold')) and c == 0
                ff = self.font_for('sans', bold)
                set_font(run, ff['latin'], ff['ea'], 12 if r == 0 else 16, ff['bold'],
                         self.c('--text-3' if r == 0 else '--text-1'))
        self.footer(s, d.get('footer', ''), page_no, total)

    def quote(self, d, page_no, total):
        """大字引用（layouts/big-quote.html）：引号 140px、正文 56px、署名 20px，居中。"""
        s = self.slide()
        x, w = 200, 1200
        txt = str(d['text'])
        # 引用页的字号按字数回退：56px 只够 14 个汉字一行，18 字仍会剩一个孤字
        size = d.get('size') or (56 if len(txt) <= 14 else (44 if len(txt) <= 24 else 36))
        self.text(s, x, 168, w, 140, [('“', 'serif', 140, True, '--accent-2')], align=PP_ALIGN.CENTER, spacing=0.9)
        self.text(s, x, 286, w, 240, [(line, 'serif', size, True, '--text-1') for line in _lines(d['text'])],
                  align=PP_ALIGN.CENTER, spacing=1.25)
        if d.get('by'):
            self.text(s, x, 300 + size * 1.9, w, 40, [(d['by'], 'sans', 20, False, '--text-2')], align=PP_ALIGN.CENTER)
        self.footer(s, d.get('footer', ''), page_no, total)

    def figure(self, d, page_no, total):
        """一图一页（C 出口的原生图片页）：图按原比例缩进版心，图注在下，图本身可换可裁。

        spec：{"type":"figure","title":…,"image":"相对 spec 的路径或绝对路径","caption":…}
        图默认不裁（contain）；要满幅请直接用 cover 页 + 背景图，别把裁剪写进这一页。
        """
        s = self.slide()
        self.head(s, d)
        src = Path(str(d['image']))
        if not src.is_absolute():
            src = (Path(getattr(self, 'base_dir', Path('.'))) / src).resolve()
        if not src.is_file():
            raise ValueError(f'figure 页图不存在：{src}')
        if src.suffix.lower() == '.svg':
            raise ValueError('figure 页不收 SVG：pptx 里只能塞位图，矢量请先在 B 出口出 PNG')
        top = max(236.0, self.head_bottom + 18)
        box_w, box_h = CW, 690 - top
        pic = s.shapes.add_picture(str(src), px(LEFT), px(top), width=px(box_w))
        if pic.height > px(box_h):
            ratio = box_h / (pic.height / 7620.0)
            pic.width, pic.height = int(pic.width * ratio), px(box_h)
        pic.left = px(LEFT + (box_w - pic.width / 7620.0) / 2)
        if d.get('caption'):
            pic_w = int(pic.width / 7620.0)
            cap_y = top + pic.height / 7620.0 + 14
            self.text(s, LEFT + (box_w - pic_w) / 2, cap_y, pic_w, 40,
                      [(d['caption'], 'sans', 15, False, '--text-3')])
        self.footer(s, d.get('footer', ''), page_no, total)

    def code(self, d, page_no, total):
        """代码页（C 出口）：面板 + 等宽行，行距固定，长行按字符折（不靠自动换行）。

        spec：{"type":"code","title":…,"lines":["…"],"lang":"bash","note":…}
        等宽字体要本机有 Menlo/Consolas/Courier New；缺了就退 Courier New，仍等宽。
        """
        s = self.slide()
        self.head(s, d)
        raw = [str(x) for x in (d.get('lines') or [])]
        if not raw:
            raise ValueError('code 页没有 lines')
        top = max(232.0, self.head_bottom + 20)
        # 等宽行高固定：一个字符格 = 字号 * 0.6，折行自己算，避免 PowerPoint 自动换行把缩进吃掉
        # 短块（≤3 行）放大字号，一两条命令不该缩在角落
        size = d.get('size') or (22 if len(raw) <= 3 else 16)
        # Menlo 的字符宽是 0.6 em；字号是 pt，版心是「120 px = 1 inch」，所以一格 = size * 120/72 * 0.6
        cell = size * PX_PER_IN / 72.0 * 0.6
        per_line = max(20, int((CW - 72) / cell))
        shown = []
        # 等宽格不能按字符数算：一个汉字占两格，按 len() 折会把行折短、按纯字符又溢出面板
        for ln in raw:
            while _cell_width(ln) > per_line:
                cut, acc = 0, 0
                for ch in ln:
                    w = _cell_width(ch)
                    if acc + w > per_line:
                        break
                    acc += w
                    cut += 1
                # 能断在空格/`-`/`/` 就断，别把 centu|ry-ave 这种词劈成两半
                sp = max(ln.rfind(' ', 0, cut), ln.rfind('-', 0, cut), ln.rfind('/', 0, cut))
                if sp > per_line // 3:
                    shown.append(ln[:sp + 1].rstrip())
                    ln = '    ' + ln[sp + 1:].lstrip()
                else:
                    shown.append(ln[:cut])
                    ln = '    ' + ln[cut:].lstrip()
            shown.append(ln)
        cap = int((690 - top - 48) // (size * 1.6))
        lines = shown[:max(1, cap)]
        box_h = max(120.0, min(690 - top, len(lines) * size * 1.6 + 48))
        # 短代码块别贴着标题吊在上半页：在正文区里垂直居中，页面重心才不歪
        if 690 - top > box_h:
            top += (690 - top - box_h) / 2
        self.panel(s, LEFT, top, CW, box_h, '--surface', '--border')
        if d.get('lang'):
            self.text(s, LEFT, top - 26, 160, 22,
                      [(str(d['lang']).upper(), 'sans', 11, True, '--text-3')])
        if len(shown) > len(lines):
            lines[-1] = lines[-1][:max(0, per_line - 3)] + '…'
        # 代码行不走 text()：它会按 sans 量宽再折行，等宽段必须自己控制换行
        box = s.shapes.add_textbox(px(LEFT + 28), px(top + 22), px(CW - 56), px(box_h - 44))
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        for i, ln in enumerate(lines):
            p_ = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p_.line_spacing = 1.15
            r = p_.add_run()
            r.text = ln if ln else ' '
            r.font.size = Pt(size)
            r.font.name = 'Menlo'
            r.font.color.rgb = self.c('--text-2')
        if d.get('note'):
            self.text(s, LEFT, top + box_h + 10, CW, 30, [(d['note'], 'sans', 14, False, '--text-3')])
        if len(shown) > len(lines):
            self.text(s, LEFT + CW - 160, top + box_h + 10, 160, 30,
                      [(f'共 {len(shown)} 行，截到 {len(lines)}', 'sans', 12, False, '--text-3')],
                      align=PP_ALIGN.RIGHT)
        self.footer(s, d.get('footer', ''), page_no, total)

    def end(self, d, page_no, total):
        s = self.slide()
        self.text(s, LEFT, 300, 1200, 200,
                  [(line, 'serif', 56, True, '--text-1') for line in _lines(d['title'])], anchor=MSO_ANCHOR.MIDDLE)
        if d.get('lede'):
            self.text(s, LEFT, 520, 900, 60, [(d['lede'], 'sans', 20, False, '--text-2')])
        self.footer(s, d.get('footer', ''), page_no, total)


def _cell_width(ch: str) -> int:
    """等宽字体里汉字的显示宽度是字母的两倍（也可直接传整串）。"""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in ch)


def _soft_shadow(shape, blur_px=34, dist_px=10, alpha_pct=16) -> None:
    """卡片要立起来才有「一张卡」的样子。CSS 的 box-shadow 换不掉，就用原生 outerShdw 近它。"""
    emu = 914400 / PX_PER_IN
    sp_pr = shape._element.spPr
    for old in sp_pr.findall(qn('a:effectLst')):
        sp_pr.remove(old)
    eff = parse_xml(
        f'<a:effectLst {nsdecls("a")}><a:outerShdw blurRad="{int(blur_px * emu)}" dist="{int(dist_px * emu)}" '
        f'dir="5400000" rotWithShape="0"><a:srgbClr val="121828"><a:alpha val="{int(alpha_pct * 1000)}"/>'
        '</a:srgbClr></a:outerShdw></a:effectLst>')
    # effectLst 在 spPr 里必须排在 fill 之后、line 之前
    ln = sp_pr.find(qn('a:ln'))
    if ln is not None:
        ln.addprevious(eff)
    else:
        sp_pr.append(eff)


def _cell_bottom(cell, hex_color: str) -> None:
    """表格单元只画下边框 1px——python-pptx 没有边框 API，得自己塞 a:lnB。"""
    tc_pr = cell._tc.get_or_add_tcPr()
    for old in tc_pr.findall(qn('a:lnB')):
        tc_pr.remove(old)
    ln = parse_xml(
        f'<a:lnB {nsdecls("a")} w="9525" cap="flat" cmpd="sng" algn="ctr">'
        f'<a:solidFill><a:srgbClr val="{hex_color.lstrip("#")[:6].upper()}"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:lnB>')
    tc_pr.insert_element_before(ln, 'a:cell3D', 'a:noFill', 'a:solidFill')



# ---------- 近似预览（不是 PowerPoint 渲染） ----------
# 本机没有 LibreOffice，PowerPoint 的 AppleScript 导出 PDF 报 -1712/-1728，qlmanage 只出首页。
# 于是自己按产物里的形状画一遍：位置、断行、字重能核对，阴影/渐变/字距核不了。
# ⛔ 这是 QA 的「眼睛」，不是交付件，也不许拿它冒充 PowerPoint 的渲染结果。
def _draw_text(dr, txt, x, y, w, h, size_px, bold, color, faces, align='left', anchor='top'):
    from PIL import ImageFont, ImageDraw
    path = faces.get('bold' if bold else 'regular') or faces.get('regular')
    if not path:
        return
    font = ImageFont.truetype(path, int(round(size_px)))
    lines = []
    for line in txt.split('\n'):
        if line:
            lines.append(line)
    lh = size_px * 1.45
    total = lh * max(len(lines), 1)
    ty = y + ((h - total) / 2 if anchor == 'middle' else 0)
    for line in lines:
        tw = font.getlength(line)
        tx = x + ((w - tw) / 2 if align == 'ctr' else (w - tw if align == 'r' else 0))
        dr.text((tx, ty), line, font=font, fill=color)
        ty += lh


def _faces_for(role_family: str) -> dict:
    """族名 → {regular: 文件, bold: 文件}：随包优先，其次本机。"""
    faces = {}
    bundle = bundled_fonts().get(role_family)
    if bundle:
        faces['regular'] = str(bundle.get('regular') or bundle.get('bold'))
        faces['bold'] = str(bundle.get('bold') or bundle.get('regular'))
        return faces
    faces['regular'] = font_file(role_family)
    faces['bold'] = faces['regular']
    return faces


def render_preview(path: Path, outdir: Path) -> list[Path]:
    from PIL import Image, ImageDraw
    prs = Presentation(str(path))
    outdir.mkdir(exist_ok=True)
    bg = tuple(int(str(s.background.fill.fore_color.rgb)[i:i + 2], 16) for i in (0, 2, 4)) if False else (255, 255, 255)
    pages = []
    for idx, slide in enumerate(prs.slides, 1):
        try:
            bg = tuple(int(str(slide.background.fill.fore_color.rgb)[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            pass
        img = Image.new('RGB', (CANVAS_W, CANVAS_H), bg)
        dr = ImageDraw.Draw(img)
        for sh in slide.shapes:
            x, y = int(sh.left / 914400 * PX_PER_IN), int(sh.top / 914400 * PX_PER_IN)
            w, h = int(sh.width / 914400 * PX_PER_IN), int(sh.height / 914400 * PX_PER_IN)
            if sh.has_table:
                tbl = sh.table
                cy = y
                for r, row in enumerate(tbl.rows):
                    cx = x
                    rh = int(row.height / 914400 * PX_PER_IN)
                    for c, cell in enumerate(row.cells):
                        cw = int(tbl.columns[c].width / 914400 * PX_PER_IN)
                        try:
                            rgb = tuple(int(str(cell.fill.fore_color.rgb)[i:i + 2], 16) for i in (0, 2, 4))
                            dr.rectangle([cx, cy, cx + cw, cy + rh], fill=rgb)
                        except Exception:
                            pass
                        dr.line([cx, cy + rh, cx + cw, cy + rh], fill=(200, 200, 200), width=1)
                        size = 15
                        bold = False
                        col = (60, 60, 60)
                        try:
                            r0 = cell.text_frame.paragraphs[0].runs[0]
                            size = (r0.font.size.pt if r0.font.size else 12) / 0.75
                            bold = bool(r0.font.bold)
                            col = tuple(int(str(r0.font.color.rgb)[i:i + 2], 16) for i in (0, 2, 4))
                        except Exception:
                            pass
                        fam = 'Inter'
                        try:
                            rpr = cell.text_frame.paragraphs[0].runs[0]._r.find(qn('a:rPr'))
                            fam = rpr.find(qn('a:ea')).get('typeface')
                        except Exception:
                            pass
                        _draw_text(dr, cell.text, cx + 14, cy + 8, cw - 28, rh - 16, size, bold, col,
                                   _faces_for(fam), align='r' if c >= 2 else 'left')
                        cx += cw
                    cy += rh
                continue
            if sh.has_text_frame and sh.text_frame.text.strip():
                anchor = 'middle' if sh.text_frame.vertical_anchor == MSO_ANCHOR.MIDDLE else 'top'
                paras = list(sh.text_frame.paragraphs)
                ty = y
                for p in paras:
                    if not p.runs:
                        ty += 10
                        continue
                    r0 = p.runs[0]
                    size = (r0.font.size.pt if r0.font.size else 12) / 0.75
                    col = (30, 30, 30)
                    try:
                        col = tuple(int(str(r0.font.color.rgb)[i:i + 2], 16) for i in (0, 2, 4))
                    except Exception:
                        pass
                    ea = 'Inter'
                    try:
                        rpr = r0._r.find(qn('a:rPr'))
                        ea = rpr.find(qn('a:ea')).get('typeface')
                    except Exception:
                        pass
                    align = {PP_ALIGN.CENTER: 'ctr', PP_ALIGN.RIGHT: 'r'}.get(p.alignment, 'left')
                    _draw_text(dr, p.text, x, ty, w, int(size * 1.6), size, bool(r0.font.bold), col,
                               _faces_for(ea), align=align, anchor=('middle' if anchor == 'middle' and len(paras) == 1 else 'top'))
                    ty += int(size * 1.6)
                continue
            try:
                rgb = tuple(int(str(sh.fill.fore_color.rgb)[i:i + 2], 16) for i in (0, 2, 4))
            except Exception:
                rgb = None
            if rgb is None:
                continue
            oval = 'OVAL' in str(getattr(sh, 'auto_shape_type', ''))
            if w >= 300 and h >= 100:  # 大块面板给一点影子，否则浅底浅边在预览里等于不存在
                dr.rectangle([x + 6, y + 9, x + w + 6, y + h + 9], fill=tuple(max(0, ch - 6) for ch in bg))
            if oval:
                dr.ellipse([x, y, x + w, y + h], fill=rgb)
            else:
                dr.rectangle([x, y, x + w, y + h], fill=rgb)
        page = outdir / f'{idx:02d}.png'
        img.save(page)
        pages.append(page)
    return pages


PAGES = {
    'cover': 'cover', 'bullets': 'bullets', 'kpi': 'kpi', 'end': 'end',
    'comparison': 'comparison', 'timeline': 'timeline', 'table': 'table', 'quote': 'quote',
    'figure': 'figure', 'code': 'code',
    'chart': 'chart', 'wash': 'wash',
}


def verify(path: Path, expected_slides: int) -> list[str]:
    """回读产物：页数、形状数、字符数。少得像截图就红——截图 deck 一页只有 1 个 picture。"""
    problems = []
    if not path.is_file() or path.stat().st_size == 0:
        return [f'产物不存在或为空：{path}']
    prs = Presentation(str(path))
    slides = list(prs.slides)
    if len(slides) != expected_slides:
        problems.append(f'页数不符：产物 {len(slides)} ≠ spec {expected_slides}')
    for i, s in enumerate(slides, 1):
        shapes = list(s.shapes)
        chars = 0
        full_bleed_pic = False
        for sh in shapes:
            if sh.has_text_frame:
                chars += len(sh.text_frame.text.strip())
            if sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        chars += len(cell.text.strip())
            if sh.shape_type == 13:  # PICTURE
                if sh.width >= px(CANVAS_W) * 0.9 and sh.height >= px(CANVAS_H) * 0.9:
                    full_bleed_pic = True
        if full_bleed_pic:
            problems.append(f'第 {i} 页是整页贴图（截图 deck）')
        if len(shapes) < 3:
            problems.append(f'第 {i} 页只有 {len(shapes)} 个形状，像截图不像排过版')
        if chars < 4:
            problems.append(f'第 {i} 页正文 {chars} 字，读不出内容')
    return problems


def bundle_fonts(out: Path, picked: list[dict]) -> Path | None:
    """把用到的随包 ttf 拷到产物旁，并写一份给自己/客户看的安装说明。

    为什么不在 pptx 里塞字体：PowerPoint 的 fntdata 要 EOT 包裹，raw TTF 会被静默忽略，
    macOS 版 PowerPoint 与 Keynote 又都不认嵌入字体——花了工也不保证收件人看得见。
    拷文件 + 说清楚，比一个看不见有没有生效的嵌入字段诚实。
    """
    files = []
    for spec in picked:
        for key in ('path', 'bold_path'):
            p = spec.get(key)
            if p and str(p).startswith(str(FONT_DIR)) and p not in files:
                files.append(p)
    if not files:
        return None
    dest = out.with_name(f'{out.stem}-fonts')
    dest.mkdir(exist_ok=True)
    for p in files:
        shutil.copy2(p, dest / Path(p).name)
    (dest / '安装字体.command').write_text(
        '#!/bin/bash\n# 来雪亭：把随包字体装进用户字体库，装完重开 PowerPoint\n'
        'cd "$(dirname "$0")" || exit 1\nmkdir -p ~/Library/Fonts\n'
        'cp -v *.ttf ~/Library/Fonts/ && echo "已装入 ~/Library/Fonts"\n',
        encoding='utf-8')
    (dest / '安装字体.command').chmod(0o755)
    (dest / 'README.txt').write_text(
        '这些字体是给「打开这份 pptx 的人」准备的，不是给 pptx 本身用的。\n\n'
        'macOS：双击「安装字体.command」，或在「字体册」里把 *.ttf 拖进去。\n'
        'Windows：全选 *.ttf，右键 → 安装。\n\n'
        '为什么需要：PPT 没有网页那种按需加载字体，字体只认「这台机器装了什么」。\n'
        '缺字时 PowerPoint 会拿别的字面顶上，字形和断行都会变。\n'
        '本库已把断行锁成硬段，行不会乱跑；字形仍要靠装字体才一致。\n\n'
        '许可：Playfair Display / Inter 均为 SIL Open Font License 1.1，可随作品分发。\n',
        encoding='utf-8')
    return dest




SPPR_ORDER = ('xfrm', 'prstGeom', 'custGeom', 'noFill', 'solidFill', 'gradFill', 'pattFill',
              'blipFill', 'grpFill', 'ln', 'effectLst', 'effectDag', 'scene3d', 'sp3d', 'extLst')


def normalize_sp_pr(prs) -> int:
    """按 CT_ShapeProperties 的元素次序重排 spPr。

    不改语义，只改次序：OpenXML 是序列校验的，<a:ln> 排在 <a:effectLst> 之后
    就是非法——PowerPoint 容错、别的渲染器不容错，校验器会红。
    """
    from pptx.oxml.ns import qn
    fixed = 0
    for slide in prs.slides:
        for sp in slide.shapes._spTree.iterchildren(qn('p:sp')):
            spPr = sp.find(qn('p:spPr'))
            if spPr is None:
                continue
            kids = list(spPr)
            key = lambda e: SPPR_ORDER.index(e.tag.split('}')[-1]) if e.tag.split('}')[-1] in SPPR_ORDER else 99
            ranked = sorted(kids, key=key)
            if [id(k) for k in ranked] != [id(k) for k in kids]:
                for k in kids:
                    spPr.remove(k)
                for k in ranked:
                    spPr.append(k)
                fixed += 1
    return fixed


# --- 页切换：瓦作说多快、走哪个方向，PPT 就写哪个 ---
#
# 只收 OOXML 里能验的切换类型。飞书幻灯片那套名字（slides-flip / page-curl-double /
# peel-off）是它自己的转写，不是 PresentationML 的元素名，硬映射只会写出 PowerPoint
# 认不出的东西——所以宁可错手也报红，不静默改写成最像的那个。

NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_P14 = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
NS_P159 = 'http://schemas.microsoft.com/office/powerpoint/2015/09/main'
NS_MC = 'http://schemas.openxmlformats.org/markup-compatibility/2006'

# python-pptx 自动起的名字：'TextBox 3'、'Rectangle 7'、'Oval 2'……
# 序号是**每页独立**的，跨页没有任何含义，morph 也就对不上（见 Deck.role_names）。
DEFAULT_SHAPE_NAME = re.compile(
    r'^(?:TextBox|Rectangle|Oval|Rounded Rectangle|Freeform|Shape|Arc|Line|Connector)\s*\d*$')

DIRS = {'from-left': 'l', 'from-right': 'r', 'from-top': 'u', 'from-bottom': 'd',
        'from-top-left': 'lu', 'from-top-right': 'ru',
        'from-bottom-left': 'ld', 'from-bottom-right': 'rd',
        'l': 'l', 'r': 'r', 'u': 'u', 'd': 'd',
        'lu': 'lu', 'ru': 'ru', 'ld': 'ld', 'rd': 'rd'}

# type -> (元素名, 允许的参数键)
TRANSITIONS = {
    'fade': ('fade', {'thru_blk'}),
    'cut': ('cut', set()),
    'dissolve': ('dissolve', set()),
    'random': ('random', set()),
    'zoom': ('zoom', set()),
    'circle': ('circle', set()),
    'diamond': ('diamond', set()),
    'plus': ('plus', set()),
    'wedge': ('wedge', set()),
    'newsflash': ('newsflash', set()),
    'push': ('push', {'direction'}),
    'wipe': ('wipe', {'direction'}),
    'cover': ('cover', {'direction'}),
    'pull': ('pull', {'direction'}),
    'split': ('split', {'orientation', 'direction'}),
    'blinds': ('blinds', {'orientation'}),
    'comb': ('comb', {'orientation'}),
    'strips': ('strips', {'direction'}),
    'wheel': ('wheel', {'spokes'}),
    'morph': ('morph', {'option'}),
}


def _css_decl_block(paths: list[Path], selector: str) -> str:
    """把几份 CSS 里某选择器的声明块按顺序拼起来（后面的覆盖前面的）。"""
    pat = re.compile(r'(?<![\w.-])' + re.escape(selector) + r'\s*\{([^}]*)\}')
    out = ''
    for p in paths:
        if p and p.is_file():
            for m in pat.finditer(p.read_text(encoding='utf-8')):
                out += m.group(1) + ';'
    return out


def transition_metrics(theme: str, deck_css: Path | None) -> dict:
    """从瓦作读出页切换的真实语义：.slide 的 transition 时长与位移幅度。

    base.css 里 `.slide{opacity:0; transform:translateX(30px); transition:opacity .5s …, transform .5s …}`
    ——所以「页切换」在本库是一层透明度 + 一小段横移，不是整页推移。
    时长按最后一条 `transition:` 的第一个时间值算；位移记下来，供 push 时给方向。
    报出**真正给值的那份文件**，别让读的是 base.css、说的是主题文件。
    """
    paths = [ASSETS / 'base.css', THEMES / f'{theme}.css']
    if deck_css:
        paths.append(deck_css)
    ms, shift, hit = 500, 0.0, None
    for p in paths:
        block = _css_decl_block([p], '.slide')
        for decl in block.split(';'):
            if decl.strip().startswith('transition:'):
                times = re.findall(r'([\d.]+)(m?s)\b', decl)
                if times:
                    v, unit = times[0]
                    ms, hit = int(float(v) * (1000 if unit == 's' else 1)), p.name
            if decl.strip().startswith('transform:'):
                m = re.search(r'translateX\(\s*(-?[\d.]+)px', decl)
                if m:
                    shift = float(m.group(1))
    return {'duration_ms': ms, 'shift_px': shift,
            'source': hit or f'{theme}.css'}   # 没有 .slide 切换声明时，报主题文件（默认值由它兜）



def _write_notes(slide, d) -> None:
    """讲稿进 PowerPoint 备注页（page-record.md 硬约束 6：notes 不上面）。

    两种形态都接：str（pages/NN.md 派生的讲稿）、list（老 spec 的逐条副文案）。
    ⛔ 以前这里根本没写备注页，`notes` 反而被 bullets() 当正页小注画上去了——
    讲稿泄到观众页、备注页却是空的（2026-11-23 三席评审共识 #C）。
    """
    v = d.get('notes')
    if not v:
        return
    txt = '\n'.join(_lines(v)) if not isinstance(v, str) else v.strip()
    if not txt:
        return
    try:
        slide.notes_slide.notes_text_frame.text = txt
    except Exception as e:          # 备注页是加分项，不能因为它出件失败
        print(f'  ⚠ 第 {slide.slide_id} 页写备注页失败：{e}', file=sys.stderr)



def strip_stray_placeholders(prs) -> int:
    """删掉母版与版式里残留的「日期 / 页脚 / 页码」占位。

    python-pptx 自带模板在这些版式上留了三个空占位，PowerPoint 放映时通常不显示，
    但第三方渲染器（officecli、LibreOffice）会把它们连同 `1/27/13` 这种残留日期一起画出来，
    于是成品图上凭空多出一行小字。整册都是 blank 版式，删掉不影响任何内容页。
    """
    import re as _re
    pat = _re.compile(r'(Date|Footer|Slide Number) Placeholder', _re.I)
    n = 0
    for m in list(prs.slide_masters):
        for s in list(m.shapes):
            if pat.search(s.name or ''):
                s._element.getparent().remove(s._element)
                n += 1
        for lay in list(m.slide_layouts):
            for s in list(lay.shapes):
                if pat.search(s.name or ''):
                    s._element.getparent().remove(s._element)
                    n += 1
    return n


def build_timing(groups: list[list[int]], dur_ms: int = 400) -> "lxml.etree._Element":
    """写这一页的 p:timing：每个 group 一次点击，组内形状同一次淡入。

    为什么分组而不逐形状：一页真要按形状点 9 次，放映时没人受得了。这里把形状按
    阅读顺序切成 N 组（默认 ≤4 组），一组一次回车。树形是 PowerPoint 自己的写法：
    一次点击 = 一个 `clickEffect`，组内其余形状挂 `withEffect`，grpId 相同。
    """
    dur = max(50, int(dur_ms))

    def eff(sp: int, k: int, first: bool, i: int) -> str:
        base = nid[0]
        nid[0] += 3
        kind = 'clickEffect' if first else 'withEffect'
        return (
            f'<p:par><p:cTn id="{base}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" '
            f'grpId="{k}" nodeType="{kind}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{base + 1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName>'
            f'</p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{base + 2}" dur="{dur}"/>'
            f'<p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>'
            f'</p:childTnLst></p:cTn></p:par>'
        )

    nid = [3]
    blocks = []
    for k, grp in enumerate(groups):
        outer = nid[0]; nid[0] += 1
        hold = nid[0]; nid[0] += 1
        inner = ''.join(eff(sp, k, i == 0, i) for i, sp in enumerate(grp))
        blocks.append(
            f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
            f'<p:childTnLst><p:par><p:cTn id="{hold}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
        )
    xml = (
        f'<p:timing {nsdecls("p")}><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
        f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst>{"".join(blocks)}</p:childTnLst></p:cTn>'
        f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f'</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
    )
    return parse_xml(xml)


def build_transition(tr: dict) -> "lxml.etree._Element":
    """把 {'type','duration_ms','direction','orientation','option',…} 变成 p:transition。

    morph 要包进 mc:AlternateContent：老版本 PowerPoint 走 fade 兜底，
    新版本走 p159:morph——这是 PowerPoint 自己写 morph 的方式。
    """
    kind = tr['type']
    ms = int(tr.get('duration_ms', 500))
    spd = 'fast' if ms <= 400 else ('med' if ms <= 800 else 'slow')
    if kind == 'none':
        tag = f'<p:transition xmlns:p="{NS_P}" spd="{spd}"><p:cut/></p:transition>'
    elif kind == 'morph':
        option = {'byObject': 'byObject', 'byWord': 'byWord', 'byCharacter': 'byCharacter'}.get(
            tr.get('option', 'byObject'))
        tag = (
            f'<mc:AlternateContent xmlns:mc="{NS_MC}" xmlns:p="{NS_P}" xmlns:p14="{NS_P14}" '
            f'xmlns:p159="{NS_P159}">'
            f'<mc:Choice Requires="p159">'
            f'<p:transition spd="{spd}" p14:dur="{ms}">'
            f'<p159:morph option="{option}"/>'
            f'</p:transition></mc:Choice>'
            f'<mc:Fallback><p:transition spd="{spd}" p14:dur="{ms}"><p:fade/></p:transition>'
            f'</mc:Fallback></mc:AlternateContent>')
    else:
        name, allowed = TRANSITIONS[kind]
        attrs = ''
        if 'direction' in allowed and tr.get('direction'):
            # split 的 dir 是「分开的方向」in/out，不是四个来向——两套枚举，别混
            attrs += f' dir="{tr["direction"]}"' if kind == 'split' else f' dir="{DIRS[tr["direction"]]}"'
        if 'orientation' in allowed and tr.get('orientation'):
            axis = 'horz' if tr['orientation'] == 'horizontal' else 'vert'
            # split 用 orient=，blinds / comb 用 dir=，两处枚举同值不同属性名
            attrs += f' orient="{axis}"' if kind == 'split' else f' dir="{axis}"'
        if kind == 'wheel' and tr.get('spokes'):
            attrs += f' spokes="{int(tr["spokes"])}"'
        if kind == 'fade' and tr.get('thru_blk'):
            attrs += ' thruBlk="1"'
        tag = f'<p:transition xmlns:p="{NS_P}" xmlns:p14="{NS_P14}" spd="{spd}" p14:dur="{ms}">' \
              f'<p:{name}{attrs}/></p:transition>'
    return etree.fromstring(tag.encode('utf-8'))


def check_transition(tr: dict) -> str | None:
    """参数的合法性：每种切换只认自己那一组，写错就报出来，不猜。"""
    kind = tr.get('type', 'fade')
    if kind == 'none':
        return None
    if kind not in TRANSITIONS:
        return (f'页切换 {kind} 不是 OOXML 的切换类型；可选：'
                + '/'.join(sorted(TRANSITIONS)) + '/none（飞书那套 slides-flip、page-curl 之类不是元素名，不收）')
    allowed = TRANSITIONS[kind][1] | {'duration_ms', 'type'}
    extra = set(tr) - allowed
    if extra:
        return f'页切换 {kind} 不接受参数 {"/".join(sorted(extra))}（只认 {"/".join(sorted(allowed - {"duration_ms", "type"})) or "无"}）'
    if tr.get('direction') and 'direction' in TRANSITIONS[kind][1]:
        legal = ('in', 'out') if kind == 'split' else tuple(DIRS)
        if tr['direction'] not in legal:
            return f'页切换 {kind} 的 direction 只认 ' + ' / '.join(legal) + f'，收到 {tr["direction"]}'
    if tr.get('orientation') and tr['orientation'] not in ('horizontal', 'vertical'):
        return f'页切换 {kind} 的 orientation 只认 horizontal / vertical'
    if kind == 'morph' and tr.get('option') and tr['option'] not in ('byObject', 'byWord', 'byCharacter'):
        return f'morph 的 option 只认 byObject / byWord / byCharacter'
    if kind == 'wheel' and tr.get('spokes') and not (1 <= int(tr['spokes']) <= 8):
        return 'wheel 的 spokes 只能是 1–8'
    return None


def find_officecli() -> str | None:
    """officecli 是单二进制、不依赖 Office 的读/写/校验/渲染工具。
    本机常装在 ~/.local/bin，PATH 里未必有，所以两处都找。"""
    found = shutil.which('officecli')
    if found:
        return found
    guess = Path.home() / '.local' / 'bin' / 'officecli'
    return str(guess) if guess.is_file() else None


def render_check(out: Path, pages: int, grid: bool = False, only: list[int] | None = None) -> dict:
    """真渲染核验：结构问题清单 + OpenXML 校验 + 逐页 PNG。拿不到 officecli 就明确说没做。

    三处效率口径（都是拿 officecli 自己的批量/轻量模式换来的，不是内化它）：
    - `view issues` 0.2 s 给的是**可判的问题类型**（低对比、图被压扁、preset 调整被拒…），
      比 schema 通不通更有用，所以放在 validate 前面跑，先拿快的。
    - `--grid auto --page 1-N` 一次调用（约 5 s）出整册缩略拼图，管「有没有炸版」；
      全分辨率逐页要 5–7 s/页，所以只在要留证据或点名页时跑。
    - `--render-pages` 只重渲点名页：改一页不必把 20 页全渲一遍。
    """
    exe = find_officecli()
    if not exe:
        return {'available': False, 'note': '未找到 officecli（~/.local/bin/officecli）'}
    info: dict = {'available': True, 'exe': exe}
    # 先关掉可能存在的驻留：它可能拿着「上一次」的副本，校验会报已经修掉的错。
    subprocess.run([exe, 'close', str(out)], capture_output=True, text=True, timeout=60)
    # ① 结构问题（快）
    try:
        r = subprocess.run([exe, 'view', str(out), 'issues', '--json'],
                           capture_output=True, text=True, timeout=120)
        doc = json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}
        data = doc.get('data') or {}
        info['issues'] = data.get('count', 0)
        info['issue_types'] = sorted({i.get('type', '?') for i in (data.get('issues') or [])})[:6]
    except Exception:
        info['issues'] = None
    # ② schema 校验
    proc = subprocess.run([exe, 'validate', str(out)], capture_output=True, text=True, timeout=120)
    info['validate'] = (proc.stdout + proc.stderr).strip().splitlines()[-1:] or ['']
    info['validate'] = info['validate'][0] if info['validate'] else ''
    info['validate_ok'] = proc.returncode == 0
    shot_dir = out.with_name(f'{out.stem}-render')
    shot_dir.mkdir(parents=True, exist_ok=True)
    made: list[str] = []
    if grid:
        target = shot_dir / 'grid.png'
        subprocess.run([exe, 'view', str(out), 'screenshot', '--page', f'1-{pages}', '--grid', 'auto',
                        '--screenshot-width', '1600', '-o', str(target)],
                       capture_output=True, text=True, timeout=300)
        if target.is_file():
            made.append(str(target))
        info['grid'] = str(target) if target.is_file() else None
    else:
        for i in (only or range(1, pages + 1)):
            target = shot_dir / f'{i:02d}.png'
            subprocess.run([exe, 'view', str(out), 'screenshot', '--page', str(i),
                            '--screenshot-width', '1600', '--screenshot-height', '900',
                            '-o', str(target)], capture_output=True, text=True, timeout=180)
            if target.is_file():
                made.append(str(target))
    info['renders'] = made
    return info


def prose_gate(slides):
    """成稿闸（references/prose-gate.md 的九条）：红一条就不该出片。
    文不对题的一页出来，比版式错十处更贵——所以闸放在出件前，不放在渲染后。"""
    import importlib.util
    path = Path(__file__).with_name('check-prose.py')
    if not path.is_file():
        return {'red': 0, 'warn': 0, 'lines': []}
    spec = importlib.util.spec_from_file_location('check_prose', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.red.clear(), mod.warn.clear()
    for i, d in enumerate(slides, 1):
        mod.check_page(d, i)
    lines = ['✗ %s 第 %s 页 %s：%s' % r[:4] for r in mod.red] + \
            ['⚠ %s 第 %s 页 %s：%s' % w[:4] for w in mod.warn]
    return {'red': len(mod.red), 'warn': len(mod.warn), 'lines': lines}


def main() -> int:
    ap = argparse.ArgumentParser(description='用主题 token 出原生可编辑 PPTX（C 出口）')
    ap.add_argument('spec', help='deck spec JSON（slides[] 里 type ∈ ' + '/'.join(PAGES) + '）')
    ap.add_argument('-o', '--out', required=True, help='输出 .pptx')
    ap.add_argument('--theme', default='century-sq', help='瓦作：assets/themes/<name>.css')
    ap.add_argument('--hb-measure', action='store_true',
                    help='用 uharfbuzz 整段 shaping 量宽（装了才有；会改变断行结果，默认不开）')
    ap.add_argument('--deck-css', help='整册模板的 style.css：标题的字体角色/字号优先从它读')
    ap.add_argument('--force', action='store_true', help='覆盖已有产物（先留 .bak 基线）')
    ap.add_argument('--no-lock', action='store_true', help='不锁断行（默认按 HTML 侧字面量宽后写死换行）')
    ap.add_argument('--bundle-fonts', action='store_true', help='把用到的随包字体拷到产物旁的 <name>-fonts/')
    ap.add_argument('--preview', action='store_true', help='另出逐页近似 PNG（<out>-preview/NN.png），只作核对')
    ap.add_argument('--render-check', action='store_true',
                    help='出件后用 officecli 做结构问题清单 + OpenXML 校验 + 逐页真渲染（<out>-render/NN.png）')
    ap.add_argument('--render-grid', action='store_true',
                    help='只出整册缩略拼图（<out>-render/grid.png）：一次调用约 5 秒，管炸版不替证据')
    ap.add_argument('--render-pages', default=None,
                    help='只重渲点名页（逗号分隔，如 1,3）：改一页不必全渲')
    ap.add_argument('--transition', default=None,
                    help='页切换类型（默认按瓦作推：fade + .slide 的 transition 时长）。'
                         '可选 ' + '/'.join(sorted(TRANSITIONS)) + '/none；页面里写 "transition" 可单页覆盖')
    ap.add_argument('--transition-ms', type=int, default=None, help='页切换时长（默认读 .slide 的 transition 时长）')
    ap.add_argument('--allow-prose', action='store_true',
                    help='成稿闸报红也照样出片（默认：红一条就不出）')
    ap.add_argument('--animate', action='store_true',
                    help='逐块揭示：每页写 p:timing，放映时按回车一块一块淡入（页面写 animate:false 可单页关）')
    ap.add_argument('--animate-ms', type=int, default=400, help='每块淡入时长（毫秒）')
    ap.add_argument('--json', action='store_true', help='末行输出机器可读摘要')
    args = ap.parse_args()

    spec_path, out = Path(args.spec).expanduser().resolve(), Path(args.out).expanduser().resolve()
    if not spec_path.is_file():
        print(f'✗ spec 不存在：{spec_path}', file=sys.stderr)
        return 2
    if not (THEMES / f'{args.theme}.css').is_file():
        print(f'✗ 主题不存在：{args.theme}', file=sys.stderr)
        return 2
    if out.exists() and not args.force:
        print(f'= 已存在，跳过：{out}（要覆盖加 --force）')
        return 0
    if out.exists():
        bak = out.with_name(f'{out.name}.bak-{time.strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(out, bak)
        print(f'  回滚基线：{bak}')

    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    slides = spec['slides']
    prose = prose_gate(slides)
    if prose['red']:
        for line in prose['lines']:
            print(line, file=sys.stderr)
        if not args.allow_prose:
            print(f'✗ 成稿闸拦下：{prose["red"]} 条红（改字或加 --allow-prose；细则见 references/prose-gate.md）',
                  file=sys.stderr)
            return 1
        print(f'  ⚠ 成稿闸 {prose["red"]} 条红，按 --allow-prose 放行')
    elif prose['warn']:
        print(f'  成稿闸：红 0 / 警告 {prose["warn"]}（可以出片）')
    tokens = read_tokens(args.theme)
    have = installed_families()
    serif_stack, sans_stack = declared_families()
    bundled = bundled_fonts()
    fonts = {
        'serif': resolve_font('serif', have, serif_stack, bundled),
        'sans': resolve_font('sans', have, sans_stack, bundled),
        'latin-serif': resolve_font('latin-serif', have, serif_stack, bundled),
        'latin-sans': resolve_font('latin-sans', have, sans_stack, bundled),
    }

    deck_css = Path(args.deck_css).expanduser() if args.deck_css else None
    if deck_css and not deck_css.is_file():
        print(f'✗ --deck-css 不存在：{deck_css}', file=sys.stderr)
        return 2
    head = head_metrics(args.theme, deck_css)
    tr_metrics = transition_metrics(args.theme, deck_css)
    tr_default = {'type': args.transition or 'fade',
                  'duration_ms': args.transition_ms or tr_metrics['duration_ms']}
    if tr_default['type'] in ('push', 'cover', 'pull', 'wipe') and tr_metrics['shift_px']:
        # 瓦作里 .slide 是 translateX(30px) 进场、-30px 退场，正号即「从右侧来」
        tr_default['direction'] = 'from-right' if tr_metrics['shift_px'] > 0 else 'from-left'
    wash_css = [ASSETS / 'base.css', THEMES / f'{args.theme}.css'] + ([deck_css] if deck_css else [])
    deck = Deck(tokens, fonts, lock=not args.no_lock, head=head, transition=tr_default,
                wash_css=wash_css)
    deck.base_dir = spec_path.parent
    total = len(slides)
    for i, d in enumerate(slides, 1):
        kind = d.get('type')
        if kind not in PAGES:
            print(f'✗ 第 {i} 页 type 未知：{kind}（可选 {"/".join(PAGES)}）', file=sys.stderr)
            return 2
        deck.pending_wash = d.get('wash') or d.get('shapes')
        try:
            getattr(deck, PAGES[kind])(d, i, total)
            deck.role_names(deck.prs.slides[-1], kind)
            deck.apply_transition(deck.prs.slides[-1], d)
            deck.apply_timing(deck.prs.slides[-1], d, args.animate, args.animate_ms)
            _write_notes(deck.prs.slides[-1], d)
        except ValueError as e:
            print(f'✗ 第 {i} 页 {e}', file=sys.stderr)
            return 2

    out.parent.mkdir(parents=True, exist_ok=True)
    normalize_sp_pr(deck.prs)
    deck.prs.save(str(out))
    problems = verify(out, total)
    for p in problems:
        print(f'✗ {p}', file=sys.stderr)

    font_dir = None
    if not problems and args.bundle_fonts:
        font_dir = bundle_fonts(out, list(fonts.values()))
    pages = []
    if not problems and args.preview:
        try:
            pages = render_preview(out, out.with_name(f'{out.stem}-preview'))
        except ImportError:
            print('  ⚠ 缺 Pillow，跳过近似预览', file=sys.stderr)

    only = None
    if args.render_pages:
        try:
            only = [int(x) for x in str(args.render_pages).replace('，', ',').split(',') if x.strip()]
        except ValueError:
            print('  ⚠ --render-pages 只认逗号分隔的页号，已忽略', file=sys.stderr)
    render = (render_check(out, total, grid=args.render_grid, only=only)
              if (not problems and (args.render_check or args.render_grid or only)) else None)

    summary = {
        'ok': not problems,
        'out': str(out),
        'slides': total,
        'bytes': out.stat().st_size,
        'theme': args.theme,
        'fonts': {r: {'family': v['family'], 'real_bold': bool(v.get('bold_path')), 'status': v['state']}
                  for r, v in fonts.items()},
        'locked_boxes': deck.locked_runs,
        'head': {'role': head[0], 'size_px': head[1], 'source': str(deck_css) if deck_css else args.theme},
        'wash': {'shapes': deck.wash_shapes, 'curve_bool': deck.wash_curve_bool,
                 'degraded': deck.wash_degraded, 'backend': wb.backend_report()},
        'timing': {'pages': deck.timed, 'shapes': deck.timed_shapes, 'clicks': deck.timed_clicks, 'ms': args.animate_ms},
        'transition': {'default': tr_default, 'pages': deck.transitions,
                       'source': 'CLI' if (args.transition or args.transition_ms) else tr_metrics['source']},
        'font_bundle': str(font_dir) if font_dir else None,
        'preview_pages': len(pages),
        'font_probe': 'fc-list' if have is not None else 'unavailable',
        'render': None if render is None else {
            'available': render['available'], 'validate_ok': render.get('validate_ok'),
            'issues': render.get('issues'), 'issue_types': render.get('issue_types', []),
            'pages': len(render.get('renders', [])), 'grid': bool(render.get('grid'))},
        'prose': {'red': prose['red'], 'warn': prose['warn']},
    }
    if problems:
        return 1
    size_kb = out.stat().st_size / 1024
    print(f'✓ 原生 PPTX：{out}（{total} 页，{size_kb:.0f} KB）')
    global HB_MEASURE
    HB_MEASURE = bool(args.hb_measure)
    print(f'  瓦作：{args.theme}（色与字号取自 :root，渐变/纹理不还原）')
    if HB_MEASURE:
        print('  量宽：uharfbuzz 整段 shaping' if wb.HAS_UHARFBUZZ
              else '  量宽：要 --hb-measure 但没装 uharfbuzz，已回落逐字')
    for role, spec_ in fonts.items():
        if spec_['state'] == '降级':
            print(f'  ⚠ 字体降级：{role} → {spec_["family"]}（{FALLBACK_NOTE}）')
    print(f'  标题：{head[1]:.0f}px / {head[0]}（读自 {deck_css.name if deck_css else args.theme + ".css"} 的 h2 规则）')
    if deck.wash_shapes:
        print(f'  染层：{deck.wash_shapes} 个形状（渐变/布尔/path 在导出时求值，见 wash_bridge.py）')
        if deck.wash_curve_bool:
            print(f'  曲线布尔：{deck.wash_curve_bool} 个走 skia-pathops 真裁剪（结果带 cubicBezTo）')
        if deck.wash_degraded:
            print(f'  ⚠ 降级：{len(deck.wash_degraded)} 个布尔退回折线——本机没装 skia-pathops')
    if getattr(deck, 'stripped_placeholders', 0):
        print(f'  模板清理：删掉 {deck.stripped_placeholders} 个残留页脚占位（渲染器会多画一行日期/页码）')
    if deck.timed:
        print(f'  逐块揭示：{deck.timed} 页 / {deck.timed_shapes} 个形状 / {deck.timed_clicks} 次点击'
              f'（每页 ≤4 组，淡入 {args.animate_ms}ms；放映时按回车出下一组）')
    elif args.animate:
        print('  逐块揭示：没有一页有三块以上内容，未写 timing')
    if deck.transitions:
        src = '命令行' if (args.transition or args.transition_ms) else f'{tr_metrics["source"]} 的 .slide'
        print(f'  页切换：{tr_default["type"]} {tr_default["duration_ms"]}ms × {deck.transitions} 页（读自 {src}）')
    else:
        print('  页切换：关闭（页面写了 transition: none，或全册 none）')
    if deck.locked_runs:
        print(f'  断行锁定：{deck.locked_runs} 个文本框按 HTML 侧字面量宽后写死换行'
              f'（量宽 {deck.runs_measured} 段、失败 {deck.measure_fail} 段）')
    elif deck.measure_fail:
        print(f'  ⚠ 断行未锁定：{deck.measure_fail} 段量字宽失败（缺字体文件或 Pillow），'
              f'收件人换字面时会重排')
    elif deck.runs_measured:
        print(f'  断行：{deck.runs_measured} 段全部单行，无需锁定（量字宽可用）')
    elif not args.no_lock:
        print('  ⚠ 断行未锁定：这份 spec 没有任何文本框，等于没验')
    if font_dir:
        print(f'  随包字体：{font_dir}（含安装说明；许可 OFL 1.1）')
    if pages:
        print(f'  近似预览：{out.with_name(f"{out.stem}-preview")}（{len(pages)} 张；位置/断行可核，渐变阴影不可核）')
    if render:
        if not render['available']:
            print(f'  ⚠ 未做真渲染核验：{render["note"]}')
        else:
            n_issue = render.get('issues')
            extra = ''
            if n_issue:
                extra = f'；结构问题 {n_issue} 个（{"/".join(render.get("issue_types") or [])}）'
            elif n_issue == 0:
                extra = '；结构问题 0'
            if render.get('grid'):
                print(f'  真渲染核验：OpenXML {"通过" if render["validate_ok"] else "有错"}，'
                      f'整册缩略 grid.png → {out.stem}-render/{extra}')
            else:
                print(f'  真渲染核验：OpenXML {"通过" if render["validate_ok"] else "有错"}，'
                      f'{len(render["renders"])} 页 PNG → {out.stem}-render/{extra}')
            if not render['validate_ok']:
                print(f'    {render["validate"]}', file=sys.stderr)
    if have is None:
        print('  ⚠ 本机没有 fc-list，字体是否命中未验证')
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
