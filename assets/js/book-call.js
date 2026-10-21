// "Book a call" popup → Mailchimp.
//
//  - Any link marked [data-book-call] (every booking CTA; added at build time
//    in build_us_locale() / book_call_inject()) opens the popup instead of
//    navigating. Without JS the link falls back to the /demo/ interstitial.
//  - Fills the hidden UTM merge fields from the page URL (or the tab's saved
//    set), submits via Mailchimp's JSONP endpoint, then redirects to the
//    confirmation page named in the form's data-confirm.
(function () {
  var modal = document.querySelector('[data-book-call-modal]');
  if (!modal) return;
  var form = modal.querySelector('form');
  var msg = modal.querySelector('[data-bc-msg]');
  var submit = form.querySelector('[type=submit]');
  var jsonUrl = form.getAttribute('data-mc-json');
  var confirmUrl = form.getAttribute('data-confirm');
  var STORE = 'kz-utm';
  var lastFocus = null;

  // ── UTM attribution (same store/keys as trial-form.js) ────────────
  var saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(STORE) || '{}') || {}; } catch (e) {}
  var params = new URLSearchParams(window.location.search);
  var utmEls = form.querySelectorAll('input[data-utm]');
  var fromUrl = Array.prototype.some.call(utmEls, function (el) { return params.has(el.getAttribute('data-utm')); });
  utmEls.forEach(function (el) {
    var key = el.getAttribute('data-utm');
    el.value = (fromUrl ? (params.get(key) || '') : (saved[key] || '')).slice(0, 255);
    saved[key] = el.value;
  });
  if (fromUrl) { try { sessionStorage.setItem(STORE, JSON.stringify(saved)); } catch (e) {} }

  // ── Open / close ──────────────────────────────────────────────────
  function open() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add('kz-bc-open');
    var first = form.querySelector('input:not([type=hidden])');
    if (first) first.focus();
  }
  function close() {
    modal.hidden = true;
    document.body.classList.remove('kz-bc-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-book-call], a[href$="/demo/"]');
    if (a) { e.preventDefault(); open(); return; }
    if (e.target.closest && e.target.closest('[data-bc-close]')) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) close();
  });

  // ── Submit ────────────────────────────────────────────────────────
  function show(text) { msg.textContent = text; msg.classList.toggle('is-shown', !!text); }
  function clean(m) {
    var d = document.createElement('div');
    d.innerHTML = String(m || '').replace(/^\d+\s*-\s*/, '');
    return (d.textContent || '').trim();
  }
  form.addEventListener('submit', function (e) {
    if (!jsonUrl) return;
    e.preventDefault();
    if (!form.reportValidity()) return;
    show('');
    submit.disabled = true;
    var body = new URLSearchParams(new FormData(form)).toString();
    var cb = 'kzBookCall_' + Date.now();
    var s = document.createElement('script');
    function finish() {
      submit.disabled = false;
      delete window[cb];
      if (s.parentNode) s.parentNode.removeChild(s);
    }
    window[cb] = function (data) {
      finish();
      if (data && data.result === 'success') {
        try { sessionStorage.removeItem(STORE); } catch (e) {}
        if (window.dataLayer) window.dataLayer.push({ event: 'book_call_signup' });
        window.location.href = confirmUrl;
      } else {
        show(clean(data && data.msg) || 'Something went wrong, please try again.');
      }
    };
    s.onerror = function () { finish(); show('Network error, please try again.'); };
    s.src = jsonUrl + '&' + body + '&c=' + cb;
    document.body.appendChild(s);
  });
})();
