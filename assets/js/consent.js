/* Kaizan — cookie consent dialog.
   Markup lives in tools/build.py (cookie_consent_html, emitted by page_foot
   on every page); styles are the .cb-* rules in assets/css/site.css. This
   file wires up the dialog's behavior and syncs consent to our trackers.

   GTM itself always loads (see gtm_head_snippet() in tools/build.py, which
   also sets Google Consent Mode v2 defaults to "denied"). This file calls
   gtag('consent', 'update', …) once a visitor chooses, mapped from our
   categories to Google's signals — Statistics → analytics_storage,
   Marketing → ad_storage/ad_user_data/ad_personalization, Preferences →
   functionality_storage/personalization_storage. Whether GTM's own
   third-party tags (HubSpot, LinkedIn, ads pixels) actually respect that is
   down to "Additional Consent Checks" configured per tag inside the GTM
   container itself — outside this repo.
   HubSpot's own direct tracking script (not routed through GTM) still loads
   only once "Marketing" is allowed, since that one we fully control here.
   Declining a category that was previously granted clears its cookies and
   reloads (a fired tag can't be un-fired any other way). Choice is stored
   for 12 months; bump VERSION to re-prompt everyone after a material
   cookie-policy change.
   The footer's "Cookie settings" link ([data-cookie-settings]) reopens the
   dialog so a choice can be changed at any time.
*/
(function () {
  'use strict';

  var KEY = 'kz-consent';
  var VERSION = 2;
  var MAX_AGE_MS = 365 * 24 * 60 * 60 * 1000; // 12 months

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

  // Once a category has been granted this page view, downgrading it clears
  // its cookies and reloads instead of trying to un-fire already-fired tags.
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

  // Cookies set by the trackers we gate (GA via GTM, HubSpot). Deleted
  // best-effort when a visitor withdraws consent for that category.
  var GA_COOKIES = /^(_ga|_gid|_gat)/;
  var HS_COOKIES = /^(__hstc|hubspotutk|__hssc|__hssrc|__hs)/;

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

  function open(tab) {
    var saved = read() || {};
    switches.forEach(function (s) { s.checked = !!saved[s.dataset.cat]; });   // all OFF by default
    showTab(tab || 'consent');
    overlay.hidden = false;
    overlay.classList.remove('cb-in'); void overlay.offsetWidth; overlay.classList.add('cb-in');
    document.documentElement.style.overflow = 'hidden';
    dialog.focus();
  }
  function close() {
    overlay.hidden = true;
    document.documentElement.style.overflow = '';
  }

  function announce(v) {
    syncConsentMode(v);
    if (v.marketing) loadHubSpot();
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

  // Arrow keys between tabs + keep focus inside the dialog
  overlay.addEventListener('keydown', function (e) {
    if (e.target.classList.contains('cb-tab') && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
      var i = tabs.indexOf(e.target), n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      showTab(n.dataset.tab); n.focus(); return;
    }
    if (e.key !== 'Tab') return;
    var f = [].slice.call(dialog.querySelectorAll('button,input,a[href]')).filter(function (el) {
      return !el.disabled && el.offsetParent !== null; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && (document.activeElement === first || document.activeElement === dialog)) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  // Footer "Cookie settings" link reopens the dialog.
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-cookie-settings]');
    if (!t) return;
    e.preventDefault();
    open('consent');
  });

  // Public API: CookieBanner.open() from a "Cookie settings" link, .get() for current choice
  window.CookieBanner = { open: open, get: read, reset: function () {
    try { localStorage.removeItem(KEY); } catch (e) {}
    open('consent');
  } };

  // Show straight away on first visit (or after 12 months / a version bump);
  // otherwise re-apply the saved choice on every page view.
  var existing = read();
  if (!existing) open('consent'); else announce(existing);
})();
