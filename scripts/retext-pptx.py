#!/usr/bin/env python3
"""来雪亭Lesciotia :: retext-pptx.py — 往返闭环的最后一环：只改字，不动几何

用法：
    python3 scripts/retext-pptx.py deck.pptx --dump texts.json        # 先抽出可改的字
    python3 scripts/retext-pptx.py deck.pptx --edits texts.json -o out.pptx
    python3 scripts/retext-pptx.py deck.pptx --edits texts.json -o out.pptx --verify

为什么这样做：手上有份 pptx，只想换几句话时，最稳的路不是「读成 spec 再重排」——
那条路会把版式重新解释一遍，位置、字号、断行都可能挪。这里**在原文件上改**：
只动文字节点，几何、颜色、形状名、动画全留着；改完还逐形状核对一遍 `spPr` 没被动过。

edits.json 形状（`texts.json` 就是它的骨架，改哪个填哪个）：

    {"edits": [
      {"slide": 2, "id": 7, "text": "新的整段文字\\n第二段"},
      {"slide": 3, "name": "wash-s0", "text": "另一段"},
      {"slide": 1, "id": 4, "notes": "讲稿改这里"}
    ]}

`id` 优先，`name` 兜底（同一页重名会报错，不猜）。`text` 里用 `\\n` 分段，
新段沿用上一段的段落属性，斜体/字色/字号取自该段第一个 run。

⛔ 不做的事：不换字体族、不改版式、不重排断行。要那些，走 `pptx-to-html.py` 再回 spec。
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

GEOM_TAGS = ('spPr', 'xfrm', 'prstGeom', 'custGeom', 'txBody')


def _sp_hash(shape) -> str:
    """形状「非文字」部分的指纹：位置、尺寸、几何、填充、线。文字改了它不该变。"""
    from lxml import etree
    el = shape._element
    ns = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
    parts = []
    for tag in ('spPr', 'style'):
        for found in el.iter(ns + tag):
            parts.append(etree.tostring(found))
    # 文本内容与文字属性不在指纹里：只留 txBody 的 bodyPr
    for body in el.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}bodyPr'):
        parts.append(etree.tostring(body))
    h = hashlib.sha256(b''.join(parts)).hexdigest()[:16]
    return h


def inventory(prs) -> list[dict]:
    rows = []
    for si, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if not getattr(sh, 'has_text_frame', False) or not sh.has_text_frame:
                continue
            if not sh.text_frame.text.strip():
                continue
            rows.append({'slide': si, 'id': sh.shape_id, 'name': sh.name,
                         'text': sh.text_frame.text,
                         'paras': len(sh.text_frame.paragraphs),
                         'runs': sum(len(p.runs) for p in sh.text_frame.paragraphs),
                         'geom': _sp_hash(sh)})
    return rows


def _set_text_frame(tf, text: str) -> None:
    """替换文字，保留段落属性与首个 run 的字面（字号/字色/字重/字族）。"""
    from pptx.util import Pt  # noqa: F401  —— 让调用方拿到一致的依赖
    lines = text.split('\n')
    paras = tf.paragraphs
    proto = paras[0]
    proto_run = proto.runs[0] if proto.runs else None
    # 先把多余的段落删掉（只留第一段做模板）
    txBody = tf._txBody
    for p in list(paras)[1:]:
        txBody.remove(p._p)
    # 第一段：把首个 run 换成新文字，删掉其余 run
    p0 = tf.paragraphs[0]
    for r in list(p0.runs)[1:]:
        p0._p.remove(r._r)
    if p0.runs:
        p0.runs[0].text = lines[0]
    else:
        p0.add_run().text = lines[0]
    # 其余行：复制第一段的 pPr 与首个 run 的 rPr
    for line in lines[1:]:
        newp = copy.deepcopy(p0._p)
        # 清掉复制来的文字，留一个 run 壳
        for r in newp.findall('{http://schemas.openxmlformats.org/drawingml/2006/main}r'):
            newp.remove(r)
        txBody.append(newp)
        par = tf.paragraphs[-1]
        run = par.add_run() if proto_run is not None else par.add_run()
        run.text = line
        if proto_run is not None and proto_run._r.find(
                '{http://schemas.openxmlformats.org/drawingml/2006/main}rPr') is not None:
            rPr = proto_run._r.find('{http://schemas.openxmlformats.org/drawingml/2006/main}rPr')
            run._r.insert(0, copy.deepcopy(rPr))


def apply_edits(prs, edits: list[dict]) -> dict:
    rep = {'applied': 0, 'skipped': [], 'geom_changed': [], 'pages': set()}
    for e in edits:
        si = int(e.get('slide', 0))
        if not (1 <= si <= len(prs.slides._sldIdLst)):
            rep['skipped'].append(f'第 {si} 页不存在：{e}')
            continue
        slide = prs.slides[si - 1]
        # 只改讲稿时不必点名形状：{"slide":1,"notes":"…"} 就是对这一页的备注
        if 'notes' in e and 'id' not in e and 'name' not in e and 'text' not in e:
            slide.notes_slide.notes_text_frame.text = str(e['notes'])
            rep['applied'] += 1
            rep['pages'].add(si)
            continue
        target = None
        if 'id' in e:
            for sh in slide.shapes:
                if sh.shape_id == int(e['id']):
                    target = sh
                    break
        elif 'name' in e:
            hits = [sh for sh in slide.shapes if sh.name == e['name']]
            if len(hits) > 1:
                rep['skipped'].append(f'第 {si} 页有 {len(hits)} 个同名形状 {e["name"]}，请改用 id')
                continue
            target = hits[0] if hits else None
        if target is None:
            rep['skipped'].append(f'第 {si} 页找不到 {e.get("id") or e.get("name")}')
            continue
        before = _sp_hash(target)
        if 'notes' in e:
            tf = slide.notes_slide.notes_text_frame
            tf.text = str(e['notes'])
        if 'text' in e:
            if not getattr(target, 'has_text_frame', False) or not target.has_text_frame:
                rep['skipped'].append(f'第 {si} 页 id={target.shape_id} 不是文本框')
                continue
            _set_text_frame(target.text_frame, str(e['text']))
        if _sp_hash(target) != before:
            rep['geom_changed'].append(f'第 {si} 页 id={target.shape_id}')
        rep['applied'] += 1
        rep['pages'].add(si)
    rep['pages'] = sorted(rep['pages'])
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description='PPTX 往返：只改文字，几何不动')
    ap.add_argument('pptx')
    ap.add_argument('--dump', help='把可改的文字清单写成 JSON 到这个路径（不改文件）')
    ap.add_argument('--edits', help='要应用的 edits JSON')
    ap.add_argument('-o', '--out', help='改完的输出 .pptx（默认 <原名>-retext.pptx）')
    ap.add_argument('--verify', action='store_true', help='改完用 officecli 校验（缺工具就明说）')
    args = ap.parse_args()
    src = Path(args.pptx).expanduser().resolve()
    if not src.is_file():
        print(f'✗ 不存在：{src}', file=sys.stderr)
        return 2

    from pptx import Presentation
    prs = Presentation(str(src))

    if args.dump:
        rows = inventory(prs)
        Path(args.dump).expanduser().write_text(
            json.dumps({'source': str(src), 'shapes': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'✓ 文字清单：{args.dump}（{len(rows)} 个非空文本框，{len(prs.slides._sldIdLst)} 页）')
        return 0

    if not args.edits:
        print('要么 --dump 抽清单，要么 --edits 应用改动（见 --help）', file=sys.stderr)
        return 2

    edits_doc = json.loads(Path(args.edits).expanduser().read_text(encoding='utf-8'))
    edits = edits_doc.get('edits') if isinstance(edits_doc, dict) else edits_doc
    rep = apply_edits(prs, edits)
    out = Path(args.out) if args.out else src.with_name(src.stem + '-retext.pptx')
    prs.save(str(out))
    print(f'✓ 改完：{out}（应用 {rep["applied"]} 处，涉及第 {",".join(map(str, rep["pages"])) or "无"} 页）')
    if rep['geom_changed']:
        print('  ⚠ 这些形状的几何指纹变了（不该发生）：' + '、'.join(rep['geom_changed']))
    for s in rep['skipped']:
        print('  · ' + s)

    if args.verify:
        exe = None
        for cand in (Path.home() / '.local/bin/officecli', Path('/usr/local/bin/officecli')):
            if cand.is_file():
                exe = str(cand)
                break
        if not exe:
            print('  ⚠ 未找到 officecli，校验没做')
        else:
            import subprocess
            subprocess.run([exe, 'close', str(out)], capture_output=True, timeout=60)
            v = subprocess.run([exe, 'validate', str(out)], capture_output=True, text=True, timeout=120)
            i = subprocess.run([exe, 'view', str(out), 'issues', '--json'], capture_output=True, text=True, timeout=120)
            print(f'  校验：{"通过" if v.returncode == 0 else "未通过"}；问题：{i.stdout.strip()[:200]}')
    return 1 if rep['skipped'] and not rep['applied'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
