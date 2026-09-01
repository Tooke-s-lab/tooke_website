# Drop a photo here to replace one on the site

Upload a photo straight off your phone or camera. **Name it after the picture it
replaces**, and nothing else — `hero-news.heic`, `person-joe.jpg`. The extension
does not matter; HEIC, JPEG and PNG all work.

Within a minute or so a bot converts it into every size the site needs, updates
the pages, deletes your upload, and commits the result to this branch. If it
cannot use your photo it says why, and changes nothing.

## The names you can use

| Name | Where it appears |
|---|---|
| `hero-research` | the big image at the top of Research |
| `hero-people` | the big image at the top of Meet the Lab |
| `hero-news` | the big image at the top of News |
| `hero-opportunities` | the big image at the top of Opportunities |
| `crystal-drops` | the full-screen image on the home page |
| `route-research` | the small image on the Research card, home page |
| `route-people` | the small image on the Meet the Lab card, home page |
| `route-news` | the small image on the News card, home page |
| `route-opportunities` | the small image on the Opportunities card, home page |
| `person-cat` | Cat's portrait |
| `person-harry` | Harry's portrait |
| `person-joe` | Joe's portrait |
| `person-xandi` | Xandi's portrait |
| `scope-crystals` `scope-density` `scope-activesite` | the first Scope slideshow on Research, in that order |
| `scope-chip` `scope-droplet` `scope-timeres` | the second Scope slideshow on Research, in that order |

Get one wrong and the bot prints the current list back at you, so you do not have
to keep this table in your head.

## Two things it will refuse

**A photo that is too small.** The big header images are used up to 2560px wide.
Anything smaller gets rejected rather than blown up, because a stretched photo
looks soft and the page would end up asking for a size that does not exist.
Phone photos are about 4000px, so this normally only bites on a screenshot or
something saved off a website.

**A name that is not in the table.** Better a clear complaint than a file quietly
landing somewhere nobody looks.

## What it does to the picture

- **Portraits** (`person-*`) are cropped square, centred, sitting slightly high
  in the frame because the avatars are circles and a dead-centre crop puts the
  chin in the middle of the circle. If the crop lands badly, crop it square
  yourself before uploading and it will be left alone.
- **Scope images** are cropped to 4:3, which is the frame the slideshow uses.
- **Everything else** keeps its shape and gets the same light colour grade as
  the rest of the set, so a new photo does not sit brighter than its neighbours.

Nothing here is published — `build.sh` never copies this folder to the website.
