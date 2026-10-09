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
        var open = nav.classList.toggle('is-mobile-open');
        // The open mobile menu renders the dropdown panels inline (see the
        // 1024px breakpoint in site.css), so the triggers are expanded in
        // fact — say so, or assistive tech announces them as collapsed.
        nav.querySelectorAll('.kz-mega-trigger').forEach(function (t) {
          t.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
      });
      // Close on link click
      nav.querySelectorAll('.kz-nav-links a').forEach(function (a) {
        a.addEventListener('click', function () { nav.classList.remove('is-mobile-open'); });
      });
    });
  }

  // ── Product mega-menu (hover with delay) ─────────────────────────
  function initMegaMenu() {
    function canHover() { return window.matchMedia('(hover: hover)').matches; }
    var touchRoots = [];
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

      // Touch: on a device that can't hover (a tablet in landscape is still
      // above the 1024px mobile-nav breakpoint, so it gets the desktop nav),
      // the first tap opens the panel instead of following the trigger's
      // href; a second tap navigates as normal.
      //
      // The open state can't be read off aria-expanded here: a tap fires
      // mousedown -> focus -> mouseup -> click, and the focus handler above
      // has already set it to "true" by the time click arrives. Track the
      // tap separately.
      var tapOpened = false;
      // Capture phase, so this runs before the anchor's own click handlers —
      // initMobileNav's "close on link click" is one of them, and it strips
      // is-mobile-open, which the mobile check below needs to still see.
      root.addEventListener('click', function (e) {
        if (!trigger.contains(e.target)) return;
        if (canHover()) return;
        // Keyboard Enter also fires click, with detail 0 — let it navigate on
        // the first press rather than making it take two.
        if (!e.detail) return;
        // In the open mobile menu the panel is already rendered inline, so
        // there is nothing to open: the trigger is a plain link again.
        if (trigger.closest('.kz-nav.is-mobile-open')) return;
        if (tapOpened) return;
        e.preventDefault();
        tapOpened = true;
        open();
      }, true);
      touchRoots.push({ root: root, trigger: trigger, reset: function () {
        tapOpened = false;
        trigger.setAttribute('aria-expanded', 'false');
      } });
    });

    // Tapping outside any dropdown closes it. One listener for all of them,
    // and it ignores taps on the hamburger — that click sets aria-expanded on
    // every trigger (the open mobile menu shows the panels inline) and would
    // otherwise be undone here as it bubbles.
    document.addEventListener('click', function (e) {
      if (canHover()) return;
      if (e.target.closest && e.target.closest('.kz-nav-toggle')) return;
      if (document.querySelector('.kz-nav.is-mobile-open')) return;
      touchRoots.forEach(function (d) {
        if (!d.root.contains(e.target)) d.reset();
      });
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
    // Pages with no /us/ twin opt out: <meta name="kz-no-us-page">.
    if (onUS || chosen || document.querySelector('meta[name="kz-no-us-page"]')) return;
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
    var isUS = /^America\/(New_York|Detroit|Chicago|Denver|Los_Angeles|Phoenix|Anchorage|Adak|Boise|Juneau|Sitka|Menominee|Indiana|Kentucky|North_Dakota)/.test(tz)
      || tz === 'Pacific/Honolulu';
    if (!isUS) return;

    var bar = document.createElement('div');
    bar.className = 'kz-locale-banner';
    bar.innerHTML =
      '<span>Looks like you’re in the US. See the US site?</span>' +
      '<a class="kz-btn kz-btn-yellow" href="' + usPath() + '" data-go-us>View US site</a>' +
      '<button type="button" class="kz-locale-banner__x" aria-label="Dismiss">×</button>';
    document.body.appendChild(bar);
    function remember(v) { try { localStorage.setItem('kz-locale', v); } catch (e) {} }
    bar.querySelector('[data-go-us]').addEventListener('click', function () { remember('us'); });
    bar.querySelector('.kz-locale-banner__x').addEventListener('click', function () {
      remember('uk'); bar.remove();
    });
  }

  // ── Hero reel: play when scrolled into view, pause when out ───────
  function initReel() {
    var vids = document.querySelectorAll('[data-play-inview]');
    if (!vids.length) return;
    if (!('IntersectionObserver' in window)) {
      vids.forEach(function (v) { v.play().catch(function () {}); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) {
          try { v.currentTime = 0; } catch (err) {}  // restart from the beginning each time it scrolls into view
          v.play().catch(function () {});
        } else {
          v.pause();
        }
      });
    }, { threshold: 0.35 });
    vids.forEach(function (v) { io.observe(v); });
  }

  // ── Playbooks section: bubbles travel between sub-sections on scroll ──
  function initPbConnectors() {
    var root = document.getElementById('sceneRoot');
    if (!root) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    function applyRealPath(originId, destId, selector) {
      try {
        var origin = document.getElementById(originId);
        var dest = document.getElementById(destId);
        var travelers = document.querySelectorAll(selector);
        if (!origin || !dest || !travelers.length) return;
        var rRect = root.getBoundingClientRect();
        var oRect = origin.getBoundingClientRect();
        var dRect = dest.getBoundingClientRect();
        var ox = oRect.left - rRect.left + oRect.width / 2;
        var oy = oRect.top - rRect.top + oRect.height / 2;
        var dx = dRect.left - rRect.left + dRect.width / 2;
        var dy = dRect.top - rRect.top + dRect.height / 2;
        var c1x = ox + (dx - ox) * 0.25, c1y = oy + (dy - oy) * 0.32;
        var c2x = ox + (dx - ox) * 0.6,  c2y = oy + (dy - oy) * 0.78;
        var d = 'M' + ox + ',' + oy + ' C' + c1x + ',' + c1y + ' ' + c2x + ',' + c2y + ' ' + dx + ',' + dy;
        travelers.forEach(function (el) { el.style.offsetPath = "path('" + d + "')"; el.style.offsetRotate = '0deg'; });
      } catch (e) { /* keep fallback */ }
    }
    function applyAllPaths() {
      applyRealPath('bubbleOriginA', 'bubbleDestA', '.connA');
      applyRealPath('bubbleOriginB', 'bubbleDestB', '.connB');
      applyRealPath('bubbleOrigin', 'bubbleDest', '.connC');
    }
    function trackProgress(trackId) {
      var el = document.getElementById(trackId);
      if (!el) return 0;
      var rect = el.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var total = rect.height + vh;
      if (total <= 0) return 0;
      return Math.min(1, Math.max(0, (vh - rect.top) / total));
    }
    var legs = [
      { track: 'launchZoneA', selector: '.connA' },
      { track: 'launchZoneB', selector: '.connB' },
      { track: 'launchZone',  selector: '.connC' }
    ];
    var state = {};
    function tick() {
      legs.forEach(function (leg) {
        var master = trackProgress(leg.track);
        var travelers = document.querySelectorAll(leg.selector);
        travelers.forEach(function (el, i) {
          var stagger = i * 0.07;
          var target = Math.min(1, Math.max(0, master - stagger));
          var key = leg.selector + i;
          var cur = state[key] === undefined ? target : state[key];
          var next = cur + (target - cur) * 0.18;
          state[key] = next;
          var fadeIn = Math.min(1, next / 0.08);
          var fadeOut = Math.min(1, (1 - next) / 0.05);
          var opacity = Math.max(0, Math.min(fadeIn, fadeOut));
          var scale = 0.5 + 0.9 * Math.sin(Math.PI * Math.min(1, Math.max(0, next)));
          var rotate = -4 + 6 * next;
          el.style.offsetDistance = (next * 100) + '%';
          el.style.opacity = String(opacity);
          el.style.transform = 'scale(' + scale.toFixed(3) + ') rotate(' + rotate.toFixed(1) + 'deg)';
        });
      });
      requestAnimationFrame(tick);
    }
    function remeasure() { requestAnimationFrame(function () { requestAnimationFrame(applyAllPaths); }); }
    remeasure();
    window.addEventListener('load', remeasure);
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(remeasure).catch(function () {}); }
    var rt = null;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(applyAllPaths, 150); });
    requestAnimationFrame(tick);
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
    initReel();
    initPbConnectors();
    initSecurityTabs();
    initVideoLightbox();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
