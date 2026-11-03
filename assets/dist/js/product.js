(function () {
'use strict';
function initBubbleReveal() {
var rows = document.querySelectorAll('[data-reveal-row]');
if (!rows.length) return;
if (!('IntersectionObserver' in window)) {
rows.forEach(function (r) { r.classList.add('in-view'); });
return;
}
var io = new IntersectionObserver(function (entries) {
entries.forEach(function (e) {
if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); }
});
}, { threshold: 0.3 });
rows.forEach(function (r) { io.observe(r); });
}
function initCareSpotlight() {
var cards = [].slice.call(document.querySelectorAll('.kz-care-card')).filter(function (c) {
return c.querySelector('video[data-hover-play]');
});
if (!cards.length) return;
var grid = cards[0].parentElement;
var vids = cards.map(function (c) {
var v = c.querySelector('video');
v.muted = true; v.playsInline = true; v.loop = false;
return v;
});
var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var vis = vids.map(function () { return 0; });
var active = -1;
function isRow() { return grid.scrollWidth > grid.clientWidth + 4; }
function seen(i) { return vis[i] >= 0.5; }
function play(v) {
v.muted = true;
var p = v.play();
if (p && p.catch) p.catch(function () {});
}
function rest(i) {
cards[i].classList.remove('is-playing');
vids[i].pause();
try { vids[i].load(); } catch (e) {}
}
function activate(i) {
if (active !== -1 && active !== i) rest(active);
active = i;
cards[i].classList.add('is-playing');
try { vids[i].currentTime = 0; } catch (e) {}
play(vids[i]);
}
function slideTo(i) {
if (!isRow()) return;
grid.scrollTo({ left: cards[i].offsetLeft - cards[0].offsetLeft, behavior: 'smooth' });
}
vids.forEach(function (v, i) {
v.addEventListener('ended', function () {
if (i !== active) return;
if (reduced || !seen(i)) { rest(i); active = -1; return; }
var next = (i + 1) % cards.length;
slideTo(next);
activate(next);
});
});
cards.forEach(function (c, i) {
c.addEventListener('mouseenter', function () { if (i !== active) activate(i); });
c.addEventListener('click', function () { if (i !== active) activate(i); });
});
if (reduced) return;
if (!('IntersectionObserver' in window)) { activate(0); return; }
var io = new IntersectionObserver(function (entries) {
entries.forEach(function (e) { vis[vids.indexOf(e.target)] = e.intersectionRatio; });
if (active !== -1 && seen(active)) {
if (vids[active].paused && !vids[active].ended) play(vids[active]);
return;
}
for (var i = 0; i < cards.length; i++) {
if (seen(i)) { activate(i); return; }
}
if (active !== -1) vids[active].pause();
}, { threshold: [0, 0.5, 1] });
vids.forEach(function (v) { io.observe(v); });
}
function initRoles() {
var root = document.querySelector('[data-roles]');
if (!root) return;
var tabs = root.querySelectorAll('[data-role-tab]');
var panels = root.querySelectorAll('[data-role-panel]');
function activate(i) {
tabs.forEach(function (t, j) { t.classList.toggle('is-active', j === i); });
panels.forEach(function (p, j) { p.classList.toggle('is-active', j === i); });
if (panels[i]) {
panels[i].querySelectorAll('video').forEach(function (v) {
try { v.currentTime = 0; } catch (err) {}
v.play().catch(function () {});
});
}
}
tabs.forEach(function (tab, i) {
tab.addEventListener('click', function () { activate(i); });
});
activate(0);
}
function initScrollPlayVideos() {
var vids = document.querySelectorAll('[data-play-on-scroll]');
if (!vids.length || !('IntersectionObserver' in window)) return;
var io = new IntersectionObserver(function (entries) {
entries.forEach(function (e) {
var v = e.target;
if (e.isIntersecting) {
try { v.currentTime = 0; } catch (err) {}
v.muted = true;
var p = v.play();
if (p && p.catch) p.catch(function () {});
} else {
v.pause();
}
});
}, { threshold: 0.5 });
function start() {
window.removeEventListener('scroll', start);
vids.forEach(function (v) { io.observe(v); });
}
window.addEventListener('scroll', start, { passive: true });
}
function initSectionBubbles() {
var badges = ['#ai-assistant', '#care', '#health-model', '#client-360'].map(function (id) {
return document.querySelector(id + ' .kz-eyebrow');
}).filter(Boolean);
if (!badges.length) return;
if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
var raf = 0;
function ease(t) { return 1 - Math.pow(1 - t, 3); }
function place() {
raf = 0;
var vh = window.innerHeight || document.documentElement.clientHeight;
badges.forEach(function (b, i) {
var top = b.getBoundingClientRect().top - (parseFloat(b.dataset.dy) || 0);
var t = Math.max(0, Math.min(1, (vh - top) / (vh * 0.38)));
var e = ease(t);
var dx = (1 - e) * -70, dy = (1 - e) * -120;
var rot = (1 - e) * (i % 2 ? 9 : -9);
b.dataset.dy = dy;
b.style.transform = 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg) scale(' + (0.6 + 0.4 * e).toFixed(3) + ')';
b.style.opacity = Math.min(1, t * 1.6).toFixed(2);
});
}
function req() { if (!raf) raf = requestAnimationFrame(place); }
window.addEventListener('scroll', req, { passive: true });
window.addEventListener('resize', req);
place();
}
function initCareTarget() {
var id = location.hash.slice(1);
if (!/^care-/.test(id)) return;
var card = document.getElementById(id);
if (card) card.classList.add('is-target');
}
function boot() {
initCareTarget();
initBubbleReveal();
initCareSpotlight();
initScrollPlayVideos();
initRoles();
initSectionBubbles();
}
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', boot);
} else {
boot();
}
})();
