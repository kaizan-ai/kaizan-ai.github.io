(function () {
'use strict';
function initMobileNav() {
document.querySelectorAll('.kz-nav').forEach(function (nav) {
var toggle = nav.querySelector('.kz-nav-toggle');
if (!toggle) return;
toggle.addEventListener('click', function () {
var open = nav.classList.toggle('is-mobile-open');
nav.querySelectorAll('.kz-mega-trigger').forEach(function (t) {
t.setAttribute('aria-expanded', open ? 'true' : 'false');
});
});
nav.querySelectorAll('.kz-nav-links a').forEach(function (a) {
a.addEventListener('click', function () { nav.classList.remove('is-mobile-open'); });
});
});
}
function initMegaMenu() {
function canHover() { return window.matchMedia('(hover: hover)').matches; }
var touchRoots = [];
document.querySelectorAll('[data-mega-menu]').forEach(function (root) {
var trigger = root.querySelector('.kz-mega-trigger');
var panel = root.querySelector('.kz-mega-panel');
if (!trigger || !panel) return;
var closeT = null;
function open()  { if (closeT) clearTimeout(closeT); trigger.setAttribute('aria-expanded', 'true'); }
function close() { closeT = setTimeout(function () { trigger.setAttribute('aria-expanded', 'false'); }, 120); }
root.addEventListener('mouseenter', open);
root.addEventListener('mouseleave', close);
panel.addEventListener('mouseenter', open);
panel.addEventListener('mouseleave', close);
trigger.addEventListener('focus', open);
trigger.addEventListener('blur', close);
var tapOpened = false;
root.addEventListener('click', function (e) {
if (!trigger.contains(e.target)) return;
if (canHover()) return;
if (!e.detail) return;
if (trigger.closest('.kz-nav.is-mobile-open')) return;
if (tapOpened) return;
e.preventDefault();
tapOpened = true;
open();
}, true);
touchRoots.push({ root: root, trigger: trigger, reset: function () {
tapOpened = false;
trigger.setAttribute('aria-expanded', 'false');
} });
});
document.addEventListener('click', function (e) {
if (canHover()) return;
if (e.target.closest && e.target.closest('.kz-nav-toggle')) return;
if (document.querySelector('.kz-nav.is-mobile-open')) return;
touchRoots.forEach(function (d) {
if (!d.root.contains(e.target)) d.reset();
});
});
}
function initTour() {
var root = document.querySelector('[data-tour]');
if (!root) return;
var tabs = root.querySelectorAll('[data-tour-tab]');
var frames = root.querySelectorAll('[data-scene]');
var badge = root.querySelector('[data-tour-badge]');
var labels = ['SCENE 01', 'SCENE 02', 'SCENE 03', 'SCENE 04'];
tabs.forEach(function (tab, i) {
tab.addEventListener('click', function () {
tabs.forEach(function (t) { t.classList.remove('is-active'); });
frames.forEach(function (f) { f.classList.remove('is-active'); });
tab.classList.add('is-active');
if (frames[i]) frames[i].classList.add('is-active');
if (badge) badge.textContent = labels[i] + ' · ACME CREATIVE';
});
});
}
function initHelpers() {
var root = document.querySelector('[data-helpers]');
if (!root) return;
var tabs = root.querySelectorAll('[data-helper-tab]');
var panels = root.querySelectorAll('[data-helper-panel]');
tabs.forEach(function (tab, i) {
tab.addEventListener('click', function () {
tabs.forEach(function (t) { t.classList.remove('is-active'); });
panels.forEach(function (p) { p.style.display = 'none'; });
tab.classList.add('is-active');
if (panels[i]) panels[i].style.display = '';
});
});
panels.forEach(function (p, i) { p.style.display = i === 0 ? '' : 'none'; });
}
function initSecurityTabs() {
document.querySelectorAll('[data-sec-group]').forEach(function (group) {
var tabs = group.querySelectorAll('[data-sec-tab]');
var visuals = group.querySelectorAll('.kz-sec-visual');
tabs.forEach(function (tab) {
tab.addEventListener('click', function () {
var target = tab.getAttribute('data-sec-target');
tabs.forEach(function (t) { t.classList.remove('is-active'); });
tab.classList.add('is-active');
visuals.forEach(function (v) {
v.classList.toggle('is-active', v.id === target);
});
});
});
});
}
function initHeroVideo() {
var video = document.querySelector('[data-hero-video]');
var overlay = document.querySelector('[data-hero-overlay]');
if (!video || !overlay) return;
function activate(e) {
if (e) e.preventDefault();
overlay.classList.add('is-hidden');
video.controls = true;
video.muted = false;
video.volume = 1;
try { video.currentTime = 0; } catch (_) {}
var p = video.play();
if (p && typeof p.then === 'function') {
p.catch(function () {
overlay.classList.remove('is-hidden');
video.controls = false;
});
}
}
overlay.addEventListener('click', activate);
overlay.addEventListener('keydown', function (e) {
if (e.key === 'Enter' || e.key === ' ') activate(e);
});
}
function initVideoLightbox() {
var triggers = document.querySelectorAll('[data-video-btn]');
if (!triggers.length) return;
var lb = document.createElement('div');
lb.className = 'kz-video-lightbox';
lb.innerHTML =
'<div class="kz-video-lightbox__frame">' +
'<button class="kz-video-lightbox__close" type="button" aria-label="Close video">×</button>' +
'<video controls playsinline></video>' +
'</div>';
document.body.appendChild(lb);
var video = lb.querySelector('video');
var closeBtn = lb.querySelector('.kz-video-lightbox__close');
function open(src) {
video.src = src;
lb.classList.add('is-open');
document.body.style.overflow = 'hidden';
var p = video.play();
if (p && typeof p.then === 'function') p.catch(function () {});
}
function close() {
lb.classList.remove('is-open');
video.pause();
video.removeAttribute('src');
video.load();
document.body.style.overflow = '';
}
triggers.forEach(function (b) {
b.addEventListener('click', function () {
var src = b.getAttribute('data-video-src');
if (src) open(src);
});
});
closeBtn.addEventListener('click', close);
lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
document.addEventListener('keydown', function (e) {
if (e.key === 'Escape' && lb.classList.contains('is-open')) close();
});
}
function initQuoteCarousel() {
document.querySelectorAll('[data-carousel]').forEach(function (root) {
var vp = root.querySelector('[data-carousel-viewport]');
if (!vp) return;
var cards = Array.prototype.slice.call(vp.children);
if (!cards.length) return;
var prev = root.querySelector('[data-carousel-prev]');
var next = root.querySelector('[data-carousel-next]');
var dotsWrap = root.parentElement.querySelector('[data-carousel-dots]');
var dots = dotsWrap ? Array.prototype.slice.call(dotsWrap.children) : [];
function step() {
var gap = parseFloat(getComputedStyle(vp).gap) || 20;
return cards[0].getBoundingClientRect().width + gap;
}
function index() { return Math.round(vp.scrollLeft / step()); }
function atEnd() { return vp.scrollLeft >= vp.scrollWidth - vp.clientWidth - 2; }
function goTo(i) {
i = Math.max(0, Math.min(cards.length - 1, i));
vp.scrollTo({ left: i * step(), behavior: 'smooth' });
}
function refresh() {
var i = index();
dots.forEach(function (d, di) { d.classList.toggle('is-active', di === i); });
if (prev) prev.disabled = vp.scrollLeft <= 2;
if (next) next.disabled = atEnd();
}
if (prev) prev.addEventListener('click', function () { goTo(index() - 1); });
if (next) next.addEventListener('click', function () { goTo(index() + 1); });
dots.forEach(function (d, di) { d.addEventListener('click', function () { goTo(di); }); });
var t;
vp.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(refresh, 90); });
window.addEventListener('resize', refresh);
var timer = null;
var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function play() { if (reduce) return; stop(); timer = setInterval(function () { atEnd() ? goTo(0) : goTo(index() + 1); }, 5500); }
function stop() { if (timer) { clearInterval(timer); timer = null; } }
['pointerenter', 'pointerdown', 'focusin'].forEach(function (e) { root.addEventListener(e, stop); });
['pointerleave', 'focusout'].forEach(function (e) { root.addEventListener(e, play); });
refresh();
play();
});
}
function initLocale() {
var onUS = location.pathname === '/us' || location.pathname.indexOf('/us/') === 0;
function ukPath() { return location.pathname.replace(/^\/us(\/|$)/, '/'); }
function usPath() { return '/us' + location.pathname; }
var sw = document.querySelector('[data-locale-switch]');
if (sw) {
sw.textContent = onUS ? 'View UK site' : 'View US site';
sw.href = onUS ? ukPath() : usPath();
sw.hidden = false;
sw.addEventListener('click', function () {
try { localStorage.setItem('kz-locale', onUS ? 'uk' : 'us'); } catch (e) {}
});
}
var chosen = null;
try { chosen = localStorage.getItem('kz-locale'); } catch (e) {}
if (onUS || chosen || document.querySelector('meta[name="kz-no-us-page"]')) return;
var tz = '';
try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
var isUS = /^America\/(New_York|Detroit|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Adak|Boise|Juneau|Sitka|Menominee|Indiana|Kentucky|North_Dakota)/.test(tz)
|| tz === 'Pacific/Honolulu';
if (!isUS) return;
var bar = document.createElement('div');
bar.className = 'kz-locale-banner';
bar.innerHTML =
'<span>Looks like you’re in the US. See the US site?</span>' +
'<a class="kz-btn kz-btn-yellow" href="' + usPath() + '" data-go-us>View US site</a>' +
'<button type="button" class="kz-locale-banner__x" aria-label="Dismiss">×</button>';
document.body.appendChild(bar);
function remember(v) { try { localStorage.setItem('kz-locale', v); } catch (e) {} }
bar.querySelector('[data-go-us]').addEventListener('click', function () { remember('us'); });
bar.querySelector('.kz-locale-banner__x').addEventListener('click', function () {
remember('uk'); bar.remove();
});
}
function initReel() {
var vids = document.querySelectorAll('[data-play-inview]');
if (!vids.length) return;
if (!('IntersectionObserver' in window)) {
vids.forEach(function (v) { v.play().catch(function () {}); });
return;
}
vids.forEach(function (v) {
v.muted = true; v.playsInline = true;
var start = parseFloat(v.getAttribute('data-start')) || 0;
if (start) {
var seek = function () { if (v.currentTime < start) { try { v.currentTime = start; } catch (err) {} } };
if (v.readyState >= 1) seek(); else v.addEventListener('loadedmetadata', seek, { once: true });
}
});
var io = new IntersectionObserver(function (entries) {
entries.forEach(function (e) {
var v = e.target;
if (e.isIntersecting) {
if (!v.hasAttribute('data-play-resume')) {
try { v.currentTime = parseFloat(v.getAttribute('data-start')) || 0; } catch (err) {}
}
v.muted = true;
v.play().then(function () {
if (v.parentElement) v.parentElement.classList.remove('is-blocked');
}).catch(function (err) {
if (!err || err.name !== 'NotAllowedError') return;
var box = v.parentElement;
if (!box || box.classList.contains('is-blocked')) return;
box.classList.add('is-blocked');
v.addEventListener('playing', function () { box.classList.remove('is-blocked'); });
v.addEventListener('click', function () { if (v.paused) v.play().catch(function () {}); });
});
} else {
v.pause();
}
});
}, { threshold: 0.35 });
vids.forEach(function (v) { io.observe(v); });
}
function initPbConnectors() {
var root = document.getElementById('sceneRoot');
if (!root) return;
if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
function applyRealPath(originId, destId, selector) {
try {
var origin = document.getElementById(originId);
var dest = document.getElementById(destId);
var travelers = document.querySelectorAll(selector);
if (!origin || !dest || !travelers.length) return;
var rRect = root.getBoundingClientRect();
var oRect = origin.getBoundingClientRect();
var dRect = dest.getBoundingClientRect();
var ox = oRect.left - rRect.left + oRect.width / 2;
var oy = oRect.top - rRect.top + oRect.height / 2;
var dx = dRect.left - rRect.left + dRect.width / 2;
var dy = dRect.top - rRect.top + dRect.height / 2;
var c1x = ox + (dx - ox) * 0.25, c1y = oy + (dy - oy) * 0.32;
var c2x = ox + (dx - ox) * 0.6,  c2y = oy + (dy - oy) * 0.78;
var d = 'M' + ox + ',' + oy + ' C' + c1x + ',' + c1y + ' ' + c2x + ',' + c2y + ' ' + dx + ',' + dy;
travelers.forEach(function (el) { el.style.offsetPath = "path('" + d + "')"; el.style.offsetRotate = '0deg'; });
} catch (e) {  }
}
function applyAllPaths() {
applyRealPath('bubbleOriginA', 'bubbleDestA', '.connA');
applyRealPath('bubbleOriginB', 'bubbleDestB', '.connB');
applyRealPath('bubbleOrigin', 'bubbleDest', '.connC');
}
function trackProgress(trackId) {
var el = document.getElementById(trackId);
if (!el) return 0;
var rect = el.getBoundingClientRect();
var vh = window.innerHeight || document.documentElement.clientHeight;
var total = rect.height + vh;
if (total <= 0) return 0;
return Math.min(1, Math.max(0, (vh - rect.top) / total));
}
var legs = [
{ track: 'launchZoneA', selector: '.connA' },
{ track: 'launchZoneB', selector: '.connB' },
{ track: 'launchZone',  selector: '.connC' }
];
var state = {};
function tick() {
legs.forEach(function (leg) {
var master = trackProgress(leg.track);
var travelers = document.querySelectorAll(leg.selector);
travelers.forEach(function (el, i) {
var stagger = i * 0.07;
var target = Math.min(1, Math.max(0, master - stagger));
var key = leg.selector + i;
var cur = state[key] === undefined ? target : state[key];
var next = cur + (target - cur) * 0.18;
state[key] = next;
var fadeIn = Math.min(1, next / 0.08);
var fadeOut = Math.min(1, (1 - next) / 0.05);
var opacity = Math.max(0, Math.min(fadeIn, fadeOut));
var scale = 0.5 + 0.9 * Math.sin(Math.PI * Math.min(1, Math.max(0, next)));
var rotate = -4 + 6 * next;
el.style.offsetDistance = (next * 100) + '%';
el.style.opacity = String(opacity);
el.style.transform = 'scale(' + scale.toFixed(3) + ') rotate(' + rotate.toFixed(1) + 'deg)';
});
});
requestAnimationFrame(tick);
}
function remeasure() { requestAnimationFrame(function () { requestAnimationFrame(applyAllPaths); }); }
remeasure();
window.addEventListener('load', remeasure);
if (document.fonts && document.fonts.ready) { document.fonts.ready.then(remeasure).catch(function () {}); }
var rt = null;
window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(applyAllPaths, 150); });
requestAnimationFrame(tick);
}
function initSwipeRows() {
document.querySelectorAll('[data-swipe-row]').forEach(function (row) {
var items = [].slice.call(row.children).filter(function (el) {
return el.getAttribute('aria-hidden') !== 'true' && getComputedStyle(el).position !== 'absolute';
});
if (items.length < 2) return;
var bar = document.createElement('div');
bar.className = 'kz-swipe-ctrl';
bar.innerHTML =
'<button type="button" class="kz-swipe-btn" data-dir="-1" aria-label="Previous">&lsaquo;</button>' +
'<span class="kz-swipe-dots">' + items.map(function (_, i) {
return '<button type="button" class="kz-swipe-dot" aria-label="Go to ' + (i + 1) + '"></button>';
}).join('') + '</span>' +
'<button type="button" class="kz-swipe-btn" data-dir="1" aria-label="Next">&rsaquo;</button>';
row.parentNode.insertBefore(bar, row.nextSibling);
var dots = [].slice.call(bar.querySelectorAll('.kz-swipe-dot'));
var prev = bar.querySelector('[data-dir="-1"]'), next = bar.querySelector('[data-dir="1"]');
function current() {
var x = row.scrollLeft, best = 0, bestD = Infinity;
items.forEach(function (el, i) {
var d = Math.abs(el.offsetLeft - items[0].offsetLeft - x);
if (d < bestD) { bestD = d; best = i; }
});
return best;
}
function go(i) {
i = Math.max(0, Math.min(items.length - 1, i));
row.scrollTo({ left: items[i].offsetLeft - items[0].offsetLeft, behavior: 'smooth' });
}
function sync() {
var c = current();
dots.forEach(function (d, i) { d.classList.toggle('is-on', i === c); });
prev.disabled = row.scrollLeft <= 2;
next.disabled = row.scrollLeft >= row.scrollWidth - row.clientWidth - 2;
bar.hidden = row.scrollWidth <= row.clientWidth + 4;
}
prev.addEventListener('click', function () { go(current() - 1); });
next.addEventListener('click', function () { go(current() + 1); });
dots.forEach(function (d, i) { d.addEventListener('click', function () { go(i); }); });
var raf = 0;
row.addEventListener('scroll', function () {
if (raf) return;
raf = requestAnimationFrame(function () { raf = 0; sync(); });
}, { passive: true });
window.addEventListener('resize', sync);
document.addEventListener('click', function () { setTimeout(sync, 50); });
sync();
});
}
function initPbThread() {
var root = document.getElementById('sceneRoot');
if (!root || !window.matchMedia) return;
var phone = window.matchMedia('(max-width: 560px)');
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
var secs = [].slice.call(root.children).filter(function (el) { return el.tagName === 'SECTION'; });
if (!secs.length) return;
var bub = document.createElement('div');
bub.className = 'kz-pb-thread-bubble';
bub.setAttribute('aria-hidden', 'true');
root.appendChild(bub);
var raf = 0;
function place() {
raf = 0;
if (!phone.matches) return;
var r = root.getBoundingClientRect();
var first = secs[0].querySelector('h2'), last = secs[secs.length - 1];
var top = first ? first.getBoundingClientRect().top - r.top : 0;
var lr = last.getBoundingClientRect();
var bottom = (lr.top + lr.height / 2) - r.top;
var y = window.innerHeight * 0.45 - r.top;
y = Math.max(top, Math.min(bottom, y));
bub.style.transform = 'translateY(' + Math.round(y) + 'px)';
for (var i = secs.length - 1; i >= 0; i--) {
if (secs[i].getBoundingClientRect().top - r.top <= y) {
bub.style.background = getComputedStyle(secs[i]).getPropertyValue('--pb-c') || '';
break;
}
}
}
function req() { if (!raf) raf = requestAnimationFrame(place); }
window.addEventListener('scroll', req, { passive: true });
window.addEventListener('resize', req);
place();
}
function initNewsletter() {
Array.prototype.forEach.call(document.querySelectorAll('[data-newsletter]'), function (form) {
var jsonUrl = form.getAttribute('data-mc-json');
var msg = form.querySelector('.kz-footer-news-msg');
var btn = form.querySelector('button[type=submit]');
var role = form.querySelector('[name=ROLE]');
var emailIn = form.querySelector('[name=EMAIL]');
function open() { form.classList.add('is-open'); }
emailIn.addEventListener('focus', open);
emailIn.addEventListener('input', open);
function show(text, ok) {
msg.textContent = text;
msg.classList.toggle('is-error', !ok);
msg.hidden = false;
}
form.addEventListener('submit', function (e) {
if (!jsonUrl) return;
e.preventDefault();
var email = form.querySelector('[name=EMAIL]');
if (!email.value || !email.checkValidity()) { show('Please enter a valid email address.', false); return; }
form.classList.add('is-open');
if (role && !role.value) { show('Please choose your job role.', false); role.focus(); return; }
msg.hidden = true;
btn.disabled = true;
var cb = 'kzNl_' + Date.now(), s = document.createElement('script');
window[cb] = function (data) {
btn.disabled = false;
if (data && data.result === 'success') {
form.querySelector('.kz-footer-news-row').hidden = true;
form.classList.remove('is-open'); form.querySelector('[data-newsletter-role]').style.display = 'none';
show('Thanks, you\u2019re subscribed.', true);
} else if (data && /already subscribed/i.test(data.msg || '')) {
form.querySelector('.kz-footer-news-row').hidden = true;
form.classList.remove('is-open'); form.querySelector('[data-newsletter-role]').style.display = 'none';
show('You\u2019re already subscribed. Thanks!', true);
} else {
var m = (data && data.msg) ? String(data.msg).replace(/<[^>]*>/g, '').replace(/^\d+\s*-\s*/, '') : '';
show(m || 'Something went wrong. Please try again.', false);
}
delete window[cb];
if (s.parentNode) s.parentNode.removeChild(s);
};
s.src = jsonUrl + '&' + new URLSearchParams(new FormData(form)).toString() + '&c=' + cb;
s.onerror = function () { btn.disabled = false; show('Network error. Please try again.', false); };
document.body.appendChild(s);
});
});
}
function initNewsBubble() {
var b = document.querySelector('.kz-footer-news-icon');
if (!b || (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
var raf = 0;
function ease(t) { return 1 - Math.pow(1 - t, 3); }
function place() {
raf = 0;
var vh = window.innerHeight || document.documentElement.clientHeight;
var top = b.getBoundingClientRect().top - (parseFloat(b.dataset.dy) || 0);
var t = Math.max(0, Math.min(1, (vh - top) / (vh * 0.38)));
var atEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
if (atEnd && top < vh) t = 1;
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
}
function boot() {
initMobileNav();
initMegaMenu();
initTour();
initQuoteCarousel();
initLocale();
initHelpers();
initHeroVideo();
initReel();
initPbConnectors();
initSecurityTabs();
initVideoLightbox();
initSwipeRows();
initPbThread();
initNewsletter();
initNewsBubble();
}
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', boot);
} else {
boot();
}
})();
