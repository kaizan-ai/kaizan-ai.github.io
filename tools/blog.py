#!/usr/bin/env python3
"""
Blog content pipeline for the Kaizan site.

Posts are authored as Markdown with frontmatter at:
    content/blog/<slug>/index.md
with images colocated in the same folder. This module loads those files,
parses the frontmatter, converts the Markdown body to HTML, and returns post
dicts in the shape that build.py's render_blog_post / render_blog_index expect.

Markdown -> HTML uses the vendored, stdlib-only tools/markdown2.py.

Authors never compute relative paths: they write `![alt](photo.jpg)` and drop
photo.jpg next to index.md. At build time copy_post_images() copies the files to
assets/img/blog/<slug>/ and md_to_html() rewrites the <img> src to the correct
depth-3 path (../../../assets/img/blog/<slug>/photo.jpg).
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import markdown2  # vendored single-file lib (tools/markdown2.py)

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / 'content' / 'blog'
IMG_OUT_DIR = ROOT / 'assets' / 'img' / 'blog'

# Allowed editorial categories (shown as the card/eyebrow label).
CATEGORIES = ['POV', 'PRODUCT', 'FIELD NOTES', 'BENCHMARK', 'INTERVIEW', 'CUSTOMER STORY']

# Allowed topics (the URL segment: /blog/<topic>/<slug>/) with their display label
# and a one-line description used on the topic landing page.
TOPICS = {
    'client-health': ('Client health',
                      'Spot churn risk early and keep client relationships healthy: signals, metrics and real-world examples.'),
    'client-software': ('Client software',
                        'The tools, data and systems behind client service, and how to choose, build and connect them.'),
    'playbooks-and-templates': ('Playbooks and templates',
                                'Practical how-to guides, frameworks and templates for client service and account teams.'),
    'agency-profitability': ('Agency profitability',
                             'Protect revenue, save time and grow margin across your client portfolio.'),
    'ai-for-client-service': ('AI for client service',
                              'How client service and account teams are using AI today, and what is coming next.'),
    'qa': ('Q&A',
           'Conversations with client service leaders about AI, retention and building great client teams.'),
}

MARKDOWN_EXTRAS = ['fenced-code-blocks', 'tables', 'cuddled-lists', 'strike', 'footnotes']

_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December']

_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.avif'}


# ─────────────────────────────────────────────────────────────────────
# Frontmatter
# ─────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _coerce(value: str):
    """Coerce a frontmatter scalar: bools, [list], or stripped string."""
    v = value.strip()
    if v.startswith('[') and v.endswith(']'):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"\'') for item in inner.split(',') if item.strip()]
    low = v.lower()
    if low in ('true', 'yes'):
        return True
    if low in ('false', 'no'):
        return False
    # strip matching surrounding quotes
    if len(v) >= 2 and v[0] == v[-1] and v[0] in '"\'':
        v = v[1:-1]
    return v


def parse_frontmatter(text: str):
    """Return (meta: dict, body_md: str). Frontmatter is a leading --- ... --- block."""
    text = text.lstrip('﻿')  # strip BOM if present
    if not text.startswith('---'):
        return {}, text
    # Match the first fenced block: ---\n ... \n---
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    meta = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        meta[key.strip()] = _coerce(value)
    return meta, body


def format_date(iso: str) -> str:
    """ '2026-05-02' -> '2 May 2026'. Returns the input unchanged if unparseable."""
    if not iso:
        return ''
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', str(iso))
    if not m:
        return str(iso)
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= month <= 12):
        return str(iso)
    return f"{day} {_MONTHS[month - 1]} {year}"


# ─────────────────────────────────────────────────────────────────────
# Markdown -> HTML
# ─────────────────────────────────────────────────────────────────────

def _img_v(path: Path) -> str:
    """"?v=<hash8>" from the image's content, so browsers refetch a replaced image."""
    import hashlib
    if not path.is_file():
        return ''
    return '?v=' + hashlib.md5(path.read_bytes()).hexdigest()[:8]


def _rewrite_img(match: re.Match, slug: str) -> str:
    """Rewrite a bare/relative <img src> to the depth-3 blog asset path and lazy-load it."""
    tag = match.group(0)
    src_m = re.search(r'src="([^"]*)"', tag)
    if not src_m:
        return tag
    src = src_m.group(1)
    if not re.match(r'^(https?:|data:|/|\.\./)', src):
        name = src.lstrip('./')
        new_src = f"../../../assets/img/blog/{slug}/{name}{_img_v(CONTENT_DIR / slug / name)}"
        tag = tag.replace(f'src="{src}"', f'src="{new_src}"')
    if 'loading=' not in tag:
        tag = tag.replace('<img', '<img loading="lazy" decoding="async"', 1)
    return tag


_CALLOUT_H2 = re.compile(r'^(the short (answer|version)|key takeaways|tl;?dr|in short)\b', re.I)
_FAQ_H2 = re.compile(r'\b(frequently asked questions|faqs?)\s*$', re.I)


def _h2_text(h2: str) -> str:
    return re.sub(r'<[^>]+>', '', h2).strip()


_SEQ = r'(?:Day|Days|Week|Weeks|Month|Months|Step|Stage|Phase|Minute|Quarter)\s[-\d][^<:.]{0,12}'
_DAY_RUN = re.compile(r'(?:<p><strong>%s\.</strong>.*?</p>\s*){3,}' % _SEQ, re.S)
_STEP_H3 = re.compile(r'<h3>(%s)[:.]\s*(.*?)</h3>' % _SEQ, re.S)


def _flows(html: str) -> str:
    """Turn sequences into a scroll-animated timeline (.kz-flow, driven by blog-post.js):
    3+ paragraphs led by "**Day 6.**"-style labels, and 3+ consecutive "### Step 1: …" sections."""
    def day_run(m):
        items = re.findall(r'<p><strong>(%s)\.</strong>\s*(.*?)</p>' % _SEQ, m.group(0), re.S)
        lis = ''.join(f'<li class="kz-flow-item"><span class="kz-flow-label">{lab}</span>'
                      f'<div class="kz-flow-card"><p>{txt}</p></div></li>' for lab, txt in items)
        return f'<ol class="kz-flow" data-flow>{lis}</ol>\n'
    html = _DAY_RUN.sub(day_run, html)

    chunks = re.split(r'(?=<h[23][ >])', html)
    out, run = [], []

    def flush():
        if len(run) >= 3:
            items = ''
            for c in run:
                m = _STEP_H3.match(c)
                items += (f'<li class="kz-flow-item"><span class="kz-flow-label">{m.group(1)}</span>'
                          f'<div class="kz-flow-step"><h3>{m.group(2)}</h3>{c[m.end():].strip()}</div></li>')
            out.append(f'<ol class="kz-flow kz-flow-steps" data-flow>{items}</ol>\n')
        else:
            out.extend(run)
        run.clear()

    for c in chunks:
        if _STEP_H3.match(c):
            run.append(c)
        else:
            flush()
            out.append(c)
    flush()
    return ''.join(out)


def _cards(section: str) -> str:
    """Inside one h2 section, 3+ h3 sub-sections become numbered cards (.kz-cards)."""
    if 'kz-flow-steps' in section:
        return section  # its h3s are already timeline steps
    for t in re.findall(r'<table>(.*?)</table>', section, re.S):
        if len(re.findall(r'<th\b', t.split('</tr>', 1)[0])) >= 5:
            return section  # a many-column table needs the full width, not a card
    chunks = re.split(r'(?=<h3[ >])', section)
    head, subs = chunks[0], chunks[1:]
    if len(subs) < 3:
        return section
    cards = ''.join(
        f'<li class="kz-card"><span class="kz-card-n">{n:02d}</span>{c.strip()}</li>'
        for n, c in enumerate(subs, 1))
    return f'{head}<ol class="kz-cards">{cards}</ol>\n'


_STAT = re.compile(r'(?<![\w$£€.])(\d+(?:\.\d+)?(?:%|x\b|×)(?:\+)?)')


def _stats(html: str) -> str:
    """Highlight figures like 69%, 2.5x in body paragraphs and list items (not links, code or tables)."""
    def in_block(m):
        parts = re.split(r'(<[^>]+>)', m.group(0))
        depth = 0
        for i, p in enumerate(parts):
            if p.startswith('<'):
                if re.match(r'<(a|code)\b', p):
                    depth += 1
                elif re.match(r'</(a|code)>', p):
                    depth -= 1
            elif depth == 0:
                parts[i] = _STAT.sub(r'<mark class="kz-stat">\1</mark>', p)
        return ''.join(parts)
    # Leave tables and preformatted blocks alone.
    pieces = re.split(r'(<table>.*?</table>|<pre>.*?</pre>)', html, flags=re.S)
    for i in range(0, len(pieces), 2):
        pieces[i] = re.sub(r'<(p|li)\b[^>]*>.*?</\1>', in_block, pieces[i], flags=re.S)
    return ''.join(pieces)


LOGO_DIR = ROOT / 'assets' / 'img' / 'logos'
# Tool name (as written in a table) -> logo file in assets/img/logos/.
_LOGOS = {
    'Kaizan': '../kaizan-icon.png', 'HubSpot': 'hubspot.svg', 'Salesforce': 'salesforce.svg',
    'Pipedrive': 'pipedrive.png', 'Zoho CRM': 'zoho-crm.svg', 'monday.com': 'monday.svg',
    'monday CRM': 'monday.svg', 'SuiteDash': 'suitedash.svg', 'Moxo': 'moxo.svg',
    'Productive': 'productive.svg', 'Scoro': 'scoro.svg', 'Gainsight': 'gainsight.svg',
    'Planhat': 'planhat.svg', 'ChurnZero': 'churnzero.png', 'Vitally': 'vitally.svg',
    'Totango': 'totango.svg', 'Odie': 'odie.svg', 'AgencyAnalytics': 'agencyanalytics.svg',
    'Looker Studio': 'looker.svg', 'Databox': 'databox.svg', 'Swydo': 'swydo.svg',
    'DashThis': 'dashthis.svg', 'Whatagraph': 'whatagraph.svg', 'ClientSuccess': 'clientsuccess.svg',
    'Notion': 'notion.svg', 'Asana': 'asana.svg', 'ClickUp': 'clickup.svg', 'Wrike': 'wrike.svg',
    'Airtable': 'airtable.svg', 'Slack': 'slack.svg', 'Teamwork': 'teamwork.svg', 'Jira': 'jira.svg',
    'Rocketlane': 'rocketlane.svg', 'GUIDEcx': 'guidecx.svg', 'Typeform': 'typeform.svg',
    'Content Snare': 'content-snare.svg', 'Qualtrics': 'qualtrics.svg', 'Gong': 'gong.svg',
    'Fathom': 'fathom.svg', 'Otter': 'otter.svg', 'Fireflies': 'fireflies.svg', 'Zapier': 'zapier.svg',
    'Make': 'make.svg', 'Float': 'float.svg', 'Harvest': 'harvest.svg', 'Toggl': 'toggl.svg',
    'Xero': 'xero.svg', 'QuickBooks': 'quickbooks.svg', 'Kantata': 'kantata.svg', 'Deltek': 'deltek.svg',
    'Accelo': 'accelo.svg', 'Workamajig': 'workamajig.svg', 'Figma': 'figma.svg', 'Canva': 'canva.svg',
    'Dock': 'dock.svg', 'ChatGPT': 'chatgpt.svg', 'Claude': 'claude.svg', 'Gemini': 'gemini.png',
    'Microsoft Teams': 'microsoft-teams.svg', 'Zoom': 'zoom.svg', 'Gmail': 'gmail.svg',
    'Outlook': 'outlook.svg', 'Google Drive': 'google-drive.svg', 'SharePoint': 'sharepoint.svg',
}


def _logo_ratio(path: Path) -> float:
    """Width / height of a logo, from its SVG viewBox or PNG header."""
    data = path.read_bytes()
    if path.suffix == '.png':
        import struct
        w, h = struct.unpack('>II', data[16:24])
        return w / h
    m = re.search(rb'viewBox="([^"]+)"', data)
    v = [float(x) for x in re.split(r'[ ,]+', m.group(1).decode().strip())]
    return v[2] / v[3]


def _logo_cell(cell_html: str) -> str:
    """If a table cell starts with a known tool name, put its logo in front.
    Wordmark logos (wide) replace the name; icon logos sit beside it."""
    text = re.sub(r'<[^>]+>', '', cell_html).strip()
    if len(text) > 40:
        return cell_html
    for name in sorted(_LOGOS, key=len, reverse=True):
        if re.match(re.escape(name) + r'(?![\w.])', text, re.I):
            path = (LOGO_DIR / _LOGOS[name]).resolve()
            if not path.is_file():
                return cell_html
            src = '../../../assets/img/' + str(path.relative_to(ROOT / 'assets' / 'img'))
            rest = text[len(name):].strip()
            rest_html = f'<span class="kz-tl-note">{rest}</span>' if rest else ''
            if _logo_ratio(path) >= 2:
                logo = f'<img class="kz-tl-wm" src="{src}" alt="{text[:len(name)]}">'
            else:
                logo = f'<img class="kz-tl-icon" src="{src}" alt="">{text[:len(name)]}'
            return f'<span class="kz-tl">{logo}</span>{rest_html}'
    return cell_html


def _tables(html: str) -> str:
    """Logos in the first column and header row; flag the Kaizan row and column."""
    def table(m):
        t = m.group(0)
        t = re.sub(r'(<tr>\s*<td[^>]*>)(.*?)(</td>)', lambda c: c.group(1) + _logo_cell(c.group(2)) + c.group(3), t, flags=re.S)
        t = re.sub(r'(<th[^>]*>)(.*?)(</th>)', lambda c: c.group(1) + _logo_cell(c.group(2)) + c.group(3), t, flags=re.S)
        t = re.sub(r'<tr>(\s*<td[^>]*><span class="kz-tl"><img[^>]*kaizan-icon)', r'<tr class="kz-row-kaizan">\1', t)
        t = re.sub(r'<tr>(\s*<td[^>]*>\s*Kaizan\b)', r'<tr class="kz-row-kaizan">\1', t)
        t = re.sub(r'<th([^>]*)>(<span class="kz-tl"><img[^>]*>Kaizan)', r'<th\1 class="kz-th-kaizan">\2', t)
        heads = re.findall(r'<th\b[^>]*>', t)
        col = next((i for i, h in enumerate(heads) if 'kz-th-kaizan' in h), None)
        if col is not None:
            def row(r):
                n = [-1]
                def cell(c):
                    n[0] += 1
                    return '<td class="kz-col-kaizan"' if n[0] == col else c.group(0)
                return re.sub(r'<td(?=[\s>])', cell, r.group(0))
            t = re.sub(r'<tr\b[^>]*>.*?</tr>', row, t, flags=re.S)
        return t
    return re.sub(r'<table>.*?</table>', table, html, flags=re.S)


def _faq_items(section: str) -> str:
    """FAQ questions as the site's accordion (<details class="kz-faq-item">, styled in
    site.css/resources.css). A question is an <h3>, or a paragraph led by a bold "...?";
    everything up to the next question is its answer."""
    m = re.match(r'(<h2[^>]*>.*?</h2>)(.*)', section, re.S)
    if not m:
        return section
    head, body = m.group(1), m.group(2)
    blocks = [b.group(0) for b in re.finditer(r'<(h3|p|ul|ol|blockquote|div|table|pre)\b.*?</\1>', body, re.S)]
    intro, items, outro = [], [], []
    for b in blocks:
        q = re.match(r'<h3[^>]*>(.*?)</h3>$', b, re.S)
        if q:
            items.append([q.group(1).strip(), []])
            continue
        q = re.match(r'<p>\s*<strong>([^<]*\?)</strong>\s*(.*)</p>$', b, re.S)
        if q:
            items.append([q.group(1).strip(), [f'<p>{q.group(2).strip()}</p>'] if q.group(2).strip() else []])
            continue
        if items and re.match(r'<p>\s*<em>.*</em>\s*</p>$', b, re.S):
            outro.append(b)  # an italic source note closes the section, not the last answer
            continue
        (items[-1][1] if items else intro).append(b)
    if len(items) < 2:
        return section
    acc = ''.join(
        f'<details class="kz-faq-item"><summary><h3>{q}</h3><span class="ic" aria-hidden="true">+</span>'
        f'</summary><div class="kz-faq-a">{"".join(a)}</div></details>' for q, a in items)
    return head + ''.join(intro) + acc + ''.join(outro)


PEOPLE_DIR = ROOT / 'assets' / 'img' / 'people' / 'quotes'


def _quotes(html: str) -> str:
    """Quotes signed "— Name, Title, Company": the attribution becomes a caption, and a
    named person with a headshot in assets/img/people/quotes/<name-slug>.jpg gets a quote card."""
    def quote(m):
        q = m.group(0)
        sig = re.search(r'\s*<p>\s*(?:—|&#8212;|&mdash;)\s*(.*?)</p>\s*</blockquote>$', q, re.S)
        if not sig:
            return q
        body = q[:sig.start()].replace('<blockquote>', '', 1).strip()
        who = sig.group(1).strip()
        name, _, role = who.partition(',')
        photo = PEOPLE_DIR / f'{slugify(name)}.jpg'
        if photo.is_file():
            src = f'../../../assets/img/people/quotes/{photo.name}{_img_v(photo)}'
            return (f'<figure class="kz-quote-card"><blockquote>{body}</blockquote>'
                    f'<figcaption><img class="kz-qc-photo" src="{src}" alt="{name.strip()}" loading="lazy">'
                    f'<span><strong>{name.strip()}</strong><span>{role.strip()}</span></span></figcaption></figure>')
        return f'<blockquote>{body}<p class="kz-quote-by">{who}</p></blockquote>'
    return re.sub(r'<blockquote>.*?</blockquote>', quote, html, flags=re.S)


def _emails(html: str) -> str:
    """Script blocks that start with "Subject:" render as an email (subject line, body in the
    normal font, [placeholders] marked); any other preformatted block becomes a light card."""
    def block(m):
        inner = re.sub(r'</?code[^>]*>', '', m.group(1)).strip('\n')
        ph = lambda t: re.sub(r'\[([^\]\n]{1,60})\]', r'<span class="kz-ph">[\1]</span>', t)
        sm = re.match(r'Subject:\s*(.*?)\n(.*)$', inner, re.S)
        if not sm:
            return f'<div class="kz-snippet">{inner}</div>'
        return ('<div class="kz-email"><div class="kz-email-bar"><span class="kz-email-dots"><i></i><i></i><i></i></span>'
                '<span>New message</span></div>'
                f'<div class="kz-email-subj"><span class="kz-email-k">Subject</span>{ph(sm.group(1).strip())}</div>'
                f'<div class="kz-email-body">{ph(sm.group(2).strip())}</div></div>')
    return re.sub(r'<pre>(.*?)</pre>', block, html, flags=re.S)


def _decorate(html: str) -> str:
    """Make long posts easier on the eye: a lede, sequences as timelines, sub-sections as
    cards, highlighted figures, pale summary/FAQ panels, and tables that scroll on phones."""
    html = re.sub(r'^\s*<p>', '<p class="kz-lede-p">', html, count=1)
    html = _emails(html)
    html = _flows(html)
    html = _quotes(html)
    html = _stats(html)
    secs = re.split(r'(?=<h2[ >])', html)
    for i, s in enumerate(secs):
        m = re.match(r'(<h2[^>]*>.*?</h2>)', s, re.S)
        title = _h2_text(m.group(1)) if m else ''
        if not (_FAQ_H2.search(title) or _CALLOUT_H2.match(title)):
            secs[i] = _cards(s)
    html = ''.join(secs)
    # "**Key takeaways**" followed by a list -> a callout panel.
    html = re.sub(
        r'<p><strong>(Key takeaways|The short answer:?|In short:?)</strong></p>\s*(<(ul|ol)>.*?</\3>)',
        lambda m: f'<div class="kz-callout"><p class="kz-callout-label">{m.group(1).rstrip(":")}</p>{m.group(2)}</div>',
        html, flags=re.S)
    # An h2 section (heading up to the next h2) -> callout or FAQ panel.
    parts = re.split(r'(?=<h2[ >])', html)
    for i, part in enumerate(parts):
        m = re.match(r'(<h2[^>]*>.*?</h2>)(.*)', part, re.S)
        if not m:
            continue
        title = _h2_text(m.group(1))
        if _CALLOUT_H2.match(title):
            parts[i] = f'<section class="kz-callout">{part.strip()}</section>\n'
        elif _FAQ_H2.search(title):
            # A closing line after an <hr> belongs to the post, not the FAQ.
            faq, hr, rest = part.partition('<hr')
            parts[i] = f'<section class="kz-faq">{_faq_items(faq.strip())}</section>\n' + (hr + rest if hr else '')
    html = ''.join(parts)
    html = _tables(html)
    def wrap(m):
        cols = len(re.findall(r'<th\b', m.group(1).split('</tr>', 1)[0]))
        cls = 'kz-table kz-table-wide' if cols >= 5 else 'kz-table'
        return f'<div class="{cls}"><table>{m.group(1)}</table></div>'
    html = re.sub(r'<table>(.*?)</table>', wrap, html, flags=re.S)
    return html


def image_text_html(slug: str, image_name: str) -> str:
    """The "Show text in this graphic" dropdown for an image, from <image>.text.md beside it
    in the post folder: the graphic's words as real page text people can copy and bots can read."""
    src = CONTENT_DIR / slug / (Path(image_name).stem + '.text.md')
    if not src.is_file():
        return ''
    inner = str(markdown2.markdown(src.read_text(encoding='utf-8'), extras=MARKDOWN_EXTRAS)).strip()
    return ('<details class="kz-imgtext"><summary><span>Show text in this graphic</span>'
            '<span class="ic" aria-hidden="true">+</span></summary>'
            f'<div class="kz-imgtext-body">{inner}</div></details>')


def _image_texts(html: str, slug: str, held: list) -> str:
    """Put a placeholder for each standalone image's text dropdown straight after it. The
    dropdown itself is held back and put in after _decorate, so it stays plain text (no logo
    pills, cards or highlights from the post-body treatment)."""
    def add(m):
        name = re.search(r'/assets/img/blog/[^/]+/([^"?]+)', m.group(0))
        dropdown = image_text_html(slug, name.group(1)) if name else ''
        if not dropdown:
            return m.group(0)
        held.append(dropdown)
        return m.group(0) + f'<!--kz-imgtext-{len(held) - 1}-->'
    return re.sub(r'<p>\s*<img\b[^>]*>\s*</p>', add, html)


def md_to_html(body_md: str, slug: str) -> str:
    html = markdown2.markdown(body_md, extras=MARKDOWN_EXTRAS)
    html = re.sub(r'<img\b[^>]*>', lambda m: _rewrite_img(m, slug), html)
    held = []
    html = _image_texts(str(html), slug, held)
    html = _decorate(html)
    html = re.sub(r'<!--kz-imgtext-(\d+)-->', lambda m: held[int(m.group(1))], html)
    return html.strip()


# ─────────────────────────────────────────────────────────────────────
# Load + images
# ─────────────────────────────────────────────────────────────────────

def _cover_asset(slug: str, meta: dict, post_dir: Path):
    """Return the cover path relative to assets/img/ (e.g. 'blog/<slug>/cover.jpg'),
    or None to let the renderer fall back to a generated gradient."""
    cover = meta.get('cover')
    if cover and (post_dir / cover).exists():
        return f"blog/{slug}/{cover}"
    return None


def _load_schema_nodes(post_dir) -> list:
    """Optional hand-authored JSON-LD @graph nodes for a post (schema.jsonld beside index.md).
    URL tokens (@@PAGE@@, @@ROOT@@) and the language token are resolved per locale at build time."""
    f = post_dir / 'schema.jsonld'
    if not f.is_file():
        return []
    try:
        return json.loads(f.read_text(encoding='utf-8')).get('@graph', [])
    except ValueError as e:
        print(f"  [blog] WARN {post_dir.name}: schema.jsonld is not valid JSON ({e})")
        return []


def load_posts(include_drafts: bool = False) -> list:
    """Load all posts from content/blog/*/index.md, newest first.

    Each returned dict has: slug, title, excerpt, author, category, iso_date,
    date (display), cover_asset (path under assets/img/ or None), body (HTML),
    canonical, tags, draft. Shape is compatible with build.py's blog renderers.
    """
    posts = []
    if not CONTENT_DIR.is_dir():
        return posts
    for md_path in sorted(CONTENT_DIR.glob('*/index.md')):
        slug = md_path.parent.name
        meta, body_md = parse_frontmatter(md_path.read_text(encoding='utf-8'))
        draft = bool(meta.get('draft', True))
        if draft and not include_drafts:
            continue

        # `author` is optional — bylines are not shown on the blog.
        missing = [k for k in ('title', 'date', 'category', 'excerpt') if not meta.get(k)]
        if missing:
            print(f"  [blog] WARN {slug}: missing frontmatter {missing}")
        topic = str(meta.get('topic', ''))
        if topic not in TOPICS:
            print(f"  [blog] WARN {slug}: topic '{topic}' not in {list(TOPICS)}")
        category = str(meta.get('category', 'POV')).upper()
        if category not in CATEGORIES:
            print(f"  [blog] WARN {slug}: category '{category}' not in {CATEGORIES}")

        iso = str(meta.get('date', ''))
        posts.append(dict(
            slug=slug,
            topic=topic,
            title=meta.get('title', slug.replace('-', ' ').title()),
            excerpt=meta.get('excerpt', ''),
            meta_title=meta.get('meta_title', ''),
            meta_description=meta.get('meta_description', ''),
            schema=bool(meta.get('schema', not meta.get('canonical'))),
            date_modified=str(meta.get('date_modified', '')),
            keywords=meta.get('keywords', []) if isinstance(meta.get('keywords', []), list) else [meta.get('keywords')],
            meta_author=str(meta.get('meta_author', '')),
            schema_nodes=_load_schema_nodes(md_path.parent),
            author=meta.get('author', 'Kaizan'),
            category=category,
            iso_date=iso,
            date=format_date(iso),
            cover_asset=_cover_asset(slug, meta, md_path.parent),
            body=md_to_html(body_md, slug),
            canonical=meta.get('canonical', ''),
            tags=meta.get('tags', []),
            draft=draft,
        ))
    posts.sort(key=lambda p: p['iso_date'], reverse=True)
    return posts


def copy_post_images(slug: str) -> None:
    """Copy colocated images from content/blog/<slug>/ to assets/img/blog/<slug>/."""
    src_dir = CONTENT_DIR / slug
    if not src_dir.is_dir():
        return
    out_dir = IMG_OUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in src_dir.iterdir():
        if f.is_file() and f.suffix.lower() in _IMG_EXTS:
            shutil.copy2(f, out_dir / f.name)
