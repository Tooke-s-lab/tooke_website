# How to post news

Adding a post is three things: convert the photo, write the post into one file,
push. Nothing else on the site needs touching, and you cannot break the live site
by getting it wrong — a mistake fails the deploy and the old version keeps
serving.

You need the repo on your machine and the ability to push to it.

---

## 1. The photo

**Do not copy a photo into the repo by hand.** Photos off a phone are HEIC, a
format Chrome and Firefox cannot display at all, and they are roughly forty times
larger than the page needs. The site would show a broken image while the file
looks perfectly fine in Explorer.

From the repo root:

```bash
python scripts/prepare-news-photo.py "C:\path\to\IMG_4821.HEIC" beamtime-october
```

The second word is a short name of your choosing — it becomes the filename. It
prints something like:

```
1400x1050, 2.6MB -> 209KB

Now put this in the "photo" field of news-data.js:
    "photo": "beamtime-october.webp",
```

It needs Pillow (`python -m pip install pillow`), plus `pillow-heif` if the photo
is a HEIC. It will tell you if either is missing.

Skip this step entirely if the post has no photo.

---

## 2. The words

Open **`news-data.js`**. It is the only file that changes. It looks like this:

```js
window.__TOOKE_NEWS = [
  {
    "date": "2026-08-12",
    "title": "Beamtime at Diamond",
    "body": "Two or three sentences, first person and friendly.",
    "photo": "news-beamtime-at-diamond.webp",
    "alt": "The experimental hutch at beamline I24."
  }
];
```

Copy one whole `{ ... }` block, paste it **above** the others, and fill it in.

- **newest post first**
- `date` is `YYYY-MM-DD`. The site prints it as "12 August 2026".
- `photo` — the filename step 1 gave you, or `null` if there is no photo.
- `alt` — describe the picture for someone who cannot see it. Required whenever
  there is a photo.

Three things bite people, all in the `body`:

- **Paragraphs.** You cannot press Enter inside the quotes — the whole post has
  to stay on one line, however long it gets. To break a paragraph, *type* the
  characters `\n\n` where the gap goes:

  ```js
  "body": "We went to Diamond for three days.\n\nIt worked.",
  ```

  That renders as two paragraphs.

- **Quote marks** inside your text must be written `\"`:

  ```js
  "body": "It was a \"good\" run.",
  ```

  The apostrophe in *didn't* is fine as it is — only double quotes need this.

- **The comma between `}` and `{`.** Every block needs one after it except the
  last. A missing comma stops the whole list being readable, not just one post.

---

## 3. Check it

```bash
python scripts/check-news.py
```

`News OK` and you are fine. Otherwise it names the post and the problem — a bad
date, a photo it cannot find, a missing alt text, or a punctuation mistake with
the three usual causes listed.

It also runs automatically during deployment, so **if you push something broken
the deploy fails and the site carries on serving the last good version.** The
news page cannot go blank because of a typo.

To see it before pushing, run `serve.cmd` and open
<http://localhost:8899/news.html>. Hard-reload with Ctrl+Shift+R — an ordinary
reload will serve you the old `news-data.js`.

---

## 4. Publish

```bash
git add -A
git commit -m "news: beamtime at Diamond"
git push
```

Live in under a minute.

---

## Editing or deleting a post

Edit the text in place, or delete its whole `{ ... }` block — including the comma
that follows it. If you delete a post, also delete its photo from `assets/news/`,
since nothing else refers to it.

---

## Two things no check can do for you

- **Photo consent.** If identifiable people are in the shot, they need to agree
  before it goes on a public site. A group photo from a trip counts.
- **Whether the facts are right.** Names, dates, whose paper it was.
