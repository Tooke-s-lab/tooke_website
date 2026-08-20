# How to put a news post on the website

**For Cat and Harry. No code, no software to install, nothing to break.**

---

## The short version

1. Open the **News studio** — use the link whoever runs the site gives you. (If
   you have the website folder on your own computer instead, double-click
   `studio.html`.)
2. Fill in the form. The preview on the right is the actual news page — what you
   see there is exactly what a visitor will see.
3. Drop in a photo if you have one. It gets shrunk for the web automatically, so
   a huge photo straight off a phone is fine.
4. Press **Add this post**, then the **two download buttons**.
5. Email or message **both downloaded files** to whoever looks after the site.

That is the whole job. Ten minutes for the first one, two minutes after that.

---

## What you are writing

Four things, and only the first three are compulsory:

| Field | What it wants |
|---|---|
| **Date** | When it happened. Posts sort themselves newest-first — you do not have to put them in order. |
| **Headline** | Short and plain. "Beamtime at Diamond", not "Successful data collection campaign". |
| **The post** | Two or three sentences, written the way you would say it to someone in the corridor. Blank line between paragraphs if you want two. |
| **Photo** | Optional. If you add one, you must also describe it in one line — that description is what a blind reader gets instead of the picture. |

The newest post is shown large at the top of the page with its photo beside it.
Everything older drops into a row of cards below. You do not have to do anything
to make that happen.

---

## The two files you get

- **`news-data.js`** — the words. Every post on the site is in this one file, so
  it *replaces* the old copy rather than being added alongside it.
- **A `.webp` or `.jpg` photo** — named for you, e.g. `news-beamtime-at-diamond.webp`.

If the studio hands you more than one photo (because you wrote several posts in
one sitting) Chrome may ask whether to allow multiple downloads. Say yes.

---

## Things that catch people out

**iPhone photos.** iPhones save as HEIC, which no web browser can open. The
studio will tell you if you hit this. Easiest fix: email the photo to yourself
— it converts to JPEG on the way. Permanent fix: on the iPhone, *Settings →
Camera → Formats → Most Compatible*.

**You cannot break the website from the studio.** Nothing is published until
those files are put in place by whoever runs the site. Experiment freely.

**Removing a post** in the studio only changes the file you are about to
download. The live site keeps the old post until the new file is installed.

**Writing with Gemini or ChatGPT is fine** — write it however you like and paste
it into the box. It is the paste that matters, not where the words came from.

---

## If you have the website folder yourself

Put `news-data.js` in the site folder (replacing the one already there), and the
photo into `assets/news/`. Reload the news page. Done.

---

## For whoever maintains the site

`news.html` contains **no post markup at all** — `news.js` renders
everything from `news-data.js`. Installing a post is therefore: drop in the
replacement `news-data.js`, drop the photo into `assets/news/`, commit, deploy.
Nothing else in the repo changes, so a bad post can never be more than a
one-file revert.

Worth a skim before it goes live, for the two things the studio cannot check:
that the facts are right, and that everyone identifiable in the photo is happy
to be on a public website.
