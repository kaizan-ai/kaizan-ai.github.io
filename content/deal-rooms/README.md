# Deal rooms

Private sales rooms at `kaizan.ai/room/<slug>/`. They are never indexed, never linked from the site and
never in the sitemap. Only someone with the link can find a room, but anyone the link is forwarded to
can open it, so keep contract terms and anything confidential out of room files.

## The general room

`rooms/dealroom.json` has no prospect set, so it shows general wording (no call quotes, target or
"prepared for" note) and can be sent to anyone. Its `"path": "dealroom"` publishes it at
`https://kaizan.ai/dealroom/` instead of under /room/.

## Make a room for a prospect

1. `python3 tools/deal_rooms.py new "Acme Agency"` creates `rooms/acme-agency-<code>.json`. The random code
   keeps the URL unguessable.
2. Fill in the file:
   - `prospect`, `ae`, `aeEmail`, `bookingUrl` (the AE's calendar link; empty falls back to email)
   - `problem`: their problem in their own words, from discovery
   - `toldUs`: three quotes from the call, each with its timestamp `t` (e.g. `"12:40"`); `callRecordingUrl` makes them clickable
   - `targetNumber` and `targetLabel`: the number the room is built around
   - `priceBand`: shown on the pricing page; leave empty to show only "your contact will send the business case"
   - `mapDates`: dates for the seven steps of the mutual action plan (kickoff to decision)
3. Set `"draft": false` when it's ready. Drafts only build with `python3 tools/build.py --drafts`.
4. Open a PR as usual. After merge, the room is live at `https://kaizan.ai/room/<file name without .json>/`.

To take a room down, delete its file and merge.

## Shared content

- `template.html`: the room itself (pages, copy, FAQs, the Client Memory tour).
- `shared.json`: what every room shows: the film and demo, role and case study videos, case study people, IT
  document links and the mutual action plan steps.
- Videos and images: `assets/video/deal-room/` and `assets/img/deal-room/`.

## Replacing a video

Overwrite the file in `assets/video/deal-room/` under the same name and merge. The room links the
file with a `?v=` content hash, but the build only re-runs for changes under `content/`,
`tools/`, `assets/css/` and `assets/js/`: include a small change under `content/` (this
README will do) in the same PR, so the hash updates and visitors get the new video.
