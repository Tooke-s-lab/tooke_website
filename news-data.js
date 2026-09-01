/* ============================================================
   NEWS POSTS — the whole of the news page lives in this file.

   THIS IS THE ONLY FILE THAT CHANGES WHEN A POST IS ADDED.
   Nobody needs to touch HTML or CSS to publish news.

   TO ADD A POST
   -------------
   1. If it has a photo, from the repo root run:
          python scripts/prepare-news-photo.py <your-photo> <a-short-name>
      That converts it to a web-ready .webp in assets/news/ and prints the
      filename to use below. Do NOT copy a photo in by hand — phone photos are
      HEIC, which no browser can display, and are ~40x larger than needed.

   2. Copy an existing { ... } block, paste it ABOVE the others, and fill it in.

   3. Check it before pushing:
          python scripts/check-news.py

   THE RULES
   ---------
     · newest post FIRST
     · every " inside your text must be written as \"
     · date is YYYY-MM-DD  (the site prints it as "12 August 2026")
     · photo is a filename inside assets/news/, or null for no photo
     · alt describes the photo for a reader who cannot see it —
       it is required whenever there is a photo
     · to start a new paragraph, TYPE the four characters \n\n where the break
       goes. You cannot press Enter inside the quotes — the text must stay on
       one line, however long it gets.
     · keep the commas between } and { — a missing one blanks the page
     · no JS comments inside the list below - it is pure data

   The last three are the ones that bite, and all three are caught by
   check-news.py, which also runs during the deploy — so a mistake fails the
   build instead of quietly emptying the news page. If you push something
   broken, the site keeps serving the last good version. It does not go blank.

   See HOW-TO-POST-NEWS.md for the same thing written out at length.
   ============================================================ */
window.__TOOKE_NEWS = [
  {
    "date": "2026-08-24",
    "title": "A new paper on KPC inhibition",
    "body": "[DEMO POST — delete before launch.] Placeholder body of about the length a real post would run to, so the lead block can be judged at a realistic size rather than against one short sentence.\n\nA second paragraph, because the lead is the one place two paragraphs will actually appear side by side with the photo.",
    "photo": "demo-crystal-drop.webp",
    "alt": "A crystallisation drop under the microscope."
  },
  {
    "date": "2026-08-18",
    "title": "Joe joins the lab",
    "body": "[DEMO POST — delete before launch.] A short one, to show how a card looks when there is much less to say than the post above it.",
    "photo": "demo-gel-dish.webp",
    "alt": "A stained protein gel in a dish."
  },
  {
    "date": "2026-08-15",
    "title": "Poster prize at the SWSBC meeting, and a longer title to see how two lines wrap",
    "body": "[DEMO POST — delete before launch.] This one has no photo at all, which is the layout case worth checking: the card has to hold its own in the grid next to two that do.",
    "photo": null,
    "alt": ""
  },
  {
    "date": "2026-08-12",
    "title": "Beamtime at Diamond",
    "body": "[Two or three sentences, first person and friendly. What we went to do, who went, and whether it worked. Cat to write.]",
    "photo": "news-beamtime-at-diamond.webp",
    "alt": "[Placeholder image — replace with Cat's own photo from the trip, and describe it here.]"
  }
];
