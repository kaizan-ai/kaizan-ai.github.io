/* ================================================================
   White paper landing — interactions + HubSpot submission
================================================================ */

(function () {
  'use strict';

  var HUBSPOT_PORTAL_ID = '144688314';
  var HUBSPOT_FORM_GUID = 'bae37d8b-ce80-453b-8a02-6a378decb06e';

  var FREE_EMAIL_DOMAINS = [
    'gmail.com','googlemail.com','yahoo.com','yahoo.co.uk','hotmail.com','hotmail.co.uk',
    'outlook.com','live.com','msn.com','aol.com','icloud.com','me.com','mac.com',
    'proton.me','protonmail.com','gmx.com','gmx.de','mail.com','yandex.com','zoho.com',
    'fastmail.com','tutanota.com','duck.com','hey.com'
  ];

  // ---------------- Reveal on scroll ----------------
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-in'); });
  }

  // ---------------- Counting animation on big numbers ----------------
  function animateCount(el) {
    if (el.dataset.counted) return;
    el.dataset.counted = '1';
    var originalHTML = el.innerHTML;
    var m = originalHTML.match(/^([\d.,]+)/);
    if (!m) return;
    var numStr = m[1];
    var target = parseFloat(numStr.replace(/,/g, ''));
    if (!Number.isFinite(target)) return;
    var isInt = !numStr.includes('.');
    var hasCommas = numStr.includes(',');
    var rest = originalHTML.slice(numStr.length);
    var dur = 1400 + Math.min(600, target / 20);
    var start = performance.now();
    function frame(now) {
      var p = Math.min(1, (now - start) / dur);
      var e = 1 - Math.pow(1 - p, 3);
      var v = target * e;
      var formatted;
      if (isInt) {
        formatted = Math.round(v);
        if (hasCommas) formatted = formatted.toLocaleString('en-US');
      } else {
        formatted = v.toFixed(1);
      }
      el.innerHTML = formatted + rest;
      if (p < 1) requestAnimationFrame(frame);
      else el.innerHTML = originalHTML;
    }
    requestAnimationFrame(frame);
  }

  var countTargets = document.querySelectorAll('.authority__num, .stat__num, .care-card__callout-num');
  if ('IntersectionObserver' in window && countTargets.length) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          animateCount(e.target);
          cio.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.35 });
    countTargets.forEach(function (el) { cio.observe(el); });
  }

  // ---------------- Form validation + HubSpot submit ----------------
  function ensureErrorNode(field) {
    var err = field.querySelector('.field__err');
    if (!err) {
      err = document.createElement('div');
      err.className = 'field__err';
      field.appendChild(err);
    }
    return err;
  }

  function setFieldError(field, msg) {
    field.classList.add('has-error');
    ensureErrorNode(field).textContent = msg;
  }

  function clearFieldError(field) {
    field.classList.remove('has-error');
    var err = field.querySelector('.field__err');
    if (err) err.textContent = '';
  }

  function validateEmail(value) {
    if (!value) return 'Please enter your work email.';
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!re.test(value)) return 'That doesn’t look like a valid email.';
    var domain = value.split('@')[1].toLowerCase();
    if (FREE_EMAIL_DOMAINS.indexOf(domain) !== -1) {
      return 'Please use your work email, not a personal address.';
    }
    return null;
  }

  function validateRole(value) {
    if (!value) return 'Please select your job title.';
    return null;
  }

  function ensureFormError(form) {
    var box = form.querySelector('.form-error');
    if (!box) {
      box = document.createElement('div');
      box.className = 'form-error';
      box.setAttribute('role', 'alert');
      box.textContent = 'Something went wrong. Please try again.';
      var btn = form.querySelector('.btn[type="submit"]');
      if (btn && btn.parentNode) btn.parentNode.insertBefore(box, btn.nextSibling);
      else form.appendChild(box);
    }
    return box;
  }

  function submitToHubSpot(payload) {
    var endpoint = 'https://api.hsforms.com/submissions/v3/integration/submit/'
      + encodeURIComponent(HUBSPOT_PORTAL_ID) + '/'
      + encodeURIComponent(HUBSPOT_FORM_GUID);
    return fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (res) {
      if (!res.ok) throw new Error('HubSpot submission failed: ' + res.status);
      return res.json().catch(function () { return {}; });
    });
  }

  document.querySelectorAll('.lead-form').forEach(function (form) {
    var emailInput = form.querySelector('input[type="email"]');
    var roleInput = form.querySelector('select[name="role"]');
    var emailField = emailInput ? emailInput.closest('.field') : null;
    var roleField = roleInput ? roleInput.closest('.field') : null;
    var submitBtn = form.querySelector('.btn[type="submit"]');
    var formError = ensureFormError(form);

    if (emailInput) emailInput.addEventListener('input', function () { if (emailField) clearFieldError(emailField); });
    if (roleInput) roleInput.addEventListener('change', function () { if (roleField) clearFieldError(roleField); });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      formError.classList.remove('is-visible');

      var emailVal = emailInput ? emailInput.value.trim() : '';
      var roleVal = roleInput ? roleInput.value : '';

      var emailErr = validateEmail(emailVal);
      var roleErr = validateRole(roleVal);

      if (emailField) { emailErr ? setFieldError(emailField, emailErr) : clearFieldError(emailField); }
      if (roleField) { roleErr ? setFieldError(roleField, roleErr) : clearFieldError(roleField); }

      if (emailErr || roleErr) {
        var firstBad = emailErr ? emailInput : roleInput;
        if (firstBad) firstBad.focus();
        return;
      }

      if (!submitBtn || submitBtn.disabled) return;
      var originalHTML = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Submitting…';

      var payload = {
        fields: [
          { objectTypeId: '0-1', name: 'email', value: emailVal },
          { objectTypeId: '0-1', name: 'jobtitle', value: roleVal }
        ],
        context: {
          pageUri: window.location.href,
          pageName: document.title,
          hutk: (document.cookie.match(/hubspotutk=([^;]+)/) || [])[1]
        }
      };

      submitToHubSpot(payload).then(function () {
        submitBtn.classList.add('btn--success');
        submitBtn.innerHTML =
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> On its way to your inbox';
        submitBtn.animate(
          [
            { transform: 'translateY(0) scale(1)' },
            { transform: 'translateY(-2px) scale(1.015)' },
            { transform: 'translateY(0) scale(1)' }
          ],
          { duration: 360, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)' }
        );
        if (window.dataLayer) {
          window.dataLayer.push({
            event: 'white_paper_download',
            form_id: form.id || 'unknown',
            role: roleVal
          });
        }
      }).catch(function () {
        formError.classList.add('is-visible');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
      });
    });
  });
})();
