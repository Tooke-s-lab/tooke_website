#!/usr/bin/env python3
"""
Converts photos dropped into incoming/ into the web-ready files the site uses.

Why this exists:
  Changing a photo here is not "replace one file". A hero image is three files
  at three widths; a scope image is two, cropped to 4:3; a portrait is a square
  crop; and the <img> tags declare width/height that check-links.py verifies
  against the real file. On top of all that, photos off a phone are HEIC, which
  no browser can display.

  Doing that by hand needs a terminal, Python and Pillow. The people who own the
  content have none of those and should not have to. So this runs on GitHub's
  machines instead (.github/workflows/photos.yml), triggered by uploading a file
  through the GitHub website: no clone, no terminal, nothing installed.

What it does:
  incoming/replace/<slot>.<ext>  ->  rebuilds assets/photos/<slot>-<width>.webp
                                     at exactly the widths the pages ask for,
                                     then syncs the declared width/height.
  incoming/news/<name>.<ext>     ->  assets/news/<name>.webp, and prints the
                                     line to paste into news-data.js.

  The raw upload is deleted once it has been converted, so the phone-sized
  original never ships.

The HTML is the source of truth for which widths exist. That is deliberate: the
bug check-links.py was written for was a page asking for a width that had never
been generated, which 404s only on high-DPI screens. Generating exactly what the
pages reference makes that unrepresentable rather than merely detectable.

Usage:  python scripts/convert-incoming-photos.py            (from the repo root)
        python scripts/convert-incoming-photos.py --dry-run
Exit:   1 if an upload cannot be used, so it can fail a CI run visibly.
"""

import os
import re
import sys
import glob

from PIL import Image, ImageOps, ImageEnhance

# Only needed for HEIC/HEIF, which is what phones produce. Imported lazily so
# the script still runs for JPEG/PNG on a machine without it.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF = True
except ImportError:
    HEIF = False

PHOTOS = "assets/photos"
NEWS = "assets/news"
IN_REPLACE = "incoming/replace"
IN_NEWS = "incoming/news"

QUALITY = 78          # matches prepare-photos.py, so a replacement sits in the set
NEWS_QUALITY = 82     # matches prepare-news-photo.py
NEWS_MAXW = 1400      # matches prepare-news-photo.py
SCOPE_ASPECT = 4 / 3  # the frame the scope slideshow crops to

RAW = (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")

# Same reference shapes check-links.py looks for: src/href, srcset candidates,
# and the inline url('...') the route cards use for their background.
REF = re.compile(r'(?:src|href)="([^"]+\.webp)"')
SRCSET = re.compile(r'srcset="([^"]+)"')
CSSURL = re.compile(r"url\('([^']+)'\)")
IMGTAG = re.compile(r"<img\b[^>]*>", re.S)
ATTR = re.compile(r'(\w+)="([^"]*)"')
SLOT = re.compile(r"^(?P<slot>.+)-(?P<width>\d+)\.webp$")


def photo_refs(text):
    """Every assets/photos/*.webp this page asks the browser to fetch."""
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
    return {r for r in out if r.startswith(PHOTOS + "/")}


def scan_slots():
    """slot name -> the set of widths the pages reference for it.

    Read from the HTML rather than from what happens to be on disk, so a slot
    can never be rebuilt at a width no page uses, nor miss one that a page does.
    """
    slots = {}
    for page in sorted(glob.glob("*.html")):
        text = open(page, encoding="utf8").read()
        for ref in photo_refs(text):
            m = SLOT.match(os.path.basename(ref))
            if m:
                slots.setdefault(m.group("slot"), set()).add(int(m.group("width")))
    return slots


def grade(im):
    """The grade prepare-photos.py applies to the existing set. A replacement
    that skips it would be visibly punchier than everything around it."""
    im = ImageEnhance.Color(im).enhance(0.88)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return im


def crop_to_aspect(im, aspect):
    w, h = im.size
    if w / h > aspect:
        new = int(round(h * aspect))
        x = (w - new) // 2
        return im.crop((x, 0, x + new, h))
    new = int(round(w / aspect))
    y = (h - new) // 2
    return im.crop((0, y, w, y + new))


def square_crop(im):
    """Centred horizontally, biased up the frame: in a head-and-shoulders shot
    the face sits above the middle, and the avatars are circles, so a dead-centre
    square puts the chin in the middle of the circle."""
    w, h = im.size
    side = min(w, h)
    x = (w - side) // 2
    y = max(0, min(h - side, int(h * 0.42) - side // 2))
    return im.crop((x, y, x + side, y + side))


def prepare(im, slot):
    """Everything that happens once, before the per-width resizes."""
    im = ImageOps.exif_transpose(im)      # phones record rotation in EXIF
    im = im.convert("RGB")
    if slot.startswith("person-"):
        return square_crop(im)
    if slot.startswith("scope-"):
        return crop_to_aspect(im, SCOPE_ASPECT)
    return grade(im)


def sync_declared_sizes(rebuilt, dry_run):
    """Point each <img>'s declared width/height at what the new file actually is.

    A replacement photo rarely has the same shape as the one it replaces, and a
    stale declaration makes the page jump as the image loads. check-links.py
    reports that; this stops it happening in the first place.
    """
    changed = []
    for page in sorted(glob.glob("*.html")):
        text = open(page, encoding="utf8", newline="").read()
        out = text
        for tag in IMGTAG.findall(text):
            a = dict(ATTR.findall(tag))
            src = a.get("src")
            if not src or src not in rebuilt:
                continue

            # Nothing here can know what is in the new picture, and the old
            # description survives the swap looking perfectly valid. A blind
            # person gets told about a photograph that is no longer there, and
            # no check can catch it -- so say it out loud, every time.
            # Not for portraits: their alt text is the person's name, and a new
            # photo of Xandi is still a photo of Xandi. Warning there would cry
            # wolf on the one case that is almost always already correct.
            alt = (a.get("alt") or "").strip()
            if alt and not os.path.basename(src).startswith("person-"):
                changed.append('%s: the alt text for %s still describes the OLD '
                               'photo -- "%s". Edit it to describe the new one.'
                               % (page, os.path.basename(src), alt))

            if not (a.get("width") and a.get("height")):
                continue
            with Image.open(src) as im:
                fw, fh = im.size
            if (str(fw), str(fh)) == (a["width"], a["height"]):
                continue
            new = re.sub(r'width="\d+"', 'width="%d"' % fw, tag)
            new = re.sub(r'height="\d+"', 'height="%d"' % fh, new)
            out = out.replace(tag, new)
            changed.append("%s: %s now declared %dx%d (was %sx%s)"
                           % (page, os.path.basename(src), fw, fh,
                              a["width"], a["height"]))
        if out != text and not dry_run:
            open(page, "w", encoding="utf8", newline="").write(out)
    return changed


def uploads(folder):
    if not os.path.isdir(folder):
        return []
    found = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        if name.lower().endswith(".md"):        # the folder's own README
            continue
        # Reported back to a person, who will be looking at a URL, not a
        # Windows path -- keep the separator the same in both places.
        found.append(path.replace(os.sep, "/"))
    return found


def open_source(path, problems):
    ext = os.path.splitext(path)[1].lower()
    if ext not in RAW:
        problems.append("%s is a %s file. Upload a photo: %s."
                        % (path, ext or "no-extension", ", ".join(RAW)))
        return None
    if ext in (".heic", ".heif") and not HEIF:
        problems.append("%s is HEIC and pillow-heif is not installed here. "
                        "Run: python -m pip install pillow-heif" % path)
        return None
    try:
        return Image.open(path)
    except Exception as e:
        problems.append("%s could not be opened as an image (%s)." % (path, e))
        return None


def do_replacements(slots, dry_run, problems, notes, done):
    rebuilt = set()
    for path in uploads(IN_REPLACE):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem not in slots:
            problems.append(
                "%s does not name a photo on the site.\n"
                "     The name before the dot must be one of:\n       %s"
                % (path, "\n       ".join(sorted(slots))))
            continue

        im = open_source(path, problems)
        if im is None:
            continue

        widths = sorted(slots[stem])
        base = prepare(im, stem)

        need = max(widths)
        have = min(base.size) if stem.startswith("person-") else base.width
        if have < need:
            problems.append(
                "%s is too small. %s is used at up to %dpx and your photo only "
                "gives %dpx after cropping. Upscaling would look soft, and the "
                "page would ask for a size that cannot exist. Use a larger "
                "original." % (path, stem, need, have))
            continue

        for w in widths:
            if stem.startswith("person-"):
                out = base.resize((w, w), Image.LANCZOS)
            else:
                h = round(base.height * w / base.width)
                out = base.resize((w, h), Image.LANCZOS)
            dst = "%s/%s-%d.webp" % (PHOTOS, stem, w)
            if not dry_run:
                out.save(dst, "WEBP", quality=QUALITY, method=6)
            rebuilt.add(dst)
            done.append("%s  (%dx%d)" % (dst, out.width, out.height))

        # Portraits are written at whatever width the page declares. If the
        # source could have carried more detail, say so rather than silently
        # throwing it away -- the fix is a one-line HTML change, not a reupload.
        if stem.startswith("person-") and min(base.size) > max(widths):
            notes.append("%s is declared at %dpx in the HTML, but your photo "
                         "could support %dpx. Ask for the page to be updated if "
                         "you want it sharper."
                         % (stem, max(widths), min(base.size)))

        if not dry_run:
            os.remove(path)
    return rebuilt


def do_news(dry_run, problems, notes, done):
    for path in uploads(IN_NEWS):
        stem = os.path.splitext(os.path.basename(path))[0]
        safe = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
        if not safe:
            problems.append("%s has no usable name." % path)
            continue

        im = open_source(path, problems)
        if im is None:
            continue

        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width > NEWS_MAXW:
            h = round(im.height * NEWS_MAXW / im.width)
            im = im.resize((NEWS_MAXW, h), Image.LANCZOS)

        dst = "%s/%s.webp" % (NEWS, safe)
        if not dry_run:
            os.makedirs(NEWS, exist_ok=True)
            im.save(dst, "WEBP", quality=NEWS_QUALITY, method=6)
            os.remove(path)
        done.append("%s  (%dx%d)" % (dst, im.width, im.height))
        notes.append('news photo ready. In news-data.js put:  "photo": "%s.webp"'
                     % safe)


def report(title, lines):
    if not lines:
        return
    print()
    print(title)
    for line in lines:
        print("   - %s" % line)


def main():
    dry_run = "--dry-run" in sys.argv

    if not os.path.isdir(PHOTOS):
        sys.exit("%s is missing - run this from the repo root." % PHOTOS)

    slots = scan_slots()
    if not slots:
        sys.exit("Found no photo references in the pages. That should not "
                 "happen from the repo root; check where this is running.")

    problems, notes, done = [], [], []
    rebuilt = do_replacements(slots, dry_run, problems, notes, done)
    do_news(dry_run, problems, notes, done)

    if rebuilt:
        notes.extend(sync_declared_sizes(rebuilt, dry_run))

    if not done and not problems:
        print("Nothing to convert: incoming/ is empty.")
        return 0

    report("WROTE", done)
    report("NOTE", notes)

    if problems:
        print()
        print("COULD NOT USE (%d):" % len(problems))
        for p in problems:
            print("   - %s" % p)
        print()
        print("Nothing was changed for the files listed above. Fix the name or "
              "the photo and upload it again.")
        return 1

    print()
    print("Done%s." % (" (dry run - nothing written)" if dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
