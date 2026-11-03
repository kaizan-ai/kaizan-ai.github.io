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
