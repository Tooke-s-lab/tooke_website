#!/usr/bin/env python3
"""
Resolves the lab's publications from Europe PMC and renders each paper's first
page as a thumbnail for the publications list on the research page.

Nothing here is typed in by hand: the search is by author, and the title,
authors, journal, year, DOI, citation count and link all come back from Europe
PMC. That matters on a publications page — a hand-keyed DOI that points at the
wrong paper is worse than no link at all, and a hand-kept list goes stale the
moment something new is published. Re-run this and the page is current.

First pages come from `europepmc.org/articles/<PMCID>?pdf=render`, which serves
the PDF for anything Europe PMC holds full text for. Papers with no PMCID (still
paywalled, or too new to be deposited) get no thumbnail and the site falls back
to a typographic card; this script prints which ones, so they can be supplied by
hand — drop a file named `pub-<key>.webp` into assets/publications and it will
be picked up.

Records with no journal are dropped: in Europe PMC those are almost always the
preprint of a paper that also appears here in its published form, and listing
both makes it look as though the lab published the same work twice.

The list is peer-reviewed journal articles only. Preprints, a thesis and a
conference abstract were added on request and then deliberately removed again
(20 Aug): a preprint sits in the list alongside its own published version and
reads as the same work counted twice, and a thesis or an abstract listed among
journal papers flattens a distinction the reader is entitled to see.

If something ever does need adding by hand — a book chapter, say — create
publications-extra.json holding a list of records shaped like the
output below, and it is merged in automatically; the file is optional and the
script simply skips it when absent. Extras are matched against the API results
by title, so if one later appears in a journal the published record wins and the
extra drops out rather than becoming a duplicate. Give a record a 'kind' field
(for example 'Book chapter') and the list labels it as such.

Usage:  python scripts/fetch-publications.py
Output: assets/publications/pub-<key>.webp
        publications.json
"""

import io
import os
import re
import json
import time
import urllib.parse
import urllib.request

import fitz  # pymupdf
from PIL import Image

AUTHOR = "Tooke CL"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PDF = "https://europepmc.org/articles/%s?pdf=render"
UA = {"User-Agent": "Mozilla/5.0 (compatible; tooke-lab-site build script)"}
OUT_IMG = "assets/publications"
OUT_JSON = "publications.json"
OUT_DATA_JS = "publications-data.js"
EXTRA = "publications-extra.json"
THUMB_W = 480          # ~2x the 240px the card shows it at
MAX_THUMB_ASPECT = 1.6  # crop the page to the top if it is very tall


def get(url, timeout=60):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout).read()


def fetch_all():
    url = "%s?query=%s&format=json&pageSize=100&resultType=core" % (
        API, urllib.parse.quote('AUTH:"%s"' % AUTHOR))
    return json.loads(get(url))["resultList"]["result"]


def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "")          # strip <i>, <sub> etc
    return re.sub(r"\s+", " ", t).strip().rstrip(".")


def key_for(rec, taken):
    base = re.sub(r"[^a-z0-9]+", "-", clean(rec.get("title", "")).lower())
    base = "-".join([w for w in base.split("-") if w][:4]) or "paper"
    k, n = base, 2
    while k in taken:
        k, n = "%s-%d" % (base, n), n + 1
    return k


def authors(rec):
    lst = rec.get("authorList", {}).get("author", [])
    if not lst:
        return (rec.get("authorString") or "").split(",")[0].strip()
    first = lst[0].get("fullName") or lst[0].get("lastName", "")
    return first + (" et al." if len(lst) > 1 else "")


def thumbnail(pdf_bytes, dst):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    zoom = THUMB_W / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    # A4 is ~1.41:1; some journals use a longer page. Crop from the top so the
    # title block is always what shows rather than shrinking the whole page.
    if im.height / im.width > MAX_THUMB_ASPECT:
        im = im.crop((0, 0, im.width, int(im.width * MAX_THUMB_ASPECT)))
    im.save(dst, "WEBP", quality=80, method=6)
    return im.size


def main():
    os.makedirs(OUT_IMG, exist_ok=True)
    records = fetch_all()
    print("  %d records for %s" % (len(records), AUTHOR))

    seen, out = set(), []
    for rec in records:
        journal = (rec.get("journalInfo", {}).get("journal", {})
                   .get("medlineAbbreviation")) or ""
        if not journal:
            continue                                  # preprint duplicate
        dedupe = (rec.get("doi") or clean(rec.get("title", "")).lower())
        if dedupe in seen:
            continue
        seen.add(dedupe)

        item = {
            "title": clean(rec.get("title", "")),
            "authors": authors(rec),
            "year": rec.get("pubYear", ""),
            "journal": journal,
            "doi": rec.get("doi", ""),
            "url": ("https://doi.org/" + rec["doi"]) if rec.get("doi")
                   else ("https://europepmc.org/article/MED/%s" % rec["pmid"]
                         if rec.get("pmid") else ""),
            "citations": rec.get("citedByCount", 0),
            "thumb": None,
        }
        item["key"] = key_for(rec, {i["key"] for i in out})

        pmcid = rec.get("pmcid")
        if pmcid:
            dst = os.path.join(OUT_IMG, "pub-%s.webp" % item["key"])
            if os.path.exists(dst):
                item["thumb"] = os.path.basename(dst)
                with Image.open(dst) as im:
                    item["thumbW"], item["thumbH"] = im.size
            else:
                # Europe PMC rate-limits a fast run, which looks identical to
                # a paywall from here. Back off and retry before giving up.
                for attempt in range(3):
                    try:
                        w, h = thumbnail(get(PDF % pmcid), dst)
                        item["thumb"] = os.path.basename(dst)
                        item["thumbW"], item["thumbH"] = w, h
                        break
                    except Exception as e:
                        if attempt == 2:
                            print("     %-38s no PDF (%s)" % (item["key"], type(e).__name__))
                        else:
                            time.sleep(3 * (attempt + 1))
                time.sleep(1.2)
        out.append(item)

    # --- merge the hand-maintained extras -----------------------------------
    def words(t):
        return set(re.sub(r"[^a-z0-9 ]", " ", t.lower()).split())

    added, superseded = 0, []
    if os.path.exists(EXTRA):
        for x in json.load(io.open(EXTRA, encoding="utf8")):
            xw = words(x["title"])
            # A published record covering the same work wins. 0.6 of the shorter
            # title's words overlapping catches retitling between preprint and
            # journal version, which is common, without merging unrelated papers.
            match = None
            for p in out:
                pw = words(p["title"])
                if len(xw & pw) / max(1, min(len(xw), len(pw))) >= 0.6:
                    match = p
                    break
            if match:
                superseded.append((x["title"], match["title"], match["journal"]))
                continue
            x.setdefault("citations", 0)
            x.setdefault("thumb", None)
            x.setdefault("key", re.sub(r"[^a-z0-9]+", "-",
                                       x["title"].lower())[:40].strip("-"))
            # An extra can still have a first page supplied by hand.
            dst = os.path.join(OUT_IMG, "pub-%s.webp" % x["key"])
            if os.path.exists(dst):
                x["thumb"] = os.path.basename(dst)
                with Image.open(dst) as im:
                    x["thumbW"], x["thumbH"] = im.size
            out.append(x)
            added += 1

    out.sort(key=lambda r: (r["year"] or "0", r["citations"]), reverse=True)
    json.dump(out, io.open(OUT_JSON, "w", encoding="utf8"),
              indent=1, ensure_ascii=False)

    # Same data as a plain script file. fetch() is blocked on a file:// origin,
    # so a page opened by double-clicking it in Explorer — which is how this gets
    # previewed — would otherwise show an empty publications list. A <script> tag
    # has no such restriction, so the list works with or without a web server.
    header = "/* Generated by scripts/fetch-publications.py — do not edit by hand. */"
    io.open(OUT_DATA_JS, "w", encoding="utf8", newline="").write(
        header + "\nwindow.__TOOKE_PUBS = "
        + json.dumps(out, indent=1, ensure_ascii=False) + ";\n")

    if added:
        print("  +%d from %s" % (added, EXTRA))
    for t, m, j in superseded:
        print("  SKIPPED extra (already here as the published version):")
        print("     %s" % t[:72])
        print("     -> %s (%s)" % (m[:66], j))

    withthumb = [i for i in out if i["thumb"]]
    print("\n  %d publications -> %s" % (len(out), OUT_JSON))
    print("  %d with a first-page image, %d without"
          % (len(withthumb), len(out) - len(withthumb)))
    for i in out:
        if not i["thumb"]:
            print("     needs an image by hand: assets/publications/pub-%s.webp"
                  "   (%s %s)" % (i["key"], i["year"], i["journal"]))


if __name__ == "__main__":
    main()
