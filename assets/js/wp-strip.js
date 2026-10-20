/* White-paper lead strip + blog pop-up: mounts the native HubSpot form
   ("White Paper", portal 144688314) into every [data-wp-hs]. Using the real
   embed (not a custom <form> + API call) keeps submissions on that form in
   HubSpot instead of also being logged as an auto-collected "non-HubSpot form". */
(function () {
  'use strict';
  var mounts = document.querySelectorAll('[data-wp-hs]');
  if (!mounts.length) return;
  var DAYS = 14;

  function mount(el) {
    if (el.getAttribute('data-wp-ready')) return;
    el.setAttribute('data-wp-ready', '1');
    window.hbspt.forms.create({
      portalId: '144688314',
      formId: 'bae37d8b-ce80-453b-8a02-6a378decb06e',
      region: 'eu1',
      target: '#' + el.id,
      css: '',
      redirectUrl: 'https://kaizan.ai/white-paper-confirmation',
      onFormSubmit: function () {
        if (window.dataLayer) window.dataLayer.push({ event: 'white_paper_download', form_id: 'wp-strip' });
        try { localStorage.setItem('kz-wp-popup', String(Date.now() + DAYS * 864e5)); } catch (e) {}
      }
    });
  }

  function mountAll() { mounts.forEach(mount); }

  mounts.forEach(function (el, i) { if (!el.id) el.id = 'wp-hs-' + i; });

  if (window.hbspt && window.hbspt.forms) { mountAll(); return; }
  var s = document.createElement('script');
  s.charset = 'utf-8';
  s.src = 'https://js-eu1.hsforms.net/forms/embed/v2.js';
  s.onload = mountAll;
  document.head.appendChild(s);
})();

/* Blog pop-up: opens 5s after load. Dismissing hides it for 14 days; a
   successful submit (see the form handler above) also suppresses it. */
(function () {
  'use strict';
  var pop = document.getElementById('wp-popup');
  if (!pop) return;
  var KEY = 'kz-wp-popup', DAYS = 14;
  function suppressed() {
    try { var t = parseInt(localStorage.getItem(KEY), 10); return t && Date.now() < t; } catch (e) { return false; }
  }
  function suppress() {
    try { localStorage.setItem(KEY, String(Date.now() + DAYS * 864e5)); } catch (e) {}
  }
  if (suppressed()) return;

  function close() { pop.hidden = true; document.removeEventListener('keydown', onKey); suppress(); }
  function onKey(e) { if (e.key === 'Escape') close(); }

  setTimeout(function () {
    if (suppressed()) return;
    pop.hidden = false;
    document.addEventListener('keydown', onKey);
  }, 5000);

  pop.querySelector('.wp-popup__close').addEventListener('click', close);
})();
