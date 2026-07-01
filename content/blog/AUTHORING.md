# Writing a blog post (with Claude)

This is the guide for **publishing a new article on kaizan.ai/blog** — written so a
non-technical author can do it with Claude (claude.ai + the GitHub connector) without
touching code.

You never edit HTML and you never run a build. You write the article in Markdown;
the site builds itself when your post is merged.

---

## The fastest path: ask Claude

In claude.ai (with the **GitHub connector** enabled for `kaizan-ai/kaizan-ai.github.io`),
paste your draft and say:

> "Publish this as a new Kaizan blog post."

Claude will follow the steps below for you. If you'd rather do it by hand, or want to
know exactly what Claude is doing, read on.

---

## What a post is

One folder per post:

```
content/blog/<slug>/
  index.md      ← the article: frontmatter + Markdown
  cover.jpg     ← the cover/hero image
  chart-1.png   ← any other images you reference
```

- `<slug>` is the URL: `content/blog/the-care-framework/` → `kaizan.ai/blog/the-care-framework/`.
  Use lowercase words separated by hyphens.
- **Images live in the same folder as `index.md`.** Reference them by filename only —
  `![A chart](chart-1.png)`. The build copies them to the right place automatically; you
  never write `../../assets/...`.

## `index.md` template

```markdown
---
title: The CARE framework, explained
date: 2026-06-22
author: Lia Sutton
category: POV
excerpt: One clear sentence — used on the blog card and as the social/preview description.
cover: cover.jpg
draft: true
tags: [client success, CARE]
---

Opening paragraph. Write in Markdown.

## A section heading

More text. **Bold**, *italic*, and [a link](https://kaizan.ai). Lists:

- first point
- second point

> A pull quote.

![Caption for the image](chart-1.png)
```

### Frontmatter fields
| Field | Required | Notes |
|---|---|---|
| `title` | yes | Plain text. |
| `date` | yes | `YYYY-MM-DD`. Shown as e.g. "22 June 2026". |
| `author` | optional | Not shown on the blog (no bylines); keep for your own records if useful. |
| `category` | yes | One of: **POV, PRODUCT, FIELD NOTES, BENCHMARK, INTERVIEW, CUSTOMER STORY**. |
| `excerpt` | yes | One sentence; card + meta description. |
| `cover` | recommended | Filename of the cover image in this folder. If omitted, a gradient is used. |
| `draft` | yes | **Keep `true` until it's ready.** Drafts never appear on the live site. |
| `tags` | optional | `[a, b]`. |
| `canonical` | optional | Only for posts republished elsewhere. |

## Publishing

1. Create a branch: `blog/<slug>` (never commit to `main`).
2. Add the folder `content/blog/<slug>/` with `index.md` + images.
3. Open a **Pull Request** titled `Blog: <title>`.
4. An editor reviews it. When they're happy they set `draft: false` and merge.
5. On merge, the site rebuilds automatically (GitHub Action) and the post goes live at
   `kaizan.ai/blog/<slug>/` within a couple of minutes. **No one runs a build by hand.**

## Rules of thumb
- **Markdown only** in the body — no raw HTML needed.
- Keep `draft: true` until an editor signs off.
- Put every image in the post folder and reference it by filename.
- One idea per post; lead with the excerpt sentence.
- Don't edit anything under `/blog/` or `/assets/` directly — those are generated.
