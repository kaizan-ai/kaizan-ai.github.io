/* White-paper lead strip: validation + HubSpot submit.
   Same HubSpot form and thank-you page as /white-paper/ (assets/js/white-paper.js). */
(function () {
  'use strict';
  var PORTAL = '144688314', GUID = 'bae37d8b-ce80-453b-8a02-6a378decb06e';
  var FREE = ['gmail.com','googlemail.com','yahoo.com','yahoo.co.uk','hotmail.com','hotmail.co.uk',
    'outlook.com','live.com','msn.com','aol.com','icloud.com','me.com','mac.com','proton.me',
    'protonmail.com','gmx.com','gmx.de','mail.com','yandex.com','zoho.com','fastmail.com',
    'tutanota.com','duck.com','hey.com'];

  function emailError(v) {
    if (!v) return 'Please enter your work email.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'That doesn\u2019t look like a valid email.';
    if (FREE.indexOf(v.split('@')[1].toLowerCase()) !== -1) return 'Please use your work email, not a personal address.';
    return null;
  }
  function setErr(field, msg) {
    field.classList.toggle('has-error', !!msg);
    field.querySelector('.wp-strip__err').textContent = msg || '';
  }

  document.querySelectorAll('.wp-strip__form').forEach(function (form) {
    var email = form.querySelector('input[type="email"]');
    var role = form.querySelector('select');
    var eField = email.closest('.wp-strip__field'), rField = role.closest('.wp-strip__field');
    var btn = form.querySelector('button[type="submit"]');
    var fail = form.querySelector('.wp-strip__fail');
    email.addEventListener('input', function () { setErr(eField, null); });
    role.addEventListener('change', function () { setErr(rField, null); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      fail.classList.remove('is-visible');
      var eErr = emailError(email.value.trim());
      var rErr = role.value ? null : 'Please select your job title.';
      setErr(eField, eErr); setErr(rField, rErr);
      if (eErr || rErr) { (eErr ? email : role).focus(); return; }
      if (btn.disabled) return;
      var label = btn.innerHTML;
      btn.disabled = true; btn.innerHTML = 'Submitting\u2026';

      var fields = [
        { objectTypeId: '0-1', name: 'email', value: email.value.trim() },
        { objectTypeId: '0-1', name: 'jobtitle', value: role.value }
      ];
      var params = new URLSearchParams(window.location.search);
      ['utm_source','utm_medium','utm_campaign','utm_content','utm_term'].forEach(function (k) {
        if (params.get(k)) fields.push({ objectTypeId: '0-1', name: k, value: params.get(k) });
      });
      fetch('https://api.hsforms.com/submissions/v3/integration/submit/' + PORTAL + '/' + GUID, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fields: fields,
          context: { pageUri: window.location.href, pageName: document.title,
                     hutk: (document.cookie.match(/hubspotutk=([^;]+)/) || [])[1] }
        })
      }).then(function (res) {
        if (!res.ok) throw new Error('HubSpot ' + res.status);
        if (window.dataLayer) window.dataLayer.push({ event: 'white_paper_download', form_id: 'wp-strip', role: role.value });
        try { localStorage.setItem('kz-wp-popup', String(Date.now() + 14 * 864e5)); } catch (e) {}
        window.location.href = 'https://kaizan.ai/white-paper-confirmation';
      }).catch(function () {
        fail.classList.add('is-visible');
        btn.disabled = false; btn.innerHTML = label;
      });
    });
  });
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
