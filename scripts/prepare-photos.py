#!/usr/bin/env python3
"""
Turns the raw iPhone HEICs into web-ready images.

Why this exists:
  - HEIC is an Apple format. Chrome and Firefox cannot display it at all, so the
    originals are unusable on the web and MUST be converted.
  - The originals are 12MP (4032x3024) and ~2MB each. Shipping those would be
    absurd; each one is resized to the widths a browser actually needs.
  - They were shot on a phone across two locations on different days, so they
    are inconsistent in colour. A light, uniform grade pulls them together
    enough to read as one set without looking filtered.

Requires: pillow, pillow-heif   (python -m pip install pillow pillow-heif)
Usage:    python scripts/prepare-photos.py   (run from the repo root)
Output:   assets/photos/<name>-<width>.webp
"""

import os
from PIL import Image, ImageOps, ImageEnhance
import pillow_heif

pillow_heif.register_heif_opener()

SRC = "source/photos"
OUT = "assets/photos"
WIDTHS = [400, 800, 1600]
QUALITY = 78

# Curated selection. The two shots of the STFC poster wall are deliberately
# excluded: they are photographs OF someone else's copyrighted promotional
# photography, and republishing them would be a rights problem.
#
# "people" flags shots containing identifiable individuals — fine for an
# internal review, but they need those people's permission before going live.
PHOTOS = [
    ("20260805_143353946_iOS.heic", "diamond-hall",      False),
    ("20260805_091046187_iOS.heic", "diamond-hall-tall", False),
    ("20260805_095839233_iOS.heic", "beamline-control",  False),
    ("20260805_130632735_iOS.heic", "beamline-data",     False),
    ("20260805_125732716_iOS.heic", "beamline-team",     True),
    ("20260805_094820668_iOS.heic", "beamline-optics",   True),
    ("20260807_144006885_iOS.heic", "crystal-drop",      False),
    ("20260814_131902420_iOS.heic", "gel-dish",          False),
    ("20260813_102527919_iOS.heic", "gel-tank",          False),
    ("20260812_092856425_iOS.heic", "sonicator",         False),
    ("20260812_155709222_iOS.heic", "centrifuge",        False),
    ("20260812_095214165_iOS.heic", "bench-work",        True),
]


def grade(im):
    """Light, uniform grade so a set of phone snaps reads as one collection.
    Deliberately subtle — enough to unify, not enough to look 'filtered'."""
    im = ImageEnhance.Color(im).enhance(0.88)      # pull back phone oversaturation
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    people = []

    print(f"{'name':<20}{'source':>12}{'  ->  '}{'webp widths':<28}{'total'}")
    print("-" * 78)

    for src, name, has_people in PHOTOS:
        path = os.path.join(SRC, src)
        if not os.path.exists(path):
            print(f"{name:<20}  MISSING: {src}")
            continue

        im = Image.open(path)
        im = ImageOps.exif_transpose(im)           # iOS stores rotation in EXIF
        im = im.convert("RGB")
        im = grade(im)

        before = os.path.getsize(path)
        made = []
        size_sum = 0

        for w in WIDTHS:
            if w > im.width:
                continue
            h = round(im.height * w / im.width)
            resized = im.resize((w, h), Image.LANCZOS)
            dst = os.path.join(OUT, f"{name}-{w}.webp")
            resized.save(dst, "WEBP", quality=QUALITY, method=6)
            made.append(str(w))
            size_sum += os.path.getsize(dst)

        total += size_sum
        if has_people:
            people.append(name)
        print(f"{name:<20}{before/1024/1024:10.1f}MB  ->  "
              f"{','.join(made):<28}{size_sum/1024:6.0f}KB")

    print("-" * 78)
    print(f"{'TOTAL':<20}{'':10}      {'':28}{total/1024:6.0f}KB")
    if people:
        print()
        print("Contains identifiable people — needs their permission before the")
        print("site goes public: " + ", ".join(people))


if __name__ == "__main__":
    main()
