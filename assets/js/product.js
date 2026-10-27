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
  // Each card's video plays once, in order (C → A → R → E, repeating), with
  // the playing card highlighted and the rest on their posters. A card only
  // starts once its video is at least half on screen, so the cycle doesn't
  // run ahead while the visitor is still reading. On phones the cards sit in
  // a swipe row: finishing a card slides the row to the next one, and
  // swiping to a card plays it. Hover/tap jumps to a card. With reduced
  // motion nothing auto-plays: cards play only on hover/tap.
  function initCareSpotlight() {
    var cards = [].slice.call(document.querySelectorAll('.kz-care-card')).filter(function (c) {
      return c.querySelector('video[data-hover-play]');
    });
    if (!cards.length) return;
    var grid = cards[0].parentElement;
    var vids = cards.map(function (c) {
      var v = c.querySelector('video');
      // Force the muted/playsinline PROPERTIES (the attributes alone don't
      // reliably satisfy autoplay policy).
      v.muted = true; v.playsInline = true; v.loop = false;
      return v;
    });
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var vis = vids.map(function () { return 0; });
    var active = -1;

    function isRow() { return grid.scrollWidth > grid.clientWidth + 4; }
    function seen(i) { return vis[i] >= 0.5; }
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
    function slideTo(i) {
      if (!isRow()) return;
      grid.scrollTo({ left: cards[i].offsetLeft - cards[0].offsetLeft, behavior: 'smooth' });
    }

    vids.forEach(function (v, i) {
      v.addEventListener('ended', function () {
        if (i !== active) return;
        if (reduced || !seen(i)) { rest(i); active = -1; return; }
        var next = (i + 1) % cards.length;
        slideTo(next);
        activate(next);
      });
    });
    cards.forEach(function (c, i) {
      c.addEventListener('mouseenter', function () { if (i !== active) activate(i); });
      c.addEventListener('click', function () { if (i !== active) activate(i); });
    });

    if (reduced) return;
    if (!('IntersectionObserver' in window)) { activate(0); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { vis[vids.indexOf(e.target)] = e.intersectionRatio; });
      if (active !== -1 && seen(active)) {
        if (vids[active].paused && !vids[active].ended) play(vids[active]);
        return;
      }
      // Active card is off screen (scrolled away, or swiped past): play the
      // first card that is in view instead, or pause until one is.
      for (var i = 0; i < cards.length; i++) {
        if (seen(i)) { activate(i); return; }
      }
      if (active !== -1) vids[active].pause();
    }, { threshold: [0, 0.5, 1] });
    vids.forEach(function (v) { io.observe(v); });
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

  // ── Section bubbles: each pillar section's label is a speech bubble that
  // matches a hero bubble. As the section scrolls into view the bubble drifts
  // in from above-left (the hero's direction) and settles into place; it is
  // scroll-linked, so scrolling back up sends it back. Reduced motion: static.
  function initSectionBubbles() {
    var badges = ['#ai-assistant', '#care', '#health-model', '#client-360'].map(function (id) {
      return document.querySelector(id + ' .kz-eyebrow');
    }).filter(Boolean);
    if (!badges.length) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var raf = 0;
    function ease(t) { return 1 - Math.pow(1 - t, 3); }
    function place() {
      raf = 0;
      var vh = window.innerHeight || document.documentElement.clientHeight;
      badges.forEach(function (b, i) {
        // Measure the resting position (ignore the current transform).
        var top = b.getBoundingClientRect().top - (parseFloat(b.dataset.dy) || 0);
        // 0 when the label is at the bottom of the screen, 1 by 62% of the way up.
        var t = Math.max(0, Math.min(1, (vh - top) / (vh * 0.38)));
        var e = ease(t);
        var dx = (1 - e) * -70, dy = (1 - e) * -120;
        var rot = (1 - e) * (i % 2 ? 9 : -9);
        b.dataset.dy = dy;
        b.style.transform = 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg) scale(' + (0.6 + 0.4 * e).toFixed(3) + ')';
        b.style.opacity = Math.min(1, t * 1.6).toFixed(2);
      });
    }
    function req() { if (!raf) raf = requestAnimationFrame(place); }
    window.addEventListener('scroll', req, { passive: true });
    window.addEventListener('resize', req);
    place();
  }

  // Arriving on /product/#care-<pillar> (e.g. from a Hall of Fame award
  // category): flash that CARE card so it's clear which pillar was meant.
  function initCareTarget() {
    var id = location.hash.slice(1);
    if (!/^care-/.test(id)) return;
    var card = document.getElementById(id);
    if (card) card.classList.add('is-target');
  }

  function boot() {
    initCareTarget();
    initBubbleReveal();
    initCareSpotlight();
    initScrollPlayVideos();
    initRoles();
    initSectionBubbles();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
