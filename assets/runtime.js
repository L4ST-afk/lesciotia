/* 来雪亭 :: runtime.js（2026-11-23 自写；与旧版同一套页面契约，16 族与 5 套整册不用改一行）
   本件只做六件事：缩放画布、翻页并同步各处状态、触发入场动效、开讲稿与总览、开演讲者窗、记深链。
   三条纪律：
     ① 不拿 DOM 里的 slide 数当页数（总览会克隆整页，数出来翻倍），页数只认初始集合；
     ② 所有状态只从一个 go(n) 出口写出去，别在键位里各写一半，否则观众屏与演讲者窗会不同步；
     ③ 观众屏与演讲者窗各管自己的键位，两边只通过 BroadcastChannel 说话。
   键位：←/→/空格/PgUp/PgDn/Enter/Home/End 翻页；F 全屏；S 演讲者窗；N 讲稿抽屉；O 总览；
        T 换主题（读 data-themes）；A 换当前页动效；B 黑屏；G 参考线；Esc 收浮层。 */
(function () {
  'use strict';

  /* 27 项：26 个 CSS 类 + counter-up（由本件的计数器实现）。⛔ 改名要同步 animations.css 与文档计数。 */
  const ANIMS = ['fade-up','fade-down','fade-left','fade-right','rise-in','drop-in',
    'zoom-pop','blur-in','glitch-in','typewriter','neon-glow','shimmer-sweep',
    'gradient-flow','stagger-list','counter-up','path-draw','parallax-tilt',
    'card-flip-3d','cube-rotate-3d','page-turn-3d','perspective-zoom',
    'marquee-scroll','kenburns','confetti-burst','spotlight','morph-shape','ripple-reveal'];

  /* 讲稿三种写法都认；⛔ 改这里要同步 base.css 的隐藏规则，否则稿子会投到墙上 */
  const NOTE_SEL = '.notes, aside.notes, .speaker-notes';

  const ready = fn => document.readyState !== 'loading' ? fn() : document.addEventListener('DOMContentLoaded', fn);

  /* 出图态：`?render` 掐掉过渡与入场动效，交给无头截图。
     为什么要它（2026-11-23 实测）：CSS 过渡不吃 `--virtual-time-budget`，跳页截图会截在
     opacity 0.5 的半路上，整页发灰。别用「多等几秒」去赌，直接把动效关掉。 */
  if (/[?&]render(=|&|$)/.test(location.search || '')) document.documentElement.setAttribute('data-render','1');

  /* 预览态：`?preview=N` 只显示第 N 页，无 chrome、无键位、不改 hash。演讲者窗靠它拿像素级小样。 */
  function previewIdx() {
    const m = /[?&]preview=(\d+)/.exec(location.search || '');
    return m ? parseInt(m[1], 10) - 1 : -1;
  }

  /* 画布缩放：固定设计尺寸，只缩不重排。 */
  function fitCanvas(deck) {
    if (document.body.getAttribute('data-fit') === 'fluid') return;
    const w = parseInt(deck.getAttribute('data-w'), 10) || 1920;
    const h = parseInt(deck.getAttribute('data-h'), 10) || 1080;
    deck.style.setProperty('--deck-w', w + 'px');
    deck.style.setProperty('--deck-h', h + 'px');
    const scale = () => deck.style.setProperty('--deck-scale', Math.min(window.innerWidth / w, window.innerHeight / h));
    scale();
    window.addEventListener('resize', scale);
    if (window.visualViewport) window.visualViewport.addEventListener('resize', scale);
  }

  ready(function () {
    const deck = document.querySelector('.deck');
    if (!deck) return;
    fitCanvas(deck);

    const slides = Array.from(deck.querySelectorAll('.slide'));
    const total = slides.length;
    const preview = previewIdx();
    const locked = preview >= 0;
    let idx = locked ? Math.min(preview, total - 1) : 0;

    /* —— 进度条 —— */
    let bar = document.querySelector('.progress-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.className = 'progress-bar';
      bar.innerHTML = '<span></span>';
      document.body.appendChild(bar);
    }
    const barFill = bar.querySelector('span');
    if (locked) bar.style.display = 'none';

    /* —— 讲稿抽屉（N） —— */
    let notes = document.querySelector('.notes-overlay');
    if (!notes) {
      notes = document.createElement('div');
      notes.className = 'notes-overlay';
      document.body.appendChild(notes);
    }

    /* —— 黑屏与参考线（B / G）：两个独立浮层，不参与翻页，也不进总览 —— */
    const blank = document.createElement('div');
    blank.style.cssText = 'position:fixed;inset:0;background:#000;z-index:60;display:none';
    document.body.appendChild(blank);
    const guide = document.createElement('div');
    guide.style.cssText = 'position:fixed;inset:0;z-index:59;display:none;pointer-events:none;' +
      'background-image:linear-gradient(to right,rgba(255,60,60,.45) 1px,transparent 1px),' +
      'linear-gradient(to bottom,rgba(255,60,60,.45) 1px,transparent 1px);background-size:112px 72px';
    document.body.appendChild(guide);

    /* —— logo：一册一枚，随画布缩放；印刷改由每页 ::after 画 —— */
    let logoEl = document.querySelector('.deck-logo');
    (function logo() {
      const src = document.body.getAttribute('data-logo');
      if (!logoEl && src) {
        logoEl = document.createElement('img');
        logoEl.className = 'deck-logo';
        logoEl.src = src;
        logoEl.alt = '';
        logoEl.setAttribute('data-pos', document.body.getAttribute('data-logo-position') || 'bottom-right');
        deck.appendChild(logoEl);
      }
      if (!logoEl) return;
      const pos = logoEl.getAttribute('data-pos') || 'bottom-right';
      const css = getComputedStyle(logoEl);
      deck.setAttribute('data-logo-print', pos);
      deck.style.setProperty('--logo-print', 'url("' + (logoEl.getAttribute('src') || '') + '")');
      deck.style.setProperty('--logo-size', css.height);
      deck.style.setProperty('--logo-opacity', css.opacity || '.9');
      const ix = parseFloat(css.left) || parseFloat(css.right);
      const iy = parseFloat(css.top) || parseFloat(css.bottom);
      if (ix) deck.style.setProperty('--logo-inset-x', ix + 'px');
      if (iy) deck.style.setProperty('--logo-inset-y', iy + 'px');
    })();

    function syncLogo(slide) {
      if (!logoEl) return;
      logoEl.style.display = slide && slide.hasAttribute('data-no-logo') ? 'none' : '';
    }

    /* —— 主题轮换（T）—— */
    const root = document.documentElement;
    const themes = (root.getAttribute('data-themes') || document.body.getAttribute('data-themes') || '')
      .split(',').map(s => s.trim()).filter(Boolean);
    let themeIdx = Math.max(0, themes.indexOf(root.getAttribute('data-theme') || ''));
    let themeBase = root.getAttribute('data-theme-base');
    if (!themeBase) {
      const href = (document.getElementById('theme-link') || {}).getAttribute
        ? (document.getElementById('theme-link').getAttribute('href') || '') : '';
      const cut = href.lastIndexOf('/');
      themeBase = cut >= 0 ? href.slice(0, cut + 1) : 'assets/themes/';
    }
    function applyTheme(name) {
      let link = document.getElementById('theme-link');
      if (!link) {
        link = document.createElement('link');
        link.rel = 'stylesheet';
        link.id = 'theme-link';
        document.head.appendChild(link);
      }
      link.href = themeBase + name + '.css';
      root.setAttribute('data-theme', name);
      const ind = document.querySelector('.theme-indicator');
      if (ind) ind.textContent = name;
    }

    /* —— 总览（O）：克隆整页缩小放进格子（所以 DOM 里的 slide 数会翻倍） —— */
    let overview = document.querySelector('.overview');
    if (!overview) {
      overview = document.createElement('div');
      overview.className = 'overview';
      slides.forEach((s, i) => {
        const thumb = document.createElement('div');
        thumb.className = 'thumb';
        const mini = document.createElement('div');
        mini.className = 'mini-slide';
        mini.style.cssText = 'position:absolute;top:0;left:0;width:1920px;height:1080px;' +
          'transform-origin:top left;pointer-events:none;background:var(--bg)';
        const clone = s.cloneNode(true);
        clone.className = 'slide is-active';
        clone.style.cssText = 'position:absolute;inset:0;transform:none;opacity:1;padding:72px 112px';
        mini.appendChild(clone);
        thumb.appendChild(mini);
        const n = document.createElement('div');
        n.className = 'n';
        n.textContent = String(i + 1);
        thumb.appendChild(n);
        const t = document.createElement('div');
        t.className = 't';
        t.textContent = (s.getAttribute('data-title') ||
          (s.querySelector('h1,h2,h3') || {}).textContent || ('第 ' + (i + 1) + ' 页')).trim().slice(0, 80);
        thumb.appendChild(t);
        thumb.addEventListener('click', () => { go(i); toggleOverview(false); });
        overview.appendChild(thumb);
      });
      document.body.appendChild(overview);
    }

    function toggleNotes(force) {
      notes.classList.toggle('open', force !== undefined ? force : !notes.classList.contains('open'));
    }
    function toggleOverview(force) {
      const open = force !== undefined ? force : !overview.classList.contains('open');
      overview.classList.toggle('open', open);
      if (!open) return;
      requestAnimationFrame(() => {
        const first = overview.querySelector('.thumb');
        if (!first || !first.clientWidth) return;
        const scale = first.clientWidth / 1920;
        overview.querySelectorAll('.mini-slide').forEach(m => { m.style.transform = 'scale(' + scale + ')'; });
      });
    }

    /* —— 翻页：唯一的状态出口 —— */
    let channel = null;
    try { channel = new BroadcastChannel('lx-deck:' + location.pathname); } catch (e) { channel = null; }

    function playAnimations(slide) {
      slide.querySelectorAll('[data-anim]').forEach(el => {
        const a = el.getAttribute('data-anim');
        el.classList.remove('anim-' + a);
        void el.offsetWidth;
        el.classList.add('anim-' + a);
      });
      slide.querySelectorAll('.counter').forEach(el => {
        const to = parseFloat(el.getAttribute('data-to') || el.textContent || '0');
        const dur = parseInt(el.getAttribute('data-dur') || '1200', 10);
        const t0 = performance.now();
        const step = now => {
          const p = Math.min(1, (now - t0) / dur);
          const v = to * (1 - Math.pow(1 - p, 3));      /* 缓出：先快后慢，读数才像在落定 */
          el.textContent = Number.isInteger(to) ? String(Math.round(v)) : v.toFixed(1);
          if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }

    /* —— 元素级分步（data-build）：整段标 data-build，子元素标 .step；空格先走步，走完再翻页 —— */
    const buildAt = new WeakMap();
    function buildSteps(slide) { return Array.from(slide.querySelectorAll('[data-build] .step')); }
    function resetBuild(slide) {
      if (!slide) return;
      const st = buildSteps(slide);
      const render = document.documentElement.hasAttribute('data-render');
      st.forEach((el, i) => el.classList.toggle('is-on', render || i === 0));
      if (st.length) buildAt.set(slide, render ? st.length : 1);
    }
    function advanceBuild(slide) {
      const st = buildSteps(slide);
      const n = buildAt.get(slide) || 0;
      if (!st.length || n >= st.length) return false;
      st[n].classList.add('is-on');
      buildAt.set(slide, n + 1);
      return true;
    }

    function go(n, fromRemote) {
      n = Math.max(0, Math.min(total - 1, n));
      slides.forEach((s, i) => {
        s.classList.toggle('is-active', i === n);
        s.classList.toggle('is-prev', i < n);
      });
      idx = n;
      syncLogo(slides[n]);
      if (barFill) barFill.style.width = ((n + 1) / total * 100) + '%';
      const num = document.querySelector('.slide-number');
      if (num) { num.setAttribute('data-current', String(n + 1)); num.setAttribute('data-total', String(total)); }
      const note = slides[n].querySelector(NOTE_SEL);
      notes.innerHTML = note ? note.innerHTML : '';
      if (!locked) {
        const hash = '#/' + (n + 1);
        if (location.hash !== hash) history.replaceState(null, '', hash);
      }
      playAnimations(slides[n]);
      resetBuild(slides[n]);
      if (!fromRemote && channel) channel.postMessage({ type: 'go', idx: n });
    }

    if (channel) channel.onmessage = e => {
      const d = e.data || {};
      if (d.type === 'go' && typeof d.idx === 'number') go(d.idx, true);
      if (d.type === 'theme' && d.name) {
        const i = themes.indexOf(d.name);
        if (i >= 0) themeIdx = i;
        applyTheme(d.name);
      }
    };

    /* —— 演讲者窗（S）：当前页 / 下一页 / 逐字稿 / 计时，四张可拖的卡 —— */
    let presenter = null;
    function slideMeta() {
      return slides.map(s => {
        const note = s.querySelector(NOTE_SEL);
        return {
          title: (s.getAttribute('data-title') || (s.querySelector('h1,h2,h3') || {}).textContent || '').trim(),
          notes: note ? note.innerHTML : ''
        };
      });
    }
    function openPresenter() {
      if (presenter && !presenter.closed) { presenter.focus(); return; }
      const deckUrl = location.protocol + '//' + location.host + location.pathname;
      const win = window.open('', 'lx-presenter', 'width=1280,height=860');
      if (!win) { alert('请允许弹窗，演讲者视图需要开一个新窗'); return; }
      presenter = win;
      win.document.write(presenterHTML(deckUrl, slideMeta(), idx, total));
      win.document.close();
    }

    /* 四张卡的版式：左上当前、右上下一页、左下逐字稿、右下计时。拖标题栏换位，松手不吸附——位置是人的事。 */
    function presenterHTML(deckUrl, meta, start, count) {
      const data = JSON.stringify(meta).replace(/</g, '\\u003c');   /* 讲稿里若有 </script>，不能截断内联脚本 */
      return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>演讲者视图</title><style>' +
        'html,body{margin:0;height:100%;background:#101216;color:#e9ecf3;font:14px/1.6 system-ui,"PingFang SC",sans-serif;overflow:hidden}' +
        '.card{position:absolute;background:#1b1e26;border:1px solid #2c313d;border-radius:10px;overflow:hidden;display:flex;flex-direction:column}' +
        '.bar{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;font-size:12px;color:#8d95a6;cursor:move;user-select:none;border-bottom:1px solid #262b35}' +
        '.body{flex:1;position:relative;overflow:hidden}' +
        '.body iframe{position:absolute;inset:0;width:100%;height:100%;border:0}' +
        '.script{padding:16px 20px;overflow:auto;font-size:19px;line-height:1.7}' +
        '.num{font-variant-numeric:tabular-nums}' +
        'button{background:#2a3040;color:#dfe4ee;border:1px solid #3a4252;border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}' +
        '</style>' +
        '<div class="card" style="left:2%;top:2%;width:56%;height:52%"><div class="bar"><span>当前页 <b class="num" id="c-i">1</b>/' + count + '</span><span>观众屏同步</span></div><div class="body"><iframe id="f-cur"></iframe></div></div>' +
        '<div class="card" style="left:60%;top:2%;width:38%;height:52%"><div class="bar"><span>下一页</span></div><div class="body"><iframe id="f-nxt"></iframe></div></div>' +
        '<div class="card" style="left:2%;top:56%;width:72%;height:42%"><div class="bar"><span>逐字稿</span></div><div class="script" id="scr"></div></div>' +
        '<div class="card" style="left:76%;top:56%;width:22%;height:42%"><div class="bar"><span>计时</span></div><div style="padding:14px;display:flex;flex-direction:column;gap:10px">' +
        '<div id="clock" class="num" style="font-size:40px;font-weight:700">00:00</div>' +
        '<div style="display:flex;gap:8px"><button id="prev">上一页</button><button id="next">下一页</button></div>' +
        '<button id="reset">R 重置计时</button></div></div>' +
        '<script>(function(){var M=' + data + ',N=' + count + ',T=' + start + ',i=T,t0=Date.now();' +
        'var cur=document.getElementById("f-cur"),nxt=document.getElementById("f-nxt"),scr=document.getElementById("scr"),' +
        'ci=document.getElementById("c-i"),clk=document.getElementById("clock");' +
        'var q=location.search?location.search.slice(1)+"&":"";' +
        'var bc;try{bc=new BroadcastChannel("lx-deck:"+(location.pathname.replace(/\\/(index\\.html)?$/,"")+"/index.html"))}catch(e){}' +
        'function show(k){var m=Math.max(0,Math.min(N-1,k));i=m;' +
        'cur.src="?"+q+"preview="+(m+1);' +
        'nxt.src="?"+q+"preview="+(m+2<=N?m+2:m+1);' +
        'ci.textContent=m+1;scr.innerHTML=(M[m]&&M[m].notes)||"<p style=\\"opacity:.5\\">本页没有写讲稿</p>";}' +
        'function go(k){show(k);bc&&bc.postMessage({type:"go",idx:i});}' +
        'function tick(){var s=Math.floor((Date.now()-t0)/1000);clk.textContent=String(Math.floor(s/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");}' +
        'setInterval(tick,1000);tick();' +
        'bc&&(bc.onmessage=function(e){var d=e.data||{};if(d.type==="go")show(d.idx)});' +
        'document.getElementById("prev").onclick=function(){go(i-1)};' +
        'document.getElementById("next").onclick=function(){go(i+1)};' +
        'document.getElementById("reset").onclick=function(){t0=Date.now();tick()};' +
        'document.addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key===" "||e.key==="PageDown"){go(i+1);e.preventDefault()}' +
        'else if(e.key==="ArrowLeft"||e.key==="PageUp"){go(i-1);e.preventDefault()}else if(e.key==="r"||e.key==="R"){t0=Date.now()}});' +
        'show(T);' +
        'document.querySelectorAll(".card").forEach(function(c){var b=c.querySelector(".bar");' +
        'b.addEventListener("mousedown",function(e){var sx=e.clientX,sy=e.clientY,l=parseFloat(c.style.left),t=parseFloat(c.style.top);' +
        'function mv(ev){c.style.left=(l+(ev.clientX-sx)/innerWidth*100)+"%";c.style.top=(t+(ev.clientY-sy)/innerHeight*100)+"%"}' +
        'function up(){document.removeEventListener("mousemove",mv);document.removeEventListener("mouseup",up)}' +
        'document.addEventListener("mousemove",mv);document.addEventListener("mouseup",up);e.preventDefault()})});' +
        '})();<\/script></html>';
    }

    /* —— 键位 —— */
    function fullscreen() {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
    }
    let animIdx = 0;
    function cycleAnim() {
      animIdx = (animIdx + 1) % ANIMS.length;
      const a = ANIMS[animIdx];
      const target = slides[idx].querySelector('[data-anim-target]') || slides[idx];
      ANIMS.forEach(x => target.classList.remove('anim-' + x));
      void target.offsetWidth;
      target.classList.add('anim-' + a);
      target.setAttribute('data-anim', a);
      const ind = document.querySelector('.anim-indicator');
      if (ind) ind.textContent = a;
    }

    if (!locked) {
      document.addEventListener('keydown', e => {
        if (e.metaKey || e.ctrlKey || e.altKey) return;
        switch (e.key) {
          case 'ArrowRight': case ' ': case 'PageDown': case 'Enter': advanceBuild(slides[idx]) ? 0 : go(idx + 1); e.preventDefault(); break;
          case 'ArrowLeft': case 'PageUp': case 'Backspace': go(idx - 1); e.preventDefault(); break;
          case 'Home': go(0); break;
          case 'End': go(total - 1); break;
          case 'f': case 'F': fullscreen(); break;
          case 's': case 'S': openPresenter(); break;
          case 'n': case 'N': toggleNotes(); break;
          case 'o': case 'O': toggleOverview(); break;
          case 't': case 'T':
            if (themes.length) {
              themeIdx = (themeIdx + 1) % themes.length;
              applyTheme(themes[themeIdx]);
              if (channel) channel.postMessage({ type: 'theme', name: themes[themeIdx] });
            }
            break;
          case 'a': case 'A': cycleAnim(); break;
          case 'b': case 'B': blank.style.display = blank.style.display === 'block' ? 'none' : 'block'; break;
          case 'g': case 'G': guide.style.display = guide.style.display === 'block' ? 'none' : 'block'; break;
          case 'Escape': toggleOverview(false); toggleNotes(false); blank.style.display = 'none'; guide.style.display = 'none'; break;
        }
      });

      /* 触屏翻页：被动监听，不抢捏合与原生滚动；一指、横向、50px 以上、800ms 内才算。 */
      let x0 = 0, y0 = 0, t0 = 0, tracking = false;
      const opts = { passive: true };
      const skip = ['overview', 'notes-overlay'];
      document.addEventListener('touchstart', e => {
        const hit = e.target.closest && e.target.closest('.overview,.notes-overlay,a,button,input,textarea,select,[data-no-swipe]');
        if (e.touches.length !== 1 || hit) { tracking = false; return; }
        x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now(); tracking = true;
      }, opts);
      document.addEventListener('touchmove', e => { if (e.touches.length > 1) tracking = false; }, opts);
      document.addEventListener('touchend', e => {
        if (!tracking) return;
        tracking = false;
        const t = e.changedTouches && e.changedTouches[0];
        if (!t || Date.now() - t0 > 800) return;
        const dx = t.clientX - x0, dy = t.clientY - y0;
        if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
        go(dx < 0 ? idx + 1 : idx - 1);
      }, opts);
      document.addEventListener('touchcancel', () => { tracking = false; }, opts);

      window.addEventListener('hashchange', () => {
        const m = /^#\/(\d+)/.exec(location.hash || '');
        if (m) go(Math.max(0, parseInt(m[1], 10) - 1), true);
      });
    }

    /* 先按深链落位，再同步一次；预览态只落位、不改 hash */
    const deep = locked ? null : /^#\/(\d+)/.exec(location.hash || '');
    go(deep ? Math.max(0, parseInt(deep[1], 10) - 1) : idx);
    try { window.parent && window.parent.postMessage({ type: 'preview-ready', index: idx }, '*'); } catch (e) {}
  });
})();
