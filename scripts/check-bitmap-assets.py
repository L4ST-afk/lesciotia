#!/usr/bin/env python3
"""位图资产闸：登记表 vs 磁盘 vs 主题 CSS 的三方对账。

为什么需要它
------------
AI 生成的材质位图一旦进库，就同时带来四个新风险，全部是静默的：

  1. **漂移**：`marble-gray-1024.png` 被谁重新导出过一次，登记表的 sha 就过期了，
     但页面照常渲染——没有闸就没人发现「这张图已经不是上次验收的那张」。
  2. **越权**：位图容易带进来源不明的素材（网络图、字体厂商的样张、别人的照片）。
     没有许可字段就等于没有复制权。
  3. **越重**：一张 4K 彩色 PNG 塞进预览页，单文件从 3MB 变 9MB，页还能开，
     但「体量预算」这条纪律就无声地破了。
  4. **悬空 / 错层**：登记的图在 CSS 里没人引用（悬空资产），或者 CSS 引用的图没登记
     （黑户），两种都会在打包分发时变成断链。

判据（任一不成立就红）
--------------------
  B1 登记表能解析；每条必填字段齐全（id / theme / role / source / derived / blend /
     license / derived_sha256 / derived_w / derived_h / derived_mode / max_bytes / stage）
  B2 `derived` 文件存在；sha256 前缀与登记一致；宽高一致；PNG 色彩类型与 `derived_mode` 一致（L=0 灰度）
  B3 体积 ≤ `max_bytes`
  B4 `blend` 在允许集合内（multiply / soft-light / overlay / screen / none / mask）
  B5 `source` 文件存在（派生件的来源必须在库内，否则无法复现）
  B6 许可：`license=self-generated` 时，`ATTRIBUTION.md` 必须出现该 id（自制资产登记）；
     其它取值时必须在 `ATTRIBUTION.md` 出现 `license` 字符串
  B7 `stage=wired` 时，`wired`（形如 `assets/themes/<theme>.css::.cp-marble`）所指的 CSS 文件里
     必须出现 `derived` 的文件名；`stage=staged` 只印 INFO，不算问题
  B8 `assets/textures-src/` 下（除 `_work/`）所有 PNG/JPG 都必须是某个条目的 `source`
     ——没有登记的图不许躺在源目录里
  B9 **去重**：两条条目的 `derived_sha256` 相同（或 `derived` 路径相同）就红——一张 tile 只能登记
     一条，多处消费走 `used_by`。⛔ 按主题复制同一张图 = 抄一份 sha 出来，闸必须拦住
  B10 **分档预算**：`max_bytes` 本身也要合规——1024 面 ≤ 400000、512 面 ≤ 180000、更小 ≤ 200000。
  B11 **结构闸**：接线所在的主题 CSS 必须能正常解析——括号配平，且不允许「声明行紧接着选择器行」
      这种缺失右括号的形态。⛔ 少了那个 `}`，整段位图规则会被浏览器当成上一条规则的无效声明
      整段丢弃：选择器、blend、opacity 全都在文件里（B7 会判它绿），却在页面上完全不存在。
     只查「文件没超声明」会放过「声明写得很松」的条目

字段口径（v2）
-------------
  一条 = 一张 tile。`used_by` 是消费方数组，每项 `{theme, sel, blend, opacity, bg}`：
  同一张图被 2 个以上主题使用时，`used_by` 长度 ≥ 2 就是「家族共用件」，`stage=wired` 时
  每一处都要在对应主题 CSS 里真的接上（文件名 / 选择器 / blend / opacity 四项都要对得上）。

用法
----
    python3 scripts/check-bitmap-assets.py
    python3 scripts/check-bitmap-assets.py --registry /tmp/reg.json --src-root /tmp/src
    python3 scripts/check-bitmap-assets.py --json /tmp/out.json

退出码 0 = 全过；1 = 至少一条 FAIL；2 = 没跑成（找不到登记表等）。
⛔ 不联网、不写业务文件；`--json` 才写你指定的那个文件。
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

REQUIRED = ('id', 'family', 'role', 'source', 'derived', 'builder', 'blend', 'license',
            'derived_sha256', 'derived_w', 'derived_h', 'derived_mode',
            'max_bytes', 'stage', 'license_detail', 'used_by')
BUDGET = {1024: 400000, 512: 180000}   # 按面分档：主面 1024、次面 512；更小的一档见 budget_for()
BLENDS = {'multiply', 'soft-light', 'overlay', 'screen', 'none', 'mask'}
STAGES = {'staged', 'wired'}
COLOR_TYPES = {'L': 0, 'RGB': 2, 'P': 3, 'RGBA': 6}


def png_header(path):
    """只读 PNG 头：宽、高、位深、色彩类型。退出码不能当判据，产物本身才是。"""
    with open(path, 'rb') as f:
        head = f.read(33)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('不是 PNG（缺签名）')
    w, h, depth, ctype = struct.unpack('>IIBB', head[16:26])
    return w, h, depth, ctype


def sha256_prefix(path, n=16):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()[:n]


def budget_for(width, role=''):
    """按「面」给预算：1024 主面 400KB，512 次面 180KB，再小的 90KB。
    `role=hero-vein` 指不重复、按 cover 只铺一块版面的大脉络图——它不能靠拼贴摊薄体积，
    且是 1024 幅面的照片型灰阶（PNG 压不下去），因此单独一档 520KB。"""
    if role == 'hero-vein':
        return 520000 if width >= 1024 else 200000
    for edge in (1024, 512):
        if width >= edge:
            return BUDGET[edge]
    return 90000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--registry', default=os.path.join(ROOT, 'assets', 'textures-src', 'registry.json'))
    ap.add_argument('--src-root', default=None)
    ap.add_argument('--root', default=ROOT, help='被测根（做负例时指向一份临时拷贝）')
    ap.add_argument('--json', default=None)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    reg_path = os.path.abspath(args.registry)
    src_root = os.path.abspath(args.src_root or os.path.join(root, 'assets', 'textures-src'))
    print(f'skill_root={root}')
    print(f'registry={reg_path}')
    print(f'src_root={src_root}')

    if not os.path.isfile(reg_path):
        print(f'✗ 找不到登记表 {reg_path}', file=sys.stderr)
        return 2
    try:
        reg = json.load(open(reg_path, encoding='utf-8'))
    except json.JSONDecodeError as e:
        print(f'✗ 登记表不是合法 JSON：{e}', file=sys.stderr)
        return 2

    problems, infos = [], []
    assets = reg.get('assets') or []
    if not isinstance(assets, list) or not assets:
        problems.append('B1 登记表里没有任何条目')

    attr_path = os.path.join(root, 'ATTRIBUTION.md')
    attr = open(attr_path, encoding='utf-8').read() if os.path.isfile(attr_path) else ''
    if not attr:
        problems.append('B6 读不到 ATTRIBUTION.md，许可无从核对')

    declared_sources = set()
    seen_ids = set()
    for a in assets:
        aid = a.get('id', '<无 id>')
        missing = [k for k in REQUIRED if a.get(k) in (None, '')]
        if missing:
            problems.append(f'B1 {aid} 缺字段：{", ".join(missing)}')
            continue
        if aid in seen_ids:
            problems.append(f'B1 id 重复：{aid}')
        seen_ids.add(aid)

        if a['stage'] not in STAGES:
            problems.append(f'B1 {aid} stage 非法：{a["stage"]}（只认 {sorted(STAGES)}）')
        if a['blend'] not in BLENDS:
            problems.append(f'B4 {aid} blend 非法：{a["blend"]}（只认 {sorted(BLENDS)}）')

        derived = os.path.join(root, a['derived'])
        source = os.path.join(root, a['source'])
        declared_sources.add(os.path.abspath(source))

        if not os.path.isfile(source):
            problems.append(f'B5 {aid} 源图不存在：{a["source"]}（派生件无法复现）')

        if not os.path.isfile(derived):
            problems.append(f'B2 {aid} 派生件不存在：{a["derived"]}')
            continue
        try:
            w, h, depth, ctype = png_header(derived)
        except ValueError as e:
            problems.append(f'B2 {aid} {e}')
            continue
        if (w, h) != (a['derived_w'], a['derived_h']):
            problems.append(f'B2 {aid} 尺寸不符：磁盘 {w}x{h} ≠ 登记 {a["derived_w"]}x{a["derived_h"]}')
        want_ct = COLOR_TYPES.get(a['derived_mode'])
        if want_ct is None:
            problems.append(f'B2 {aid} derived_mode 不认识：{a["derived_mode"]}')
        elif ctype != want_ct:
            problems.append(f'B2 {aid} 色彩类型不符：PNG color_type={ctype} ≠ {a["derived_mode"]}({want_ct})'
                            f'——位图必须是灰度，颜色只能留在 :root')
        got_sha = sha256_prefix(derived)
        if got_sha != a['derived_sha256']:
            problems.append(f'B2 {aid} sha 漂移：磁盘 {got_sha} ≠ 登记 {a["derived_sha256"]}'
                            f'（图被重出过，重新验收后再改登记）')
        size = os.path.getsize(derived)
        if size > a['max_bytes']:
            problems.append(f'B3 {aid} 超体积预算：{size} B > {a["max_bytes"]} B')

        # B6 许可
        if not attr:
            pass
        elif a['license'] == 'self-generated':
            if aid not in attr:
                problems.append(f'B6 {aid} 标 self-generated 但 ATTRIBUTION.md 里没有该 id')
        elif a['license'] not in attr:
            problems.append(f'B6 {aid} 许可 {a["license"]} 未在 ATTRIBUTION.md 登记')

        # B10 声明预算本身是否合规（按面分档）
        allowed = budget_for(a['derived_w'], a.get('role', ''))
        if a['max_bytes'] > allowed:
            problems.append(f'B10 {aid} 声明的 max_bytes={a["max_bytes"]} 超过 {a["derived_w"]}px 面预算 {allowed}'
                            f'——分档预算不许写松')

        # B7 接线：一个 tile 的每个消费方都要真接上
        uses = a.get('used_by') or []
        if not isinstance(uses, list) or not uses:
            problems.append(f'B7 {aid} used_by 为空（没有任何消费方，这张图就是悬空的）')
        for u in uses:
            if not isinstance(u, dict) or not u.get('theme') or not u.get('sel'):
                problems.append(f'B7 {aid} used_by 条目缺 theme/sel：{u!r}')
                continue
            css_rel = 'assets/themes/%s.css' % u['theme']
            css_path = os.path.join(root, css_rel)
            if not os.path.isfile(css_path):
                problems.append(f'B7 {aid} 消费方主题不存在：{css_rel}')
                continue
            if a['stage'] != 'wired':
                continue
            text = open(css_path, encoding='utf-8').read()
            # 掩膜可以内联在 mask-image 里，也可以先提成 :root 的自定义属性（--marble-vein-mask）
            inline_mask = bool(re.search(r'(mask-image:url\("data:image/png;base64'
                                        r'|--[A-Za-z0-9_-]+:url\("data:image/png;base64)', text))
            if os.path.basename(a['derived']) not in text and not (u.get('blend') == 'mask' and inline_mask):
                problems.append(f'B7 {aid} 声明已接到 {u["theme"]}，但 {css_rel} 里没有 {os.path.basename(a["derived"])}')
            if u['sel'] not in text:
                problems.append(f'B7 {aid} 选择器 {u["sel"]} 不在 {css_rel} 里')
            blend = u.get('blend', a['blend'])
            if blend == 'mask':
                # 掩膜层没有 mix-blend-mode：形状靠 mask-image，颜色靠 token 的 background-color
                if 'mask-image:' not in text.replace('-webkit-mask-image:', 'mask-image:'):
                    problems.append(f'B7 {aid} {u["theme"]} 声明 mask 接线，但 {css_rel} 里没有 mask-image')
                elif 'var(--' not in text.split('mask-image:')[0][-800:]:
                    problems.append(f'B7 {aid} {u["theme"]} 掩膜层没有用 token 上色（bg 必须是 var(--…)）')
            elif blend.endswith('(bg)'):
                # 位图挪进元素自身的 background-image、由 background-blend-mode 与底色合成
                bg_line = re.search(r'background-blend-mode:[^;}]+', text)
                if not bg_line or blend[:-4] not in bg_line.group(0):
                    problems.append(f'B7 {aid} {u["theme"]} 的背景混合与登记不符：期望 background-blend-mode:{blend[:-4]}'
                                    f'（{css_rel} 里找不到）')
            elif 'mix-blend-mode:%s' % blend not in text:
                problems.append(f'B7 {aid} {u["theme"]} 的 blend 与登记不符：期望 {u.get("blend", a["blend"])}'
                                f'（{css_rel} 里找不到该值）')
            if u.get('opacity') not in ('', '1') and 'opacity:%s' % u['opacity'] not in text:
                problems.append(f'B7 {aid} {u["theme"]} 的 opacity 与登记不符：期望 {u["opacity"]}')
        # B11 结构闸：接线主题的 CSS 必须能解析（括号配平 + 无「声明→选择器」接缝）
        wired_themes = sorted({u.get('theme') for u in uses if isinstance(u, dict) and u.get('theme')})
        for th in wired_themes:
            css_path = os.path.join(root, 'assets/themes/%s.css' % th)
            if not os.path.isfile(css_path):
                continue   # B7 已报缺失
            text = open(css_path, encoding='utf-8').read()
            if text.count('{') != text.count('}'):
                problems.append(f'B11 {th}.css 括号不配平：{text.count("{")} 个 {{ vs {text.count("}")} 个 }}'
                                f'——整段规则会被静默丢弃')
                continue
            lines = text.split('\n')
            for i in range(len(lines) - 1):
                cur, nxt = lines[i].rstrip(), lines[i + 1].strip()
                if (cur.endswith(';') and not cur.lstrip().startswith(('/*', '*', '//'))
                        and nxt[:1] in '.#a-zA-Z[' and '{' in nxt):
                    problems.append(f'B11 {th}.css 第 {i + 2} 行缺右括号：{cur[:44]!r} 紧跟选择器 {nxt[:32]!r}'
                                    f'——上一条规则没闭合，后面的位图规则会整段作废')

        if a['stage'] != 'wired':
            infos.append(f'B7 {aid} 仍处 staged（未接进主题 CSS），不进页面 —— {a.get("stage_note", "")}')
        elif len(uses) >= 2:
            infos.append(f'· {aid} 为家族共用件：{len(uses)} 处消费 ' +
                         ','.join('%s%s' % (u['theme'], u['sel']) for u in uses))

    # B8 源目录里的孤儿
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if d != '_work']
        for fn in filenames:
            if not fn.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                continue
            full = os.path.abspath(os.path.join(dirpath, fn))
            if full not in declared_sources:
                rel = os.path.relpath(full, root)
                problems.append(f'B8 源目录里有未登记的图：{rel}（要么登记进 registry.json，要么删掉）')

    # B9 去重：一张 tile 只许一条
    by_sha, by_path = {}, {}
    for a in assets:
        if not a.get('derived_sha256'):
            continue
        sha = a['derived_sha256']
        path = os.path.normpath(a.get('derived') or '')
        if sha in by_sha or path in by_path:
            problems.append(f'B9 {a.get("id")} 与 {by_sha.get(sha) or by_path.get(path)} 是同一张 tile'
                            f'（sha/路径重复）——并成一条，多处消费写进 used_by')
        by_sha.setdefault(sha, a.get('id'))
        by_path.setdefault(path, a.get('id'))

    for p in problems:
        print(f'  ✗ {p}')
    for i in infos:
        print(f'  · {i}')
    total_px = sum(1 for _ in assets)
    print(f'\n{"FAIL" if problems else "PASS"} {len(assets)} 条目 / {len(problems)} 问题 / {len(infos)} 提示')

    if args.json:
        json.dump({'assets': len(assets), 'problems': problems, 'infos': infos},
                  open(args.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
