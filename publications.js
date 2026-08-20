/* Publications list.

   Reads publications.json, which is written by scripts/fetch-publications.py
   from Europe PMC — title, authors, year, journal, DOI and citation count all
   come from the record, so nothing here is hand-keyed and the list cannot drift
   from what has actually been published. Re-run the script to refresh it.

   Rendered client-side rather than baked into the HTML for exactly that reason:
   the page and the data stay separable, so updating the list never means
   editing markup. The fallback below matters — with no JS, or if the fetch
   fails, the reader still gets a link to the full list on the Bath portal
   rather than an empty box. */
(function () {
  var list = document.getElementById('pubList');
  if (!list) return;

  var PORTAL = 'https://researchportal.bath.ac.uk/en/persons/catherine-tooke';

  function fail(msg) {
    list.innerHTML = '<p class="pub-fallback">' + msg +
      ' <a href="' + PORTAL + '">See the full list on the Bath research portal</a>.</p>';
  }

  // publications-data.js sets this. Preferred over fetch() because fetch is
  // blocked on a file:// origin, so a page opened straight from Explorer would
  // otherwise show an empty list. Falls back to the JSON if the script is absent.
  var embedded = window.__TOOKE_PUBS;
  var source = embedded
    ? Promise.resolve(embedded)
    : fetch('publications.json').then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      });

  source
    .then(function (pubs) {
      if (!pubs.length) return fail('No publications loaded.');

      var frag = document.createDocumentFragment();
      var lastYear = null;

      pubs.forEach(function (p) {
        // A year marker whenever the year changes, so a long scroll stays
        // navigable without repeating the year on every single row.
        if (p.year !== lastYear) {
          var y = document.createElement('div');
          y.className = 'pub-year';
          y.textContent = p.year;
          frag.appendChild(y);
          lastYear = p.year;
        }

        var a = document.createElement('a');
        a.className = 'pub-row' + (p.thumb ? '' : ' pub-row--nothumb');
        a.href = p.url || PORTAL;
        a.rel = 'noopener';

        var shot = '';
        if (p.thumb) {
          // width/height are written by the build script, so the row reserves
          // its space before the image arrives and nothing jumps on load.
          shot = '<span class="pub-shot"><img src="assets/publications/' +
                 p.thumb + '" alt="" width="' + (p.thumbW || 480) +
                 '" height="' + (p.thumbH || 640) +
                 '" loading="lazy" decoding="async"></span>';
        } else {
          // No PDF in Europe PMC (too new, or paywalled). A hatched blank reads
          // as a broken image; setting the journal in the tile instead makes the
          // gap look considered and still tells you something.
          shot = '<span class="pub-shot pub-shot--none" aria-hidden="true">' +
                 '<span>' + p.journal + '</span></span>';
        }

        a.innerHTML =
          '<span class="pub-text">' +
            '<span class="pub-title">' + p.title + '</span>' +
            '<span class="pub-meta">' + p.authors + ' · ' + p.journal + ' · ' + p.year + '</span>' +
            // Preprints, theses and abstracts are labelled: a reader scanning a
            // publications list is entitled to know which entries are
            // peer-reviewed journal articles and which are not.
            (p.kind ? '<span class="pub-kind">' + p.kind + '</span>' : '') +
          '</span>' + shot;

        frag.appendChild(a);
      });

      list.innerHTML = '';
      list.appendChild(frag);
    })
    .catch(function (e) {
      console.warn('Publications failed to load.', e);
      fail('The publication list could not be loaded.');
    });
})();
