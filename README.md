# The Tooke Lab — website

The website of the Tooke Lab, Department of Life Sciences & Centre for Evolution,
University of Bath.

Static HTML/CSS/JS. **No build step** — the repo root *is* the site. Cloudflare
Pages serves these files exactly as they are committed.

---

## Running it locally

Double-click **`serve.cmd`** (Windows), or:

```bash
python -m http.server 8899
```

Then open `http://localhost:8899/`.

Do not open the `.html` files straight from Explorer. A `file://` address blocks
the structure viewer from loading `.pdb` files and blocks the publications fetch,
so the pages break in ways that have nothing to do with the pages.

> **Use a hard reload (Ctrl+Shift+R) when checking changes.** A `?v=` query on the
> HTML does *not* bust `style.css` or the JS files — they have their own URLs, and
> the browser will happily serve a stale stylesheet while you debug code that was
> never the problem.

---

## Layout

```
index.html            home
research.html         research + the PDB structure browser
people.html           the group
news.html             news — holds NO post markup; news.js renders it
opportunities.html    joining the lab
404.html              not-found page (root-absolute URLs — see DEPLOY.md)

style.css             the whole stylesheet
nav.js                mobile menu
pagehead.js           shared masthead
slideshow.js          research-page slideshow
collection.js         PDB structure browser
news-data.js          EVERY news post — the only file a post changes
news.js               renders the news page from news-data.js
publications-data.js  generated publication list
publications.json     same data, fetched by publications.js
publications.js       renders the publications list

assets/               EVERYTHING HERE IS DEPLOYED — keep it lean
  logo.png              Cat's hand-drawn logo
  favicon.png           site icon
  brand/                partner + university logos
    norm/                 monochrome-normalised versions actually used on the site
  news/                 one photo per news post
  photos/               web-ready WebP at 400/800/1600w
  publications/         one thumbnail per paper
  structures/lite/      16 PDB depositions, backbone + ligand (~95KB each)

scripts/              build steps — all run from the repo ROOT, never deployed
  download-structures.sh   fetch Cat's 16 depositions from RCSB
  optimise-structures.py   strip them down for the web
  cif-to-pdb.py            convert the two mmCIF-only entries
  prepare-photos.py        HEIC -> graded, resized WebP
  prepare-logos.py         normalise partner logos to one ink tone
  fetch-publications.py    rebuild publications-data.js + thumbnails
  prepare-news-photo.py    one photo -> a web-ready .webp for a news post
  check-links.py           verify every referenced local file exists
  check-news.py            verify news-data.js parses and is complete
```

Every file in `assets/` is referenced by a page — that is enforced, not assumed.
Deployed payload is ~7MB.

### Where the originals went

The source material — original iPhone HEICs, raw RCSB downloads, the PowerPoint
decks — is **not in this repo**, on purpose. Cloudflare Pages clones the whole
repository on every build, so ~690MB of inputs would be paid for on every deploy.

It lives in `tooke-lab-archive/` alongside this folder:

```
tooke-lab-archive/
  powerpoints/               SWSBC 2026, CDD figure ideas, the logo deck
  source/photos/             original iPhone HEICs
  source/structures/         raw RCSB downloads
  source/structures-full/    full-detail structures (unused by the site)
  source/people/             original people photos
  source/reference/          earlier concepts, supplied design snippets
  unused-processed-assets/   web-ready images the current site does not use
```

**Back this folder up somewhere durable** (OneDrive or an external drive — not
WhatsApp, which recompresses and destroys photo quality). Everything in `assets/`
can be regenerated from it; nothing in it can be regenerated from `assets/`.

---

## Adding a news post

Nobody should ever edit HTML to publish news. One file changes: **`news-data.js`**.

```bash
python scripts/prepare-news-photo.py <photo> <short-name>   # if there is a photo
# ...write the post into news-data.js...
python scripts/check-news.py
git commit -am "news: ..." && git push
```

`HOW-TO-POST-NEWS.md` is the version to forward to someone who does not code.

`check-news.py` runs inside `build.sh`, so a malformed post **fails the deploy**
rather than silently emptying the news page — which is the whole failure mode
worth engineering against, since the posts are one JSON array and a single
missing comma takes out all of them at once.

There used to be a `studio.html` — a browser form that generated `news-data.js`
and resized the photo for you. It was removed: 650 lines of client-side JS whose
output you still had to commit by hand, sitting on a public research site looking
like an admin panel. The one thing it genuinely did is now
`scripts/prepare-news-photo.py`.

---

## Regenerating assets

Everything in `assets/` is reproducible from the archive — nothing is hand-edited.
Restore `tooke-lab-archive/source/` to `source/` in this folder first; it is
gitignored, so it will not be committed.

```bash
bash scripts/download-structures.sh      # -> source/structures/
python scripts/optimise-structures.py    # -> assets/structures/lite/
python scripts/cif-to-pdb.py             # -> the two mmCIF-only entries
python scripts/prepare-photos.py         # -> assets/photos/   (needs pillow, pillow-heif)
python scripts/prepare-logos.py          # -> assets/brand/norm/
python scripts/fetch-publications.py     # -> publications-data.js + assets/publications/
python scripts/check-links.py            # verify nothing is missing — exit 1 gates a deploy
```

`prepare-photos.py` needs `python -m pip install pillow pillow-heif`. HEIC is an
Apple format that Chrome and Firefox cannot display at all, so the conversion is
not optional.

---

## Before this goes live

Not exhaustive. The blocking ones:

1. **Logo resolution.** `assets/logo.png` is 284×94px — already at its ceiling.
   Cat's original artwork is needed for anything larger.
2. **Photo consent.** Three photos contain identifiable people who have not agreed
   to appear on a public website.
3. **Logo permissions.** The University of Bath, Bristol, Oxford, Diamond and
   Ljubljana logos are trademarks; partner sites normally seek written permission.
4. **Copy.** Most body text is Latin placeholder or bracketed. Everything factual
   still needs Cat to check it.

---

## Deployment

**Cloudflare Pages**, from this git repo. See `DEPLOY.md` for the full setup.

- Build command: *(none)*
- Build output directory: `/`
- Every push to `main` publishes; every push to another branch gets a preview URL.
