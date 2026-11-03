(function () {
'use strict';
var KEY = 'kz-consent';
var VERSION = 2;
var MAX_AGE_MS = 365 * 24 * 60 * 60 * 1000;
var overlay = document.getElementById('cb-overlay');
if (!overlay) return;
var dialog  = document.getElementById('cb-dialog');
var tabs    = [].slice.call(overlay.querySelectorAll('.cb-tab'));
var panels  = [].slice.call(overlay.querySelectorAll('[data-panel]'));
var foots   = [].slice.call(overlay.querySelectorAll('[data-foot]'));
var switches = [].slice.call(overlay.querySelectorAll('input[data-cat]'));
function read() {
try {
var c = JSON.parse(localStorage.getItem(KEY));
if (!c || c.v !== VERSION) return null;
if (Date.now() - c.t > MAX_AGE_MS) return null;
return c;
} catch (e) { return null; }
}
function write(v) {
try { localStorage.setItem(KEY, JSON.stringify({ v: VERSION, t: Date.now(), necessary: true,
preferences: v.preferences, statistics: v.statistics, marketing: v.marketing })); } catch (e) {}
}
var statsGranted = false, mktGranted = false;
function syncConsentMode(v) {
if (!window.gtag) return;
window.gtag('consent', 'update', {
'analytics_storage': v.statistics ? 'granted' : 'denied',
'ad_storage': v.marketing ? 'granted' : 'denied',
'ad_user_data': v.marketing ? 'granted' : 'denied',
'ad_personalization': v.marketing ? 'granted' : 'denied',
'functionality_storage': v.preferences ? 'granted' : 'denied',
'personalization_storage': v.preferences ? 'granted' : 'denied'
});
if (v.statistics) statsGranted = true;
}
function loadHubSpot() {
if (mktGranted) return;
mktGranted = true;
var h = document.createElement('script');
h.async = true;
h.defer = true;
h.id = 'hs-script-loader';
h.src = 'https://js-eu1.hs-scripts.com/144688314.js';
document.head.appendChild(h);
}
function loadMetaPixel() {
if (window.fbq) return;
var f = window, b = document, e = 'script', v = 'https://connect.facebook.net/en_US/fbevents.js', n, t, s;
n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
if (!f._fbq) f._fbq = n;
n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
t = b.createElement(e); t.async = true; t.src = v;
s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
f.fbq('init', '1749079612993241');
f.fbq('track', 'PageView');
}
var GA_COOKIES = /^(_ga|_gid|_gat)/;
var HS_COOKIES = /^(__hstc|hubspotutk|__hssc|__hssrc|__hs|_fbp|_fbc)/;
function clearCookies(pattern) {
var host = location.hostname;
var domains = ['', host, '.' + host];
var parent = host.split('.').slice(1).join('.');
if (parent.indexOf('.') > -1) domains.push('.' + parent);
document.cookie.split(';').forEach(function (c) {
var name = c.split('=')[0].trim();
if (!pattern.test(name)) return;
domains.forEach(function (d) {
document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' +
(d ? '; domain=' + d : '');
});
});
}
function showTab(name) {
tabs.forEach(function (t) {
var on = t.dataset.tab === name;
t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1;
});
panels.forEach(function (p) { p.hidden = p.dataset.panel !== name; });
foots.forEach(function (f) { f.hidden = f.dataset.foot !== (name === 'consent' ? 'consent' : 'details'); });
overlay.querySelector('.cb-body').scrollTop = 0;
}
function open(tab, focus) {
var saved = read() || {};
switches.forEach(function (s) { s.checked = !!saved[s.dataset.cat]; });
showTab(tab || 'consent');
overlay.hidden = false;
overlay.classList.remove('cb-in'); void overlay.offsetWidth; overlay.classList.add('cb-in');
if (focus) dialog.focus({ preventScroll: true });
}
function close() {
overlay.hidden = true;
}
function announce(v) {
syncConsentMode(v);
if (v.marketing) { loadHubSpot(); loadMetaPixel(); }
window.dispatchEvent(new CustomEvent('cookie-consent', { detail: v }));
}
function save(prefs) {
var v = { necessary: true, preferences: !!prefs.preferences, statistics: !!prefs.statistics, marketing: !!prefs.marketing };
write(v);
close();
var needsReload = false;
if (!v.statistics && statsGranted) { clearCookies(GA_COOKIES); needsReload = true; }
if (!v.marketing && mktGranted) { clearCookies(HS_COOKIES); needsReload = true; }
if (needsReload) { location.reload(); return; }
announce(v);
}
overlay.addEventListener('click', function (e) {
var b = e.target.closest('[data-act]'); if (b) {
var a = b.dataset.act;
if (a === 'accept')    save({ preferences: true, statistics: true, marketing: true });
if (a === 'reject')    save({});
if (a === 'manage')    showTab('details');
if (a === 'selection') { var p = {}; switches.forEach(function (s) { p[s.dataset.cat] = s.checked; }); save(p); }
return;
}
var t = e.target.closest('.cb-tab'); if (t) { showTab(t.dataset.tab); return; }
var c = e.target.closest('.cb-cat-toggle'); if (c) {
var expanded = c.getAttribute('aria-expanded') === 'true';
c.setAttribute('aria-expanded', !expanded);
document.getElementById(c.getAttribute('aria-controls')).hidden = expanded;
}
});
overlay.addEventListener('keydown', function (e) {
if (e.target.classList.contains('cb-tab') && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
var i = tabs.indexOf(e.target), n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
showTab(n.dataset.tab); n.focus();
}
});
document.addEventListener('click', function (e) {
var t = e.target.closest && e.target.closest('[data-cookie-settings]');
if (!t) return;
e.preventDefault();
open('consent', true);
});
window.CookieBanner = { open: function (tab) { open(tab, true); }, get: read, reset: function () {
try { localStorage.removeItem(KEY); } catch (e) {}
open('consent', true);
} };
var existing = read();
if (!existing) open('consent'); else announce(existing);
})();
