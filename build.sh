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

rm -rf _site
mkdir -p _site

cp -r assets _site/
cp *.html *.css *.js *.json _site/
cp _headers _site/ 2>/dev/null || true

# The link checker is the deploy gate: it catches a page referencing a file that
# was never generated, which is invisible on the machine that built it (see the
# comment at the top of check-links.py). A missing file must fail the build, not
# reach a visitor as a broken image.
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/check-links.py
elif command -v python >/dev/null 2>&1; then
  python scripts/check-links.py
fi

echo "_site staged: $(find _site -type f | wc -l) files, $(du -sh _site | cut -f1)"
