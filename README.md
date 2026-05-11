# Kaizan website (B-lite)

Static site implementation of the Kaizan B-lite design — built for GitHub Pages.
Pure HTML + CSS + a tiny vanilla-JS file. No build step, no React in production.

## What's here

```
index.html                              Home
product/index.html                      Product
customers/index.html                    Clients (case-study index)
customers/<slug>/index.html             5 case-study detail pages
insights/index.html                     Blog / Insights (linked as "Blog" in nav)
about/index.html                        CEO essay + seed announcement + investors
for/<persona-slug>/index.html           8 persona pages
blog/index.html                         **Hidden** blog landing — not in main nav
404.html                                Custom 404
assets/css/tokens.css                   Brand palette + base button styles
assets/css/site.css                     Component classes + responsive breakpoints
assets/js/site.js                       Mobile nav, mega menu, tab switchers
assets/img/                             Logos and investor marks
tools/build.py                          Regenerates the HTML from data dicts
.nojekyll                               Tells GH Pages to serve files as-is
```

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

The site is generated from data inside `tools/build.py`. To change copy or add content:

1. Edit the relevant data dict at the top of the file (`PERSONAS`, `CASE_DATA`, `INSIGHTS_POSTS`, `POSTS`, `QUOTES`, `NAV`, etc.) **or** edit the `render_*` template strings further down.
2. Run:
   ```
   python3 tools/build.py
   ```
3. Commit the regenerated HTML files and push.

## Adding a blog post (hidden blog)

The hidden blog at `/blog/` is the staging ground for posts. Append to `POSTS` in `tools/build.py`:

```python
POSTS = [
    dict(
        slug='hello-world',
        title='Hello, world',
        excerpt='A short opener.',
        date='9 May 2026',
        author='Glen Calvert',
        category='POV',
        cover=cover('#FFB900', '#FFD86B', 'KZ'),
        body='<p>Markdown? Just write HTML here. Use &lt;p&gt;, &lt;h2&gt;, &lt;blockquote&gt;, &lt;ul&gt; etc.</p>',
    ),
]
```

Run `python3 tools/build.py`. The build creates `/blog/index.html` (the hidden listing) and `/blog/<slug>/index.html` for each post.

When you're ready to make the blog public, edit `NAV` in `tools/build.py` to point the `Blog` item at `blog/` instead of `insights/`, and either delete or keep `/insights/` as a separate "POV / white papers" section.

## Replacing placeholder media

The design ships with placeholders in three places:

- **Hero video** on the home page — currently a black panel with a "drop a video src here" hint. To wire a real video, edit `tools/build.py` → `render_home()` → search for `kz-hero-video` and add a `<video src="…" autoplay muted loop playsinline>` inside.
- **Marquee logos** — currently rendered as text logos (matches the design). Replace by editing `CLIENT_LOGOS` and `INTEGRATIONS` to use `<img>` tags, or restyle the marquee in `site.css`.
- **Blog post covers** — gradient SVG data-URIs. Replace `cover(...)` calls in `INSIGHTS_POSTS` with an image path under `assets/img/`.

Drop any new images into `assets/img/`. Reference them by relative path; the depth is automatic via `relpath(depth)` in `build.py`.

## Local preview

Any static file server works. From the repo root:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

## Browser support

Modern evergreen browsers. The CSS uses `aspect-ratio`, `gap`, `clamp()` and CSS custom properties — all widely supported since 2022. No polyfills required.

## Responsive

Three breakpoints in `assets/css/site.css`: 1280px, 1024px, 768px, 480px. The full design is 1440px wide; below 1024px the mobile nav (hamburger) takes over and multi-column grids collapse.

## Source design

This site implements `Kaizan B-lite — full site.html` from the Claude Design handoff bundle. Original design files (React/JSX prototypes) are not included — see the bundle for reference.
