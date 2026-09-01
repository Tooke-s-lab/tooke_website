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

import io
import os
import re
import sys
import glob

from PIL import Image, ImageOps, ImageEnhance, ImageCms

# HEIC is what an iPhone produces by default and what a Pixel produces if its
# camera is set to "storage saver". Optional so the script still runs for JPEG
# and PNG on a machine without it; the workflow always installs it.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF = True
except ImportError:
    HEIF = False

# Pillow 11.3 and later read AVIF natively. Older ones can with a plugin, so try
# that too rather than telling someone their perfectly good photo is unreadable.
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

SRGB = ImageCms.createProfile("sRGB")

PHOTOS = "assets/photos"
NEWS = "assets/news"
IN_REPLACE = "incoming/replace"
IN_NEWS = "incoming/news"

QUALITY = 78          # matches prepare-photos.py, so a replacement sits in the set
NEWS_QUALITY = 82     # matches prepare-news-photo.py
NEWS_MAXW = 1400      # matches prepare-news-photo.py
SCOPE_ASPECT = 4 / 3  # the frame the scope slideshow crops to

# The full set of widths each family is designed around.
#
# Held here rather than read from the pages for one reason: a small upload drops
# the rungs it cannot fill, and if the ladder were only ever "what the HTML
# currently says", that drop would be permanent. The first 900px figure anybody
# uploaded would quietly cap that slot at 800px forever, and no later photo,
# however good, could raise it again. With a fixed ladder the change goes both
# ways -- a big upload restores the rungs a small one removed.
LADDERS = (
    ("hero-", (1200, 1920, 2560)),
    ("crystal-drops", (1200, 1920, 2560)),
    ("scope-", (800, 1600)),
    ("route-", (800,)),
    ("person-", (320,)),
)

# Camera RAW extensions, kept only so a RAW upload gets a useful sentence rather
# than a decode error. Every one of these is a TIFF underneath, so sniff() sees
# them as "tiff" and Pillow then fails to make sense of the payload.
RAW_EXT = (".dng", ".raw", ".arw", ".cr2", ".cr3", ".nef", ".orf", ".rw2",
           ".raf", ".srw", ".pef")

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


def flatten_alpha(im):
    """Put transparency onto white rather than letting it become black.

    .convert("RGB") on a transparent PNG composites onto black, which turns a
    screenshot's rounded corners into black notches. Nobody uploads a photo with
    an alpha channel on purpose, but screenshots and exported figures have one.
    """
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        icc = im.info.get("icc_profile")
        rgba = im.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        out = Image.alpha_composite(white, rgba).convert("RGB")
        if icc:
            out.info["icc_profile"] = icc     # convert() drops it; colour next
        return out
    return im


def to_srgb(im):
    """Convert a wide-gamut photo into sRGB instead of reinterpreting it.

    Both Pixels and iPhones tag their photos Display P3, a wider gamut than the
    sRGB a browser assumes when a file carries no profile. Dropping the profile
    and keeping the numbers -- which is what .convert("RGB") does -- leaves every
    colour reading as a more saturated version of itself: skin goes ruddy, the
    teal in the branding goes acid. It looks like a deliberate grade, so it gets
    argued about rather than fixed.

    Converting properly and shipping no profile is the right pair: the numbers
    are moved into sRGB, which is exactly what an untagged file is taken to be.
    """
    icc = im.info.get("icc_profile")
    if not icc:
        return im                              # untagged: already assumed sRGB
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        if ImageCms.getProfileDescription(src).strip().lower().startswith("srgb"):
            return im
        return ImageCms.profileToProfile(im, src, SRGB, outputMode="RGB")
    except Exception:
        # A broken or exotic profile is not worth failing an upload over; the
        # untagged fallback is what the site did before this existed.
        return im


def prepare(im, slot):
    """Everything that happens once, before the per-width resizes."""
    im = ImageOps.exif_transpose(im)      # phones record rotation in EXIF
    im = flatten_alpha(im)
    im = to_srgb(im)
    im = im.convert("RGB")
    if slot.startswith("person-"):
        return square_crop(im)
    if slot.startswith("scope-"):
        return crop_to_aspect(im, SCOPE_ASPECT)
    return grade(im)


def ladder_for(slot, declared):
    """Every width this slot could have, whether or not it currently has it.

    The family ladder wins outright over what the pages currently say, rather
    than being merged with it. Merging looks kinder and is a trap: an undersized
    upload writes a one-off width into the HTML (565px, say), the next run reads
    that back as a legitimate rung, and the slot carries the odd size for good.
    Taking the ladder as authoritative means those one-offs are cleaned up by
    the next upload instead of accumulating.
    """
    for prefix, widths in LADDERS:
        if slot.startswith(prefix):
            return sorted(widths)
    return sorted(declared)


def rewrite_refs(slot, old_widths, new_widths, dry_run):
    """Point the pages at the sizes that now exist, and only those.

    A photo that cannot fill the top of the ladder used to be refused outright.
    That was too strict to live with: a figure from a paper or a microscope
    capture is often 900px, and it is frequently the only copy in existence.

    So the srcset shrinks to fit instead. Nothing is ever upscaled -- the file
    written is exactly as big as the photo really is -- and because the page is
    rewritten to match, it never asks for a size that does not exist, which is
    the failure check-links.py was written for.
    """
    olds, news = sorted(old_widths), sorted(new_widths)
    prefix = "%s/%s-" % (PHOTOS, slot)
    changed = []

    def nearest(w):
        below = [n for n in news if n <= w]
        return max(below) if below else min(news)

    def rebuild(m):
        body = m.group(1)
        cands = [c.strip().split()[0] for c in body.split(",") if c.strip()]
        # Only touch a srcset that is entirely this slot's. A mixed one would be
        # destroyed by rebuilding it from one slot's widths.
        if not cands or not all(c.startswith(prefix) for c in cands):
            return m.group(0)
        gap = re.search(r",\s*\n(\s*)", body)
        sep = ",\n" + gap.group(1) if gap else ", "
        return 'srcset="%s"' % sep.join(
            "%s%d.webp %dw" % (prefix, w, w) for w in news)

    for page in sorted(glob.glob("*.html")):
        text = open(page, encoding="utf8", newline="").read()
        if prefix not in text:
            continue
        # [^"]+ spans newlines, so this matches the srcsets written over
        # several lines as well as the ones written on one.
        out = SRCSET.sub(rebuild, text)

        # Whatever is left pointing at a width that no longer exists -- the src
        # fallback, and the url('...') the home-page cards use.
        for w in olds:
            if w not in news:
                out = out.replace("%s%d.webp" % (prefix, w),
                                  "%s%d.webp" % (prefix, nearest(w)))
        if out != text:
            if not dry_run:
                open(page, "w", encoding="utf8", newline="").write(out)
            changed.append(page)

    # The dropped sizes are now referenced by nothing. Leaving them would break
    # the rule that everything in assets/ is used by a page.
    for w in olds:
        if w not in news:
            stale = "%s%d.webp" % (prefix, w)
            if os.path.exists(stale) and not dry_run:
                os.remove(stale)

    return changed


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


def sniff(path):
    """Identify the file from its first bytes rather than its name.

    Extensions lie. Phones, chat apps and Google Photos all rename things on the
    way out, people rename them by hand, and Windows hides the extension while
    they do it. The bytes do not lie, so a photo saved as `.jpg` that is really
    HEIC still converts, and a video renamed `.jpg` is still caught.
    """
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return "unreadable"

    if head[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[4:8] == b"ftyp":
        # One container, many meanings. The brand says which.
        brand = head[8:12]
        if brand in (b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx",
                     b"hevm", b"hevs", b"mif1", b"msf1"):
            return "heif"
        if brand in (b"avif", b"avis"):
            return "avif"
        return "video"
    if head[:2] in (b"II", b"MM"):
        # TIFF byte order marks. Every camera RAW is a TIFF underneath, so this
        # covers .dng/.cr2/.nef/.arw as well as an actual .tif.
        return "tiff"
    return "unknown"


def open_source(path, problems):
    """Open an upload, or explain -- in terms its owner can act on -- why not."""
    kind = sniff(path)
    ext = os.path.splitext(path)[1].lower()

    if kind == "unreadable":
        problems.append("%s could not be read at all." % path)
        return None

    if kind == "video":
        problems.append(
            "%s is a video, not a photo.\n"
            "     If this came off a Pixel it is probably a Motion Photo. Open "
            "it in Google Photos, use Export > Still photo (or the three-dot "
            "menu > Export), and upload the still." % path)
        return None

    if kind == "heif" and not HEIF:
        problems.append("%s is HEIC/HEIF and pillow-heif is not installed here. "
                        "Run: python -m pip install pillow-heif\n"
                        "     (On GitHub it is always installed, so this only "
                        "happens when running the script locally.)" % path)
        return None

    if kind == "unknown":
        problems.append("%s is not an image file. Its name says %s, but the "
                        "contents are not a photo in any format this "
                        "understands." % (path, ext or "no extension"))
        return None

    try:
        # Read into memory rather than opening the path. Pillow keeps the file
        # handle alive behind a lazily-decoded image, and Windows will not let
        # you delete a file that is still open -- so the tidy-up at the end of a
        # successful conversion failed there while working fine on Linux. A
        # phone photo is a few MB; holding it in memory costs nothing.
        with open(path, "rb") as f:
            data = f.read()
        im = Image.open(io.BytesIO(data))
        im.load()               # force the decode now, so a truncated upload
        return im               # fails here rather than halfway through a resize
    except Exception as e:
        if kind == "tiff" and ext in RAW_EXT:
            problems.append(
                "%s is a camera RAW file, which cannot be published directly.\n"
                "     Your phone saved an ordinary .jpg of the same shot at the "
                "same moment -- upload that one instead." % path)
        elif kind == "avif":
            problems.append(
                "%s is an AVIF image and this copy of Pillow cannot read it "
                "(needs Pillow 11.3 or newer). Re-save it as JPEG, or run "
                "python -m pip install --upgrade pillow." % path)
        else:
            problems.append("%s looks like a %s file but could not be decoded "
                            "(%s). It may have been truncated by the upload."
                            % (path, kind, e))
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

        declared = sorted(slots[stem])
        base = prepare(im, stem)

        # A portrait is cropped square, so its limit is the short side.
        have = min(base.size) if stem.startswith("person-") else base.width
        ladder = ladder_for(stem, declared)
        widths = [w for w in ladder if w <= have]
        undersized = not widths

        if undersized:
            # Smaller than even the bottom of the ladder. Write it at its true
            # size rather than refusing: it is usually a figure or a microscope
            # capture, and often the only copy that exists. The browser will
            # stretch it, so say so plainly -- and it is visible in the preview.
            widths = [have]
            notes.append(
                "%s is only %dpx wide, smaller than the %dpx this slot normally "
                "uses. It is written at its real size rather than being blown "
                "up, so nothing is faked -- but the page will stretch it and it "
                "WILL look soft, most of all on a laptop screen. Look at the "
                "preview before merging, and use a bigger original if there is "
                "one." % (path, have, min(ladder)))

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

        if sorted(widths) != declared:
            gone = [w for w in declared if w not in widths]
            added = [w for w in widths if w not in declared]
            rewrite_refs(stem, declared, widths, dry_run)
            # A dropped width below the new top is a leftover being cleaned up,
            # not a size the photo failed to reach. Saying "not big enough" for
            # a 565px rung removed by a 4032px photo reads as nonsense.
            too_big = [w for w in gone if w > max(widths)]
            leftover = [w for w in gone if w <= max(widths)]
            if too_big:
                notes.append("%s: dropped the %s size%s, which your photo is "
                             "not big enough for. The pages now ask only for "
                             "what exists."
                             % (stem, ", ".join("%dpx" % w for w in too_big),
                                "" if len(too_big) == 1 else "s"))
            if leftover:
                notes.append("%s: removed the odd %s size left behind by an "
                             "earlier undersized photo."
                             % (stem, ", ".join("%dpx" % w for w in leftover)))
            # Not when undersized: the one width there is the photo's own size,
            # a fallback rather than a rung gained, and calling it an upgrade
            # would contradict the warning printed directly above it.
            if added and not undersized:
                notes.append("%s: added the %s size%s, which the previous photo "
                             "was too small for. Sharper on high-resolution "
                             "screens."
                             % (stem, ", ".join("%dpx" % w for w in added),
                                "" if len(added) == 1 else "s"))

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
