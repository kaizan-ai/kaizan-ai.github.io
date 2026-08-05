/* Kaizan — cookie consent gate.
   Analytics (Google Tag Manager) and HubSpot tracking are only loaded after
   the visitor accepts optional cookies. A declined or absent choice loads
   nothing. The choice is stored for 12 months; bump VERSION to re-prompt
   everyone after a material cookie-policy change.
   The footer's "Cookie settings" link ([data-cookie-settings]) reopens the
   banner so a choice can be changed at any time.
*/
(function () {
  'use strict';

  var KEY = 'kz-consent';
  var VERSION = 1;
  var MAX_AGE_MS = 365 * 24 * 60 * 60 * 1000; // 12 months

  function readChoice() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return null;
      var c = JSON.parse(raw);
      if (c.v !== VERSION) return null;
      if (Date.now() - c.t > MAX_AGE_MS) return null;
      return c.choice === 'accepted' || c.choice === 'declined' ? c.choice : null;
    } catch (e) { return null; }
  }

  function saveChoice(choice) {
    try {
      localStorage.setItem(KEY, JSON.stringify({ v: VERSION, t: Date.now(), choice: choice }));
    } catch (e) { /* private mode etc. — treated as no choice next visit */ }
  }

  function loadTrackers() {
    if (window.__kzTrackersLoaded) return;
    window.__kzTrackersLoaded = true;
    // Google Tag Manager
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    var g = document.createElement('script');
    g.async = true;
    g.src = 'https://www.googletagmanager.com/gtm.js?id=GTM-NCXT2FLQ';
    document.head.appendChild(g);
    // HubSpot tracking
    var h = document.createElement('script');
    h.async = true;
    h.defer = true;
    h.id = 'hs-script-loader';
    h.src = 'https://js-eu1.hs-scripts.com/144688314.js';
    document.head.appendChild(h);
  }

  // Cookies set by the trackers we gate (GA via GTM, HubSpot). Deleted
  // best-effort when a visitor withdraws consent.
  var TRACKING_COOKIES = /^(_ga|_gid|_gat|__hstc|hubspotutk|__hssc|__hssrc|__hs)/;

  function clearTrackingCookies() {
    var host = location.hostname;
    var domains = ['', host, '.' + host];
    var parent = host.split('.').slice(1).join('.');
    if (parent.indexOf('.') > -1) domains.push('.' + parent);
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (!TRACKING_COOKIES.test(name)) return;
      domains.forEach(function (d) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' +
          (d ? '; domain=' + d : '');
      });
    });
  }

  function banner() {
    var el = document.querySelector('.kz-consent');
    if (el) return el;
    el = document.createElement('div');
    el.className = 'kz-consent';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Cookie consent');
    el.innerHTML =
      '<div class="kz-consent-title">Cookies</div>' +
      '<p>We use optional cookies to understand how the site is used and to improve ' +
      'our marketing. We won’t set them unless you accept. See our ' +
      '<a href="/cookie-policy/">Cookie Policy</a>.</p>' +
      '<div class="kz-consent-btns">' +
      '<button type="button" class="kz-btn kz-btn-yellow" data-consent-accept>Accept</button>' +
      '<button type="button" class="kz-btn kz-btn-ghost" data-consent-decline>Decline</button>' +
      '</div>';
    el.querySelector('[data-consent-accept]').addEventListener('click', function () {
      saveChoice('accepted');
      loadTrackers();
      hide();
    });
    el.querySelector('[data-consent-decline]').addEventListener('click', function () {
      var hadTrackers = !!window.__kzTrackersLoaded;
      saveChoice('declined');
      hide();
      if (hadTrackers) {
        // Consent withdrawn after trackers already ran: delete their cookies
        // (best effort) and reload so the running scripts stop too.
        clearTrackingCookies();
        location.reload();
      }
    });
    document.body.appendChild(el);
    return el;
  }

  function show() { banner().classList.add('is-visible'); }
  function hide() {
    var el = document.querySelector('.kz-consent');
    if (el) el.classList.remove('is-visible');
  }

  function init() {
    var choice = readChoice();
    if (choice === 'accepted') loadTrackers();
    else if (choice === null) show();

    // Footer "Cookie settings" link reopens the banner.
    document.addEventListener('click', function (e) {
      var t = e.target.closest && e.target.closest('[data-cookie-settings]');
      if (!t) return;
      e.preventDefault();
      show();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
