#!/usr/bin/env python3
"""
Turns one photo into a web-ready image for a news post.

Why this exists:
  - Photos off a phone are HEIC. Chrome and Firefox cannot display HEIC AT ALL,
    so dropping one into assets/news/ gives every visitor a broken image while
    looking perfectly fine in Windows Explorer. This is the failure this script
    exists to prevent.
  - They are also ~2-4MB. The news card is never drawn wider than about 700px,
    so an untouched original is roughly forty times the bytes needed and would
    outweigh the entire rest of the site.
  - Phones write rotation into an EXIF tag rather than the pixels. Without
    honouring it, a portrait photo arrives on its side.

Requires: pillow          (python -m pip install pillow)
          pillow-heif     — only if you are converting a .HEIC
Usage:    python scripts/prepare-news-photo.py <photo> [name]
          run from the repo root

  python scripts/prepare-news-photo.py ~/Desktop/IMG_4821.HEIC
      -> assets/news/img-4821.webp

  python scripts/prepare-news-photo.py trip.jpg beamtime-october
      -> assets/news/beamtime-october.webp

Print the filename it gives you into the "photo" field of news-data.js.
"""

import os
import re
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is not installed.  python -m pip install pillow")

# Matches studio.html, which this replaces: wider than the card is ever drawn on
# any screen, including at 2x on a high-DPI laptop.
MAXW = 1400
QUALITY = 82
OUT = "assets/news"


def slug(text):
    """A filename that is safe in a URL and readable in a git diff."""
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text) or "photo"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())

    src = os.path.expanduser(sys.argv[1])
    if not os.path.isfile(src):
        sys.exit("No such file: %s" % src)

    if not os.path.isdir(OUT):
        sys.exit("Run this from the repo root — %s does not exist here." % OUT)

    name = slug(sys.argv[2]) if len(sys.argv) > 2 \
        else slug(os.path.splitext(os.path.basename(src))[0])
    dst = os.path.join(OUT, name + ".webp")

    # Registered lazily and only for HEIC, so that someone converting an
    # ordinary .jpg is not told to install a library they do not need.
    if os.path.splitext(src)[1].lower() in (".heic", ".heif"):
        try:
            import pillow_heif
        except ImportError:
            sys.exit("That is a HEIC. Converting it needs one more library:\n"
                     "    python -m pip install pillow-heif")
        pillow_heif.register_heif_opener()

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # honour the phone's rotation tag
        im = im.convert("RGB")                    # drop alpha; WebP photos want none
        if im.width > MAXW:
            h = round(im.height * MAXW / im.width)
            im = im.resize((MAXW, h), Image.LANCZOS)
        if os.path.exists(dst):
            print("note: overwriting the existing %s" % dst)
        im.save(dst, "WEBP", quality=QUALITY, method=6)
        w, h = im.size

    before = os.path.getsize(src)
    after = os.path.getsize(dst)
    print("%s  ->  %s" % (src, dst))
    print("%dx%d, %.1fMB -> %.0fKB" % (w, h, before / 1e6, after / 1024))
    print()
    print('Now put this in the "photo" field of news-data.js:')
    print("    \"photo\": \"%s\"," % (name + ".webp"))
    print('and describe the picture in the "alt" field next to it.')


if __name__ == "__main__":
    main()
