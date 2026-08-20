#!/usr/bin/env python3
"""
Builds the Concept 2 splash background: a teal-duotone crop of Cat's own
crystallisation drops.

Why this exists (and why it is not just prepare-photos.py with a filter):

  - Source is slide 21 of SWSBC_2026_090726.pptx ("Crystals -> microcrystals ->
    droplets"), 3384x2708: sitting drops under oil, photographed down the
    plate microscope. It is her actual technique, not a stock metaphor.
  - The raw frame is a WIDE FIELD of ~20 small drops, which reads as ambiguous
    abstract bubbles. We crop into the left two thirds so two or three
    foreground drops are large enough to be legible as drops, with the crystal
    faces inside the biggest one visible.
  - The right-hand third of the source carries BURNT-IN RED MEASUREMENT
    ANNOTATIONS ("(3) Length 41,74 um" etc.) across the best microcrystal drop,
    plus a scale bar bottom-right and an instrument caption bottom-left. The
    crop is chosen to exclude all three; do not widen it without re-checking.
  - The source has a strong lavender colour cast (the plate illumination) that
    belongs to no part of the brand palette. Rather than neutralising it, the
    image is mapped to a TEAL DUOTONE built from the brand ramp, so the
    photograph and the palette are literally the same colours.

Requires: pillow            (python -m pip install pillow)
Usage:    python scripts/prepare-splash-photo.py     (run from the repo root)
Output:   assets/photos/crystal-drops-<width>.webp
"""

import os
from PIL import Image, ImageEnhance, ImageFilter

SRC = "source/powerpoint/swsbc-2026-090726/s21_image59.png"
OUT = "assets/photos"
NAME = "crystal-drops"

# Left-of-frame 3:2 crop. 2240x1493 native — every output width below is a
# DOWNSCALE, nothing is invented.
CROP = (0, 60, 2240, 1553)
WIDTHS = [1200, 1920, 2240]
# 72, not the 78-80 used elsewhere: after the duotone this is a smooth, largely
# flat image and it costs 172KB at 1920 instead of 277KB. It is also the page's
# LCP element, and most of it sits under a 95% scrim.
QUALITY = 72

# Duotone ramp: shadow -> highlight, expressed as (luminance stop, rgb).
# Endpoints are the page's own tokens, so the photo cannot drift away from the
# palette: --ink #12241D at the bottom, --bg #F4F7F5 at the top, with --teal-deep
# #1F6B52 and --teal #47A284 carrying the midtones where the drops live.
RAMP = [
    (0.00, (0x10, 0x25, 0x1E)),
    (0.30, (0x1F, 0x6B, 0x52)),
    (0.55, (0x47, 0xA2, 0x84)),
    (0.78, (0xA9, 0xD4, 0xC4)),
    (1.00, (0xF4, 0xF7, 0xF5)),
]


def duotone_lut():
    """256-entry per-channel LUT interpolating the ramp above."""
    lut = [[], [], []]
    for i in range(256):
        t = i / 255
        for k in range(len(RAMP) - 1):
            t0, c0 = RAMP[k]
            t1, c1 = RAMP[k + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                for ch in range(3):
                    lut[ch].append(round(c0[ch] + (c1[ch] - c0[ch]) * f))
                break
    return lut[0] + lut[1] + lut[2]


def main():
    os.makedirs(OUT, exist_ok=True)
    im = Image.open(SRC).convert("RGB").crop(CROP)

    # Grade BEFORE the duotone, on luminance:
    #  - contrast opens up the gap between drop and background, which the flat
    #    lavender original does not have;
    #  - unsharp mask brings back the crystal faces inside the drops, which is
    #    the whole point of using this photograph.
    g = im.convert("L")
    g = ImageEnhance.Contrast(g).enhance(1.22)
    g = ImageEnhance.Brightness(g).enhance(1.04)
    g = g.filter(ImageFilter.UnsharpMask(radius=3, percent=95, threshold=3))

    img = g.convert("RGB").point(duotone_lut())

    made = []
    for w in WIDTHS:
        if w > img.width:            # never upscale
            continue
        h = round(img.height * w / img.width)
        dst = os.path.join(OUT, f"{NAME}-{w}.webp")
        img.resize((w, h), Image.LANCZOS).save(dst, "WEBP", quality=QUALITY, method=6)
        made.append(f"{w}w {os.path.getsize(dst)/1024:.0f}KB")

    print(f"{NAME}: source {Image.open(SRC).size} -> crop {img.size}")
    print("  " + " · ".join(made))


if __name__ == "__main__":
    main()
