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
depth-2 path (../../assets/img/blog/<slug>/photo.jpg).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import markdown2  # vendored single-file lib (tools/markdown2.py)

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / 'content' / 'blog'
IMG_OUT_DIR = ROOT / 'assets' / 'img' / 'blog'

# Allowed editorial categories (shown as the card/eyebrow label).
CATEGORIES = ['POV', 'PRODUCT', 'FIELD NOTES', 'BENCHMARK', 'INTERVIEW', 'CUSTOMER STORY']

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

def _rewrite_img(match: re.Match, slug: str) -> str:
    """Rewrite a bare/relative <img src> to the depth-2 blog asset path and lazy-load it."""
    tag = match.group(0)
    src_m = re.search(r'src="([^"]*)"', tag)
    if not src_m:
        return tag
    src = src_m.group(1)
    if not re.match(r'^(https?:|data:|/|\.\./)', src):
        new_src = f"../../assets/img/blog/{slug}/{src.lstrip('./')}"
        tag = tag.replace(f'src="{src}"', f'src="{new_src}"')
    if 'loading=' not in tag:
        tag = tag.replace('<img', '<img loading="lazy" decoding="async"', 1)
    return tag


def md_to_html(body_md: str, slug: str) -> str:
    html = markdown2.markdown(body_md, extras=MARKDOWN_EXTRAS)
    html = re.sub(r'<img\b[^>]*>', lambda m: _rewrite_img(m, slug), html)
    return str(html).strip()


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
        category = str(meta.get('category', 'POV')).upper()
        if category not in CATEGORIES:
            print(f"  [blog] WARN {slug}: category '{category}' not in {CATEGORIES}")

        iso = str(meta.get('date', ''))
        posts.append(dict(
            slug=slug,
            title=meta.get('title', slug.replace('-', ' ').title()),
            excerpt=meta.get('excerpt', ''),
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
