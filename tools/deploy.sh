#!/usr/bin/env bash
#
# Deploy /Users/prav/Kaizan/website → kaizan-ai/kaizan-ai.github.io
#
# Run this from anywhere:
#   /Users/prav/Kaizan/website/tools/deploy.sh
#
# What it does:
#   1. Rebuilds HTML from the build script (so you never deploy stale output).
#   2. Wipes the target clone (keeps .git and CNAME if present).
#   3. Copies the source folder over, minus .git and the 173MB hero source.
#   4. Commits with a message borrowed from the source repo's last commit.
#   5. Pushes to whatever branch the target repo's HEAD is on.
#
# Prereqs (one-time):
#   - The target repo is cloned to /Users/prav/Kaizan/kaizan-ai.github.io
#       git clone git@github.com:kaizan-ai/kaizan-ai.github.io.git /Users/prav/Kaizan/kaizan-ai.github.io
#   - Your SSH key is paired with GitHub (test: ssh -T git@github.com)
#   - In the GitHub repo settings, Pages → Source = main / (root)

set -euo pipefail

SRC="/Users/prav/Kaizan/website"
DST="/Users/prav/Kaizan/kaizan-ai.github.io"

red()    { printf "\033[31m%s\033[0m\n" "$*"; }
green()  { printf "\033[32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
step()   { printf "\033[1m→ %s\033[0m\n" "$*"; }

# ── Sanity checks ────────────────────────────────────────────
if [ ! -d "$SRC/.git" ]; then
  red "✗ Source repo not found at $SRC"
  exit 1
fi

if [ ! -d "$DST/.git" ]; then
  red "✗ Target repo not found at $DST"
  echo "Clone it first:"
  echo "  git clone git@github.com:kaizan-ai/kaizan-ai.github.io.git $DST"
  exit 1
fi

# ── 1. Rebuild HTML ──────────────────────────────────────────
step "Rebuilding site from $SRC/tools/build.py"
python3 "$SRC/tools/build.py" > /dev/null

# ── 2. Warn if source has uncommitted changes ────────────────
if ! (cd "$SRC" && git diff --quiet && git diff --cached --quiet); then
  yellow "⚠ $SRC has uncommitted changes — deploying them anyway."
  yellow "  Consider committing in source for clean history:"
  yellow "      cd $SRC && git add -A && git commit -m '...'"
  echo
fi

# ── 3. Wipe target (keep .git, .nojekyll, CNAME) ─────────────
step "Clearing target $DST (keeping .git, .nojekyll, CNAME)"
find "$DST" -mindepth 1 -maxdepth 1 \
  ! -name '.git' \
  ! -name 'CNAME' \
  -exec rm -rf {} +

# ── 4. Mirror source into target ─────────────────────────────
step "Copying source files into target (rsync)"
rsync -a \
  --exclude='.git/' \
  --exclude='assets/video/hero-source.mp4' \
  --exclude='.DS_Store' \
  "$SRC/" "$DST/"

# ── 5. Commit & push ─────────────────────────────────────────
cd "$DST"
git add -A

if git diff --cached --quiet; then
  green "✓ Target is already up to date — nothing to deploy."
  exit 0
fi

# Borrow the source repo's last commit message for traceability
SRC_MSG=$(cd "$SRC" && git log -1 --format='%s')
SRC_HASH=$(cd "$SRC" && git rev-parse --short HEAD)

step "Committing"
git -c user.email="${GIT_AUTHOR_EMAIL:-pravin@kaizan.ai}" \
    -c user.name="${GIT_AUTHOR_NAME:-Prav}" \
    commit -m "Deploy: ${SRC_MSG}" \
           -m "Source: kaizan website repo @ ${SRC_HASH}"

BR=$(git rev-parse --abbrev-ref HEAD)
step "Pushing to origin/$BR"
git push origin "$BR"

green ""
green "✓ Deployed."
green "  Live in ~30–60 seconds at https://kaizan-ai.github.io/"
green ""
