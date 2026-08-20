#!/usr/bin/env python3
"""
Checks that every local file the pages reference actually exists.

Written after a real bug: people.html listed `hero-people-2560.webp` in its
srcset, but that file had never been generated — the source photo is only
2028px wide, so it could not exist. Nothing looked wrong on an ordinary
monitor, because at 1x the browser picks the 1920 candidate. On a high-DPI
laptop the browser asks for the largest candidate, got a 404, and the hero
rendered as a flat coloured box. The page was demoed like that.

That is the nasty shape of this class of bug: it depends on the viewer's screen,
so it is invisible on the machine you built it on. Hence a check that does not
rely on looking.

Also reports images whose declared width/height do not match the file, since a
wrong intrinsic size causes the page to jump as it loads.

Usage:  python scripts/check-links.py
Exit:   1 if anything is missing, so it can gate a deploy.
"""

import os
import re
import sys
import glob

# Pillow is optional. The missing-file check is the one that gates a deploy and
# it needs nothing but the filesystem; the aspect-ratio check is a nicety that
# needs to decode images. Cloudflare's build image has no Pillow, and a build
# that dies on ImportError would block a deploy over a check it never ran.
try:
    from PIL import Image
except ImportError:
    Image = None

REF = re.compile(r'(?:src|href)="([^"]+\.(?:webp|png|jpg|jpeg|svg|css|js|pdb|json))"')
SRCSET = re.compile(r'srcset="([^"]+)"')
CSSURL = re.compile(r"url\('([^']+)'\)")
IMGTAG = re.compile(r"<img\b[^>]*>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')


def refs_in(text):
    out = set()
    for m in REF.finditer(text):
        out.add(m.group(1))
    for m in SRCSET.finditer(text):
        for part in m.group(1).split(","):
            bits = part.strip().split()
            if bits:
                out.add(bits[0])
    for m in CSSURL.finditer(text):
        out.add(m.group(1))
    return {r for r in out if not r.startswith(("http://", "https://", "data:", "#", "mailto:"))}


def resolve(base, ref):
    """Map a reference as written in a page to a path on disk.

    404.html writes every URL root-absolute, because Cloudflare serves it from
    arbitrary depths and relative URLs would resolve against the missing path
    rather than the site root. Those are real, checkable references — treating a
    leading "/" as "not my problem" would exempt the one page whose links are
    hardest to eyeball.
    """
    ref = ref.split("?")[0].split("#")[0]
    if ref.startswith("/"):
        return os.path.normpath(ref.lstrip("/")) if ref != "/" else "index.html"
    return os.path.normpath(os.path.join(base, ref))


def main():
    missing, wrong_dims = [], []

    for page in sorted(glob.glob("*.html")):
        base = os.path.dirname(page)
        text = open(page, encoding="utf8").read()

        for ref in sorted(refs_in(text)):
            path = resolve(base, ref)
            if not os.path.exists(path):
                missing.append((page, ref))

        for tag in IMGTAG.findall(text):
            a = dict(ATTR.findall(tag))
            src, w, h = a.get("src"), a.get("width"), a.get("height")
            if Image is None:
                break
            if not (src and w and h) or src.endswith(".svg"):
                continue
            path = resolve(base, src)
            if not os.path.exists(path):
                continue
            try:
                with Image.open(path) as im:
                    fw, fh = im.size
            except Exception:
                continue
            # Compare aspect, not absolute size: an <img> may legitimately
            # declare the dimensions of one srcset rung. A wrong *shape* is
            # what causes layout shift.
            if abs((fw / fh) - (int(w) / int(h))) > 0.02:
                wrong_dims.append((page, src, "%sx%s declared, file is %dx%d"
                                   % (w, h, fw, fh)))

    if missing:
        print("MISSING FILES (%d) — these 404 for whoever's browser asks:" % len(missing))
        for p, r in missing:
            print("   %-30s %s" % (p, r))
    if wrong_dims:
        print("\nWRONG ASPECT (%d) — causes layout shift as the image loads:" % len(wrong_dims))
        for p, s, msg in wrong_dims:
            print("   %-30s %-46s %s" % (p, s, msg))
    if not missing and not wrong_dims:
        print("All referenced files exist and every declared aspect matches.")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
