/* ── Homepage-only behaviours ─────────────────────────────────────────
   Injected on the homepage only (render_customer_success_software with
   keep_nav).

   1. Stats band count-up: each stat number ("26%+", "5.4 hrs", "3.9M") counts
      up from 0 to its value when the band scrolls into view, keeping its
      prefix/suffix and decimal places. Numbers stay at their real values
      without JS.

   2. "Let's talk" bubbles slide in smoothly left to right when scrolled into
      view, then float gently (hidden only once this runs, via
      html.js-lt-bubbles; the animation itself is CSS in the homepage head). */
(function () {
  'use strict';
  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!('IntersectionObserver' in window) || REDUCED) return;

  // ── 2. "Let's talk" bubbles ──────────────────────────────────────────
  var lt = document.querySelector('.cs-lt-grid');
  if (lt) {
    document.documentElement.classList.add('js-lt-bubbles');
    var ltIo = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) { ltIo.disconnect(); lt.classList.add('is-in'); }
    }, { threshold: 0.4 });
    ltIo.observe(lt);
  }

  // ── 1. Stats band count-up ───────────────────────────────────────────
  var grid = document.querySelector('.kz-statsband-grid');
  if (!grid) return;

  var DURATION = 1400, STAGGER = 90;
  var nums = Array.prototype.slice.call(grid.querySelectorAll(':scope > div > div:first-of-type > div'));
  var stats = nums.map(function (el) {
    var m = el.textContent.trim().match(/^([^\d]*)([\d,]*\.?\d+)(.*)$/);
    if (!m) return null;
    var raw = m[2].replace(/,/g, '');
    var dec = raw.indexOf('.') >= 0 ? raw.split('.')[1].length : 0;
    return { el: el, pre: m[1], target: parseFloat(raw), dec: dec, suf: m[3], text: el.textContent };
  }).filter(Boolean);
  if (!stats.length) return;

  function fmt(s, v) { return s.pre + v.toFixed(s.dec) + s.suf; }
  function ease(t) { return 1 - Math.pow(1 - t, 3); }

  stats.forEach(function (s) { s.el.textContent = fmt(s, 0); });

  function run() {
    var t0 = performance.now();
    function frame(now) {
      var done = true;
      stats.forEach(function (s, i) {
        var t = Math.min(1, Math.max(0, (now - t0 - i * STAGGER) / DURATION));
        if (t < 1) done = false;
        s.el.textContent = t >= 1 ? s.text : fmt(s, s.target * ease(t));
      });
      if (!done) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  var io = new IntersectionObserver(function (entries) {
    if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); run(); }
  }, { threshold: 0.3 });
  io.observe(grid);
})();

/* 3. "Works inside ChatGPT / Claude / Copilot" tabs: click (or arrow keys)
      switches the mock chat; while in view it rotates on its own until the
      visitor picks one. No rotation with reduced motion.

   4. Its "Works with your AI" bubble flies in from above as the band scrolls
      into view, tied to scroll position, like the product page's section
      bubbles (product.js initSectionBubbles). */
(function () {
  'use strict';
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-ai-tab]'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('[data-ai-panel]'));
  if (!tabs.length) return;
  var cur = 0, timer = null, picked = false;

  function show(i) {
    cur = (i + tabs.length) % tabs.length;
    tabs.forEach(function (t, j) {
      t.classList.toggle('is-active', j === cur);
      t.setAttribute('aria-selected', j === cur ? 'true' : 'false');
      t.tabIndex = j === cur ? 0 : -1;
    });
    panels.forEach(function (p, j) { p.classList.toggle('is-active', j === cur); });
  }
  function stop() { picked = true; clearInterval(timer); timer = null; }

  tabs.forEach(function (t, j) {
    t.addEventListener('click', function () { stop(); show(j); });
    t.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault(); stop();
      show(cur + (e.key === 'ArrowRight' ? 1 : -1));
      tabs[cur].focus();
    });
  });
  show(0);

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;

  var io = new IntersectionObserver(function (entries) {
    var vis = entries.some(function (e) { return e.isIntersecting; });
    if (vis && !timer && !picked) timer = setInterval(function () { show(cur + 1); }, 4500);
    else if (!vis && timer) { clearInterval(timer); timer = null; }
  }, { threshold: 0.4 });
  io.observe(document.querySelector('[data-ai-demo]'));
})();

(function () {
  'use strict';
  var b = document.querySelector('.kz-ai-eyebrow');
  if (!b || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var raf = 0;
  function ease(t) { return 1 - Math.pow(1 - t, 3); }
  function place() {
    raf = 0;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    // Resting position, ignoring the current transform.
    var top = b.getBoundingClientRect().top - (parseFloat(b.dataset.dy) || 0);
    // 0 with the bubble at the bottom of the screen, 1 by 62% of the way up.
    var t = Math.max(0, Math.min(1, (vh - top) / (vh * 0.38)));
    var e = ease(t);
    var dx = (1 - e) * -70, dy = (1 - e) * -120, rot = (1 - e) * -9;
    b.dataset.dy = dy;
    b.style.transform = 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg) scale(' + (0.6 + 0.4 * e).toFixed(3) + ')';
    b.style.opacity = Math.min(1, t * 1.6).toFixed(2);
  }
  function req() { if (!raf) raf = requestAnimationFrame(place); }
  window.addEventListener('scroll', req, { passive: true });
  window.addEventListener('resize', req);
  place();
})();
