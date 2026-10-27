/* Hall of Fame winner pages: the interview's chat bubbles pop in as they
   scroll into view (CSS does the motion; this only toggles classes). Without
   JS, or with reduced motion, the bubbles are simply shown. */
(function () {
  'use strict';
  var items = document.querySelectorAll('[data-hof-reveal]');
  if (!items.length || !('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('js-hof-reveal');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.2, rootMargin: '0px 0px -8% 0px' });
  Array.prototype.forEach.call(items, function (el) { io.observe(el); });
})();
