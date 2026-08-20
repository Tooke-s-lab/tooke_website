#!/usr/bin/env python3
"""
Builds the square portraits used by the lab-members card on people.html.

The avatars are circles, so a square crop centred on the face is what's needed —
letting CSS crop a tall snapshot with object-fit puts the chin in the middle of
the circle. Each entry below records where the face actually sits in its source
image, as a fraction of width/height, plus how wide a square to take around it.

Output is 320px, which covers the largest avatar (150px) at 2x.

Sources
  cat    Her University of Bristol staff profile portrait. Bath's research
         portal has no photograph — only the default silhouette.
         https://research-information.bris.ac.uk/en/persons/catherine-l-tooke/
  harry  Slide 54 of the SWSBC 2026 deck, the acknowledgements slide that names
         Dr Harry Morgan, Joe Hoff and Laura Parkinson. Identified by the
         collaborator.
  joe    Picture1.jpg, saved into the SWSBC folder by the collaborator. Small
         (472x374), so its crop lands under the 320px ceiling and is written at
         its native size rather than upscaled — still ~2.8x the 92px it is
         displayed at.
  xandi  His own phone photograph, 20 Aug 2026 -- HEIC, indoors against a plain
         wall. Chosen over an outdoor selfie from 7 Aug that was framed too
         close: its head was taller than the frame was wide, so no square crop
         could hold both hair and chin. This one has head and shoulders in
         frame and matches the framing of the other three portraits.

Usage:  python scripts/prepare-people-photos.py
Output: assets/photos/person-<name>-320.webp
"""

import os
from PIL import Image, ImageOps

# The 2026 phone photographs are HEIC and carry an EXIF orientation flag; both
# are no-ops for the older sources below.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

OUT = "assets/photos"
SIZE = 320   # ceiling, not a target — see below, small sources are never upscaled

PEOPLE = [
    # name,  source path,                          face x,  face y,  crop width
    ("cat", "source/people/cat-bristol.jpg", 0.41, 0.400, 690),
    ("harry", "source/powerpoint/swsbc-2026-090726/s54_image156.png", 0.623, 0.495, 400),
    ("joe", "source/powerpoint/swsbc-2026-090726/Picture1.jpg", 0.497, 0.40, 210),
    ("xandi", "source/people/xandi-2026-08-20.heic", 0.521, 0.620, 2200),
]


def square_crop(im, fx, fy, side):
    w, h = im.size
    side = min(side, w, h)
    cx, cy = fx * w, fy * h
    # Clamp so the box stays inside the frame rather than filling with black.
    x = max(0, min(w - side, cx - side / 2))
    y = max(0, min(h - side, cy - side / 2))
    return im.crop((int(x), int(y), int(x + side), int(y + side)))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, src, fx, fy, side in PEOPLE:
        if not os.path.exists(src):
            print("  SKIP %-6s source missing: %s" % (name, src))
            continue
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        crop = square_crop(im, fx, fy, side)
        # Never enlarge: a small source upscaled to 320 just looks soft.
        out = min(SIZE, crop.size[0])
        crop = crop.resize((out, out), Image.LANCZOS)
        dst = os.path.join(OUT, "person-%s-%d.webp" % (name, out))
        crop.save(dst, "WEBP", quality=82, method=6)
        print("  %-6s %-12s -> %-38s %3dpx  %dKB"
              % (name, "%dx%d" % im.size, dst, out, os.path.getsize(dst) / 1024))


if __name__ == "__main__":
    main()
