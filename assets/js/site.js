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

  // ── Boot ─────────────────────────────────────────────────────────
  function boot() {
    initMobileNav();
    initMegaMenu();
    initTour();
    initHelpers();
    initHeroVideo();
    initSecurityTabs();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
