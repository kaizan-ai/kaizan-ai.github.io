/* Blog posts: step and timeline sequences (.kz-flow, built by tools/blog.py).
   Each step fades in as it scrolls into view and the rail fills in gold as the
   reader moves down it. CSS does the motion; this only toggles classes and sets
   --kz-flow-fill. Without JS, or with reduced motion, everything is simply shown. */
(function () {
  'use strict';
  var flows = document.querySelectorAll('[data-flow]');
  if (!flows.length || !('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('js-kz-flow');

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -12% 0px' });
  Array.prototype.forEach.call(flows, function (f) {
    Array.prototype.forEach.call(f.querySelectorAll('.kz-flow-item'), function (it) { io.observe(it); });
  });

  // Rail fill: how far the reading line (60% down the viewport) has travelled through each flow.
  var ticking = false;
  function fill() {
    ticking = false;
    var line = window.innerHeight * 0.6;
    Array.prototype.forEach.call(flows, function (f) {
      var r = f.getBoundingClientRect();
      var p = r.height ? (line - r.top) / r.height : 0;
      f.style.setProperty('--kz-flow-fill', Math.max(0, Math.min(1, p)).toFixed(3));
    });
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(fill); }
  }, { passive: true });
  window.addEventListener('resize', fill);
  fill();
})();
