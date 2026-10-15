/* ── Become a partner (/referral-partners/) only ──────────────────────
   Injected into the static export by tools/build.py alongside partner.css.
   "Heard this from your clients?": each "What Kaizan does about it" card
   (data-dc-tpl 64/73/82) slides in from its arrow as its row scrolls into
   view. Cards are only hidden once this script runs (html.js-reveal), so
   they always show without JS; reduced-motion visitors skip the effect. */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var rows = ['64', '73', '82']
    .map(function (id) { var c = document.querySelector('[data-dc-tpl="' + id + '"]'); return c && c.closest('.pair-row'); })
    .filter(Boolean);
  if (!rows.length) return;
  rows.forEach(function (r) { r.classList.add('kz-reveal-pair'); });
  document.documentElement.classList.add('js-reveal');
  // Rows that come into view in the same batch (e.g. a tall screen) cascade
  // one after another instead of appearing at once.
  var io = new IntersectionObserver(function (entries) {
    var n = 0;
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.style.setProperty('--reveal-delay', (0.12 + n * 0.22) + 's');
      e.target.classList.add('is-in'); io.unobserve(e.target); n++;
    });
  }, { threshold: 0.45, rootMargin: '0px 0px -8% 0px' });
  rows.forEach(function (r) { io.observe(r); });
})();
