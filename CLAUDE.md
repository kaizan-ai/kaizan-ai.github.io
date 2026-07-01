# Kaizan website — orientation for Claude

This repo is the **kaizan.ai** website and its GitHub Pages source. Read this before
making changes.

## The one rule that matters most
**The `*.html` files are generated build output — never hand-edit them.** They are
produced by `tools/build.py` from data and templates, and any manual edit is silently
overwritten on the next build. Edit the *source* (`tools/build.py`, `content/`,
`assets/css`, `assets/js`), then rebuild.

```
python3 tools/build.py            # build the production site (excludes draft blog posts)
python3 tools/build.py --drafts   # also build draft posts (local preview only)
python3 -m http.server 8000       # preview at http://localhost:8000/
```
Requires Python 3.9+ and no pip installs (stdlib only; `tools/markdown2.py` is vendored).

## Layout
- `tools/build.py` — the static-site generator (pages = `render_*` functions; `NAV` near the top).
- `content/blog/<slug>/index.md` — **blog posts** (Markdown + frontmatter) with images
  colocated in the same folder. Loaded by `tools/blog.py`. See `content/blog/AUTHORING.md`.
- `assets/css/site.css`, `assets/css/tokens.css`, `assets/js/` — styles and scripts.
- `assets/img/` — images (generated blog images land in `assets/img/blog/<slug>/`).
- `/blog/`, `/about/`, `/product/`, … — **generated**; don't edit by hand.

## Blog posts
- Add/edit a post under `content/blog/<slug>/index.md`. Use Markdown, not HTML.
- Keep `draft: true` until reviewed — drafts are excluded from the production build.
- Images: drop them in the post folder, reference by filename (`![alt](photo.jpg)`); the
  build copies them and fixes the paths.
- To create one with Claude, follow `content/blog/AUTHORING.md` (or run `/new-blog-post`
  in Claude Code).

## Working conventions
- **Open a PR; do not push to `main`** for content. Merges to `main` trigger the CI build
  (`.github/workflows/build.yml`) which regenerates the site — so content PRs contain only
  source (`content/**`), not generated HTML.
- Don't run `tools/deploy.sh` from an authoring flow (it's a separate mirror-and-push step).
- After any change, `python3 tools/build.py && git status` — the diff should only show files
  you expect; a surprise HTML diff means something hand-edited generated output.
