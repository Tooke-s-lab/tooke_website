#!/usr/bin/env python3
"""
Pulls the media and text out of the PowerPoint decks in the repo root.

A .pptx is just a ZIP: images live in ppt/media/ and the slide copy is in
ppt/slides/slideN.xml. This walks each deck, writes every image out with a name
that records which slide used it, and dumps the slide text alongside so an image
can be traced back to what it was illustrating.

Videos are catalogued but NOT extracted by default — one of them is 192MB.
Pass --with-video to include them.

Usage:  python scripts/extract-pptx.py [--with-video]
Output: source/powerpoint/<deck>/
"""

import os
import re
import sys
import glob
import json
import struct
import zipfile

OUT = "source/powerpoint"
VIDEO_EXT = {".mp4", ".mov", ".avi", ".wmv", ".m4v"}
RASTER = {".png", ".jpg", ".jpeg", ".jfif", ".gif", ".tif", ".tiff", ".bmp"}


def png_size(b):
    try:
        return struct.unpack(">II", b[16:24])
    except Exception:
        return (0, 0)


def jpeg_size(b):
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return (w, h)
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        seg = struct.unpack(">H", b[i + 2:i + 4])[0]
        i += 2 + seg
    return (0, 0)


def dims(name, data):
    e = os.path.splitext(name)[1].lower()
    if e == ".png":
        return png_size(data)
    if e in (".jpg", ".jpeg", ".jfif"):
        return jpeg_size(data)
    return (0, 0)


def slide_media_map(z):
    """Which media file does each slide reference? Resolved via slide rels."""
    used = {}
    for n in z.namelist():
        m = re.match(r"ppt/slides/_rels/(slide(\d+)\.xml)\.rels", n)
        if not m:
            continue
        sn = int(m.group(2))
        rels = z.read(n).decode("utf8", errors="replace")
        for t in re.findall(r'Target="\.\./media/([^"]+)"', rels):
            used.setdefault(t, []).append(sn)
    return used


def slide_text(z):
    out = {}
    for n in z.namelist():
        m = re.match(r"ppt/slides/slide(\d+)\.xml$", n)
        if not m:
            continue
        xml = z.read(n).decode("utf8", errors="replace")
        runs = [t.strip() for t in re.findall(r"<a:t>(.*?)</a:t>", xml) if t.strip()]
        out[int(m.group(1))] = runs
    return out


def main():
    with_video = "--with-video" in sys.argv
    decks = sorted(glob.glob("*.pptx"))
    decks = [d for d in decks if not os.path.basename(d).startswith("~$")]
    if not decks:
        print("No .pptx in the repo root.")
        return

    grand = []
    for deck in decks:
        slug = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(deck))[0].lower()).strip("-")
        dest = os.path.join(OUT, slug)
        os.makedirs(dest, exist_ok=True)

        z = zipfile.ZipFile(deck)
        used = slide_media_map(z)
        texts = slide_text(z)

        print("=" * 74)
        print("%s  ->  %s" % (os.path.basename(deck), dest))
        print("  %d slides" % len(texts))

        rows, skipped = [], 0
        for n in z.namelist():
            if not n.startswith("ppt/media/"):
                continue
            base = os.path.splitext(os.path.basename(n))[0]
            ext = os.path.splitext(n)[1].lower()
            if ext in VIDEO_EXT and not with_video:
                skipped += 1
                rows.append({"file": os.path.basename(n), "kind": "video",
                             "kb": round(z.getinfo(n).file_size / 1024),
                             "slides": used.get(os.path.basename(n), []),
                             "extracted": False})
                continue

            data = z.read(n)
            slides = used.get(os.path.basename(n), [])
            tag = ("s%s_" % "-".join(map(str, slides))) if slides else "unused_"
            path = os.path.join(dest, tag + os.path.basename(n))
            open(path, "wb").write(data)
            w, h = dims(n, data)
            rows.append({"file": os.path.basename(n), "kind": "image" if ext in RASTER else ext.lstrip("."),
                         "kb": round(len(data) / 1024), "w": w, "h": h,
                         "slides": slides, "extracted": True})

        # slide text, so an image can be traced to what it illustrated
        with open(os.path.join(dest, "_slide-text.txt"), "w", encoding="utf8") as fh:
            for i in sorted(texts):
                fh.write("--- slide %d ---\n%s\n\n" % (i, "\n".join(texts[i]) or "(no text)"))

        json.dump(rows, open(os.path.join(dest, "_media.json"), "w", encoding="utf8"), indent=1)

        imgs = [r for r in rows if r.get("extracted")]
        big = [r for r in imgs if r.get("w", 0) >= 1200]
        print("  extracted %d files (%d at >=1200px wide)" % (len(imgs), len(big)))
        if skipped:
            print("  skipped %d video(s) — rerun with --with-video to include" % skipped)
        grand.append((slug, len(imgs), len(big)))

    print("=" * 74)
    for s, a, b in grand:
        print("  %-34s %3d images, %2d large" % (s, a, b))


if __name__ == "__main__":
    main()
