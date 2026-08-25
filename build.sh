#!/bin/sh
# Stages the deployable site into _site/.
#
# There is no compilation here and there never should be — this exists only to
# decide what a visitor is allowed to download. The repo root holds the site
# *and* its toolchain: build scripts, the local preview launcher, and the
# developer documentation. None of that should be fetchable from the public
# site, and on Cloudflare Pages "deploy the repo root" would publish all of it
# verbatim.
#
# So: copy the site, leave the workshop behind.
#
# Cloudflare Pages settings that match this file:
#     Build command:            sh build.sh
#     Build output directory:   _site
#
# Local preview does NOT need this — serve.cmd serves the repo root directly.

set -e

# The two checks below are the deploy gate. Both catch a class of mistake that
# is invisible on the machine that made it, and both must fail the BUILD rather
# than reach a visitor:
#
#   check-links.py  a page referencing a file that was never generated. Only
#                   shows up on certain screen sizes (see its header comment).
#   check-news.py   a hand-edited news-data.js that will not parse, which
#                   empties the news page silently.
#
# If either exits non-zero the script stops here (set -e at the top) and
# Cloudflare keeps serving the last good deploy.
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  PY=""
fi

if [ -n "$PY" ]; then
  "$PY" scripts/check-links.py
  "$PY" scripts/check-news.py
else
  echo "WARNING: no python on PATH — deploy checks were SKIPPED." >&2
fi

rm -rf _site
mkdir -p _site

cp -r assets _site/
cp *.html *.css *.js *.json _site/
cp _headers _site/ 2>/dev/null || true

echo "_site staged: $(find _site -type f | wc -l) files, $(du -sh _site | cut -f1)"
