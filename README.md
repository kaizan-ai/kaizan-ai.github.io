# Kaizan website (B-lite)

Static site for GitHub Pages: plain HTML + CSS + a tiny vanilla-JS file, with **no
framework or bundler** in production. The catch: **every `*.html` file is generated**
by a single Python script (`tools/build.py`) from data dicts + template strings.

> ⚠️ **Never hand-edit the generated `*.html` files — edit `tools/build.py` and rebuild.**
> The HTML is build output. Any manual edit to a generated page is silently overwritten
> the next time `python3 tools/build.py` runs. This has caused real production
> regressions (a reverted GTM container id, a lost whitepaper CTA, a dropped hyperlink,
> stale pricing copy). The **only** hand-maintained HTML is `white-paper/index.html`
> (standalone — the build never writes it).

## What's here

`tools/build.py` is the **source of truth**; everything below it marked _(generated)_
is produced by running it.

```
tools/build.py                          ← SOURCE OF TRUTH. Data dicts + render_* templates.
assets/css/tokens.css                   Brand palette + base button styles
assets/css/site.css                     Component classes + responsive breakpoints
assets/js/site.js                       Mobile nav, mega menu, tab switchers
assets/img/                             Logos and investor marks
white-paper/index.html                  Whitepaper page — HAND-MAINTAINED (not generated)
.nojekyll                               Tells GH Pages to serve files as-is

index.html                              Home                              (generated)
product/index.html                      Product                           (generated)
pricing/index.html                      Pricing                           (generated)
integrations/index.html                 Integrations                      (generated)
security/index.html                     Security (in the Resources menu)  (generated)
research/index.html                     Our Research — 2026 report        (generated)
knowledge-hub/index.html                Knowledge Hub — client-success Q&A (generated)
faq/index.html                          FAQs (in the Resources menu)      (generated)
customers/index.html                    Clients (case-study index)        (generated)
customers/<slug>/index.html             Case-study detail pages           (generated)
about/index.html                        CEO essay + investors             (generated)
for/<persona-slug>/index.html           Persona pages                     (generated)
content/blog/<slug>/index.md            BLOG POSTS — Markdown source (hand-authored)
blog/index.html + blog/<slug>/          Blog index + post pages           (generated)
404.html                                Custom 404                        (generated)
```

Disabled pages (e.g. `careers/`) are removed on each build via `_remove_page()` in
`build.py`, so stale output never lingers — re-enable by restoring the `write(...)` call.

## Deploy to GitHub Pages

1. Add a remote and push:
   ```
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```

2. In the repo on GitHub: **Settings → Pages → Source:** select **Deploy from a branch**, branch `main`, folder `/ (root)`. Save. The site will be live at `https://<you>.github.io/<repo>/` within a minute or two.

3. (Optional) Custom domain: add a `CNAME` file at the repo root containing your domain (e.g. `kaizan.ai`), then point your DNS at `<you>.github.io`. GitHub will provision HTTPS automatically.

If you host at a project subpath (e.g. `<you>.github.io/<repo>/`) **all internal links work as-is** because every page uses relative paths.

## Editing content

The golden rule: **change `tools/build.py`, never the `.html` output.** To edit copy or
add content:

1. Edit the relevant data dict near the top of the file (`NAV`, `RESOURCES_MENU`,
   `PERSONAS`, `CASE_DATA`, `PRICING_TIERS`, `FAQ_DATA`, `RESEARCH_REPORT`,
   `KNOWLEDGE_HUB_DATA`, `POSTS`, `QUOTES`, …) **or** the `render_*` template strings
   further down.
2. Rebuild:
   ```
   python3 tools/build.py
   ```
3. Commit **both** `tools/build.py` **and** the regenerated HTML, then push. (Keeping the
   source change and its output in the same commit is what prevents future divergence.)

**Tip:** after editing, run `python3 tools/build.py && git status` — the diff should only
show files you expect. A surprise diff usually means someone had hand-edited the HTML.

### Nav & dropdowns

The top nav is the `NAV` list. Two items are hover dropdowns rather than plain links:
`Personas` (built from `PERSONA_LIST`) and `Resources` (built from `RESOURCES_MENU`). The
`Resources` trigger is intentionally non-clickable — it only opens the dropdown. Add or
reorder dropdown links by editing `RESOURCES_MENU`.

### Adding or disabling a page

- **Add:** write a `render_<page>()` function, then add a `write(ROOT / '<dir>' / 'index.html', render_<page>())`
  line to `main()`. Link it from `NAV`/`RESOURCES_MENU`/footer as needed.
- **Disable:** replace its `write(...)` call in `main()` with `_remove_page(ROOT / '<dir>')`.
  That stops generating it **and** deletes any already-deployed copy so it 404s instead of
  serving stale HTML. Keep the `render_*` function around for easy re-enable.

## Adding a blog post

The blog at `/blog/` is built from **Markdown** files — one folder per post:

```
content/blog/<slug>/index.md      ← frontmatter + Markdown body
content/blog/<slug>/cover.jpg     ← colocated images (referenced by filename)
```

Add a post by creating that folder, then `python3 tools/build.py`. The build (via
`tools/blog.py`, using the vendored `tools/markdown2.py`) converts the Markdown, copies
images to `assets/img/blog/<slug>/`, and writes `/blog/index.html` + `/blog/<slug>/index.html`.

- Frontmatter: `title, date (YYYY-MM-DD), author, category, excerpt`, optional `cover`,
  `draft`, `tags`, `canonical`. Categories: POV · PRODUCT · FIELD NOTES · BENCHMARK ·
  INTERVIEW · CUSTOMER STORY.
- **`draft: true` posts are excluded** from the production build; use
  `python3 tools/build.py --drafts` to preview them locally.
- Images go in the post folder and are referenced by filename (`![alt](photo.jpg)`) — no
  relative paths to compute.
- **Non-technical authors:** see `content/blog/AUTHORING.md` (write with claude.ai + the
  GitHub connector → PR). Locally, `/new-blog-post` in Claude Code does the same.
- Posts publish automatically when a content PR is merged to `main` (the
  `.github/workflows/build.yml` Action rebuilds and commits the site).

### Migrating from Medium
`tools/import_medium.py --rss https://blog.kaizan.ai/feed` imports the feed's posts as
`draft: true` Markdown with images downloaded and `canonical` set to the Medium URL.
Review, set `draft: false`, build. (RSS carries only the ~10 most recent posts; the full
archive needs a Medium "Download your information" export.)

## Replacing placeholder media

The design ships with placeholders in three places:

- **Hero video** on the home page - currently a black panel with a "drop a video src here" hint. To wire a real video, edit `tools/build.py` → `render_home()` → search for `kz-hero-video` and add a `<video src="…" autoplay muted loop playsinline>` inside.
- **Marquee logos** - currently rendered as text logos (matches the design). Replace by editing `CLIENT_LOGOS` and `INTEGRATIONS` to use `<img>` tags, or restyle the marquee in `site.css`.
- **Blog post covers** - set `cover: <filename>` in the post's frontmatter (image colocated in `content/blog/<slug>/`); omit it to fall back to a generated gradient.

Drop any new images into `assets/img/`. Reference them by relative path; the depth is automatic via `relpath(depth)` in `build.py`.

## Local preview

Any static file server works. From the repo root:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

## Browser support

Modern evergreen browsers. The CSS uses `aspect-ratio`, `gap`, `clamp()` and CSS custom properties - all widely supported since 2022. No polyfills required.

## Responsive

Three breakpoints in `assets/css/site.css`: 1280px, 1024px, 768px, 480px. The full design is 1440px wide; below 1024px the mobile nav (hamburger) takes over and multi-column grids collapse.

## Source design

This site implements `Kaizan B-lite - full site.html` from the Claude Design handoff bundle. Original design files (React/JSX prototypes) are not included - see the bundle for reference.
