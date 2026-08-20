#!/usr/bin/env python3
"""
Converts the two CIF-only depositions into the same lite PDB format as the rest.

9F0V and 9FBT (2025, benzoxaborole complexes) have no legacy PDB file on RCSB —
mmCIF only. Rather than special-case them in the viewer, they are converted here
so all 16 structures load through one identical code path.

Only the atom_site loop is read; the same waters/cryoprotectant filtering and
backbone-only reduction as optimise-structures.py is applied.

Usage: python scripts/cif-to-pdb.py
"""

import os
import glob

JUNK = {
    "HOH", "DOD", "GOL", "EDO", "PEG", "PG4", "PGE", "1PE", "P6G", "MPD",
    "TRS", "BTB", "SO4", "PO4", "ACT", "FMT", "CIT", "DMS", "IMD", "EPE",
    "MES", "NO3", "CL", "BR", "IOD",
}
BACKBONE = {"N", "CA", "C", "O", "OXT"}


def read_atom_site(path):
    """Yield dicts for each ATOM/HETATM row of the atom_site loop."""
    cols, rows, in_loop = [], [], False
    for line in open(path, encoding="utf-8", errors="replace"):
        s = line.strip()
        if s == "loop_":
            in_loop, cols = True, []
            continue
        if in_loop and s.startswith("_atom_site."):
            cols.append(s.split(".", 1)[1])
            continue
        if cols and (s.startswith("ATOM") or s.startswith("HETATM")):
            parts = s.split()
            if len(parts) == len(cols):
                rows.append(dict(zip(cols, parts)))
            continue
        if cols and rows and s.startswith("#"):
            break
    return rows


# Legacy PDB allows only a 3-character residue name. These entries use modern
# 5-character CCD codes (A1H8R, A1H1U, A1IB7) — which is precisely why RCSB
# publishes no PDB file for them. Writing them raw overflows the fixed-width
# columns and shifts every field after it, so NGL reads garbage coordinates and
# the structure renders wildly off-centre. Alias them to 3 characters; only the
# label changes, the geometry is untouched.
ALIAS = {}


def comp3(name):
    if len(name) <= 3:
        return name
    if name not in ALIAS:
        ALIAS[name] = "L%02d" % (len(ALIAS) + 1)
    return ALIAS[name]


def to_pdb_line(i, r):
    """Format one atom_site row as a fixed-width PDB ATOM/HETATM record."""
    name = r["auth_atom_id"].strip('"')
    # PDB atom names are column-sensitive: element right-aligned in cols 13-14
    name = f" {name:<3}" if len(name) < 4 else name[:4]
    return (
        f"{r['group_PDB']:<6}"
        f"{i:>5} "
        f"{name}"
        f"{'':1}"
        f"{comp3(r['auth_comp_id']):>3} "
        f"{r['auth_asym_id'][:1]:>1}"
        f"{r['auth_seq_id']:>4}"
        f"{'':4}"
        f"{float(r['Cartn_x']):>8.3f}"
        f"{float(r['Cartn_y']):>8.3f}"
        f"{float(r['Cartn_z']):>8.3f}"
        f"{float(r['occupancy']):>6.2f}"
        f"{float(r['B_iso_or_equiv']):>6.2f}"
        f"{'':10}"
        f"{r['type_symbol']:>2}\n"
    )


def convert(src, dst, backbone_only):
    rows = read_atom_site(src)
    out, n, ligands = [], 0, set()

    for r in rows:
        comp = r["auth_comp_id"]
        if r["group_PDB"] == "HETATM":
            if comp in JUNK:
                continue
            ligands.add(comp)
        elif backbone_only and r["auth_atom_id"].strip('"') not in BACKBONE:
            continue
        n += 1
        out.append(to_pdb_line(n, r))

    out.append("END\n")
    with open(dst, "w", newline="\n") as fh:
        fh.writelines(out)
    return n, sorted(ligands)


def main():
    os.makedirs("assets/structures/lite", exist_ok=True)
    os.makedirs("source/structures-full", exist_ok=True)
    for src in sorted(glob.glob("source/structures/cif/9F*.cif") + glob.glob("source/structures/cif/9FBT*.cif")):
        pdb_id = os.path.basename(src).split("_")[0]
        full = f"source/structures-full/{pdb_id}.pdb"
        lite = f"assets/structures/lite/{pdb_id}.pdb"

        convert(src, full, backbone_only=False)
        n, ligands = convert(src, lite, backbone_only=True)

        print(f"{pdb_id}  {os.path.getsize(src)/1024:6.0f}K cif -> "
              f"{os.path.getsize(lite)/1024:5.0f}K lite  "
              f"({n} atoms, ligands: {', '.join(ligands) or '-'})")


if __name__ == "__main__":
    main()
