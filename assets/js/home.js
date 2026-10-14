/* ── Homepage-only behaviours ─────────────────────────────────────────
   Injected on the homepage only (render_customer_success_software with
   keep_nav).

   1. Stats band count-up: each stat number ("21%", "5.4 hrs", "11M+") counts
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
