/* The Collection — Cat's actual PDB depositions, loaded from
   assets/structures/lite/ (backbone + ligand only, ~95KB each rather than
   ~630KB raw; see scripts/optimise-structures.py).
   9F0V and 9FBT have no legacy PDB file on RCSB (mmCIF only) and are converted
   by scripts/cif-to-pdb.py, so all 16 load through one path. */
(function () {
  var STRUCTURES = [
    { id: "9F0V", name: "KPC-2 + benzoxaborole AK63",    year: "2025" },
    { id: "9FBT", name: "KPC-2 + benzoxaborole AK431",   year: "2025" },
    { id: "6TD0", name: "KPC-2 + vaborbactam",           year: "2020" },
    { id: "6TD1", name: "KPC-2 + taniborbactam",         year: "2020" },
    { id: "6Z21", name: "KPC-2 E166Q, apo",              year: "2020" },
    { id: "6Z23", name: "KPC-2 E166Q + cefotaxime",      year: "2020" },
    { id: "6Z24", name: "KPC-2 E166Q + ceftazidime",     year: "2020" },
    { id: "6Z25", name: "KPC-4 E166Q + ceftazidime",     year: "2020" },
    { id: "6QW9", name: "KPC-2 + relebactam",            year: "2019" },
    { id: "6QWA", name: "KPC-3 + relebactam",            year: "2019" },
    { id: "6QWB", name: "KPC-4 + relebactam",            year: "2019" },
    { id: "6QWC", name: "KPC-4 + relebactam, 1 h soak",  year: "2019" },
    { id: "6QWD", name: "KPC-3, apo",                    year: "2019" },
    { id: "6QWE", name: "KPC-4, apo",                    year: "2019" },
    { id: "6QW8", name: "CTX-M-15 + relebactam",         year: "2019" },
    { id: "6QW7", name: "L2 + relebactam",               year: "2019" }
  ];

  // Newest first. The list above is already in that order; this sort is what
  // guarantees it, so appending a new deposition at the bottom still shows it
  // at the top. Deposition year is the only date we hold, and Array.sort is
  // stable, so structures sharing a year keep the order written above -- which
  // is grouped by enzyme (the KPC series, then CTX-M-15, then L2), not by ID.
  STRUCTURES.sort(function (a, b) { return Number(b.year) - Number(a.year); });

  var catList = document.getElementById('catList');
  if (!catList) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var loading = document.getElementById('viewerLoading');
  var stage = null, current = null;

  STRUCTURES.forEach(function (s, i) {
    var b = document.createElement('button');
    b.className = 'cat-item';
    b.type = 'button';
    b.setAttribute('aria-current', i === 0 ? 'true' : 'false');
    b.innerHTML = '<span class="pid">' + s.id + '</span>' +
                  '<span class="nm">' + s.name + '</span>' +
                  '<span class="yr">' + s.year + '</span>';
    b.addEventListener('click', function () { load(s, b); });
    catList.appendChild(b);
  });

  function load(s, btn) {
    if (!stage || current === s.id) return;
    current = s.id;

    document.querySelectorAll('.cat-item').forEach(function (el) {
      el.setAttribute('aria-current', 'false');
    });
    if (btn) btn.setAttribute('aria-current', 'true');

    document.getElementById('metaPid').textContent = s.id;
    document.getElementById('metaDesc').textContent = s.name;

    // Follow the selection through to the actual deposition on rcsb.org.
    // Guarded because concept 1 has no such link in its markup.
    var pdb = document.getElementById('pdbLink');
    if (pdb) {
      pdb.href = 'https://www.rcsb.org/structure/' + s.id;
      pdb.setAttribute('aria-label', 'View ' + s.id + ' in the Protein Data Bank');
    }
    loading.textContent = 'Loading ' + s.id + '…';
    loading.style.display = 'grid';

    stage.removeAllComponents();
    stage.loadFile('assets/structures/lite/' + s.id + '.pdb').then(function (o) {
      o.addRepresentation('cartoon', { color: '#47A284', opacity: .9, quality: 'medium' });
      // The bound drug is the point of these structures — show it explicitly.
      o.addRepresentation('ball+stick', {
        sele: 'ligand and not (water or ion)', color: '#D9E84F', multipleBond: 'symmetric'
      });
      o.autoView();
      loading.style.display = 'none';
      if (!reduced) stage.setSpin([0, 1, 0], 0.004);
    }).catch(function (e) {
      console.warn('Structure ' + s.id + ' failed to load.', e);
      loading.textContent = 'Could not load ' + s.id;
    });
  }

  try {
    stage = new NGL.Stage('viewer', { backgroundColor: 'transparent' });
    window.addEventListener('resize', function () { stage.handleResize(); });
    load(STRUCTURES[0], document.querySelector('.cat-item'));
  } catch (e) {
    console.warn('NGL unavailable — collection falls back to the list.', e);
    var card = document.getElementById('viewerCard');
    if (card) card.style.display = 'none';
  }
})();
