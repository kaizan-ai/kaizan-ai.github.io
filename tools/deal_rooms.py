#!/usr/bin/env python3
"""
Private sales deal rooms: kaizan.ai/room/<slug>/.

One template (content/deal-rooms/template.html) and one shared config
(content/deal-rooms/shared.json: videos, case studies, IT documents, the mutual
action plan) are combined with a small per-prospect file,
content/deal-rooms/rooms/<slug>.json, to build each room.

The <slug> is the prospect's name plus a random code (made by `new`), so rooms
cannot be guessed. Rooms are noindex, carry no canonical, are never linked from
the site and are skipped by the sitemap. Delete a room's file to take it down on
the next build.

    python3 tools/deal_rooms.py new "Acme Agency"   # creates rooms/acme-agency-<code>.json
"""

from __future__ import annotations

import json
import re
import secrets
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'content' / 'deal-rooms'
OUT = ROOT / 'room'
# Rooms may set "path" to publish at a top-level address instead, e.g. "demo-room" -> /demo-room/.
# Removing such a room leaves its folder behind: delete that folder in the same PR.
TOP_LEVEL = 'path'

# Per-prospect fields, with the defaults a new room file starts from.
ROOM_FIELDS = {
    'prospect': '',
    'ae': '',
    'aeEmail': 'hello@kaizan.ai',
    'bookingUrl': '',
    'problem': '',
    'toldUs': [{'q': '', 't': ''}, {'q': '', 't': ''}, {'q': '', 't': ''}],
    'targetNumber': '',
    'targetLabel': 'Growth from existing clients you want by Q4',
    'callRecordingUrl': '',
    'priceBand': '',
    'mapDates': ['', '', '', '', '', '', ''],
    'draft': True,
}


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def _deal(room: dict) -> dict:
    deal = json.loads((SRC / 'shared.json').read_text(encoding='utf-8'))
    for key in ROOM_FIELDS:
        if key not in ('draft', 'mapDates'):
            deal[key] = room.get(key, ROOM_FIELDS[key])
    deal['toldUs'] = [t for t in deal['toldUs'] if t.get('q')]
    for step, date in zip(deal['map'], room.get('mapDates') or []):
        step['date'] = date
    return deal


_hashes: dict = {}


def _versioned(m: re.Match) -> str:
    rel = m.group(1)
    if rel not in _hashes:
        import hashlib
        path = ROOT / rel
        _hashes[rel] = ('?v=' + hashlib.md5(path.read_bytes()).hexdigest()[:8]) if path.is_file() else ''
    return '/' + rel + _hashes[rel]  # root-relative: works at /room/<slug>/ and top-level paths


def build(include_drafts: bool = False) -> int:
    """Write every room to /room/<slug>/index.html; returns how many were built."""
    rooms = [(f, json.loads(f.read_text(encoding='utf-8'))) for f in sorted((SRC / 'rooms').glob('*.json'))]
    for d in [OUT] + [ROOT / r[TOP_LEVEL] for _, r in rooms if r.get(TOP_LEVEL)]:
        if d.exists():
            shutil.rmtree(d)
    template = (SRC / 'template.html').read_text(encoding='utf-8')
    n = 0
    for f, room in rooms:
        if room.get('draft', True) and not include_drafts:
            continue
        deal = _deal(room)
        # JSON inside <script>: escape "<" so no value can close the script tag.
        payload = json.dumps(deal, ensure_ascii=False).replace('<', '\\u003c')
        title = f"Kaizan for {deal['prospect']}" if deal['prospect'] else 'Kaizan deal room'
        html = (template.replace('/*DEAL_JSON*/', payload, 1)
                        .replace('/*DEAL_TITLE*/', title.replace('&', '&amp;').replace('<', '&lt;'), 1))
        # Version every asset link by content, so a replaced video or image is refetched.
        html = re.sub(r'\.\./\.\./(assets/[A-Za-z0-9_./-]+)', _versioned, html)
        out = (ROOT / room[TOP_LEVEL] if room.get(TOP_LEVEL) else OUT / f.stem) / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding='utf-8')
        n += 1
    return n


def new(prospect: str) -> Path:
    """Create rooms/<prospect-slug>-<code>.json, ready to fill in."""
    path = SRC / 'rooms' / f'{_slug(prospect)}-{secrets.token_hex(3)}.json'
    room = dict(ROOM_FIELDS, prospect=prospect)
    path.write_text(json.dumps(room, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return path


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'new':
        p = new(sys.argv[2])
        print(f'Created {p.relative_to(ROOT)}\nRoom URL once built: https://kaizan.ai/room/{p.stem}/')
    else:
        print(__doc__)
