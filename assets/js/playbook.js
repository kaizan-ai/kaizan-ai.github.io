/* The Client Health Playbook: gated form (/resources/client-health-playbook/).
   Validates a work email + job title, submits to Mailchimp (JSONP), then reveals the download. */
(function () {
  'use strict';

  var FREE = ['gmail.com','googlemail.com','yahoo.com','yahoo.co.uk','hotmail.com','hotmail.co.uk',
    'outlook.com','live.com','msn.com','aol.com','icloud.com','me.com','mac.com','proton.me',
    'protonmail.com','gmx.com','gmx.de','mail.com','yandex.com','zoho.com','fastmail.com',
    'tutanota.com','duck.com','hey.com'];

  var form = document.getElementById('pb-form-el');
  if (!form) return;
  var card = document.getElementById('form');
  var done = card.querySelector('.pb-done');
  var email = form.elements.EMAIL;
  var role = form.elements.JOBT;
  var btn = form.querySelector('button[type="submit"]');
  var fail = form.querySelector('.pb-fail');

  function setErr(input, msg) {
    var f = input.closest('.pb-field');
    f.classList.toggle('has-error', !!msg);
    f.querySelector('.pb-err').textContent = msg || '';
    return !!msg;
  }
  function emailMsg(v) {
    if (!v) return 'Please enter your work email.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'That doesn’t look like a valid email.';
    if (FREE.indexOf(v.split('@')[1].toLowerCase()) !== -1) return 'Please use your work email, not a personal address.';
    return '';
  }
  email.addEventListener('input', function () { setErr(email, ''); });
  role.addEventListener('change', function () { setErr(role, ''); });

  // Fill the hidden UTM merge fields from the URL (kept for the tab's session, as the trial form does).
  var STORE = 'kz-utm', saved = {};
  try { saved = JSON.parse(sessionStorage.getItem(STORE) || '{}') || {}; } catch (e) {}
  var params = new URLSearchParams(window.location.search);
  var inputs = form.querySelectorAll('input[data-utm]'), fromUrl = false, replaceSet = false;
  inputs.forEach(function (el) {
    var k = el.getAttribute('data-utm');
    if (params.has(k)) { fromUrl = true; if (k !== 'gclid') replaceSet = true; }
  });
  inputs.forEach(function (el) {
    var k = el.getAttribute('data-utm');
    el.value = (replaceSet ? (params.get(k) || '') : (params.has(k) ? params.get(k) : (saved[k] || ''))).slice(0, 255);
    saved[k] = el.value;
  });
  if (fromUrl) { try { sessionStorage.setItem(STORE, JSON.stringify(saved)); } catch (e) {} }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    fail.classList.remove('is-visible');
    var ev = email.value.trim(), rv = role.value;
    var bad1 = setErr(email, emailMsg(ev));
    var bad2 = setErr(role, rv ? '' : 'Please select your job title.');
    if (bad1 || bad2) { (bad1 ? email : role).focus(); return; }
    if (btn.disabled) return;
    var label = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = 'Submitting…';

    var jsonUrl = form.getAttribute('data-mc-json');
    var cb = 'kzPlaybook_' + Date.now();
    var s = document.createElement('script');
    function finish() {
      delete window[cb];
      if (s.parentNode) s.parentNode.removeChild(s);
    }
    function failed(text) {
      finish();
      fail.textContent = text || 'Something went wrong. Please try again.';
      fail.classList.add('is-visible');
      btn.disabled = false;
      btn.innerHTML = label;
    }
    window[cb] = function (data) {
      if (!data || data.result !== 'success') {
        // Mailchimp messages look like "0 - Please enter a value" and may hold HTML.
        var d = document.createElement('div');
        d.innerHTML = String((data && data.msg) || '').replace(/^\d+\s*-\s*/, '');
        return failed((d.textContent || '').trim());
      }
      finish();
      try { sessionStorage.removeItem(STORE); } catch (e) {}
      if (window.dataLayer) window.dataLayer.push({ event: 'playbook_download', role: rv });
      done.querySelector('[data-pb-email]').textContent = ev;
      form.hidden = true;
      done.hidden = false;
      done.focus();
    };
    s.onerror = function () { failed('Network error, please try again.'); };
    s.src = jsonUrl + '&' + new URLSearchParams(new FormData(form)).toString() + '&c=' + cb;
    document.body.appendChild(s);
  });
})();
