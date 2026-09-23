// Home hero "Start your 14-day free trial" form → Mailchimp.
//
//  - Reveals company / job title / source once first name, last name, email
//    and phone are filled in.
//  - Fills the hidden UTM merge fields (UTMSRC, UTMMED, …) from the page URL's
//    query string (?utm_source=…&qr_placement=…). Values are kept for the tab's
//    session so they survive a click to another page and back.
//  - Submits via Mailchimp's JSONP endpoint so the visitor stays on the page. If
//    JS is unavailable the form still POSTs normally to Mailchimp.
(function () {
  var root = document.querySelector('[data-trial]');
  if (!root) return;
  var form = root.querySelector('form');
  var more = root.querySelector('[data-trial-more]');
  var legal = root.querySelector('[data-trial-legal]');
  var msg = root.querySelector('[data-trial-msg]');
  var done = root.querySelector('[data-trial-done]');
  var submit = form.querySelector('[type=submit]');
  var jsonUrl = form.getAttribute('data-mc-json');
  var STORE = 'kz-utm';
  root.classList.add('is-js');

  // ── UTM attribution ──────────────────────────────────────────────
  var saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(STORE) || '{}') || {}; } catch (e) {}
  var params = new URLSearchParams(window.location.search);
  var fromUrl = false;
  form.querySelectorAll('input[data-utm]').forEach(function (el) {
    if (params.has(el.getAttribute('data-utm'))) fromUrl = true;
  });
  form.querySelectorAll('input[data-utm]').forEach(function (el) {
    var key = el.getAttribute('data-utm');
    // A URL carrying any UTM parameter replaces the whole saved set, so
    // parameters from an earlier campaign click don't mix with this one.
    var val = fromUrl ? (params.get(key) || '') : (saved[key] || '');
    el.value = val.slice(0, 255);
    saved[key] = el.value;
  });
  if (fromUrl) {
    try { sessionStorage.setItem(STORE, JSON.stringify(saved)); } catch (e) {}
  }

  // ── Progressive reveal ───────────────────────────────────────────
  var required = ['FNAME', 'LNAME', 'EMAIL', 'PHONE'].map(function (n) {
    return form.querySelector('[name=' + n + ']');
  });
  function setOpen(open) {
    more.classList.toggle('is-open', open);
    legal.classList.toggle('is-open', open);
    if (open) more.removeAttribute('inert'); else more.setAttribute('inert', '');
  }
  function check() {
    var open = required.every(function (el) { return el.value.trim() !== ''; });
    // Stay open once revealed, so clearing a field doesn't hide typed answers.
    if (open || !more.classList.contains('is-open')) setOpen(open);
  }
  required.forEach(function (el) { el.addEventListener('input', check); });
  check();

  // ── Submit ───────────────────────────────────────────────────────
  function show(text) {
    msg.textContent = text;
    msg.classList.toggle('is-shown', !!text);
  }
  function clean(m) {
    // Mailchimp messages look like "0 - Please enter a value" and may hold HTML.
    var d = document.createElement('div');
    d.innerHTML = String(m || '').replace(/^\d+\s*-\s*/, '');
    return (d.textContent || '').trim();
  }
  form.addEventListener('submit', function (e) {
    if (!jsonUrl) return;               // no endpoint -> normal POST
    e.preventDefault();
    if (!form.reportValidity()) { setOpen(true); return; }
    show('');
    submit.disabled = true;
    var body = new URLSearchParams(new FormData(form)).toString();
    var cb = 'kzTrial_' + Date.now();
    var s = document.createElement('script');
    function finish() {
      submit.disabled = false;
      delete window[cb];
      if (s.parentNode) s.parentNode.removeChild(s);
    }
    window[cb] = function (data) {
      finish();
      if (data && data.result === 'success') {
        form.hidden = true;
        done.hidden = false;
        try { sessionStorage.removeItem(STORE); } catch (e) {}
        if (window.dataLayer) window.dataLayer.push({ event: 'trial_signup' });
      } else {
        show(clean(data && data.msg) || 'Something went wrong, please try again.');
      }
    };
    s.onerror = function () { finish(); show('Network error, please try again.'); };
    s.src = jsonUrl + '&' + body + '&c=' + cb;
    document.body.appendChild(s);
  });
})();
