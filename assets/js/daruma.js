/* Daruma campaign page (/daruma/): the hero doll (tap an eye to colour it in,
   tap the body to knock it over), the request form (sent to HubSpot's Forms
   Submission API, like the white paper form) and the copy-hashtag button. */
(function () {
  'use strict';

  // ── The hero doll: the ritual in two taps ──
  // Its left eye first (the viewer's right, as on the insert card) to set the
  // goal, then the right eye to complete it, which sets off the celebration.
  var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var TIPS = [
    'Set your goal: tap its left eye.',
    'Goal set. Hit it? Tap the other eye.',
    'Goal achieved. Here’s to 2027.'
  ];

  function restart(el, cls) {
    el.classList.remove(cls);
    void el.getBoundingClientRect();   // restart the animation
    el.classList.add(cls);
  }

  function confetti(stage) {
    if (REDUCED || !stage.animate) return;
    var box = document.createElement('div');
    box.className = 'dm-confetti';
    var colours = ['#FFB900', '#D9392B', '#000000', '#FFFBF0', '#FFD133'];
    for (var i = 0; i < 70; i++) {
      var p = document.createElement('i');
      var w = 6 + Math.random() * 7;
      p.style.width = w + 'px';
      p.style.height = (Math.random() < 0.5 ? w : w * 0.45) + 'px';
      p.style.background = colours[i % colours.length];
      if (p.style.background === 'rgb(255, 251, 240)') p.style.boxShadow = '0 0 0 1px rgba(0,0,0,.25)';
      box.appendChild(p);
      var angle = Math.random() * Math.PI * 2;
      var dist = 120 + Math.random() * 220;
      var dx = Math.cos(angle) * dist;
      var dy = Math.sin(angle) * dist * 0.8 - 80;
      var spin = (Math.random() * 720 - 360) + 'deg';
      p.animate([
        { transform: 'translate(-50%,-50%) rotate(0)', opacity: 1 },
        { transform: 'translate(' + dx + 'px,' + dy + 'px) rotate(' + spin + ')', opacity: 1, offset: 0.45 },
        { transform: 'translate(' + dx * 1.15 + 'px,' + (dy + 260) + 'px) rotate(' + spin + ')', opacity: 0 }
      ], { duration: 1600 + Math.random() * 900, easing: 'cubic-bezier(.2,.7,.4,1)', fill: 'forwards' });
    }
    stage.appendChild(box);
    setTimeout(function () { box.remove(); }, 2700);
  }

  document.querySelectorAll('.dm-hero-art').forEach(function (art) {
    var doll = art.querySelector('.dm-doll--hero');
    var stage = art.querySelector('.dm-stage');
    var tip = art.querySelector('.dm-tip');
    var again = art.querySelector('.dm-again');
    var first = doll.querySelector('.dm-eye[data-eye="left"]');
    var second = doll.querySelector('.dm-eye[data-eye="right"]');
    var step = 0;

    function paint(eye, on) {
      eye.querySelector('.dm-pupil').classList.toggle('is-on', on);
      eye.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    function render() {
      tip.textContent = TIPS[step];
      tip.classList.toggle('is-done', step === 2);
      first.classList.toggle('is-next', step === 0);
      second.classList.toggle('is-next', step === 1);
      again.hidden = step !== 2;
    }
    function tap(eye) {
      if (step === 0 && eye === first) { paint(first, true); step = 1; }
      else if (step === 1 && eye === second) {
        paint(second, true); step = 2;
        restart(doll, 'is-cheer'); restart(stage, 'is-cheer'); confetti(stage);
      } else if (step < 2) { restart(doll, 'is-nudge'); }   // wrong eye: a little shake, the pulse shows which
      render();
    }
    [first, second].forEach(function (eye) {
      eye.addEventListener('click', function (e) { e.stopPropagation(); tap(eye); });
      eye.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); tap(eye); }
      });
    });
    doll.querySelector('.dm-body-g').addEventListener('click', function () { restart(doll, 'is-wobble'); });
    again.addEventListener('click', function () {
      paint(first, false); paint(second, false); step = 0; render(); first.focus();
    });
    render();
  });

  // ── The story of the Daruma: reveal as you scroll ──
  // Heading lines rise in, the proverb writes itself one character at a time,
  // each chapter's picture slides in from its side, and the timeline line
  // draws down in red as you read.
  var story = document.querySelector('.dm-story');
  if (story && !REDUCED && 'IntersectionObserver' in window) {
    story.classList.add('dm-anim');
    var vert = story.querySelector('.dm-vert');
    if (vert) {
      vert.innerHTML = Array.prototype.map.call(vert.textContent.trim(), function (ch, i) {
        return '<span style="transition-delay:' + (i * 0.12) + 's">' + ch + '</span>';
      }).join('');
    }
    var revealers = [];
    story.querySelectorAll('.dm-story-head > div > *, .dm-face-guide, .dm-credits').forEach(function (el, i) {
      el.classList.add('dm-rv');
      el.style.transitionDelay = (el.closest('.dm-story-head') ? i * 0.1 : 0) + 's';
      revealers.push(el);
    });
    story.querySelectorAll('.dm-chapter').forEach(function (el) { revealers.push(el); });
    if (vert) revealers.push(vert);
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -18% 0px' });
    revealers.forEach(function (el) { io.observe(el); });

    var line = story.querySelector('.dm-chapters');
    var ticking = false;
    function drawLine() {
      ticking = false;
      var r = line.getBoundingClientRect();
      var p = (window.innerHeight * 0.65 - r.top) / r.height;
      line.style.setProperty('--dm-line', Math.max(0, Math.min(1, p)).toFixed(3));
      // Backstop for the observer (a fast jump, e.g. an anchor link, can skip past it):
      // anything already above the fold line is shown.
      var fold = window.innerHeight * 0.82;
      revealers.forEach(function (el) {
        if (!el.classList.contains('is-in') && el.getBoundingClientRect().top < fold) el.classList.add('is-in');
      });
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(drawLine); }
    }, { passive: true });
    drawLine();
  }

  // ── Kaizen timeline: draws itself when it scrolls into view ──
  var hist = document.querySelector('.dm-history');
  if (hist && !REDUCED && 'IntersectionObserver' in window) {
    document.querySelector('.dm-kaizen').classList.add('dm-anim-h');
    var showHist = function () { hist.classList.add('is-in'); };
    var hio = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) { showHist(); hio.disconnect(); }
    }, { rootMargin: '0px 0px -15% 0px' });
    hio.observe(hist);
    // Same backstop as the story: a fast jump past it still shows it.
    window.addEventListener('scroll', function () {
      if (hist.getBoundingClientRect().top < window.innerHeight * 0.85) showHist();
    }, { passive: true });
  }

  // ── Copy hashtag ──
  document.querySelectorAll('.dm-tag[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var label = btn.querySelector('small');
      var done = function () {
        btn.classList.add('is-copied');
        if (label) label.textContent = 'Copied';
        setTimeout(function () { btn.classList.remove('is-copied'); if (label) label.textContent = 'Copy'; }, 2000);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(btn.getAttribute('data-copy')).then(done, done);
    });
  });

  // ── Request form ──
  var form = document.getElementById('dm-form');
  var sent = document.getElementById('dm-sent');
  if (!form || !sent) return;
  var errorBox = form.querySelector('.dm-form-error');
  var submit = form.querySelector('.dm-submit');
  var POSTCODE = /^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$/i;

  function val(name) { var el = form.elements[name]; return el ? el.value.trim() : ''; }
  function setError(name, msg) {
    var el = form.elements[name];
    if (!el) return;
    var field = el.closest('.dm-field');
    field.classList.toggle('is-bad', !!msg);
    field.querySelector('.dm-err').textContent = msg || '';
  }
  var YOU = ['firstname', 'lastname', 'email', 'jobtitle', 'company'];
  var POST = ['address1', 'city', 'zip'];
  function validate(names) {
    var bad = null;
    names.forEach(function (n) {
      var msg = '';
      var v = val(n);
      if (!v) msg = 'Please fill this in.';
      else if (n === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) msg = 'Please enter a valid email.';
      else if (n === 'zip' && !POSTCODE.test(v)) msg = 'Please enter a UK postcode.';
      setError(n, msg);
      if (msg && !bad) bad = form.elements[n];
    });
    return bad;
  }
  form.addEventListener('input', function (e) {
    if (e.target.name && e.target.closest('.dm-field.is-bad')) setError(e.target.name, '');
  });

  function showSent() {
    form.hidden = true;
    sent.hidden = false;
    sent.focus({ preventScroll: true });
    sent.closest('.dm-form-card').scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  // The address half opens with "Continue", once the first half is filled in.
  var more = document.getElementById('dm-more');
  var cont = form.querySelector('.dm-continue');
  function openMore() {
    more.hidden = false;
    cont.hidden = true;
    cont.setAttribute('aria-expanded', 'true');
  }
  cont.addEventListener('click', function () {
    var bad = validate(YOU);
    if (bad) { bad.focus(); return; }
    openMore();
    form.elements.address1.focus();
  });
  if (location.hash === '#sent') { form.hidden = true; sent.hidden = false; }   // preview the thank-you state

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    errorBox.hidden = true;
    if (more.hidden) { cont.click(); return; }   // Enter in the first half: same as Continue
    var bad = validate(YOU.concat(POST));
    if (bad) { bad.focus(); return; }
    var jsonUrl = form.getAttribute('data-mc-json');
    if (!jsonUrl) {
      errorBox.textContent = 'This form isn’t connected yet, so nothing was sent.';
      errorBox.hidden = false;
      return;
    }
    // Mailchimp "Lead magnets" audience merge tags. ADDRESS is an address-type
    // field whose country is sent by name, as the embedded form's dropdown does.
    var q = new URLSearchParams();
    [['EMAIL', 'email'], ['FNAME', 'firstname'], ['LNAME', 'lastname'],
     ['JOBT', 'jobtitle'], ['COMPNAME', 'company'],
     ['ADDRESS[addr1]', 'address1'], ['ADDRESS[addr2]', 'address2'], ['ADDRESS[city]', 'city']
    ].forEach(function (f) { q.set(f[0], val(f[1])); });
    q.set('ADDRESS[state]', '');
    q.set('ADDRESS[zip]', val('zip').toUpperCase());
    q.set('ADDRESS[country]', 'United Kingdom');
    var params = new URLSearchParams(location.search);
    [['utm_source', 'UTMSRC'], ['utm_medium', 'UTMMED'], ['utm_campaign', 'UTMCAMP'],
     ['utm_term', 'UTMTRM'], ['utm_content', 'UTMCONT']
    ].forEach(function (u) { if (params.get(u[0])) q.set(u[1], params.get(u[0])); });
    if (form.getAttribute('data-mc-tag')) q.set('tags', form.getAttribute('data-mc-tag'));
    q.set(form.getAttribute('data-mc-honeypot'), '');   // Mailchimp bot check, must stay empty

    submit.disabled = true;
    var label = submit.textContent;
    submit.textContent = 'Sending…';
    function fail(text) {
      errorBox.textContent = text || 'Something went wrong sending that. Please try again, or email hello@kaizan.ai.';
      errorBox.hidden = false;
      submit.disabled = false;
      submit.textContent = label;
    }
    var cb = 'kzDm_' + Date.now(), s = document.createElement('script');
    window[cb] = function (data) {
      delete window[cb];
      if (s.parentNode) s.parentNode.removeChild(s);
      var msg = (data && data.msg) ? String(data.msg).replace(/<[^>]*>/g, '').replace(/^\d+\s*-\s*/, '') : '';
      if (data && data.result === 'success') {
        if (window.dataLayer) window.dataLayer.push({ event: 'daruma_request' });
        showSent();
      } else if (/already subscribed/i.test(msg)) {
        // Signup forms can't update an existing contact, so this request (and
        // its address) never reaches Mailchimp: ask them to email instead.
        fail('You’re already on our list, so we couldn’t take your address here. Email hello@kaizan.ai with your postal address and we’ll send your Daruma.');
      } else {
        fail(msg);
      }
    };
    s.src = jsonUrl + '&' + q.toString() + '&c=' + cb;
    s.onerror = function () { fail(); };
    document.body.appendChild(s);
  });
})();
