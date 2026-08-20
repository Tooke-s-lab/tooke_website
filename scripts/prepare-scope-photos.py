#!/usr/bin/env python3
"""
Builds the six images for the two Scope slideshows on the research page.

Chosen against the themes in Cat's MRC fellowship abstract, so that whatever she
writes in the two 200-word blocks, the pictures beside it already fit. Each
slideshow runs sample -> method -> result, which is the shape of both halves of
that abstract.

Block 1 — β-lactam action and resistance; structures of PBPs/BLAs bound to
          antibiotics, linked to activity data.
  crystals    s21  microcrystal needles down the microscope — the material
  density     s47  antibiotic bound in its electron density — the evidence
  activesite  s51  PBP7:penicillin G active-site contacts — the mechanism

Block 2 — dynamic structural biology; XFELs, time-resolved snapshots along the
          reaction pathway, molecular movies.
  chip        s22  fixed-target chip for room-temperature serial data
  droplet     s26  drop-on-demand injector, ~65 pL at 30 µm
  timeres     s28  structures overlaid across the reaction timepoints

All six are close to 4:3 already, which is the frame the slideshow uses, so the
crop is slight. Written at 800 and 1600 so the browser can pick per screen.

Usage:  python scripts/prepare-scope-photos.py
Output: assets/photos/scope-<name>-{800,1600}.webp
"""

import os
import glob

from PIL import Image

DECK = "source/powerpoint/swsbc-2026-090726"
OUT = "assets/photos"
WIDTHS = (800, 1600)
ASPECT = 4 / 3

# Optional third value: fraction to trim off the TOP before cropping to aspect.
# The microscope screenshot carries the capture software's status bar along its
# top edge, which reads as a defect on a website.
IMAGES = [
    ("crystals",   "image58.png", 0.09),
    ("density",    "image134.png"),
    ("activesite", "image147.png"),
    ("chip",       "image61.png"),
    ("droplet",    "image79.png"),
    ("timeres",    "image84.png"),
]


def find(name):
    """Deck files are prefixed with the slides that used them."""
    hits = glob.glob(os.path.join(DECK, "*_" + name))
    return hits[0] if hits else None


def crop_to_aspect(im):
    w, h = im.size
    if w / h > ASPECT:                      # too wide — trim the sides
        new = int(h * ASPECT)
        x = (w - new) // 2
        return im.crop((x, 0, x + new, h))
    new = int(w / ASPECT)                   # too tall — trim top and bottom
    y = (h - new) // 2
    return im.crop((0, y, w, y + new))


def main():
    os.makedirs(OUT, exist_ok=True)
    for entry in IMAGES:
        name, src_name = entry[0], entry[1]
        trim_top = entry[2] if len(entry) > 2 else 0.0
        src = find(src_name)
        if not src:
            print("  SKIP %-11s not found: %s" % (name, src_name))
            continue
        im = Image.open(src).convert("RGB")
        if trim_top:
            im = im.crop((0, int(im.size[1] * trim_top), im.size[0], im.size[1]))
        im = crop_to_aspect(im)
        line = "  %-11s %-16s" % (name, "%dx%d" % im.size)
        for w in WIDTHS:
            if w > im.size[0]:
                line += "  (skip %dw, would upscale)" % w
                continue
            out = im.resize((w, int(w / ASPECT)), Image.LANCZOS)
            dst = os.path.join(OUT, "scope-%s-%d.webp" % (name, w))
            out.save(dst, "WEBP", quality=80, method=6)
            line += "  %dw=%dKB" % (w, os.path.getsize(dst) / 1024)
        print(line)


if __name__ == "__main__":
    main()
