/* Inner-page header: transparent over the hero, solid once you scroll past it.
   Also drives the mobile menu. */
(function () {
  var head = document.querySelector('.pg-head');
  if (!head) return;

  var hero = document.querySelector('.pg-hero');
  var trigger = hero ? Math.max(80, hero.offsetHeight - head.offsetHeight - 40) : 40;

  function onScroll() {
    head.classList.toggle('is-stuck', window.scrollY > trigger);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () {
    trigger = hero ? Math.max(80, hero.offsetHeight - head.offsetHeight - 40) : 40;
    onScroll();
  });
  onScroll();

  var burger = document.getElementById('pgBurger');
  var nav = document.getElementById('pgNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        nav.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }
})();
