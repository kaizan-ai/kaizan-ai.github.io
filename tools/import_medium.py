#!/usr/bin/env python3
"""
One-time Medium -> Markdown importer for the Kaizan blog.

Reads the Medium RSS feed (blog.kaizan.ai/feed), which carries the full HTML of
the ~10 most recent posts, and writes each as a draft Markdown post:

    content/blog/<slug>/index.md      (frontmatter + Markdown, draft: true)
    content/blog/<slug>/img-N.ext     (downloaded inline images)

Usage:
    python3 tools/import_medium.py --rss https://blog.kaizan.ai/feed
    python3 tools/import_medium.py --rss https://blog.kaizan.ai/feed --limit 3

Notes:
  * RSS exposes only the most recent ~10 posts. The full back-catalogue needs a
    Medium "Download your information" export (not handled here).
  * Imports land as draft: true with canonical set to the original Medium URL, so
    nothing publishes until a human reviews it and flips draft: false.
  * Stdlib only (urllib, xml.etree, html.parser).
"""

from __future__ import annotations

import argparse
import re
import sys
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / 'content' / 'blog'

CONTENT_NS = '{http://purl.org/rss/1.0/modules/content/}encoded'
DC_CREATOR = '{http://purl.org/dc/elements/1.1/}creator'

UA = 'Mozilla/5.0 (compatible; KaizanBlogImporter/1.0)'
_EXT_FROM_CT = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
                'image/webp': '.webp', 'image/svg+xml': '.svg', 'image/avif': '.avif'}


def slugify(text: str, maxlen: int = 70) -> str:
    text = unescape(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if len(text) > maxlen:
        text = text[:maxlen].rsplit('-', 1)[0]
    return text or 'post'


# ─────────────────────────────────────────────────────────────────────
# HTML -> Markdown (tuned for Medium's content:encoded markup)
# ─────────────────────────────────────────────────────────────────────

class MediumToMarkdown(HTMLParser):
    HEADING = {'h1': '## ', 'h2': '## ', 'h3': '## ', 'h4': '### ', 'h5': '### ', 'h6': '### '}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []        # finished block strings
        self.buf = []           # inline text for the current block
        self.images = []        # list of src URLs encountered, in order
        self.prefix = ''        # block prefix (heading marker / '> ')
        self.list_stack = []    # 'ul' | 'ol' with running counter
        self.in_pre = False
        self.in_fig = False
        self.a_href = None
        self.skip_depth = 0     # inside figcaption/script/style we drop text

    # -- helpers --
    def _flush(self):
        text = ''.join(self.buf).strip()
        self.buf = []
        if text:
            self.blocks.append(self.prefix + text)
        self.prefix = ''

    def _emit(self, s):
        self.buf.append(s)

    # -- tags --
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style', 'figcaption'):
            self.skip_depth += 1
        elif tag in self.HEADING:
            self._flush(); self.prefix = self.HEADING[tag]
        elif tag == 'p':
            self._flush()
        elif tag == 'br':
            self._emit('  \n')
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i'):
            self._emit('*')
        elif tag == 'code' and not self.in_pre:
            self._emit('`')
        elif tag == 'pre':
            self._flush(); self.in_pre = True; self.blocks.append('```');
        elif tag == 'blockquote':
            self._flush(); self.prefix = '> '
        elif tag == 'a':
            self.a_href = a.get('href'); self._emit('[')
        elif tag == 'ul':
            self._flush(); self.list_stack.append(['ul', 0])
        elif tag == 'ol':
            self._flush(); self.list_stack.append(['ol', 0])
        elif tag == 'li':
            self._flush()
            if self.list_stack:
                kind = self.list_stack[-1]
                kind[1] += 1
                self.prefix = '- ' if kind[0] == 'ul' else f'{kind[1]}. '
        elif tag == 'hr':
            self._flush(); self.blocks.append('---')
        elif tag == 'img':
            src = a.get('src') or a.get('data-src')
            if src:
                self.images.append(src)
                alt = (a.get('alt') or '').strip()
                self.blocks.append(f'![{alt}](__IMG_{len(self.images) - 1}__)')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'figcaption'):
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in self.HEADING or tag == 'p' or tag == 'blockquote':
            self._flush()
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag in ('em', 'i'):
            self._emit('*')
        elif tag == 'code' and not self.in_pre:
            self._emit('`')
        elif tag == 'pre':
            self._flush(); self.blocks.append('```'); self.in_pre = False
        elif tag == 'a':
            href = self.a_href or ''
            self._emit(f']({href})')
            self.a_href = None
        elif tag in ('ul', 'ol'):
            self._flush()
            if self.list_stack:
                self.list_stack.pop()
        elif tag == 'li':
            self._flush()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.in_pre:
            # keep code verbatim as its own block line
            self.blocks.append(data.rstrip('\n'))
            return
        text = re.sub(r'\s+', ' ', data)
        if text:
            self._emit(text)

    def result(self):
        self._flush()
        md = '\n\n'.join(b for b in self.blocks if b.strip())
        md = re.sub(r'\n{3,}', '\n\n', md)
        return md.strip(), self.images


def html_to_markdown(html: str):
    parser = MediumToMarkdown()
    parser.feed(html)
    md, images = parser.result()
    # Trim Medium's trailing footer(s) — both the "... was originally published in
    # <pub> on Medium ..." blurb (with its preceding --- rule) and the older
    # "Originally published at ..." form.
    md = re.sub(r'\n+(?:---\s*\n+)?[^\n]*was originally published in[^\n]*on Medium[^\n]*\s*$',
                '', md, flags=re.IGNORECASE)
    md = re.sub(r'\n+_?Originally published at.*$', '', md, flags=re.DOTALL | re.IGNORECASE)
    return md.strip(), images


# ─────────────────────────────────────────────────────────────────────
# Fetch / download
# ─────────────────────────────────────────────────────────────────────

def fetch(url: str) -> bytes:
    req = Request(url, headers={'User-Agent': UA})
    with urlopen(req, timeout=30) as r:
        return r.read(), (r.headers.get('Content-Type') or '')


def download_image(url: str, dest_dir: Path, index: int):
    try:
        data, ctype = fetch(url)
    except (URLError, HTTPError, ValueError) as e:
        print(f"    [img] FAILED {url} ({e})")
        return None
    ext = _EXT_FROM_CT.get(ctype.split(';')[0].strip(), '')
    if not ext:
        m = re.search(r'\.(jpg|jpeg|png|gif|webp|svg|avif)(?:\?|$)', url, re.I)
        ext = ('.' + m.group(1).lower()) if m else '.jpg'
    name = f'img-{index + 1}{ext}'
    (dest_dir / name).write_bytes(data)
    return name


# ─────────────────────────────────────────────────────────────────────
# Main import
# ─────────────────────────────────────────────────────────────────────

def fm_escape(s: str) -> str:
    s = unescape(str(s)).replace('\n', ' ').strip()
    if re.search(r'[:#\[\]{}"]', s) or s.startswith(('-', '@', '&', '*', '!')):
        return '"' + s.replace('"', "'") + '"'
    return s


def import_feed(rss_url: str, limit: int = 0, overwrite: bool = False):
    import xml.etree.ElementTree as ET
    print(f"Fetching {rss_url}")
    raw, _ = fetch(rss_url)
    root = ET.fromstring(raw)
    items = root.findall('./channel/item')
    if limit:
        items = items[:limit]
    print(f"Found {len(items)} posts in feed\n")

    for item in items:
        title = (item.findtext('title') or 'Untitled').strip()
        link = (item.findtext('link') or '').strip()
        creator = (item.findtext(DC_CREATOR) or 'Kaizan').strip()
        pub = item.findtext('pubDate')
        try:
            iso = parsedate_to_datetime(pub).date().isoformat() if pub else ''
        except (TypeError, ValueError):
            iso = ''
        tags = [c.text.strip() for c in item.findall('category') if c.text]
        content_html = item.findtext(CONTENT_NS) or item.findtext('description') or ''

        slug = slugify(title)
        post_dir = CONTENT_DIR / slug
        if post_dir.exists() and not overwrite:
            print(f"SKIP  {slug} (exists; use --overwrite)")
            continue
        post_dir.mkdir(parents=True, exist_ok=True)

        md, image_urls = html_to_markdown(content_html)

        # Download images and substitute the __IMG_n__ placeholders.
        cover = ''
        for i, url in enumerate(image_urls):
            name = download_image(url, post_dir, i)
            if name:
                md = md.replace(f'__IMG_{i}__', name)
                if not cover:
                    cover = name
            else:
                # drop the broken image line
                md = re.sub(r'!\[[^\]]*\]\(__IMG_' + str(i) + r'__\)\n*', '', md)

        # The lead image becomes the post hero (cover); drop its first inline use
        # from the body so it doesn't render twice.
        if cover:
            md = re.sub(r'!\[[^\]]*\]\(' + re.escape(cover) + r'\)\s*\n*', '', md, count=1).strip()

        # First non-empty paragraph -> excerpt.
        excerpt = ''
        for block in md.split('\n\n'):
            b = block.strip()
            if b and not b.startswith(('#', '>', '-', '!', '`')):
                excerpt = re.sub(r'[*`\[\]]|\(https?://[^)]+\)', '', b)
                excerpt = re.sub(r'\s+', ' ', excerpt).strip()[:200]
                break

        fm = [
            '---',
            f'title: {fm_escape(title)}',
            f'date: {iso}',
            f'author: {fm_escape(creator)}',
            'category: POV',
            f'excerpt: {fm_escape(excerpt)}',
        ]
        if cover:
            fm.append(f'cover: {cover}')
        fm.append('draft: true')
        # No canonical: migrated posts are self-canonical to kaizan.ai/blog/<slug>/.
        if tags:
            fm.append('tags: [' + ', '.join(fm_escape(t) for t in tags[:6]) + ']')
        fm.append('---')

        (post_dir / 'index.md').write_text('\n'.join(fm) + '\n\n' + md + '\n', encoding='utf-8')
        print(f"WROTE {slug}  ({len(image_urls)} imgs, {len(md)} chars)")

    print("\nDone. Imported posts are draft: true — review, set draft: false, then build.")


# Standalone Medium UI blocks and trailing footers to scrub from extracted bodies.
_CRUFT_BLOCK = re.compile(
    r'^(--+|Listen|Share|Follow|Follow publication|Sign up|Sign in|Get app|Write|'
    r'Open in app|Member-only story|Published\b.*|\d+\s*min read)$', re.IGNORECASE)
_FOOTER = re.compile(
    r'\n+\*?\s*(Originally published at|Join the Kaizan Community)\b.*$',
    re.IGNORECASE | re.DOTALL)
_MEDIUM_FOOTER = re.compile(
    r'\n+(?:---\s*\n+)?[^\n]*was originally published in[^\n]*on Medium[^\n]*\s*$', re.IGNORECASE)


def make_excerpt(md: str) -> str:
    """First real paragraph, stripped of markup, cut at a word boundary."""
    for block in md.split('\n\n'):
        b = block.strip()
        if b and not b.startswith(('#', '>', '-', '!', '`', '*', '|')):
            e = re.sub(r'\*\*|[*`\[\]]|\(https?://[^)]+\)', '', b)
            e = re.sub(r'\s+', ' ', e).strip()
            if len(e) > 170:
                e = e[:170].rsplit(' ', 1)[0].rstrip(',;:—-') + '…'
            return e
    return ''


def scrub_body(md: str) -> str:
    md = _FOOTER.sub('', md)
    md = _MEDIUM_FOOTER.sub('', md)
    blocks = [b for b in md.split('\n\n') if not _CRUFT_BLOCK.match(b.strip())]
    md = '\n\n'.join(blocks)
    # strip Medium/Kaizan tracking query strings from links
    md = re.sub(r'(\]\(https?://[^)?\s]+)\?[^)\s]*(\))', r'\1\2', md)
    return re.sub(r'\n{3,}', '\n\n', md).strip()


def import_json(path: str, overwrite: bool = False):
    """Import posts extracted in the browser: a JSON list of
    {url,title,date,ogImage,images[],md}. Images download server-side (the
    miro.medium.com CDN is reachable even though post HTML pages 403)."""
    import json
    posts = json.load(open(path, encoding='utf-8'))
    print(f"Importing {len(posts)} extracted posts\n")
    for post in posts:
        title = (post.get('title') or 'Untitled').strip()
        slug = slugify(title)
        post_dir = CONTENT_DIR / slug
        if post_dir.exists() and not overwrite:
            print(f"SKIP  {slug} (exists)"); continue
        post_dir.mkdir(parents=True, exist_ok=True)

        md = post.get('md') or ''
        images = post.get('images') or []
        # download images; map placeholder -> filename (or drop if empty/failed)
        cover = ''
        for i, url in enumerate(images):
            name = download_image(url, post_dir, i) if url else None
            if name:
                md = md.replace(f'__IMG_{i}__', name)
                if not cover:
                    cover = name
            else:
                md = re.sub(r'!\[[^\]]*\]\(__IMG_' + str(i) + r'__\)\s*', '', md)
        # the lead image is the hero (cover) — drop its first inline occurrence
        if cover:
            md = re.sub(r'!\[[^\]]*\]\(' + re.escape(cover) + r'\)\s*', '', md, count=1)

        md = scrub_body(md)

        excerpt = make_excerpt(md)

        fm = ['---', f'title: {fm_escape(title)}', f'date: {post.get("date","")}',
              'category: POV', f'excerpt: {fm_escape(excerpt)}']
        if cover:
            fm.append(f'cover: {cover}')
        fm.append('draft: true')
        fm.append('---')
        (post_dir / 'index.md').write_text('\n'.join(fm) + '\n\n' + md + '\n', encoding='utf-8')
        print(f"WROTE {slug}  (cover={cover or 'none'}, {len(md)} chars)")
    print("\nDone. Review, set draft: false, then build.")


def main():
    ap = argparse.ArgumentParser(description='Import Medium posts into content/blog/.')
    ap.add_argument('--rss', help='Medium RSS feed URL (e.g. https://blog.kaizan.ai/feed)')
    ap.add_argument('--from-json', help='JSON list of browser-extracted posts')
    ap.add_argument('--limit', type=int, default=0, help='Only import the first N posts')
    ap.add_argument('--overwrite', action='store_true', help='Overwrite existing content/blog/<slug>/')
    args = ap.parse_args()
    if args.from_json:
        import_json(args.from_json, overwrite=args.overwrite)
    elif args.rss:
        import_feed(args.rss, limit=args.limit, overwrite=args.overwrite)
    else:
        ap.error('provide --rss or --from-json')


if __name__ == '__main__':
    sys.exit(main())
