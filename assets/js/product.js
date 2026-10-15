/* ── Product page only ────────────────────────────────────────────────
   Loaded exclusively on /product/ (via extra_head in render_product). Holds
   the behaviours unique to this page so site.js stays identical to the rest
   of the site. */
(function () {
  'use strict';

  // ── Bubble reveal: stagger the row in (left→right) when it scrolls into view ──
  function initBubbleReveal() {
    var rows = document.querySelectorAll('[data-reveal-row]');
    if (!rows.length) return;
    if (!('IntersectionObserver' in window)) {
      rows.forEach(function (r) { r.classList.add('in-view'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in-view'); io.unobserve(e.target); }
      });
    }, { threshold: 0.3 });
    rows.forEach(function (r) { io.observe(r); });
  }

  // ── CARE cards: spotlight in turn ─────────────────────────────────────
  // When the grid scrolls into view, each card's video plays once in order
  // (C → A → R → E, repeating); the playing card is highlighted and the rest
  // rest on their posters. Hovering or tapping a card jumps to it. Pauses
  // when scrolled away. With reduced motion, nothing auto-advances: cards
  // play only on hover/tap.
  function initCareSpotlight() {
    var cards = [].slice.call(document.querySelectorAll('.kz-care-card')).filter(function (c) {
      return c.querySelector('video[data-hover-play]');
    });
    if (!cards.length) return;
    var vids = cards.map(function (c) {
      var v = c.querySelector('video');
      // Force the muted/playsinline PROPERTIES (the attributes alone don't
      // reliably satisfy autoplay policy).
      v.muted = true; v.playsInline = true; v.loop = false;
      return v;
    });
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var active = -1, inView = false, started = false;

    function play(v) {
      v.muted = true;
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }
    function rest(i) {
      cards[i].classList.remove('is-playing');
      vids[i].pause();
      try { vids[i].load(); } catch (e) {}   // back to the poster
    }
    function activate(i) {
      if (active !== -1 && active !== i) rest(active);
      active = i;
      cards[i].classList.add('is-playing');
      try { vids[i].currentTime = 0; } catch (e) {}
      play(vids[i]);
    }
    vids.forEach(function (v, i) {
      v.addEventListener('ended', function () {
        if (i !== active) return;
        if (reduced || !inView) { rest(i); active = -1; return; }
        activate((i + 1) % cards.length);
      });
    });
    cards.forEach(function (c, i) {
      c.addEventListener('mouseenter', function () { if (i !== active) activate(i); });
      c.addEventListener('click', function () { if (i !== active) activate(i); });
    });

    if (reduced) return;
    var grid = cards[0].parentElement;
    if (!('IntersectionObserver' in window)) { inView = true; activate(0); return; }
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        inView = e.isIntersecting;
        if (inView) {
          if (!started) { started = true; activate(0); }
          else if (active !== -1) play(vids[active]);
          else activate(0);
        } else if (active !== -1) {
          vids[active].pause();
        }
      });
    }, { threshold: 0.4 }).observe(grid);
  }

  // ── Roles: "See how we can help you" — click a role, reveal its loops ───
  function initRoles() {
    var root = document.querySelector('[data-roles]');
    if (!root) return;
    var tabs = root.querySelectorAll('[data-role-tab]');
    var panels = root.querySelectorAll('[data-role-panel]');
    function activate(i) {
      tabs.forEach(function (t, j) { t.classList.toggle('is-active', j === i); });
      panels.forEach(function (p, j) { p.classList.toggle('is-active', j === i); });
      if (panels[i]) {
        panels[i].querySelectorAll('video').forEach(function (v) {
          try { v.currentTime = 0; } catch (err) {}
          v.play().catch(function () {});
        });
      }
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { activate(i); });
    });
    activate(0);
  }

  // ── Scroll-to-play videos (AI Assistant): the section is often already
  // partly visible on load, so wait for the visitor's first scroll, then play
  // while at least half the video is on screen (restarting each time).
  function initScrollPlayVideos() {
    var vids = document.querySelectorAll('[data-play-on-scroll]');
    if (!vids.length || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) {
          try { v.currentTime = 0; } catch (err) {}
          v.muted = true;
          var p = v.play();
          if (p && p.catch) p.catch(function () {});
        } else {
          v.pause();
        }
      });
    }, { threshold: 0.5 });
    function start() {
      window.removeEventListener('scroll', start);
      vids.forEach(function (v) { io.observe(v); });
    }
    window.addEventListener('scroll', start, { passive: true });
  }

  function boot() {
    initBubbleReveal();
    initCareSpotlight();
    initScrollPlayVideos();
    initRoles();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
