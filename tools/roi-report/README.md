# ROI breakdown email report

The A4 PDF report emailed to a prospect after they submit the ROI calculator's
"Email me the breakdown" form (the HubSpot form on `/pricing/`).

- `kaizan-roi-report-template.html` — the template. A serverless function (not in
  this repo) recomputes the figures from the prospect's raw inputs using the same
  model as `assets/js/roi-calculator.js`, substitutes the `{{TOKENS}}` (documented
  in the file's header comment), and renders to PDF with Puppeteer/Playwright
  `page.pdf({ format: 'A4', printBackground: true })`.
- `kaizan-roi-report-SAMPLE.html` — the template with sample values filled in,
  for eyeballing the design in a browser.

These are reference/source assets for that external function — they are not part
of the site build. Keep the tier prices here and in `assets/js/roi-calculator.js`
in sync with the pricing page (`PRICING_TIERS` in `tools/build.py`).
