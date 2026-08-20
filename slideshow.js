/* Scope slideshows — three images beside each block of copy.

   Deliberately quiet: a slow crossfade, no sliding, no captions moving about.
   The copy beside it is the thing being read, so the pictures must not compete
   for attention while someone is halfway down a paragraph.

   Behaviour worth knowing:
     - Auto-advance stops while the pointer is over the slideshow or while any
       dot has keyboard focus, so it never moves under someone mid-click.
     - It also stops when the tab is hidden and when the slideshow is scrolled
       off screen, which saves work and means the sequence someone comes back to
       is the one they left.
     - prefers-reduced-motion: no auto-advance and no fade at all. The dots
       still work, so the images stay reachable — the content is not withheld,
       only the movement.
     - With JS off the first image is visible and the rest are simply not shown;
       the dots are built here, so nothing dead is left in the markup. */
(function () {
  var HOLD = 5200;   // ms each image is held
  var shows = [].slice.call(document.querySelectorAll('[data-slideshow]'));
  if (!shows.length) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  shows.forEach(function (root) {
    var slides = [].slice.call(root.querySelectorAll('.slide'));
    if (slides.length < 2) return;

    var i = 0, timer = null, hovered = false, focused = false, onScreen = true;

    // Dots are generated rather than written into the markup: their number has
    // to match the images, and hand-keeping the two in sync is how you end up
    // with a fourth dot that goes nowhere.
    var dots = document.createElement('div');
    dots.className = 'slide-dots';
    var buttons = slides.map(function (_, n) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'slide-dot';
      b.setAttribute('aria-label', 'Show image ' + (n + 1) + ' of ' + slides.length);
      b.addEventListener('click', function () { show(n); restart(); });
      b.addEventListener('focus', function () { focused = true; stop(); });
      b.addEventListener('blur', function () { focused = false; restart(); });
      dots.appendChild(b);
      return b;
    });
    root.parentNode.insertBefore(dots, root.nextSibling);

    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('is-on', k === i); });
      buttons.forEach(function (b, k) {
        b.setAttribute('aria-current', k === i ? 'true' : 'false');
      });
    }

    function stop() { clearInterval(timer); timer = null; }

    function restart() {
      stop();
      if (reduced || hovered || focused || !onScreen || document.hidden) return;
      timer = setInterval(function () { show(i + 1); }, HOLD);
    }

    root.addEventListener('mouseenter', function () { hovered = true; stop(); });
    root.addEventListener('mouseleave', function () { hovered = false; restart(); });
    document.addEventListener('visibilitychange', restart);

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        onScreen = entries[0].isIntersecting;
        restart();
      }, { threshold: 0.25 }).observe(root);
    }

    show(0);
    restart();
  });
})();
