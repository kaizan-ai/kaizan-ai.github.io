#!/usr/bin/env python3
"""Render each policy version to a branded, print-friendly PDF via headless Chrome.

Not part of the site build (which stays stdlib-only): policy versions are
immutable, so each version's PDF is generated once with this script and
committed alongside the HTML source; tools/build.py just copies it.

Run: python3 tools/policy_pdf.py            (from the repo root)
Skips versions that already have a PDF; --force regenerates everything.
Requires Google Chrome (any recent version) for --print-to-pdf.
"""
import base64
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(tempfile.mkdtemp(prefix='kaizan-policy-pdf-'))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
if not Path(CHROME).exists():
    for cand in ('/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/usr/bin/chromium'):
        if Path(cand).exists():
            CHROME = cand
            break
    else:
        sys.exit('Google Chrome not found — needed for --print-to-pdf.')

POLICIES = [
    ('privacy-policy', 'Privacy Policy'),
    ('license-agreement', 'Licence Agreement'),
    ('cookie-policy', 'Cookie Policy'),
    ('data-processing-agreement', 'Data Processing Agreement'),
]

logo_b64 = base64.b64encode((ROOT / 'assets/img/kaizan-logo.png').read_bytes()).decode()

TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kaizan {title} — {updated}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&display=swap">
<style>
  @page {{ size: A4; margin: 20mm 18mm 22mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
    font-size: 10.5px; line-height: 1.6; color: #111; margin: 0;
    -webkit-print-color-adjust: exact;
  }}
  .doc-head {{
    display: flex; justify-content: space-between; align-items: flex-end;
    padding-bottom: 12px; border-bottom: 3px solid #FFB900; margin-bottom: 28px;
  }}
  .doc-head img {{ height: 22px; }}
  .doc-head .site {{ font-size: 10px; color: #555; }}
  h1 {{ font-size: 26px; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 6px; }}
  .meta {{ font-size: 10px; color: #555; margin-bottom: 26px; }}
  h2 {{ font-size: 13.5px; font-weight: 600; letter-spacing: -0.01em; margin: 22px 0 8px; break-after: avoid; }}
  p {{ margin: 0 0 8px; }}
  .n {{ font-weight: 600; }}
  .kz-clause {{ margin: 0 0 8px; }}
  .kz-clause .kz-clause {{ margin-left: 18px; margin-bottom: 6px; }}
  .kz-clause p {{ margin-bottom: 6px; }}
  ol.kz-plain {{ margin: 0 0 8px; padding-left: 1.5em; }}
  ol.kz-plain li {{ margin-bottom: 6px; }}
  ul {{ margin: 0 0 8px; padding-left: 1.3em; }}
  ul li {{ margin-bottom: 3px; }}
  ul li p {{ margin-bottom: 0; }}
  .kz-tablewrap {{ margin: 4px 0 14px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 9.5px; line-height: 1.5; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #FFF3C4; font-weight: 600; }}
  td p, th p {{ margin-bottom: 5px; }}
  td ol, td ul {{ padding-left: 1.2em; margin: 0 0 5px; }}
  a {{ color: #111; text-decoration: none; }}
  dl.kz-kv {{ margin: 0 0 10px; }}
  dl.kz-kv dt {{ font-weight: 600; margin: 8px 0 2px; }}
  dl.kz-kv dd {{ margin: 0; }}
  .kz-subproc {{ border: 1px solid #ccc; border-radius: 8px;
                padding: 10px 12px 8px; margin: 0 0 8px; break-inside: avoid; }}
  .kz-subproc h3 {{ font-size: 11px; font-weight: 600; margin: 0 0 2px; }}
  .kz-subproc .loc {{ font-weight: 400; font-size: 9px; color: #555; margin-left: 8px; }}
  .kz-subproc dl {{ margin: 4px 0 0; }}
  .kz-subproc dt {{ font-weight: 600; font-size: 8.5px; letter-spacing: .04em;
                   text-transform: uppercase; color: #777; margin-top: 5px; }}
  .kz-subproc dd {{ margin: 0; }}
  .doc-foot {{ margin-top: 32px; padding-top: 10px; border-top: 1px solid #ddd;
              font-size: 9px; color: #777; }}
</style>
</head>
<body>
<div class="doc-head">
  <img src="data:image/png;base64,{logo}" alt="Kaizan">
  <div class="site">kaizan.ai</div>
</div>
<h1>{title}</h1>
<div class="meta">Kaizan Limited &nbsp;·&nbsp; Last updated {updated} &nbsp;·&nbsp; kaizan.ai/{slug}/</div>
{body}
<div class="doc-foot">© Kaizan Ltd. &nbsp;·&nbsp; Kaizan Limited is registered in England and Wales, company number 13082820.
This document was published at kaizan.ai/{slug}/ and is the version last updated {updated}.</div>
</body>
</html>
'''


def nice_date(iso):
    d = date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%B %Y")}'


for slug, title in POLICIES:
    for src in sorted((ROOT / 'content/policies' / slug).glob('????-??-??.html')):
        if src.with_suffix('.pdf').exists() and '--force' not in sys.argv:
            print(f'{src.with_suffix(".pdf")} exists, skipping (use --force to regenerate)')
            continue
        html = TEMPLATE.format(logo=logo_b64, title=title, slug=slug,
                               updated=nice_date(src.stem), body=src.read_text())
        page = OUT / f'{slug}-{src.stem}.html'
        page.write_text(html)
        pdf = src.with_suffix('.pdf')
        r = subprocess.run([CHROME, '--headless', '--disable-gpu',
                            '--no-pdf-header-footer', '--virtual-time-budget=8000',
                            f'--print-to-pdf={pdf}', page.as_uri()],
                           capture_output=True, text=True, timeout=120)
        ok = pdf.exists() and pdf.stat().st_size > 10000
        print(f'{pdf} {"OK" if ok else "FAILED"} ({pdf.stat().st_size if pdf.exists() else 0} bytes)')
        if not ok:
            print(r.stderr[-2000:])
            sys.exit(1)
