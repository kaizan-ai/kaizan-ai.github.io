/* ── Persona pages only (/for/<slug>/) ────────────────────────────────
   Loaded exclusively on persona pages (via extra_head in render_persona).
   Holds the behaviours unique to these pages so site.js stays identical to
   the rest of the site. */
(function () {
  'use strict';

  // ── "How Kaizan helps" tabbed showcase ─────────────────────────────────
  // Auto-advances through the features while the section is on screen: a
  // video item moves on when its clip finishes one play-through, anything
  // else after FALLBACK_MS. The active item's progress bar tracks that. The
  // first click hands control to the visitor (no more auto-advance, and the
  // chosen clip loops). On narrow screens the stage moves directly under the
  // active item so the list reads as an accordion.
  var FALLBACK_MS = 7000;
  var NARROW = window.matchMedia('(max-width: 860px)');
  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)');

  function initHow() {
    var root = document.querySelector('[data-how]');
    if (!root) return;
    var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-how-tab]'));
    var panels = Array.prototype.slice.call(root.querySelectorAll('[data-how-panel]'));
    var stage = root.querySelector('[data-how-stage]');
    if (!tabs.length) return;

    var current = 0;
    var auto = !REDUCED.matches && tabs.length > 1;
    var inView = false;
    var started = 0;   // timestamp the current non-video item started
    var raf = null;

    panels.forEach(function (p) {
      var v = p.querySelector('video');
      if (!v) return;
      v.muted = true; v.playsInline = true;
      v.removeAttribute('autoplay');
      v.pause();
      v.addEventListener('ended', function () {
        if (auto && panels[current] === p) go(current + 1);
      });
    });

    function videoOf(i) { return panels[i] && panels[i].querySelector('video'); }

    function placeStage() {
      if (NARROW.matches) tabs[current].after(stage);
      else if (stage.parentNode !== root) root.appendChild(stage);
    }

    function setProgress(frac) {
      tabs.forEach(function (t, j) {
        var bar = t.querySelector('.kz-how-progress span');
        if (bar) bar.style.transform = 'scaleX(' + (j === current ? frac : 0) + ')';
      });
    }

    function tick() {
      raf = null;
      if (!auto || !inView) return;
      var v = videoOf(current);
      if (v && v.duration) setProgress(Math.min(1, v.currentTime / v.duration));
      else if (!v) {
        var frac = (performance.now() - started) / FALLBACK_MS;
        setProgress(Math.min(1, frac));
        if (frac >= 1) { go(current + 1); return; }
      }
      raf = requestAnimationFrame(tick);
    }

    function play() {
      var v = videoOf(current);
      started = performance.now();
      if (v) {
        v.loop = !auto;
        try { v.currentTime = 0; } catch (e) {}
        var pr = v.play();
        if (pr && pr.catch) pr.catch(function () {});
      }
      if (auto && inView && !raf) raf = requestAnimationFrame(tick);
    }

    function go(i) {
      current = (i + tabs.length) % tabs.length;
      tabs.forEach(function (t, j) {
        var on = j === current;
        t.classList.toggle('is-active', on);
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (p, j) {
        var on = j === current;
        p.classList.toggle('is-active', on);
        var v = p.querySelector('video');
        if (v && !on) v.pause();
      });
      root.style.setProperty('--how-accent', tabs[current].style.getPropertyValue('--accent'));
      setProgress(0);
      placeStage();
      if (inView) play();
    }

    function takeOver() {
      if (!auto) return;
      auto = false;
      root.classList.add('is-manual');
      if (raf) { cancelAnimationFrame(raf); raf = null; }
      setProgress(0);
      var v = videoOf(current);
      if (v) v.loop = true;
    }

    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { takeOver(); go(i); });
      t.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowDown' || e.key === 'ArrowRight' ? 1
              : e.key === 'ArrowUp' || e.key === 'ArrowLeft' ? -1 : 0;
        if (!d) return;
        e.preventDefault(); takeOver(); go(i + d); tabs[current].focus();
      });
    });

    if (!auto) root.classList.add('is-manual');

    // Only run (and play video) while the section is on screen.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          inView = e.isIntersecting;
          if (inView) play();
          else {
            var v = videoOf(current);
            if (v) v.pause();
            if (raf) { cancelAnimationFrame(raf); raf = null; }
          }
        });
      }, { threshold: 0.35 }).observe(root);
    } else {
      inView = true;
    }

    var onResize = function () { placeStage(); };
    if (NARROW.addEventListener) NARROW.addEventListener('change', onResize);
    go(0);
  }

  function boot() { initHow(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
