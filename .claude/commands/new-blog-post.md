---
description: Draft and open a PR for a new Kaizan blog post from rough text
---

You are helping someone publish a post on the Kaizan blog. The user's rough draft /
notes (if any) are below:

$ARGUMENTS

Follow these steps. Be friendly and do the mechanical work for them — they may be
non-technical.

1. **Gather metadata.** From the draft or by asking, get: title, author, category
   (one of: POV, PRODUCT, FIELD NOTES, BENCHMARK, INTERVIEW, CUSTOMER STORY), and a
   one-sentence excerpt. Derive `slug` = kebab-cased title; confirm it with the user.

2. **Branch.** `git checkout -b blog/<slug>` — never commit to `main`.

3. **Write the post.** Create `content/blog/<slug>/index.md` with valid frontmatter
   (set `draft: true`, today's date as `YYYY-MM-DD` unless told otherwise) and the body
   as clean Markdown. Tidy the prose (smart quotes, `##` section headings, `-` lists,
   keep links) but **do not invent facts or rewrite the author's meaning**.

4. **Images.** Save any images the user provides into `content/blog/<slug>/` and
   reference them by filename only — `![alt](photo.jpg)`. Choose a `cover`. If an image
   is a URL, download it into the folder first.

5. **Build & preview.** Run `python3 tools/build.py --drafts`, fix any frontmatter
   warnings it prints, then `python3 -m http.server 8000` and point the user at
   `http://localhost:8000/blog/<slug>/`. Iterate on their feedback.

6. **Open a PR.** `git add content/blog/<slug>/`, commit, push the branch, and
   `gh pr create --title "Blog: <title>"` with a short summary + an editorial checklist
   (facts checked, links work, excerpt set, images have alt text). **Stop after the PR.**

Guardrails: keep `draft: true` (an editor flips it on merge); PR only — never push to
`main`, never run `tools/deploy.sh`. The post goes live automatically when the PR is
merged (the build workflow regenerates the site).
