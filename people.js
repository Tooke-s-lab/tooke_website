/* Lab member biographies: the card opens a dialog, the dialog closes again.

   Things worth knowing before changing this:

     - Everything the dialog shows is READ OFF THE CARD. The prose lives in
       people.html, inside each member's .member-bio, next to the person it
       belongs to. Writing a bio means editing that markup and nothing else —
       there is deliberately no second list of people here to fall out of sync
       with the one on the page.

     - <dialog>.showModal() does the hard part: focus is trapped inside the
       dialog, Escape closes it, the rest of the page goes inert, and focus
       returns to the card afterwards. Hand-rolled modals are where all of that
       quietly goes missing, so it is not hand-rolled.

     - A browser without showModal() reveals the bio inline under the card
       instead. The words are the point; the window is not.

     - Page scroll is frozen while the dialog is open, and the width the
       scrollbar was taking is handed back as padding — without that the whole
       page jumps sideways at the moment the dialog appears. */
(function () {
  var members = [].slice.call(document.querySelectorAll('.member'));
  if (!members.length) return;

  var buttons = [].slice.call(document.querySelectorAll('.member-btn'));
  if (!buttons.length) return;

  var probe = document.createElement('dialog');
  var canModal = typeof probe.showModal === 'function';

  /* ---- Fallback: no <dialog> support, so the bio just unfolds in place ---- */
  if (!canModal) {
    buttons.forEach(function (btn) {
      var li = btn.closest('.member');
      var bio = li && li.querySelector('.member-bio');
      if (!bio) return;
      btn.setAttribute('aria-expanded', 'false');
      btn.removeAttribute('aria-haspopup');
      if (bio.id) btn.setAttribute('aria-controls', bio.id);
      li.classList.add('member--inline');
      btn.addEventListener('click', function () {
        var open = bio.hasAttribute('hidden');
        if (open) bio.removeAttribute('hidden'); else bio.setAttribute('hidden', '');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    return;
  }

  /* ---- One dialog, reused by every card -----------------------------------
     One element rather than one per person: there is only ever a single bio on
     screen, and cloning the same furniture four times only creates four places
     for it to drift apart. */
  var dlg = document.createElement('dialog');
  dlg.className = 'bio-dialog';
  dlg.setAttribute('aria-labelledby', 'bioName');
  dlg.innerHTML =
    '<button class="bio-close" type="button" aria-label="Close">' +
      '<span aria-hidden="true">×</span>' +
    '</button>' +
    '<div class="bio-inner">' +
      '<div class="bio-head">' +
        '<span class="avatar bio-avatar"><img src="" alt="" width="320" height="320"></span>' +
        '<div class="bio-who">' +
          '<h2 class="bio-name" id="bioName"></h2>' +
          '<div class="bio-roles"></div>' +
        '</div>' +
      '</div>' +
      '<div class="bio-text"></div>' +
    '</div>';
  document.body.appendChild(dlg);

  var elAvatar = dlg.querySelector('.bio-avatar');
  var elAvatarImg = elAvatar.querySelector('img');
  var elName = dlg.querySelector('.bio-name');
  var elRoles = dlg.querySelector('.bio-roles');
  var elText = dlg.querySelector('.bio-text');
  var opener = null;

  function fill(li) {
    var img = li.querySelector('.avatar img');
    // currentSrc, not src: the portrait may have come from a srcset, and the
    // resolved file is the one already in the cache.
    if (img) {
      elAvatarImg.src = img.currentSrc || img.src;
      elAvatar.hidden = false;
    } else {
      elAvatarImg.removeAttribute('src');
      elAvatar.hidden = true;
    }
    // alt stays empty throughout: the portrait is decorative here, the name is
    // right beside it, and the card behind has already announced the person.

    var nm = li.querySelector('.nm');
    elName.textContent = nm ? nm.textContent.trim() : '';

    // The role lines are rebuilt rather than cloned so the email address in the
    // dialog is ordinary selectable text — on the card it sits under the click
    // overlay and cannot be swiped.
    elRoles.textContent = '';
    [].slice.call(li.querySelectorAll('.rl')).forEach(function (rl) {
      var s = document.createElement('span');
      s.className = 'rl';
      s.textContent = rl.textContent.trim();
      elRoles.appendChild(s);
    });

    var bio = li.querySelector('.member-bio');
    elText.textContent = '';
    if (bio) {
      var copy = bio.cloneNode(true);
      while (copy.firstChild) elText.appendChild(copy.firstChild);
    }
  }

  function lockScroll() {
    var gap = window.innerWidth - document.documentElement.clientWidth;
    document.documentElement.style.overflow = 'hidden';
    if (gap > 0) document.documentElement.style.paddingRight = gap + 'px';
  }

  function unlockScroll() {
    document.documentElement.style.overflow = '';
    document.documentElement.style.paddingRight = '';
  }

  buttons.forEach(function (btn) {
    var li = btn.closest('.member');
    if (!li) return;
    btn.addEventListener('click', function () {
      opener = btn;
      fill(li);
      elText.scrollTop = 0;
      dlg.showModal();
      dlg.querySelector('.bio-inner').scrollTop = 0;
      lockScroll();
    });
  });

  dlg.querySelector('.bio-close').addEventListener('click', function () {
    dlg.close();
  });

  // A click that lands on the dialog element ITSELF is a click on the backdrop:
  // all of the visible card is .bio-inner, and the dialog carries no padding of
  // its own for a stray click to land in.
  dlg.addEventListener('click', function (e) {
    if (e.target === dlg) dlg.close();
  });

  function afterClose() {
    unlockScroll();
    // Focus is restored on the NEXT FRAME, not immediately. Closing by clicking
    // the backdrop or the × is still a click, and the browser finishes a click
    // by moving focus to the nearest focusable thing under the pointer — which,
    // once the dialog has gone, is <body>. Focus the card before that and it is
    // overwritten a moment later; focus it after and it sticks.
    var back = opener;
    opener = null;
    if (back) window.requestAnimationFrame(function () { back.focus(); });
  }

  // Watching the open attribute rather than listening for the close event.
  // Every way out of this dialog — Escape, the ×, a click on the backdrop —
  // ends by dropping that attribute, so one observer covers all of them. The
  // close event does not: it was reliable here when Escape closed the dialog
  // and silent when close() was called from script, which would have left the
  // page scroll-locked with the dialog already gone. Not worth depending on.
  new MutationObserver(function () {
    if (!dlg.open) afterClose();
  }).observe(dlg, { attributes: true, attributeFilter: ['open'] });
})();
