/* lens.js —— 玻璃透镜位移场（2026-11-23 自写；机制说明见 references/effects-lens.md）
   用法：
     <div class="lens" data-lens-src="../../assets/covers/x.jpg"
          data-lens-bend="20" data-lens-aberr="3" data-lens-n="1.5"></div>
   成功：卡里追加 <canvas>，边缘棱带折射、中心零位移、RGB 三通道错位（色散）。
   失败：data-lens-state="turb"，由 lens.css 的湍流兜底接管（整面均匀波纹）。
   ⛔ file:// 直开读不到像素（canvas 被判跨源），必然走兜底；起本地 http 才有真透镜。
   只在 window.LescioLens 挂两个方法，不改 color/fonts，不接管翻页。
*/
(function () {
  var NS = 'http://www.w3.org/2000/svg', uid = 0;

  function defs() {
    var d = document.getElementById('lescio-lens-defs');
    if (!d) {
      d = document.createElementNS(NS, 'svg');
      d.setAttribute('id', 'lescio-lens-defs');
      d.setAttribute('aria-hidden', 'true');
      d.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
      document.body.appendChild(d);
    }
    return d;
  }

  function turbId() {
    var d = defs(), id = 'lescio-turb-' + (++uid);
    var f = document.createElementNS(NS, 'filter');
    f.setAttribute('id', id);
    f.setAttribute('x', '-10%'); f.setAttribute('y', '-10%');
    f.setAttribute('width', '120%'); f.setAttribute('height', '120%');
    f.innerHTML = '<feTurbulence type="fractalNoise" baseFrequency="0.006 0.011" numOctaves="2" seed="11" result="n"/>' +
      '<feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G"/>';
    d.appendChild(f);
    return id;
  }

  // 圆角矩形有向距离场：内部为负，外部为正，棱带在 0 附近
  function sdf(x, y, w, h, r) {
    var qx = Math.abs(x - w / 2) - (w / 2 - r),
        qy = Math.abs(y - h / 2) - (h / 2 - r);
    var ax = Math.max(qx, 0), ay = Math.max(qy, 0);
    return Math.sqrt(ax * ax + ay * ay) + Math.min(Math.max(qx, qy), 0) - r;
  }

  function fallback(el, why) {
    if (el.getAttribute('data-lens-state')) return;
    // 兜底也得有东西可晃：先补一张底图，再给整块上位移滤镜
    if (!el.querySelector('img,canvas')) {
      var im = document.createElement('img');
      im.alt = '';
      im.src = el.getAttribute('data-lens-src') || '';
      el.insertBefore(im, el.firstChild);
    }
    el.setAttribute('data-lens-state', 'turb');
    el.style.filter = 'url(#' + turbId() + ')';
    if (why) el.setAttribute('data-lens-why', why);
    var badge = el.querySelector('.lens-badge');
    if (badge) badge.textContent = '湍流兜底 · 读不到像素';
  }

  function render(el, img, o) {
    var w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) throw 'size';
    // 折射是低频效果，按 820 长边出图再放大，肉眼无差，逐像素代价降到 1/5
    var cap = Math.min(1, 820 / Math.max(w, h));
    var cw = Math.round(w * cap), ch = Math.round(h * cap);

    var src = document.createElement('canvas'); src.width = cw; src.height = ch;
    var sx = src.getContext('2d', { willReadFrequently: true });
    var k = Math.max(cw / img.naturalWidth, ch / img.naturalHeight);
    var iw = img.naturalWidth * k, ih = img.naturalHeight * k;
    sx.drawImage(img, (cw - iw) / 2, (ch - ih) / 2, iw, ih);
    var data = sx.getImageData(0, 0, cw, ch).data;  // ← file:// 会在这里抛 SecurityError

    var out = document.createElement('canvas'); out.width = cw; out.height = ch;
    var oc = out.getContext('2d');
    var od = oc.createImageData(cw, ch);
    var pix = od.data;

    var r = Math.min(cw, ch) * (o.round || 0.34);
    var band = Math.min(cw, ch) * (o.band || 0.10);   // 棱带宽度：只在边缘一圈折射
    var bend = o.bend || 20, aberr = o.aberr || 3;

    for (var y = 0; y < ch; y++) {
      for (var x = 0; x < cw; x++) {
        var d = sdf(x, y, cw, ch, r);
        // t=0 在棱带外缘，t=1 在内部平台；剖面 sin(πt/2)：缘陡内平
        var t = d <= 0 ? 1 : (d >= band ? 0 : Math.sin(Math.PI / 2 * (1 - d / band)));
        var mag = bend * Math.pow(1 - t, 2);          // 位移集中在棱带，中心为 0
        // 内向法线 = -∇sdf（用差分近似）
        var gx = sdf(x + 1, y, cw, ch, r) - sdf(x - 1, y, cw, ch, r);
        var gy = sdf(x, y + 1, cw, ch, r) - sdf(x, y - 1, cw, ch, r);
        var gl = Math.sqrt(gx * gx + gy * gy) || 1;
        var nx = -gx / gl, ny = -gy / gl;

        var i = (y * cw + x) * 4;
        // 三通道各按 scale±aberr 偏折一次 → 合成即色散
        for (var c = 0; c < 3; c++) {
          var m = mag * (1 + (c - 1) * aberr / 100);
          var px = Math.min(cw - 1, Math.max(0, Math.round(x + nx * m)));
          var py = Math.min(ch - 1, Math.max(0, Math.round(y + ny * m)));
          pix[i + c] = data[(py * cw + px) * 4 + c];
        }
        pix[i + 3] = 255;
      }
    }
    oc.putImageData(od, 0, 0);
    el.appendChild(out);
    el.setAttribute('data-lens-state', 'lens');
    var badge = el.querySelector('.lens-badge');
    if (badge) badge.textContent = '透镜位移场 · SDF/Snell/色散';
  }

  function mount(el) {
    var o = {
      src: el.getAttribute('data-lens-src'),
      bend: parseFloat(el.getAttribute('data-lens-bend') || '20'),
      aberr: parseFloat(el.getAttribute('data-lens-aberr') || '3'),
      round: parseFloat(el.getAttribute('data-lens-round') || '0.34'),
      band: parseFloat(el.getAttribute('data-lens-band') || '0.10')
    };
    if (!o.src) return fallback(el, 'nosrc');
    var img = new Image();
    img.decoding = 'async';
    img.onload = function () {
      try { render(el, img, o); } catch (e) { fallback(el, e && e.name ? e.name : String(e)); }
    };
    img.onerror = function () { fallback(el, 'imgerror'); };
    img.src = o.src;
  }

  function auto() {
    var list = document.querySelectorAll('.lens[data-lens-src]');
    for (var i = 0; i < list.length; i++) mount(list[i]);
  }

  window.LescioLens = { mount: mount, fallback: fallback };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', auto);
  } else { auto(); }
})();
