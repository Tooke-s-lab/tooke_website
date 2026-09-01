# Drop a photo here to use it in a news post

Upload a photo straight off your phone. Call it whatever you like —
`beamtime-october.heic`, `poster prize.jpg`. The name becomes the filename, so
keep it short and descriptive.

A bot converts it, deletes your upload, and tells you the exact line to paste
into `news-data.js`:

```
"photo": "beamtime-october.webp",
```

Then write the post itself in `news-data.js` — see **HOW-TO-POST-NEWS.md** for
that half. The photo and the words are two separate steps; this folder is only
the photo.

Spaces and capitals in your filename are fine, they get tidied into a safe one
(`Poster Prize.JPG` becomes `poster-prize.webp`). Watch the name the bot reports
back, and use that, not what you uploaded.

Unlike the `replace/` folder there is no fixed list of names here, because a news
photo is a new picture rather than a replacement for an existing one. Nothing
gets overwritten unless you reuse a name.

Nothing here is published — `build.sh` never copies this folder to the website.
