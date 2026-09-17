/* ============================================================================
   Kaizan · ROI Calculator — vanilla JS (no framework, no build step)
   Mirrors the validated working model. British English, GBP.
   Live recompute on every input. Net-gain headline never gated.

   Model notes:
     • Pricing rebuilt for the Sept 2026 model: a free 14 day pilot, then a
       per client monthly rate with a minimum client count per tier.
       Starter £99 per client / month, minimum 10 clients.
       Growth  £119 per client / month, minimum 25 clients.
       Enterprise, bespoke, from ENTERPRISE_FROM clients.
     • Annual cost = max(tier minimum, your clients) × rate × 12.
       Below the minimum you are billed at the minimum, and the calculator
       shows the resulting real cost per client rather than the headline rate.
     • TIER BOUNDARIES: the published page no longer puts a ceiling on any
       tier, so client count alone cannot tell you which tier someone is on.
       The boundaries below exist only so the calculator can pick one. They
       follow the tier minimums (Growth starts where its 25 client minimum
       starts) and ENTERPRISE_FROM is a placeholder until that number is set.
     • Conservative defaults aligned to the validated working model:
         churnRecover 30%, capacityRecover 45%, upsellLift 44%.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.getElementById('kaizan-roi');
  if (!root) return;

  /* ── constants ──────────────────────────────────────────────────────── */
  // Match the host site's own Book-a-demo / pricing links, US or UK, so the
  // /us/ mirror never links back to the UK page.
  var IS_US = location.pathname.indexOf('/us/') === 0;
  var DEMO_URL = IS_US ? '/us/demo/' : '/demo/';
  var PRICING_URL = IS_US ? '/us/pricing/' : '/pricing/';

  var PILOT_DAYS = 14;      // free pilot, no card, before any commitment
  var ENTERPRISE_FROM = 50; // client count at which the calculator stops pricing

  // Real Kaizan pricing, per client per month, billed as one flat monthly plan.
  // Unlimited users on every tier. maxClients is a calculator-only boundary,
  // see the note above.
  var TIERS = [
    { name: 'Starter',    rate: 99,   minClients: 10, maxClients: ENTERPRISE_FROM > 25 ? 24 : ENTERPRISE_FROM - 1 },
    { name: 'Growth',     rate: 119,  minClients: 25, maxClients: ENTERPRISE_FROM - 1 },
    { name: 'Enterprise', rate: null, minClients: ENTERPRISE_FROM, maxClients: Infinity, custom: true }
  ];

  // Conservative / Expected presets drive the per-area assumptions.
  var MODES = {
    Conservative: { churnRecover: 30, upsellLift: 44, capacityRecover: 45 },
    Expected:     { churnRecover: 45, upsellLift: 60, capacityRecover: 60 }
  };

  // Fixed internal benchmarks (stated in the footnote).
  var BASE_UPSELL = 0.08; // addressable upsell pool as % of portfolio
  var ADMIN_HRS   = 9;    // admin hrs / wk / client-facing person
  var WEEKS_YEAR  = 46;   // working weeks / year
  var LOADED_RATE = 30;   // £/hr loaded cost
  var FTE_HOURS   = 1725; // hrs in one FTE-year

  var GREEN_D = '#2E6F4E', GREEN_M = '#7BAE92', GOLD = '#FFB900';

  /* ── formatters ─────────────────────────────────────────────────────── */
  function gbp0(n) { return '£' + Math.round(n).toLocaleString('en-GB'); }
  function gbpM(n) {
    if (n >= 1e6) return '£' + (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
    if (n >= 1e3) return '£' + Math.round(n / 1e3) + 'k';
    return gbp0(n);
  }
  function num(n) { return Math.round(n).toLocaleString('en-GB'); }

  /* ── state ──────────────────────────────────────────────────────────── */
  var state = {
    totalHeadcount: 50,
    team: 20,
    clients: 40,
    revPer: 60000,
    churn: 15,
    mode: 'Expected',
    churnRecover: MODES.Expected.churnRecover,
    upsellLift: MODES.Expected.upsellLift,
    capacityRecover: MODES.Expected.capacityRecover,
    showLead: false,
    leadSent: false
  };

  /* ── compute ────────────────────────────────────────────────────────── */
  function compute(s) {
    var portfolio   = s.clients * s.revPer;
    var atRisk      = portfolio * (s.churn / 100);
    var revRetained = atRisk * (s.churnRecover / 100);
    var revUpsold   = portfolio * BASE_UPSELL * (s.upsellLift / 100);
    var adminHours  = s.team * ADMIN_HRS * WEEKS_YEAR;
    var capHours    = adminHours * (s.capacityRecover / 100);
    var capacity    = capHours * LOADED_RATE;
    var fte         = capHours / FTE_HOURS;
    var gross       = revRetained + revUpsold + capacity;

    var tier = null;
    for (var i = 0; i < TIERS.length; i++) {
      if (s.clients <= TIERS[i].maxClients) { tier = TIERS[i]; break; }
    }
    if (!tier) tier = TIERS[TIERS.length - 1];

    var isCustom = tier.custom === true;

    // Below the tier minimum you are still billed for the minimum.
    var billedClients = isCustom ? s.clients : Math.max(tier.minClients, s.clients);
    var atMinimum     = !isCustom && s.clients < tier.minClients;

    var tierPrice     = isCustom ? null : billedClients * tier.rate * 12;
    var effectiveRate = isCustom ? null : (s.clients > 0 ? (tierPrice / 12) / s.clients : 0);
    var net           = isCustom ? null : gross - tierPrice;
    var roiMultiple   = isCustom ? null : (tierPrice > 0 ? gross / tierPrice : 0);
    var paybackMonths = isCustom ? null : (gross > 0 ? Math.max(1, Math.round(tierPrice / (gross / 12))) : 0);

    return {
      portfolio: portfolio, atRisk: atRisk, revRetained: revRetained, revUpsold: revUpsold,
      adminHours: adminHours, capHours: capHours, capacity: capacity, fte: fte, gross: gross,
      tier: tier, isCustom: isCustom, billedClients: billedClients, atMinimum: atMinimum,
      tierPrice: tierPrice, effectiveRate: effectiveRate, net: net,
      roiMultiple: roiMultiple, paybackMonths: paybackMonths
    };
  }

  /* ── small DOM helpers ──────────────────────────────────────────────── */
  function q(sel, ctx) { return (ctx || root).querySelector(sel); }
  function qa(sel, ctx) { return Array.prototype.slice.call((ctx || root).querySelectorAll(sel)); }
  function setText(roi, text) { var el = q('[data-roi="' + roi + '"]'); if (el) el.textContent = text; }
  function show(el, visible) { if (el) el.classList.toggle('kzroi-hidden', !visible); }
  function esc(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* ── metric block (inside black bar) ────────────────────────────────── */
  function metricHTML(label, value, unit) {
    return '<div><div class="kzroi-metric-label">' + esc(label) + '</div>' +
      '<div class="kzroi-metric-row"><span class="kzroi-metric-val">' + esc(value) + '</span>' +
      (unit ? '<span class="kzroi-metric-unit">' + esc(unit) + '</span>' : '') + '</div></div>';
  }

  /* ── render ─────────────────────────────────────────────────────────── */
  function render() {
    var r = compute(state);

    // headline label + figure
    setText('headline-label', r.isCustom ? 'Total annual benefit with Kaizan' : 'Net annual gain with Kaizan');
    setText('net', gbp0(r.isCustom ? r.gross : r.net));
    var customNote = q('[data-roi="custom-note"]');
    if (customNote) customNote.textContent = 'before platform cost, Enterprise pricing is bespoke';
    show(customNote, r.isCustom);

    // metrics block
    var metrics = '';
    if (!r.isCustom) {
      metrics += metricHTML('Return', r.roiMultiple.toFixed(1) + '×');
      metrics += metricHTML('Payback', r.paybackMonths, 'mo');
    }
    metrics += metricHTML('Capacity', '+' + r.fte.toFixed(1), 'FTE');
    if (r.isCustom) metrics += metricHTML('Pricing', 'Custom');
    q('[data-roi="metrics"]').innerHTML = metrics;

    // cost row (bottom of black bar)
    var costEl = q('[data-roi="cost-row"]');
    if (r.isCustom) {
      costEl.innerHTML =
        '<div><div class="kzroi-cost-label">Kaizan cost · Enterprise tier</div>' +
        '<div class="kzroi-cost-val">Custom</div></div>' +
        '<div class="kzroi-bar-note is-custom">' + ENTERPRISE_FROM + '+ clients, Enterprise pricing is bespoke. ' +
        'Book a demo for a tailored figure. Unlimited users included as standard, and the first ' +
        PILOT_DAYS + ' days are free.</div>';
    } else {
      var note;
      if (r.atMinimum) {
        note = 'Billed at the ' + r.tier.minClients + ' client minimum on ' + esc(r.tier.name) +
          ', so your real rate is ' + gbp0(r.effectiveRate) + ' per client. Unlimited users, and the first ' +
          PILOT_DAYS + ' days are free.';
      } else {
        note = 'Unlimited users, your whole team of ' + num(state.totalHeadcount) +
          ' on Kaizan at no extra cost. The first ' + PILOT_DAYS + ' days are free.';
      }
      costEl.innerHTML =
        '<div><div class="kzroi-cost-label">Kaizan cost · ' + esc(r.tier.name) + ' tier</div>' +
        '<div class="kzroi-cost-row"><span class="kzroi-cost-val">' + gbp0(r.tierPrice / 12) + '</span><span class="kzroi-cost-unit">/ mo</span></div></div>' +
        '<div><div class="kzroi-cost-label">Cost per client</div>' +
        '<div class="kzroi-cost-row"><span class="kzroi-cost-val">' + gbp0(r.effectiveRate) + '</span><span class="kzroi-cost-unit">/ mo</span></div></div>' +
        '<div class="kzroi-bar-note">' + note + '</div>';
    }

    // composition card
    setText('gross', gbp0(r.gross));
    var segs = [
      { key: 'Revenue retained', value: r.revRetained, color: GREEN_D },
      { key: 'Revenue upsold',   value: r.revUpsold,   color: GREEN_M },
      { key: 'Capacity (£)',     value: r.capacity,    color: GOLD }
    ];
    var trackHTML = '', legendHTML = '';
    segs.forEach(function (sgmt) {
      var pct = r.gross ? (sgmt.value / r.gross) * 100 : 0;
      trackHTML += '<div class="kzroi-seg" style="width:' + pct + '%;background:' + sgmt.color + '" title="' + esc(sgmt.key + ': ' + gbp0(sgmt.value)) + '"></div>';
      legendHTML += '<div class="kzroi-legend-item">' +
        '<span class="kzroi-legend-dot" style="background:' + sgmt.color + '"></span>' +
        '<span class="kzroi-legend-key">' + esc(sgmt.key) + '</span>' +
        '<span class="kzroi-legend-val">' + gbp0(sgmt.value) + '</span></div>';
    });
    q('[data-roi="seg-track"]').innerHTML = trackHTML;
    q('[data-roi="legend"]').innerHTML = legendHTML;

    // area card figures
    setText('fig-retained', gbp0(r.revRetained));
    setText('at-risk', gbp0(r.atRisk));
    setText('fig-upsold', gbp0(r.revUpsold));
    setText('fig-capacity', gbp0(r.capacity));
    setText('fig-fte', '+' + r.fte.toFixed(1) + ' FTE');
    setText('admin-hours', num(r.adminHours));

    // portfolio value
    setText('portfolio', gbpM(r.portfolio));

    // methodology mode-dependent numbers
    setText('m-churn', MODES[state.mode].churnRecover);
    setText('m-mode', state.mode);
    setText('m-upsell', MODES[state.mode].upsellLift);
    setText('m-capacity', MODES[state.mode].capacityRecover);

    // footnote
    var foot;
    if (r.isCustom) {
      foot = 'Total benefit ' + gbp0(r.gross) + '/yr shown before platform cost. Enterprise (' +
        ENTERPRISE_FROM + '+ clients) pricing is bespoke, book a demo for your figure. ';
    } else {
      foot = 'Net gain = ' + gbp0(r.gross) + ' benefit less ' + gbp0(r.tierPrice) + ' ' + r.tier.name +
        ' (annual, unlimited users), priced at £' + r.tier.rate + ' per client / month across ' +
        num(r.billedClients) + ' clients' + (r.atMinimum ? ', the tier minimum' : '') + '. ';
    }
    foot += 'Every engagement starts with a free ' + PILOT_DAYS + ' day pilot, so nothing is payable until it proves out. ';
    foot += 'Upsell modelled on an ' + Math.round(BASE_UPSELL * 100) + '% addressable pool, capacity on ' + ADMIN_HRS +
      ' admin hrs/person/week × ' + WEEKS_YEAR + ' weeks at £' + LOADED_RATE + '/hr, 1 FTE = ' + num(FTE_HOURS) +
      ' hrs. Satisfaction shown directionally, not monetised. Pricing set from your client count, see ' +
      '<a href="' + PRICING_URL + '">the pricing above</a>.';
    q('[data-roi="footnote"]').innerHTML = foot;

    // keep the hidden lead summary in sync
    var summaryEl = q('[data-roi="lead-summary"]');
    if (summaryEl) {
      summaryEl.value = JSON.stringify({
        totalHeadcount: state.totalHeadcount, team: state.team, clients: state.clients,
        revPer: state.revPer, churn: state.churn, mode: state.mode,
        gross: Math.round(r.gross), tier: r.tier.name,
        rate: r.isCustom ? null : r.tier.rate,
        billedClients: r.isCustom ? null : r.billedClients,
        annualCost: r.isCustom ? null : Math.round(r.tierPrice),
        net: r.isCustom ? null : Math.round(r.net)
      });
    }
  }

  /* ── number inputs (steppers + typing) ──────────────────────────────── */
  function clampVal(cfg, v) {
    if (!isNaN(cfg.max)) v = Math.min(v, cfg.max);
    if (!isNaN(cfg.min)) v = Math.max(v, cfg.min);
    return v;
  }

  function wireInputs() {
    qa('.kzroi-num').forEach(function (wrap) {
      var key = wrap.getAttribute('data-key');
      var cfg = {
        min: parseFloat(wrap.getAttribute('data-min')),
        max: parseFloat(wrap.getAttribute('data-max')),
        step: parseFloat(wrap.getAttribute('data-step')) || 1
      };
      var input = q('input', wrap);

      function paint() { input.value = state[key].toLocaleString('en-GB'); }

      input.addEventListener('input', function (e) {
        var digits = e.target.value.replace(/[^0-9]/g, '');
        var v = digits === '' ? 0 : parseInt(digits, 10);
        if (!isNaN(cfg.max)) v = Math.min(v, cfg.max);
        state[key] = v;
        render();
      });
      input.addEventListener('blur', function () {
        if (!isNaN(cfg.min) && state[key] < cfg.min) state[key] = cfg.min;
        paint();
        render();
      });

      qa('.kzroi-step', wrap).forEach(function (btn) {
        btn.addEventListener('click', function () {
          var dir = btn.getAttribute('data-act') === 'inc' ? 1 : -1;
          state[key] = clampVal(cfg, state[key] + dir * cfg.step);
          paint();
          render();
        });
      });

      paint();
    });
  }

  /* ── mode toggle ────────────────────────────────────────────────────── */
  function wireToggle() {
    qa('.kzroi-toggle-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var opt = btn.getAttribute('data-mode');
        state.mode = opt;
        state.churnRecover = MODES[opt].churnRecover;
        state.upsellLift = MODES[opt].upsellLift;
        state.capacityRecover = MODES[opt].capacityRecover;
        qa('.kzroi-toggle-btn').forEach(function (b) {
          b.classList.toggle('is-active', b === btn);
        });
        render();
      });
    });
  }

  /* ── lead capture ───────────────────────────────────────────────────── */
  function wireLead() {
    var form = q('[data-roi="lead-form"]');
    var sent = q('[data-roi="lead-sent"]');
    var toggles = qa('[data-roi="lead-toggle"], [data-roi="lead-toggle-cta"]');

    function syncLeadUI() {
      show(form, state.showLead && !state.leadSent);
      show(sent, state.leadSent);
      toggles.forEach(function (t) { show(t, !state.leadSent); });
    }

    toggles.forEach(function (t) {
      t.addEventListener('click', function () {
        // the controls button toggles; the CTA-band button always opens
        if (t.getAttribute('data-roi') === 'lead-toggle') state.showLead = !state.showLead;
        else state.showLead = true;
        syncLeadUI();
        if (state.showLead && form && typeof form.scrollIntoView === 'function') {
          form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      });
    });

    if (form) {
      form.addEventListener('submit', function (e) {
        // On a hosted (e.g. Netlify) deploy the form posts normally and captures the lead.
        // Running locally (file://) there's no backend, so just confirm inline.
        if (!window.location.hostname || window.location.protocol === 'file:') {
          e.preventDefault();
          state.leadSent = true;
          state.showLead = false;
          syncLeadUI();
        }
      });
    }

    syncLeadUI();
  }

  /* ── boot ───────────────────────────────────────────────────────────── */
  wireInputs();
  wireToggle();
  wireLead();
  render();
})();
