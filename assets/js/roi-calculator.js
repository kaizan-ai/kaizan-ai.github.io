/* ============================================================================
   Kaizan · ROI Calculator — vanilla JS (no framework, no build step)
   Mirrors the validated working model. British English, GBP.
   Live recompute on every input. Net-gain headline never gated.

   Model notes:
     • Pricing tiers are the real Kaizan tiers (kaizan.ai/pricing), unlimited users.
     • Conservative defaults aligned to the validated working model:
         churnRecover 30%, capacityRecover 45%, upsellLift 44%.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.getElementById('kaizan-roi');
  if (!root) return;

  /* ── constants ──────────────────────────────────────────────────────── */
  var DEMO_URL = 'https://calendar.app.google/Eae719Ejh3xxN3Lg8';

  // Real Kaizan pricing — annual (GBP), unlimited users.
  var TIERS = [
    { name: 'Pilot',      maxClients: 10,       price: 2995 * 12 },
    { name: 'Team',       maxClients: 30,       price: 4950 * 12 },
    { name: 'Growth',     maxClients: 75,       price: 8995 * 12 },
    { name: 'Scale',      maxClients: 150,      price: 14950 * 12 },
    { name: 'Enterprise', maxClients: Infinity, price: null, custom: true }
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

  /* ── compute (identical to the React useMemo) ───────────────────────── */
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
    var isCustom = tier.custom === true;
    var tierPrice = isCustom ? null : tier.price;
    var net = isCustom ? null : gross - tierPrice;
    var roiMultiple = isCustom ? null : (tierPrice > 0 ? gross / tierPrice : 0);
    var paybackMonths = isCustom ? null : (gross > 0 ? Math.max(1, Math.round(tierPrice / (gross / 12))) : 0);

    return {
      portfolio: portfolio, atRisk: atRisk, revRetained: revRetained, revUpsold: revUpsold,
      adminHours: adminHours, capHours: capHours, capacity: capacity, fte: fte, gross: gross,
      tier: tier, isCustom: isCustom, tierPrice: tierPrice, net: net,
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
    show(q('[data-roi="custom-note"]'), r.isCustom);

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
        '<div class="kzroi-bar-note is-custom">150+ clients — Enterprise pricing is bespoke. Book a demo for a tailored figure. Unlimited users included as standard.</div>';
    } else {
      var costPer = state.clients > 0 ? (r.tierPrice / 12) / state.clients : 0;
      costEl.innerHTML =
        '<div><div class="kzroi-cost-label">Kaizan cost · ' + esc(r.tier.name) + ' tier</div>' +
        '<div class="kzroi-cost-row"><span class="kzroi-cost-val">' + gbp0(r.tierPrice / 12) + '</span><span class="kzroi-cost-unit">/ mo</span></div></div>' +
        '<div><div class="kzroi-cost-label">Cost per client</div>' +
        '<div class="kzroi-cost-row"><span class="kzroi-cost-val">' + gbp0(costPer) + '</span><span class="kzroi-cost-unit">/ mo</span></div></div>' +
        '<div class="kzroi-bar-note">Unlimited users — your whole team of ' + num(state.totalHeadcount) + ' on Kaizan at no extra cost.</div>';
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
      foot = 'Total benefit ' + gbp0(r.gross) + '/yr shown before platform cost — Enterprise (150+ clients) pricing is bespoke; book a demo for your figure. ';
    } else {
      foot = 'Net gain = ' + gbp0(r.gross) + ' benefit − ' + gbp0(r.tierPrice) + ' ' + r.tier.name + ' (annual, unlimited users). ';
    }
    foot += 'Upsell modelled on an ' + Math.round(BASE_UPSELL * 100) + '% addressable pool; capacity on ' + ADMIN_HRS +
      ' admin hrs/person/week × ' + WEEKS_YEAR + ' weeks at £' + LOADED_RATE + '/hr; 1 FTE = ' + num(FTE_HOURS) +
      ' hrs. Satisfaction shown directionally, not monetised.';
    q('[data-roi="footnote"]').innerHTML = foot;

    // keep the hidden lead summary in sync
    var summaryEl = q('[data-roi="lead-summary"]');
    if (summaryEl) {
      summaryEl.value = JSON.stringify({
        totalHeadcount: state.totalHeadcount, team: state.team, clients: state.clients,
        revPer: state.revPer, churn: state.churn, mode: state.mode,
        gross: Math.round(r.gross), tier: r.tier.name,
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

  /* ── downloadable breakdown (print-to-PDF of the user's own numbers) ──── */
  function row(label, value) {
    return '<tr><td>' + esc(label) + '</td><td class="v">' + esc(value) + '</td></tr>';
  }
  function buildReportHTML() {
    var s = state, r = compute(s);
    var headline = r.isCustom
      ? row('Total annual benefit', gbp0(r.gross) + ' / yr')
      : row('Net annual gain', gbp0(r.net) + ' / yr');
    var costRows = r.isCustom
      ? row('Kaizan tier', 'Enterprise (bespoke)')
      : row('Kaizan cost · ' + r.tier.name + ' tier', gbp0(r.tierPrice / 12) + ' / mo  ·  ' + gbp0(r.tierPrice) + ' / yr')
        + row('Cost per client', gbp0((r.tierPrice / 12) / (s.clients || 1)) + ' / mo')
        + row('Return', r.roiMultiple.toFixed(1) + '×')
        + row('Payback', r.paybackMonths + ' months');
    return '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
      '<title>Kaizan · ROI breakdown</title><style>' +
      '*{box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:#171717;margin:0;padding:40px;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}' +
      '.wrap{max-width:720px;margin:0 auto}.eyebrow{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#9A7B0C;font-weight:700}' +
      'h1{font-size:30px;font-weight:700;letter-spacing:-.02em;margin:6px 0 2px}.sub{color:#57534E;font-size:13px;margin-bottom:24px}' +
      '.bar{background:#141210;color:#fff;border-radius:14px;padding:22px 26px;margin:18px 0}.bar .k{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#FFB900;font-weight:700}' +
      '.bar .n{font-size:40px;font-weight:800;letter-spacing:-.03em;margin-top:4px}' +
      'h2{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#9A7B0C;margin:26px 0 8px}' +
      'table{width:100%;border-collapse:collapse}td{padding:9px 0;border-bottom:1px solid rgba(0,0,0,.1);font-size:14px}td.v{text-align:right;font-weight:700}' +
      '.foot{font-size:11px;color:#777;line-height:1.6;margin-top:24px}.cta{margin-top:22px;font-size:13px}.cta a{color:#9A7B0C;font-weight:700}' +
      '</style></head><body><div class="wrap">' +
      '<div class="eyebrow">Kaizan · ROI breakdown</div>' +
      '<h1>What Kaizan returns on your portfolio</h1>' +
      '<div class="sub">' + esc(s.mode) + ' model · figures in GBP per year</div>' +
      '<div class="bar"><div class="k">' + (r.isCustom ? 'Total annual benefit with Kaizan' : 'Net annual gain with Kaizan') +
        '</div><div class="n">' + gbp0(r.isCustom ? r.gross : r.net) + ' <span style="font-size:16px;font-weight:500;color:rgba(255,255,255,.5)">/ yr</span></div></div>' +
      '<h2>Your client portfolio today</h2><table>' +
        row('Total company headcount', num(s.totalHeadcount)) +
        row('Client delivery team size', num(s.team)) +
        row('Number of clients', num(s.clients)) +
        row('Average annual revenue per client', gbp0(s.revPer)) +
        row('Typical annual client attrition', s.churn + '%') +
        row('Client portfolio value', gbp0(r.portfolio) + ' / yr') +
      '</table>' +
      '<h2>Where the ' + gbp0(r.gross) + ' of annual benefit comes from</h2><table>' +
        row('Revenue retained from churn', gbp0(r.revRetained)) +
        row('Revenue expanded through upsell', gbp0(r.revUpsold)) +
        row('Capacity recovered from admin', gbp0(r.capacity) + '  ·  +' + r.fte.toFixed(1) + ' FTE') +
      '</table>' +
      '<h2>Headline &amp; pricing</h2><table>' + headline + costRows + '</table>' +
      '<div class="cta">Ready to see your clients clearly? <a href="' + DEMO_URL + '">Book a demo →</a></div>' +
      '<div class="foot">' + (q('[data-roi="footnote"]') ? q('[data-roi="footnote"]').textContent : '') +
        ' Satisfaction is shown directionally and never monetised. Generated from your inputs on kaizan.ai.</div>' +
      '</div></body></html>';
  }
  // One-click direct download: build a real PDF with jsPDF and save it (no
  // print dialog). Falls back to the print method if jsPDF didn't load.
  // NB: jsPDF's standard fonts are Latin-1 only — avoid glyphs like "→" here.
  function downloadBreakdown() {
    var JsPDF = window.jspdf && window.jspdf.jsPDF;
    if (!JsPDF) { printBreakdownFallback(); return; }

    var s = state, r = compute(s);
    var doc = new JsPDF({ unit: 'pt', format: 'a4' });
    var PW = doc.internal.pageSize.getWidth();
    var M = 48, RIGHT = PW - M, y = 64;

    var INK = [20, 18, 16], GOLD = [255, 185, 0], MUTE = [87, 83, 78], GOLDD = [154, 123, 12],
        CREAM = [255, 251, 240], GREY = [120, 120, 120], LINE = [225, 225, 225], TXT = [45, 45, 45];
    function tcol(c) { doc.setTextColor(c[0], c[1], c[2]); }
    function fcol(c) { doc.setFillColor(c[0], c[1], c[2]); }
    function dcol(c) { doc.setDrawColor(c[0], c[1], c[2]); }

    doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5); tcol(GOLDD);
    doc.text('KAIZAN  ·  ROI BREAKDOWN', M, y); y += 20;
    doc.setFontSize(21); tcol(INK);
    doc.text('What Kaizan returns on your portfolio', M, y); y += 15;
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10); tcol(MUTE);
    doc.text(s.mode + ' model  ·  figures in GBP per year', M, y); y += 18;

    var barH = 62; fcol(INK); doc.roundedRect(M, y, RIGHT - M, barH, 8, 8, 'F');
    doc.setFont('helvetica', 'bold'); doc.setFontSize(8.5); tcol(GOLD);
    doc.text(r.isCustom ? 'TOTAL ANNUAL BENEFIT WITH KAIZAN' : 'NET ANNUAL GAIN WITH KAIZAN', M + 18, y + 23);
    doc.setFontSize(26); tcol(CREAM);
    doc.text(gbp0(r.isCustom ? r.gross : r.net) + ' / yr', M + 18, y + 48);
    y += barH + 26;

    function section(title) {
      doc.setFont('helvetica', 'bold'); doc.setFontSize(9); tcol(GOLDD);
      doc.text(title.toUpperCase(), M, y); y += 9;
      dcol(INK); doc.setLineWidth(1); doc.line(M, y, RIGHT, y); y += 16;
    }
    function rrow(label, value) {
      doc.setFont('helvetica', 'normal'); doc.setFontSize(10.5); tcol(TXT);
      doc.text(label, M, y);
      doc.setFont('helvetica', 'bold'); tcol(INK);
      doc.text(value, RIGHT, y, { align: 'right' });
      y += 9; dcol(LINE); doc.setLineWidth(0.5); doc.line(M, y, RIGHT, y); y += 15;
    }

    section('Your client portfolio today');
    rrow('Total company headcount', num(s.totalHeadcount));
    rrow('Client delivery team size', num(s.team));
    rrow('Number of clients', num(s.clients));
    rrow('Average annual revenue per client', gbp0(s.revPer));
    rrow('Typical annual client attrition', s.churn + '%');
    rrow('Client portfolio value', gbp0(r.portfolio) + ' / yr');
    y += 8;

    section('Where the ' + gbp0(r.gross) + ' of annual benefit comes from');
    rrow('Revenue retained from churn', gbp0(r.revRetained));
    rrow('Revenue expanded through upsell', gbp0(r.revUpsold));
    rrow('Capacity recovered from admin', gbp0(r.capacity) + '   ·   +' + r.fte.toFixed(1) + ' FTE');
    y += 8;

    section('Headline & pricing');
    rrow(r.isCustom ? 'Total annual benefit' : 'Net annual gain', gbp0(r.isCustom ? r.gross : r.net) + ' / yr');
    if (r.isCustom) {
      rrow('Kaizan tier', 'Enterprise (bespoke)');
    } else {
      rrow('Kaizan cost · ' + r.tier.name + ' tier', gbp0(r.tierPrice / 12) + ' / mo   ·   ' + gbp0(r.tierPrice) + ' / yr');
      rrow('Cost per client', gbp0((r.tierPrice / 12) / (s.clients || 1)) + ' / mo');
      rrow('Return', r.roiMultiple.toFixed(1) + 'x');
      rrow('Payback', r.paybackMonths + ' months');
    }
    y += 10;

    var footEl = q('[data-roi="footnote"]');
    var footText = ((footEl ? footEl.textContent : '') +
      ' Satisfaction is shown directionally and never monetised. Generated from your inputs on kaizan.ai.')
      .replace(/\s+/g, ' ').trim();
    doc.setFont('helvetica', 'normal'); doc.setFontSize(8); tcol(GREY);
    var lines = doc.splitTextToSize(footText, RIGHT - M);
    doc.text(lines, M, y); y += lines.length * 11 + 14;

    doc.setFont('helvetica', 'bold'); doc.setFontSize(10.5); tcol(GOLDD);
    doc.textWithLink('Book a demo', M, y, { url: DEMO_URL });

    doc.save('kaizan-roi-breakdown.pdf');
  }

  // Fallback used only if jsPDF failed to load: print the HTML report to PDF.
  function printBreakdownFallback() {
    var iframe = document.createElement('iframe');
    iframe.setAttribute('aria-hidden', 'true');
    iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;';
    document.body.appendChild(iframe);
    var d = iframe.contentWindow.document;
    d.open(); d.write(buildReportHTML()); d.close();
    var win = iframe.contentWindow;
    win.onafterprint = function () { if (iframe.parentNode) iframe.parentNode.removeChild(iframe); };
    setTimeout(function () { win.focus(); win.print(); }, 300);
  }

  /* ── lead capture (modal → HubSpot form → gated download) ───────────── */
  function wireLead() {
    var modal = q('[data-roi="modal"]');
    var leadBox = q('[data-roi="lead-form"]');
    var sent = q('[data-roi="lead-sent"]');
    var openers = qa('[data-roi="lead-toggle"], [data-roi="lead-toggle-cta"]');
    var closers = qa('[data-roi="modal-close"]');
    var dlBtn = q('[data-roi="download"]');

    function syncLeadUI() {
      show(modal, state.showLead);
      show(leadBox, !state.leadSent);
      show(sent, state.leadSent);
      if (document.body) document.body.classList.toggle('kzroi-body-lock', state.showLead);
    }

    // Build the HubSpot form into the modal target (lazily, on first open, so
    // it renders while visible). Idempotent via the data-built guard.
    function createHubspot(tries) {
      var target = q('#kzroi-hubspot-form');
      if (!target || target.getAttribute('data-built') === '1') return;
      if (!window.hbspt || !window.hbspt.forms) {
        if ((tries || 0) < 40) setTimeout(function () { createHubspot((tries || 0) + 1); }, 150);
        return;
      }
      target.setAttribute('data-built', '1');
      window.hbspt.forms.create({
        portalId: '144688314',
        formId: '5a6fc72e-3835-404c-97eb-fb04aa89cba8',
        region: 'eu1',
        target: '#kzroi-hubspot-form',
        onFormReady: function () {
          decorateHubspotForm(0);
        },
        onFormSubmitted: function () {
          // Step 3 of the flow: email captured → swap the modal to the download view.
          state.leadSent = true;
          syncLeadUI();
        }
      });
    }

    // HubSpot renders the form inside a same-origin iframe (src=""), so neither
    // our external CSS nor a parent-document query reach it. Reach into the
    // iframe to (1) paint the Submit button + focus ring in Kaizan colours and
    // (2) start the email field empty with the cursor in it. Retries until the
    // iframe's form DOM exists.
    function decorateHubspotForm(tries) {
      var iframe = q('#kzroi-hubspot-form iframe');
      var doc = null;
      if (iframe) { try { doc = iframe.contentDocument || iframe.contentWindow.document; } catch (e) { doc = null; } }
      var em = doc && doc.querySelector('input[type="email"], input[name="email"]');
      if (!doc || !em) {
        if ((tries || 0) < 15) setTimeout(function () { decorateHubspotForm((tries || 0) + 1); }, 100);
        return;
      }
      if (!doc.getElementById('kzroi-hs-style')) {
        var st = doc.createElement('style');
        st.id = 'kzroi-hs-style';
        st.textContent =
          '.hs-button,.hs-button.primary,input[type=submit].hs-button{' +
            'background-color:#FFB900!important;border-color:#FFB900!important;color:#141210!important;' +
            'border-radius:999px!important;font-weight:600!important;padding:11px 26px!important;' +
            'box-shadow:none!important;cursor:pointer!important;transition:background-color .15s ease!important;}' +
          '.hs-button:hover,.hs-button.primary:hover{background-color:#FFD133!important;border-color:#FFD133!important;}' +
          '.hs-input:focus{border-color:#FFB900!important;box-shadow:0 0 0 3px #FFF3C4!important;outline:none!important;}';
        (doc.head || doc.documentElement).appendChild(st);
      }
      // Start clean: disable autofill, clear any autofilled value, focus the field.
      em.setAttribute('autocomplete', 'off');
      em.value = '';
      try { em.focus({ preventScroll: true }); } catch (e) { try { em.focus(); } catch (e2) {} }
      // Chrome re-autofills the freshly-rendered field a beat after render, even
      // with autocomplete=off. Keep clearing for a short window, but bail the
      // moment the user actually types or pastes (autofill fires neither).
      if (!em.__kzGuard) {
        em.__kzGuard = true;
        var ticks = 0, stop = false;
        var giveUp = function () { stop = true; };
        em.addEventListener('keydown', giveUp);
        em.addEventListener('paste', giveUp);
        var iv = setInterval(function () {
          if (stop || ++ticks > 8) { clearInterval(iv); return; }
          if (em.value) em.value = '';
        }, 90);
      }
    }

    function openModal() {
      state.showLead = true;
      syncLeadUI();
      createHubspot(0);
      // onFormReady covers the first build; this covers re-opening a built form.
      setTimeout(function () { decorateHubspotForm(0); }, 60);
    }
    function closeModal() { state.showLead = false; syncLeadUI(); }

    openers.forEach(function (t) { t.addEventListener('click', openModal); });
    closers.forEach(function (el) { el.addEventListener('click', closeModal); });
    document.addEventListener('keydown', function (e) {
      if ((e.key === 'Escape' || e.key === 'Esc') && state.showLead) closeModal();
    });

    if (dlBtn) dlBtn.addEventListener('click', downloadBreakdown);

    syncLeadUI();
  }

  /* ── boot ───────────────────────────────────────────────────────────── */
  wireInputs();
  wireToggle();
  wireLead();
  render();
})();
