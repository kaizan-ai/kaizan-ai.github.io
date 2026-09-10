/* Kaizan v2 — site.js. Vanilla JS for nav/tabs/menus.
   Loaded with `defer`. No external dependencies.
*/
(function () {
  'use strict';

  // ── Mobile nav toggle ────────────────────────────────────────────
  function initMobileNav() {
    document.querySelectorAll('.kz-nav').forEach(function (nav) {
      var toggle = nav.querySelector('.kz-nav-toggle');
      if (!toggle) return;
      toggle.addEventListener('click', function () {
        nav.classList.toggle('is-mobile-open');
      });
      // Close on link click
      nav.querySelectorAll('.kz-nav-links a').forEach(function (a) {
        a.addEventListener('click', function () { nav.classList.remove('is-mobile-open'); });
      });
    });
  }

  // ── Product mega-menu (hover with delay) ─────────────────────────
  function initMegaMenu() {
    document.querySelectorAll('[data-mega-menu]').forEach(function (root) {
      var trigger = root.querySelector('.kz-mega-trigger');
      var panel = root.querySelector('.kz-mega-panel');
      if (!trigger || !panel) return;

      var closeT = null;
      function open()  { if (closeT) clearTimeout(closeT); trigger.setAttribute('aria-expanded', 'true'); }
      function close() { closeT = setTimeout(function () { trigger.setAttribute('aria-expanded', 'false'); }, 120); }

      root.addEventListener('mouseenter', open);
      root.addEventListener('mouseleave', close);
      panel.addEventListener('mouseenter', open);
      panel.addEventListener('mouseleave', close);

      // Keyboard: toggle on focus / blur
      trigger.addEventListener('focus', open);
      trigger.addEventListener('blur', close);
    });
  }

  // ── Product Tour scene switcher (Home page) ──────────────────────
  function initTour() {
    var root = document.querySelector('[data-tour]');
    if (!root) return;
    var tabs = root.querySelectorAll('[data-tour-tab]');
    var frames = root.querySelectorAll('[data-scene]');
    var badge = root.querySelector('[data-tour-badge]');
    var labels = ['SCENE 01', 'SCENE 02', 'SCENE 03', 'SCENE 04'];
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('is-active'); });
        frames.forEach(function (f) { f.classList.remove('is-active'); });
        tab.classList.add('is-active');
        if (frames[i]) frames[i].classList.add('is-active');
        if (badge) badge.textContent = labels[i] + ' · ACME CREATIVE';
      });
    });
  }

  // ── AI Helpers tab switcher (Product page) ───────────────────────
  function initHelpers() {
    var root = document.querySelector('[data-helpers]');
    if (!root) return;
    var tabs = root.querySelectorAll('[data-helper-tab]');
    var panels = root.querySelectorAll('[data-helper-panel]');
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) { t.classList.remove('is-active'); });
        panels.forEach(function (p) { p.style.display = 'none'; });
        tab.classList.add('is-active');
        if (panels[i]) panels[i].style.display = '';
      });
    });
    // Initialise: show first panel only
    panels.forEach(function (p, i) { p.style.display = i === 0 ? '' : 'none'; });
  }

  // ── Security: tab rail per section, swap visual + active state ───
  function initSecurityTabs() {
    document.querySelectorAll('[data-sec-group]').forEach(function (group) {
      var tabs = group.querySelectorAll('[data-sec-tab]');
      var visuals = group.querySelectorAll('.kz-sec-visual');
      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          var target = tab.getAttribute('data-sec-target');
          tabs.forEach(function (t) { t.classList.remove('is-active'); });
          tab.classList.add('is-active');
          visuals.forEach(function (v) {
            v.classList.toggle('is-active', v.id === target);
          });
        });
      });
    });
  }

  // ── Hero video: click overlay → play from start with sound ──────
  function initHeroVideo() {
    var video = document.querySelector('[data-hero-video]');
    var overlay = document.querySelector('[data-hero-overlay]');
    if (!video || !overlay) return;

    function activate(e) {
      if (e) e.preventDefault();
      overlay.classList.add('is-hidden');
      // Click is the user gesture browsers require to allow audio playback.
      // Video starts paused (no autoplay/muted attributes) — show controls
      // once the user has chosen to play, so they can pause/seek/mute.
      video.controls = true;
      video.muted = false;
      video.volume = 1;
      try { video.currentTime = 0; } catch (_) {}
      var p = video.play();
      if (p && typeof p.then === 'function') {
        p.catch(function () {
          overlay.classList.remove('is-hidden');
          video.controls = false;
        });
      }
    }

    // Click and keyboard activation (the overlay is a real <button>).
    overlay.addEventListener('click', activate);
    overlay.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') activate(e);
    });
  }

  // ── Video lightbox: click [data-video-btn] → open modal with video ──
  function initVideoLightbox() {
    var triggers = document.querySelectorAll('[data-video-btn]');
    if (!triggers.length) return;

    // Lazy-create the lightbox once on first need.
    var lb = document.createElement('div');
    lb.className = 'kz-video-lightbox';
    lb.innerHTML =
      '<div class="kz-video-lightbox__frame">' +
        '<button class="kz-video-lightbox__close" type="button" aria-label="Close video">×</button>' +
        '<video controls playsinline></video>' +
      '</div>';
    document.body.appendChild(lb);
    var video = lb.querySelector('video');
    var closeBtn = lb.querySelector('.kz-video-lightbox__close');

    function open(src) {
      video.src = src;
      lb.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      var p = video.play();
      if (p && typeof p.then === 'function') p.catch(function () {});
    }
    function close() {
      lb.classList.remove('is-open');
      video.pause();
      video.removeAttribute('src');
      video.load();
      document.body.style.overflow = '';
    }

    triggers.forEach(function (b) {
      b.addEventListener('click', function () {
        var src = b.getAttribute('data-video-src');
        if (src) open(src);
      });
    });
    closeBtn.addEventListener('click', close);
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && lb.classList.contains('is-open')) close();
    });
  }

  // ── Quote carousel ───────────────────────────────────────────────
  function initQuoteCarousel() {
    document.querySelectorAll('[data-carousel]').forEach(function (root) {
      var vp = root.querySelector('[data-carousel-viewport]');
      if (!vp) return;
      var cards = Array.prototype.slice.call(vp.children);
      if (!cards.length) return;
      var prev = root.querySelector('[data-carousel-prev]');
      var next = root.querySelector('[data-carousel-next]');
      var dotsWrap = root.parentElement.querySelector('[data-carousel-dots]');
      var dots = dotsWrap ? Array.prototype.slice.call(dotsWrap.children) : [];

      function step() {
        var gap = parseFloat(getComputedStyle(vp).gap) || 20;
        return cards[0].getBoundingClientRect().width + gap;
      }
      function index() { return Math.round(vp.scrollLeft / step()); }
      function atEnd() { return vp.scrollLeft >= vp.scrollWidth - vp.clientWidth - 2; }
      function goTo(i) {
        i = Math.max(0, Math.min(cards.length - 1, i));
        vp.scrollTo({ left: i * step(), behavior: 'smooth' });
      }
      function refresh() {
        var i = index();
        dots.forEach(function (d, di) { d.classList.toggle('is-active', di === i); });
        if (prev) prev.disabled = vp.scrollLeft <= 2;
        if (next) next.disabled = atEnd();
      }

      if (prev) prev.addEventListener('click', function () { goTo(index() - 1); });
      if (next) next.addEventListener('click', function () { goTo(index() + 1); });
      dots.forEach(function (d, di) { d.addEventListener('click', function () { goTo(di); }); });

      var t;
      vp.addEventListener('scroll', function () { clearTimeout(t); t = setTimeout(refresh, 90); });
      window.addEventListener('resize', refresh);

      // Auto-advance (skipped when the user prefers reduced motion).
      var timer = null;
      var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      function play() { if (reduce) return; stop(); timer = setInterval(function () { atEnd() ? goTo(0) : goTo(index() + 1); }, 5500); }
      function stop() { if (timer) { clearInterval(timer); timer = null; } }
      ['pointerenter', 'pointerdown', 'focusin'].forEach(function (e) { root.addEventListener(e, stop); });
      ['pointerleave', 'focusout'].forEach(function (e) { root.addEventListener(e, play); });

      refresh();
      play();
    });
  }

  // ── Locale (UK / US) switch + suggestion banner ──────────────────
  function initLocale() {
    var onUS = location.pathname === '/us' || location.pathname.indexOf('/us/') === 0;
    function ukPath() { return location.pathname.replace(/^\/us(\/|$)/, '/'); }
    function usPath() { return '/us' + location.pathname; }

    // Footer switch link.
    var sw = document.querySelector('[data-locale-switch]');
    if (sw) {
      sw.textContent = onUS ? 'View UK site' : 'View US site';
      sw.href = onUS ? ukPath() : usPath();
      sw.hidden = false;
      sw.addEventListener('click', function () {
        try { localStorage.setItem('kz-locale', onUS ? 'uk' : 'us'); } catch (e) {}
      });
    }

    // One-time suggestion banner for US-timezone visitors on the UK site.
    var chosen = null;
    try { chosen = localStorage.getItem('kz-locale'); } catch (e) {}
    if (onUS || chosen) return;
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
    var isUS = /^America\/(New_York|Detroit|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Adak|Boise|Juneau|Sitka|Menominee|Indiana|Kentucky|North_Dakota)/.test(tz)
      || tz === 'Pacific/Honolulu';
    if (!isUS) return;

    var bar = document.createElement('div');
    bar.className = 'kz-locale-banner';
    bar.innerHTML =
      '<span>Looks like you’re in the US — see the US site?</span>' +
      '<a class="kz-btn kz-btn-yellow" href="' + usPath() + '" data-go-us>View US site</a>' +
      '<button type="button" class="kz-locale-banner__x" aria-label="Dismiss">×</button>';
    document.body.appendChild(bar);
    function remember(v) { try { localStorage.setItem('kz-locale', v); } catch (e) {} }
    bar.querySelector('[data-go-us]').addEventListener('click', function () { remember('us'); });
    bar.querySelector('.kz-locale-banner__x').addEventListener('click', function () {
      remember('uk'); bar.remove();
    });
  }

  // ── Boot ─────────────────────────────────────────────────────────
  function boot() {
    initMobileNav();
    initMegaMenu();
    initTour();
    initQuoteCarousel();
    initLocale();
    initHelpers();
    initHeroVideo();
    initSecurityTabs();
    initVideoLightbox();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
