#!/usr/bin/env python3
"""装得下闸：字号阶梯抬上去之后，逐页量「有没有字掉出画布或被裁掉」。

为什么要这一支：v1.2.35 把正文从 12pt 抬到 16pt（照真件样本的档位），
字号一抬，装不下是必然后果——靠眼睛看 14 个族 × 几十段是看不完的，得机器量。

做法：拿 headless Chrome 打开页面，注入一段 JS，对每条 `.slide` 逐个检查
「带字的元素有没有越出画布、有没有被裁」，结果写进 DOM，再 --dump-dom 取回来。
不用 puppeteer / 不装 websocket——Chrome 自带的 --dump-dom 已经跑完 JS 了。

用法：
    python3 scripts/check-fit.py                       # 14 族 + 5 份示例整册
    python3 scripts/check-fit.py assets/layouts/text.html
    python3 scripts/check-fit.py --json                # 机器可读
    python3 scripts/check-fit.py --theme guanglan-rd   # 换主题再量一遍

判据（都是量出来的，不猜）：
    F1 越界   —— 带字元素的盒子超出画布右/下边 ≥3px
    F2 被裁   —— 自身 overflow:hidden 的盒子，内容比盒子高 ≥4px
    F3 溢出遮 —— 元素 scrollWidth 超 clientWidth 且没开省略号
    F4 父盒裁 —— 文字超出最近的 overflow:hidden 祖先（卡片的圆角会把字切掉，最难看）
出圈只报「带字的」元素：满幅底图、装饰色块、贴边渐变本来就该出血，不算错。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

PROBE = r"""
<script>
addEventListener('load', async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  await sleep(120);
  const out = [];
  document.querySelectorAll('.deck > section.slide, .deck > .slide').forEach((sl, i) => {
    const R = sl.getBoundingClientRect();
    const bad = [];
    const seen = new Set();
    sl.querySelectorAll('*').forEach(el => {
      // 脚本/样式里的源码不是正文，别拿它当越界
      if (el.closest('script, style')) return;
      // 讲稿浮层（.notes / .notes-overlay）是讲者屏上才出现的UI，不在画布里量
      if (el.closest('.notes, .notes-overlay, .overview, .deck-header, .deck-footer')) return;
      // 只查带「自己的」文字的元素：纯容器不管
      const own = Array.from(el.childNodes).filter(n => n.nodeType === 3)
        .map(n => n.textContent.trim()).join('');
      if (!own) return;
      const cls = (el.className || '').toString();
      if (/bleed|bg-|backdrop|decor|scrim|veil/.test(cls)) return;
      // 有可滚动祖先（长代码块）就地放过：内容滚得到，不算装不下
      for (let a = el.parentElement; a && a !== el.closest('.slide'); a = a.parentElement) {
        const s2 = getComputedStyle(a);
        if (s2.overflow === 'auto' || s2.overflow === 'scroll' ||
            s2.overflowY === 'auto' || s2.overflowY === 'scroll') return;
      }
      const b = el.getBoundingClientRect();
      const key = cls + '|' + own.slice(0, 12) + '|' + Math.round(b.top);
      if (seen.has(key)) return; seen.add(key);
      const overRight = b.right - R.right, overBottom = b.bottom - R.bottom,
            overLeft = R.left - b.left, overTop = R.top - b.top;
      if (overRight >= 3)  bad.push({why: 'F1 右越界 ' + Math.round(overRight) + 'px', t: own.slice(0, 20), c: cls});
      if (overBottom >= 3) bad.push({why: 'F1 下越界 ' + Math.round(overBottom) + 'px', t: own.slice(0, 20), c: cls});
      if (overLeft >= 3)   bad.push({why: 'F1 左越界 ' + Math.round(overLeft) + 'px', t: own.slice(0, 20), c: cls});
      if (overTop >= 3)    bad.push({why: 'F1 上越界 ' + Math.round(overTop) + 'px', t: own.slice(0, 20), c: cls});
      const st = getComputedStyle(el);
      // F4：往上找最近的裁剪祖光，比它大就算被切
      let anc = el.parentElement, clipped = false;
      while (anc && anc !== sl.parentElement) {
        const ast = getComputedStyle(anc);
        // overflow:auto/scroll 是「可滚动的容器」，不是裁掉 —— 长代码块就该滚
        if (ast.overflow === 'auto' || ast.overflow === 'scroll') break;
        if (ast.overflow === 'hidden' || ast.overflowY === 'hidden' || ast.overflowX === 'hidden') {
          const ar = anc.getBoundingClientRect();
          if (b.bottom - ar.bottom >= 4 || ar.top - b.top >= 4 || b.right - ar.right >= 4) {
            bad.push({why: 'F4 被父盒裁 ' + Math.round(b.bottom - ar.bottom) + 'px', t: own.slice(0, 20), c: cls});
          }
          break;
        }
        anc = anc.parentElement;
      }
      if (st.overflow === 'hidden' || st.overflowY === 'hidden') {
        if (el.scrollHeight - el.clientHeight >= 4)
          bad.push({why: 'F2 被裁 ' + (el.scrollHeight - el.clientHeight) + 'px', t: own.slice(0, 20), c: cls});
        if (el.scrollWidth - el.clientWidth >= 4 && st.textOverflow !== 'ellipsis')
          bad.push({why: 'F3 横向溢出 ' + (el.scrollWidth - el.clientWidth) + 'px', t: own.slice(0, 20), c: cls});
      }
    });
    out.push({page: i + 1, title: sl.dataset.title || '', bad: bad.slice(0, 12), n: bad.length});
  });
  const node = document.createElement('script');
  node.type = 'application/json'; node.id = 'fit-report';
  node.textContent = JSON.stringify(out);
  document.head.appendChild(node);
});
</script>
"""


def chrome_dump(path: Path) -> str:
    """在本机起一个只读的临时服务：请求 html 时把探针注进去，其余文件原样吐。

    ⛔ 别改回「复制到临时目录 + 软链 assets」那一版：软链会把探针注入的文件写回
    仓库里的 assets（写穿 symlink），一份 check 就能把 14 个族页全改脏。
    """
    if not os.path.exists(CHROME):
        return ''
    import http.server
    import socketserver
    import threading

    import urllib.parse
    ext = {}  # /__ext/<quote(name)> → 库外文件的真实绝对路径

    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, p):
            rel = p.lstrip('/').split('?')[0].split('#')[0]  # 保持百分号编码，与注册键同形
            if rel in ext:
                return ext[rel]
            return str(ROOT / rel)

        def do_GET(self):
            p = self.translate_path(self.path)
            if p.endswith('.html'):
                body = Path(p).read_text(encoding='utf-8')
                body = body.replace('</head>', PROBE + '</head>', 1) if '</head>' in body else PROBE + body
                raw = body.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            return super().do_GET()

        def log_message(self, *a):
            pass

    httpd = socketserver.TCPServer(('127.0.0.1', 0), Handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    try:
        ap = path.resolve()
        if ap.is_relative_to(ROOT):
            rel = str(ap.relative_to(ROOT)).replace(os.sep, '/')
        else:
            # 库外文件（已交付到 chats 的单文件 deck）走 /__ext/ 前缀，别冒充库内相对路径
            rel = '__ext/' + urllib.parse.quote(ap.name)
            ext[rel] = str(ap)
        url = 'http://127.0.0.1:%d/%s' % (port, rel)
        cmd = [CHROME, '--headless', '--disable-gpu', '--no-sandbox', '--allow-file-access-from-files',
               '--virtual-time-budget=6000', '--window-size=1920,1080', '--dump-dom', url]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return p.stdout
    finally:
        httpd.shutdown()
        httpd.server_close()


def parse(dom: str):
    m = re.search(r'<script type="application/json" id="fit-report">(.*?)</script>', dom, re.S)
    if not m:
        return None
    txt = m.group(1).replace('&quot;', '"').replace('&amp;', '&')
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None


def disp(p):
    """库内显示相对路径；已交付到库外的单文件 deck 直接给绝对路径（否则 relative_to 抛错）。"""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def collect(args):
    targets = []
    if args.files:
        targets = [Path(f) if Path(f).is_absolute() else ROOT / f for f in args.files]
    else:
        targets = sorted((ROOT / 'assets' / 'layouts').glob('*.html'))
        targets += sorted((ROOT / 'assets' / 'full-decks').glob('*/index.html'))
    return targets


def run_one(path: Path, theme: str | None):
    if theme:
        html = path.read_text(encoding='utf-8')
        html = re.sub(r'(id="theme-link" href=")[^"]+', r'\1../../assets/themes/%s.css' % theme, html, count=1)
        tmp = Path(tempfile.mkdtemp()) / path.name
        tmp.write_text(html, encoding='utf-8')
        dom = chrome_dump(tmp)
        path = tmp
    else:
        dom = chrome_dump(path)
    return parse(dom)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--theme', help='用指定主题重新量（如 guanglan-rd）')
    args = ap.parse_args()

    if not os.path.exists(CHROME):
        print('✗ 找不到 Chrome：%s；这一支只能靠真浏览器量。' % CHROME)
        return 2

    targets = collect(args)
    report, fails = [], 0
    for t in targets:
        pages = run_one(t, args.theme)
        if pages is None:
            report.append({'file': disp(t), 'error': '没拿到报告（页面没跑起来？）'})
            fails += 1
            continue
        bad_pages = [p for p in pages if p['n']]
        report.append({'file': disp(t), 'pages': len(pages), 'bad': bad_pages})
        if bad_pages:
            fails += 1

    if args.json:
        print(json.dumps({'verdict': 'fail' if fails else 'pass', 'files': report}, ensure_ascii=False, indent=1))
    else:
        for f in report:
            name = f['file']
            if 'error' in f:
                print('✗ %s：%s' % (name, f['error']))
                continue
            if not f['bad']:
                print('✓ %-46s %d 段 装得下' % (name, f['pages']))
                continue
            print('✗ %-46s %d/%d 段有余量不足' % (name, len(f['bad']), f['pages']))
            for p in f['bad']:
                print('   · 第%d段 %s' % (p['page'], p['title']))
                for b in p['bad'][:5]:
                    print('      %s ←「%s」(%s)' % (b['why'], b['t'], b['c'][:28]))
        print('\n装得下闸：%s' % ('可以交付' if not fails else '不许交付（%d 个文件有余量不足）' % fails))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
