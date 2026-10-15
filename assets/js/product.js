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

  // ── Hover-to-play videos (CARE cards): calm by default, play on hover ───
  function initHoverVideos() {
    document.querySelectorAll('[data-hover-play]').forEach(function (v) {
      // Force the muted/playsinline PROPERTIES (the attributes alone don't
      // reliably satisfy autoplay policy, so hover-play would otherwise need a
      // prior click to register as a user gesture).
      v.muted = true; v.playsInline = true;
      var card = v.closest('.kz-care-card') || v;
      var reset = null;
      function play() {
        if (reset) { clearTimeout(reset); reset = null; }
        v.muted = true;
        var p = v.play();
        if (p && p.catch) p.catch(function () {});
      }
      function stop() {
        v.pause();
        reset = setTimeout(function () { try { v.load(); } catch (e) {} }, 120);
      }
      card.addEventListener('mouseenter', play);
      card.addEventListener('mouseleave', stop);
      card.addEventListener('click', function () {
        if (v.paused) play(); else stop();
      });
    });
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

  function boot() {
    initBubbleReveal();
    initHoverVideos();
    initRoles();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
