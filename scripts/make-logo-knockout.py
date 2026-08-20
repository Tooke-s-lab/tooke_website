#!/usr/bin/env python3
"""
Builds a clean white knockout of the stacked logo, for use on dark photographs.

Why this is needed: assets/logo-stacked.png was recovered from inside a
PowerPoint rendering by knocking white to transparency with
`alpha = 255 - min(r, g, b)`. That works for placing the logo on a pale ground,
but it leaves the artwork with *proportional* alpha rather than solid alpha —
the teal molecule (#47A284, min channel 0x47) only reaches alpha 184, and the
JPEG noise around the artwork survives at alpha 30-90.

Knock that out to white with a CSS filter and you get exactly what you'd
expect: the molecule renders as 72% white (muddy grey, not white), the noise
renders as a visible speckle field, and the frame edge from the original
rendering shows up as a ghost rectangle behind the mark.

The fix is a curve on the alpha channel, not a threshold: everything at or
above SOLID becomes fully opaque, everything at or below FLOOR disappears, and
the band between them is left as a ramp so edges stay antialiased instead of
going jagged. RGB is then set to pure white everywhere, so the CSS filter is no
longer doing any work and can be dropped.

Usage:  python scripts/make-logo-knockout.py
Output: assets/logo-stacked-white.png
"""

from PIL import Image

SRC = "assets/logo-stacked.png"
DST = "assets/logo-stacked-white.png"

FLOOR = 58    # at/below this, it is extraction noise — drop it
SOLID = 124   # at/above this, it is artwork — make it fully opaque


def main():
    im = Image.open(SRC).convert("RGBA")
    a = im.getchannel("A")

    span = SOLID - FLOOR
    curve = [0 if v <= FLOOR else 255 if v >= SOLID
             else round((v - FLOOR) * 255 / span) for v in range(256)]
    a = a.point(curve)

    out = Image.new("RGBA", im.size, (255, 255, 255, 0))
    out.putalpha(a)
    out.save(DST, optimize=True)

    h = a.histogram()
    print("%s -> %s  (%dx%d)" % (SRC, DST, *im.size))
    print("  fully transparent : %d px" % h[0])
    print("  fully opaque      : %d px" % h[255])
    print("  antialiased edge  : %d px" % sum(h[1:255]))


if __name__ == "__main__":
    main()
