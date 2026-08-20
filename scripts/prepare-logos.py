#!/usr/bin/env python3
"""
Normalises partner logos into one consistent monochrome set.

Why: the source logos are wildly inconsistent — Bristol is a black-and-red
wordmark at 740x214, Oxford is a navy square crest on a white backing tile,
Ljubljana is grey at 143x54, Bath ships white-only, Diamond is a 168x53 PNG.
Dropped into one banner raw they read as a ransom note.

Rendering every mark in a single ink tone at matched optical size is the standard
fix for a partner logo strip: it looks deliberate rather than scraped, and most
institutions explicitly permit a single-colour version of their logo.

Heuristics do NOT work here — "strip the white bits" destroys Bath entirely
(its mark is white) and guts Oxford (white lettering on a navy field). So the
per-logo handling is explicit.

The set grew from six to eleven when the SWSBC 2026 deck was mined for marks
that were never sourced from the web -- SMU (previously a text placeholder),
SWBio DTP, PAL-XFEL, Berkeley and the INEOS Oxford Institute. Those arrive as
slide rasters rather than vectors, so they are keyed to alpha rather than
repainted: darkness drives opacity for a dark mark on a light ground, lightness
drives it for a white mark reversed out of a coloured tile. Keying beats a flat
fill for the same reason it does for Diamond -- SWBio's daisy is white petals
inside black outlines, and a flat fill would turn it into a blob.

Usage:  python scripts/prepare-logos.py
Output: assets/brand/norm/
"""

import os
import re

LIGHT_FLOOR = 0.45      # see do_png_key: tone below this is field, not artwork
INK = "#55605D"          # --ink-soft, so the marks sit with the banner's text
SRC = "assets/brand"
OUT = "assets/brand/norm"

# One explicit entry per mark: source file, output name, and how to get it to ink.
#   svg      strip the listed <path> indices, then repaint every fill/stroke
#   diamond  the bespoke gold-circle mask described in do_png below
#   dark     raster, dark artwork on a white or transparent ground
#            -> opacity follows darkness, so the ground drops out
#   light    raster, white artwork reversed out of a coloured tile
#            -> opacity follows lightness, so the tile drops out
LOGOS = [
    # source                            output          mode       options
    # Bath's own dark version, supplied by the collaborator. It replaces the
    # white-on-dark SVG as the source for the strip: same mark, but no longer
    # arrived at by inverting one. The white SVG stays in use in the footer,
    # which sits on ink and needs the reversed version.
    ("Uob-logo-dark.png",               "bath.png",     "dark",    {}),
    ("bristol.svg",                     "bristol.svg",  "svg",     {}),
    # 0 = white backing tile, 1 = navy field. The crest and lettering are the
    # remaining white paths, which become ink.
    ("oxford.svg",                      "oxford.svg",   "svg",     {"drop_paths": [0, 1]}),
    ("ljubljana.svg",                   "ljubljana.svg", "svg",    {}),
    # Prepared but not currently shown -- pulled from the banner by the
    # collaborator, like SWBio. Left here so it can be dropped back in.
    # 26 = the navy square the UKRI letters are reversed out of; 28 and 29 = the
    # cyan wedge beside them. Same treatment as Oxford: drop the coloured fields
    # and let the lettering carry the mark. A flat repaint instead fuses letters
    # and square into one ink block, and turns the wedge into a heavy slab that
    # outweighs every other mark in the banner.
    ("Medical_Research_Council_logo.svg", "mrc.svg",    "svg",     {"drop_paths": [26, 28, 29]}),
    ("diamond.png",                     "diamond.png",  "diamond", {}),
    ("smu.png",                         "smu.png",      "dark",    {}),
    # Prepared but not currently shown -- pulled from the banner by the
    # collaborator. Left here so it can be dropped back in without redoing it.
    ("swbio-dtp.png",                   "swbio-dtp.png", "dark",   {}),
    ("pal-xfel.png",                    "pal-xfel.png", "dark",    {}),
    ("berkeley.png",                    "berkeley.png", "dark",    {}),
    # The slide still is a 640x360 frame holding two tiles side by side against a
    # watermarked backdrop. Only the maroon INEOS tile is wanted -- Oxford's own
    # crest is already in the set -- so crop to it before keying.
    ("ineos-oxford.png",                "ineos-oxford.png", "light", {"crop": (133, 104, 338, 256)}),
]


def drop_indexed_paths(svg, idx):
    if not idx:
        return svg
    out, n = [], 0
    for part in re.split(r'(<path\b[^>]*/>)', svg):
        if part.startswith('<path'):
            if n not in idx:
                out.append(part)
            n += 1
        else:
            out.append(part)
    return ''.join(out)


def drop_white_paths(svg):
    """Remove white-filled paths so a knockout stays a knockout.

    MRC's mark is a navy square with UKRI reversed out of it in white. Repainting
    every fill to ink turns those letters the same ink as the square they sit in,
    and the mark becomes a solid block. The white path has to go, not change
    colour, so the square keeps its holes.
    """
    out = []
    for part in re.split(r'(<path\b[^>]*/>)', svg):
        if part.startswith('<path') and re.search(r'fill\s*[:=]\s*"?#(fff|ffffff)\b', part, re.I):
            continue
        out.append(part)
    return ''.join(out)


def repaint(svg):
    svg = re.sub(r'fill\s*=\s*"(?!none)[^"]*"', 'fill="%s"' % INK, svg)
    svg = re.sub(r'stroke\s*=\s*"(?!none)[^"]*"', 'stroke="%s"' % INK, svg)
    # inline <style> blocks — Bristol uses .cls-1{fill:#1d1d1b}
    svg = re.sub(r'fill\s*:\s*#[0-9a-fA-F]{3,8}', 'fill:%s' % INK, svg)
    svg = re.sub(r'stroke\s*:\s*#[0-9a-fA-F]{3,8}', 'stroke:%s' % INK, svg)
    return svg


def do_svg(src, dst, rule):
    svg = open(src, encoding='utf-8', errors='replace').read()
    svg = drop_indexed_paths(svg, set(rule.get('drop_paths', [])))
    if rule.get('drop_white'):
        svg = drop_white_paths(svg)
    svg = repaint(svg)
    open(dst, 'w', encoding='utf-8', newline='\n').write(svg)
    m = re.search(r'viewBox="([^"]+)"', svg)
    return '%s  (%d paths)' % (m.group(1) if m else '?', svg.count('<path'))


def do_png(src, dst):
    """Repaint to the ink tone while preserving knockouts.

    Diamond's mark is the white-on-dark version: a white wordmark plus a GOLD
    circle with a white star knocked out of it. A flat repaint turns the circle
    and the star the same ink, so the star vanishes and the circle becomes a
    solid blob.

    The star and the wordmark are both pure white, so colour alone can't
    separate them — but the gold circle can. Inside the circle's bounding box,
    opacity is driven by how gold a pixel is (gold -> solid ink, white -> a
    transparent hole, blends -> partial, which keeps the antialiasing clean).
    Outside it, the white wordmark simply becomes ink.
    """
    from PIL import Image
    ink = tuple(int(INK[i:i + 2], 16) for i in (1, 3, 5))
    im = Image.open(src).convert('RGBA')
    px = im.load()
    w, h = im.size

    # Bounding box of the coloured (non-white, non-transparent) element.
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 40 and b < 140:          # gold has B=3; white has B=255
                xs.append(x)
                ys.append(y)

    box = (min(xs), min(ys), max(xs), max(ys)) if xs else None

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                px[x, y] = ink + (0,)
                continue
            inside = box and box[0] <= x <= box[2] and box[1] <= y <= box[3]
            if inside:
                # 1.0 where fully gold, 0.0 where fully white (the star).
                goldness = (255 - b) / 255.0
                px[x, y] = ink + (int(a * goldness),)
            else:
                px[x, y] = ink + (a,)

    im.save(dst)
    return '%dx%d  (knockout preserved)' % (w, h)


def do_png_key(src, dst, mode, crop=None):
    """Raster -> ink, with opacity keyed to tone.

    A flat repaint is wrong for the same reason it is wrong for Diamond: these
    marks carry shape *inside* their artwork. SWBio's daisy is white petals held
    by black outlines, so filling every opaque pixel with one ink turns it into a
    blob. Keying opacity to how dark (or, for a reversed mark, how light) each
    pixel is keeps that internal drawing, and drops the ground out cleanly with
    the antialiasing intact.
    """
    from PIL import Image
    ink = tuple(int(INK[i:i + 2], 16) for i in (1, 3, 5))
    im = Image.open(src).convert('RGBA')
    if crop:
        im = im.crop(crop)
    px = im.load()
    w, h = im.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            if mode == 'light':
                # Straight lightness leaves the tile itself showing as a pale
                # wash behind the lettering, which reads as a grey box in the
                # banner. The floor drops the field outright and rescales what
                # is left, so only the reversed-out artwork survives.
                k = max(0.0, (lum - LIGHT_FLOOR) / (1.0 - LIGHT_FLOOR))
            else:
                k = 1.0 - lum
            px[x, y] = ink + (int(a * k),)

    # Trim the transparent margin so the banner sizes by the mark, not by
    # whatever padding the slide happened to carry.
    box = im.getbbox()
    if box:
        im = im.crop(box)
    im.save(dst)
    return '%dx%d  (%s-keyed)' % (im.size[0], im.size[1], mode)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, dst_name, mode, opts in LOGOS:
        src = os.path.join(SRC, name)
        dst = os.path.join(OUT, dst_name)
        if not os.path.exists(src):
            print('%-36s -- SOURCE MISSING' % name)
            continue
        if mode == 'svg':
            info = do_svg(src, dst, opts)
        elif mode == 'diamond':
            info = do_png(src, dst)
        else:
            info = do_png_key(src, dst, mode, opts.get('crop'))
        print('%-36s -> %-18s %s' % (name, dst_name, info))


if __name__ == '__main__':
    main()
