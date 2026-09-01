# How to change a photo

You need a GitHub account with access to this repository, and a web browser.
That is all. No software to install, nothing to download, no commands to type.

Changing a photo takes about five clicks and two minutes of waiting.

---

## Why it is not just "upload the new picture"

Worth thirty seconds, because it explains what the robot is doing for you.

A photo on this site is not one file. The big image at the top of Research is
**three** files — 1200, 1920 and 2560 pixels wide — so that a phone downloads a
small one and a big monitor gets a sharp one. The portraits are square crops. The
Scope slideshow images are cropped to 4:3. And every `<img>` on the site declares
how big its picture is, so the page does not jump about while it loads.

On top of that, phone photos need converting. An iPhone shoots HEIC, a format
**no browser can display** — upload one directly and you get a broken image,
even though the file looks perfectly fine on your Mac. And every modern phone,
Pixels included, records colour in a wider range than a web page uses, which has
to be translated rather than just relabelled or everything comes out looking
sunburnt.

So a robot does all of it for you. You upload one photo; it makes the sizes,
does the crops, fixes the colour, corrects the pages, and throws your original
away.

**It does not care what format you give it.** JPEG, HEIC, PNG, AVIF, WebP, TIFF
all work, and it identifies your photo by looking inside the file rather than
trusting the name — so a HEIC that something along the way renamed `.jpg` still
converts properly instead of breaking.

---

## 1. Find the name of the photo you want to change

Every picture has a name. The full list is in
[`incoming/replace/README.md`](incoming/replace/README.md), but the pattern is
easy:

| You want to change | Name |
|---|---|
| The big image at the top of a page | `hero-research`, `hero-people`, `hero-news`, `hero-opportunities` |
| The full-screen image on the home page | `crystal-drops` |
| One of the four cards on the home page | `route-research`, `route-people`, `route-news`, `route-opportunities` |
| Somebody's portrait | `person-cat`, `person-harry`, `person-joe`, `person-xandi` |
| A picture in a Scope slideshow | `scope-crystals`, `scope-density`, `scope-activesite`, `scope-chip`, `scope-droplet`, `scope-timeres` |

If you get the name wrong, nothing breaks — the robot prints the correct list
back at you and changes nothing.

## 2. Rename your photo to match

On your computer, rename the photo to that name. Keep whatever ending it already
has:

```
IMG_4821.HEIC   ->   hero-research.HEIC
```

## 3. Upload it

1. Go to the repository on github.com
2. Open the **`incoming`** folder, then **`replace`**
3. Click **Add file** → **Upload files**
4. Drag your renamed photo in

## 4. This is the important bit

Underneath the upload box are two options. Choose the **second** one:

> ○ Commit directly to the `main` branch
> ● **Create a new branch for this commit and start a pull request**

Then click **Propose changes**, and on the next screen **Create pull request**.

Choosing the first option puts your photo straight onto the live website with
nobody having looked at it. Choosing the second lets you see it first. It is the
same amount of clicking.

## 5. Wait about a minute, then look

On your new pull request you will see things happening:

- **A yellow dot, then a green tick.** That is the robot converting your photo.
  When it goes green, scroll up — it will have added a commit called
  *"Photos: convert uploads from incoming/"*. That is your photo, in every size
  the site needs.
- **A comment from Cloudflare with a link.** That is the whole website, built
  with your photo in it. Click it and look at the actual page.

If the tick goes **red** instead, click **Details** and read the message. It
tells you what was wrong in plain English — almost always either the name or a
photo that is too small. Nothing was changed; fix it and upload again.

## 6. Merge it

Happy with how it looks? Click **Merge pull request**. It is live in under a
minute.

Not happy? Upload a different photo to the same pull request and look again, or
just close the pull request and nothing ever happened.

---

## The one thing you must do by hand

**The description of the picture.** Every image on the site carries a written
description for people using a screen reader. The robot cannot know what is in
your new photo, so that description still describes the **old** one — and it
will say so, in the green tick's details:

> the alt text for hero-people-1920.webp still describes the OLD photo —
> "The group standing together in a beamline experimental hall."

Fix it in the same pull request: open the page file (`people.html`), click the
pencil icon, and edit the `alt="..."` text to describe the new picture. One
sentence. "The experimental hutch at beamline I24, with the detector in the
foreground."

It does not affect how the page looks, so it is easy to skip. Don't.

---

## Photos for a news post

Same idea, different folder. Put the photo in **`incoming/news`** instead, call
it whatever you like, and the robot converts it and tells you the line to paste:

```
"photo": "beamtime-october.webp",
```

Then write the post in `news-data.js` — see **HOW-TO-POST-NEWS.md** for that
half. The photo and the words are two separate steps.

---

## What it will refuse to do

**Blow up a small photo.** The big header images are used at up to 2560 pixels
wide. Give it something smaller and it stops rather than stretching it, because
a stretched photo looks soft and the page would end up asking for a size that
does not exist. Phone photos are around 4000 pixels, so this normally only
happens with a screenshot or an image saved from a website.

**Guess what you meant.** A name that is not on the list is rejected, not
approximated.

**Publish a video.** A Pixel's *Motion Photo* is a short video with a still
inside it, and sharing one sometimes hands you an `.mp4`. If that happens, open
the photo in Google Photos, use **Export → Still photo**, and upload the result.
The robot will tell you this if it happens; it recognises a video even when the
file is named `.jpg`.

**Publish a RAW file.** If your camera is set to RAW (`.dng`), upload the
ordinary `.jpg` your phone saved of the very same shot instead — it is sitting
right next to it in your camera roll.

---

## A note for Pixel owners

Pixel 8 and later shoot **Ultra HDR** by default. These are ordinary `.jpg`
files with extra brightness information tucked inside, so they upload and
convert with no trouble at all.

The one thing to know: web pages cannot show that extra brightness, so the
picture on the site will look slightly flatter than it does in Google Photos on
your phone. That is the web being the web, not the photo being converted badly.
If a shot depends on that HDR punch to work, it will disappoint you here —
choose one that stands up without it.

---

## Two things no robot can do for you

- **Permission.** If there are identifiable people in the shot, they need to
  agree before it goes on a public website. A group photo from a trip counts.
- **Whether it is yours to use.** A photo taken off someone else's website, or a
  photograph of someone else's poster, is their copyright, not ours.

---

## If you would rather not use the website at all

Everything above also works from a clone with Python installed:

```bash
# put your photo in incoming/replace/, then
python scripts/convert-incoming-photos.py
```

It is the same script the robot runs, and prints the same messages. Add
`--dry-run` to see what it would do without writing anything.
