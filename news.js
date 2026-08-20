/* News list.

   Reads news-data.js, which sets window.__TOOKE_NEWS. Rendered client-side for
   the same reason the publication list is: the page and the posts stay
   separable, so adding news never means editing markup. studio.html writes that
   data file, so in practice nobody involved ever opens an HTML file at all.

   A plain .js file rather than JSON on purpose — fetch() is blocked on a
   file:// origin, so a JSON feed would leave the page empty for anyone who
   opened it straight from Explorer, which is exactly how this gets checked
   before it goes live. A <script> tag has no such restriction.

   The first post is laid out as a lead: photo and text side by side, at
   reading size. The rest fall into the card grid below it. That is what makes
   a single post look deliberate instead of like a page with four cards
   missing — which matters, because the page starts life with one post on it. */
(function () {
  var lead = document.getElementById('newsLead');
  var grid = document.getElementById('newsGrid');
  if (!lead || !grid) return;

  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                'August', 'September', 'October', 'November', 'December'];

  /* "2026-08-12" -> "12 August 2026". Parsed by hand rather than with Date():
     new Date('2026-08-12') is read as UTC midnight, which prints as the 11th
     for anyone west of Greenwich. */
  function prettyDate(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || '').trim());
    if (!m) return iso || '';
    return Number(m[3]) + ' ' + MONTHS[Number(m[2]) - 1] + ' ' + m[1];
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;   // textContent, not innerHTML:
    return n;                                 // post text is typed by hand and
  }                                           // must never execute as markup.

  function photo(post, cls) {
    var fig = el('div', cls);
    var img = el('img', 'ph');
    img.src = 'assets/news/' + post.photo;
    img.alt = post.alt || '';
    img.loading = 'lazy';
    img.decoding = 'async';
    fig.appendChild(img);
    return fig;
  }

  function paragraphs(parent, body) {
    // A blank line in the body starts a new paragraph, which is the one bit of
    // formatting a non-technical writer expects to just work.
    String(body || '').split(/\n\s*\n/).forEach(function (chunk) {
      if (chunk.trim()) parent.appendChild(el('p', null, chunk.trim()));
    });
  }

  var posts = window.__TOOKE_NEWS;

  if (!posts || !posts.length) {
    console.warn('No news posts loaded — is news-data.js present?');
    return;                       // the <noscript>/empty-state copy in the HTML
  }                               // stays visible, so the band is never blank.

  // Newest first regardless of the order they were typed in, so a post added
  // in the wrong place still lands where it belongs.
  posts = posts.slice().sort(function (a, b) {
    return String(b.date).localeCompare(String(a.date));
  });

  var first = posts[0];
  var article = el('article', 'news-lead-item');
  if (first.photo) article.appendChild(photo(first, 'news-lead-shot'));

  var text = el('div', 'news-lead-text');
  text.appendChild(el('span', 'news-date', prettyDate(first.date)));
  text.appendChild(el('h2', null, first.title));
  paragraphs(text, first.body);
  article.appendChild(text);
  lead.appendChild(article);

  posts.slice(1).forEach(function (post) {
    var item = el('article', 'news-item');
    if (post.photo) item.appendChild(photo(post, 'thumb'));
    item.appendChild(el('span', 'news-date', prettyDate(post.date)));
    item.appendChild(el('h3', null, post.title));
    paragraphs(item, post.body);
    grid.appendChild(item);
  });

  // The band ships with a written empty state so it is never a bare colour
  // block; it comes out only once there is something real to replace it.
  var empty = document.getElementById('newsEmpty');
  if (empty && empty.parentNode) empty.parentNode.removeChild(empty);
})();
