# Legal policies — versioned source

Each folder is one policy; each file inside is one **version** of that policy,
named by the date it took effect: `YYYY-MM-DD.html`, with an optional matching
`YYYY-MM-DD.pdf` (the downloadable copy — versions are immutable, so the PDF is
generated once and committed, keeping the site build dependency-free). The
build (`tools/build.py`, see `POLICIES`) renders:

- the **newest** file → the live page (`/privacy-policy/`, `/license-agreement/`,
  `/cookie-policy/`),
- every **older** file → a dated archive page (`/privacy-policy/2023-01-15/`, …),
  linked from the "Version history" section at the bottom of each policy page.
  Archived versions get a banner pointing readers at the current one and are
  `noindex` for search engines, and
- every `YYYY-MM-DD.pdf` → a "Download PDF" button on that version's page
  (published as `/<slug>/kaizan-<slug>-<date>.pdf`).

## Publishing a new version

1. Copy the current newest file to a new file named with today's date
   (e.g. `cp 2025-10-01.html 2026-08-05.html`).
2. Edit the new file. **Never edit or delete an old version** — the whole point
   is that readers can see exactly what the policy said on a given date.
3. Generate the matching PDF: `python3 tools/policy_pdf.py` (uses headless
   Chrome with a branded A4 print template; skips versions that already have
   a PDF).
4. `python3 tools/build.py` and open a PR (content PRs contain only `content/**`).

## Format

The files are plain HTML fragments (no `<html>`/`<head>`), hand-editable:

- `<h2>` — unnumbered document headings (BACKGROUND, CONTACT US, …)
- `<section class="kz-sec">` — one numbered section; its `<h2>` carries the
  section number in `<span class="n">1.</span>`
- `<div class="kz-clause">` — one numbered clause; nests for sub-clauses;
  the number lives in `<span class="n">1.1</span>` at the start of the first `<p>`
- `<ol class="kz-plain">` — preliminary lists (parties, recitals)
- tables and `<ul>` lists are plain HTML

Numbers are written literally in the markup (not CSS counters), so keep them in
sequence when adding or removing clauses.

These fragments were originally imported from the Intercom help-centre articles
in August 2026; the version dates are Intercom's "last modified" dates.
