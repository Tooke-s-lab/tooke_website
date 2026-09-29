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
"date": "2026-09-29",
"title":"Maryam joins the lab",
"body": "After three years as an AMR research technician, Maryam joined the Tooke Lab to deepen her research into AMR and help address some of the field’s unanswered questions. She is excited to build on her experience in microbiology, molecular biology and genomics while developing new skills in structural biology and crystallography. She hopes to combine these approaches to identify new antibiotic targets and/or find ways to improve existing antibiotics.",
"photo": "maryam-joins.webp",
"alt": "Maryam selfie."

},


{
"date": "2026-09-28",
"title":"Harry Spotter software released",
"body": "Processing time-resolved data can be time-consuming. During drop-on-chip experiments, difficulties often arise when determining which datasets have been contaminated by ligand, and therefore need to be excluded from the 'off' dataset. To overcome this, we have built an app that runs Phenix's Fobs (target) minus Fobs (apo), and displays the results as a GIF centred on the residue of your choice in Coot. To load in your data, the app has a built in Google Drive Sync, enabling rapid access and copying of time-resolved visits and data. To find out more, and install on Windows or Mac, please visit the GitHub page (https://github.com/harrymorganbryn-ui/HarrySpotter).",
"photo": "harry-spotter.webp",
"alt": "Harry Spotter GUI landing page."

},

{
    "date": "2026-06-01",
    "title": "Harry joins the lab",
    "body": "Following completion of his PhD in AMR drug discovery and crystallography, Harry made the short journey across the Severn bridge to join the Tooke Lab at the University of Bath. Having spent 2 years of his PhD at Diamond Light Source, Harry aims to bring his crystallographic expertise in crystallisation optimisation, fragment screening, and drug discovery, and apply them to the research goals of the Tooke Lab. Harry is also dedicated to broaden his structural biology toolkit, by developing skills in neutron MX, MD simulations, and serial time-resolved crystallography. He is acutely interested in learning how these frontier techniques can be applied to understanding and overcoming resistance in PBPs and BLAs.",
    "photo": "harry-joins.webp",
    "alt": "Harry's graduation day in Cardiff."
  }
];
