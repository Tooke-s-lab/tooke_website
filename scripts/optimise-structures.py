#!/usr/bin/env python3
"""
Slims Cat's PDB depositions down to something a browser can actually load.

Raw RCSB files are 600KB-1.3MB each. Almost none of that is needed to render a
cartoon + ligand in NGL:

  - ANISOU records (anisotropic B-factors) are ~half the file and are only used
    for refinement, never for display.
  - Waters and cryoprotectant/buffer molecules (glycerol, sulfate, PEG, DMSO...)
    are crystallisation artefacts, not biology. They'd render as visual noise.
  - REMARK/JRNL/SEQRES/DBREF headers are metadata we don't read at runtime.

Kept: CRYST1 (unit cell), HELIX/SHEET/SSBOND (so NGL doesn't have to infer
secondary structure), all protein ATOM records, and any HETATM that is a real
ligand or metal — i.e. the bound drug, which is the entire point of showing
these structures at all.

Usage:  python scripts/optimise-structures.py
Output: assets/structures/lite/<ID>.pdb  (shipped — backbone + ligand)
        source/structures-full/<ID>.pdb (kept for reference, not deployed)
"""

import os
import glob

# Crystallisation additives and cryoprotectants — present because of how the
# crystal was grown, not because they mean anything. Safe to drop.
JUNK = {
    "HOH", "DOD",                        # water
    "GOL", "EDO", "PEG", "PG4", "PGE",   # cryoprotectants
    "1PE", "P6G", "MPD", "TRS", "BTB",
    "SO4", "PO4", "ACT", "FMT", "CIT",   # buffer ions / acids
    "DMS", "IMD", "EPE", "MES", "NO3",
    "CL", "BR", "IOD",                   # loose halides
}

# Records worth keeping for rendering.
KEEP_PREFIX = ("CRYST1", "HELIX ", "SHEET ", "SSBOND", "LINK  ", "MODRES")


# A cartoon representation only needs the peptide backbone to trace the fold.
# Side chains roughly quadruple the atom count and are invisible in cartoon mode,
# so the "lite" tier drops them — but always keeps the ligand in full, since the
# bound drug is the whole story of these structures.
BACKBONE = {"N", "CA", "C", "O", "OXT"}


def optimise(src, dst, backbone_only=False):
    kept_atoms = 0
    ligands = set()
    out = []

    for line in open(src, errors="replace"):
        rec = line[:6]

        if rec == "ANISOU":
            continue                      # biggest single win

        if rec == "ATOM  ":
            if backbone_only and line[12:16].strip() not in BACKBONE:
                continue
            out.append(line)
            kept_atoms += 1
            continue

        if rec == "HETATM":
            resname = line[17:20].strip()
            if resname in JUNK:
                continue
            out.append(line)
            kept_atoms += 1
            ligands.add(resname)
            continue

        if line.startswith(KEEP_PREFIX):
            out.append(line)
            continue

        if rec in ("MODEL ", "ENDMDL", "TER   "):
            out.append(line)

    out.append("END\n")

    with open(dst, "w", newline="\n") as fh:
        fh.writelines(out)

    return kept_atoms, sorted(ligands)


def main():
    os.makedirs("source/structures-full", exist_ok=True)
    os.makedirs("assets/structures/lite", exist_ok=True)
    files = sorted(glob.glob("source/structures/pdb/*.pdb"))

    if not files:
        print("No files in source/structures/pdb/ — run download-structures.sh first.")
        return

    total_before = total_full = total_lite = 0
    print(f"{'ID':<7} {'raw':>8} {'full':>8} {'lite':>8} {'saved':>7}  ligands")
    print("-" * 66)

    for src in files:
        pdb_id = os.path.basename(src).split("_")[0]

        before = os.path.getsize(src)
        _, ligands = optimise(src, os.path.join("source/structures-full", pdb_id + ".pdb"))
        optimise(src, os.path.join("assets/structures/lite", pdb_id + ".pdb"),
                 backbone_only=True)

        full = os.path.getsize(os.path.join("source/structures-full", pdb_id + ".pdb"))
        lite = os.path.getsize(os.path.join("assets/structures/lite", pdb_id + ".pdb"))

        total_before += before
        total_full += full
        total_lite += lite
        pct = 100 * (1 - lite / before)
        print(f"{pdb_id:<7} {before/1024:7.0f}K {full/1024:7.0f}K {lite/1024:7.0f}K "
              f"{pct:6.0f}%  {', '.join(ligands) if ligands else '-'}")

    print("-" * 66)
    print(f"{'TOTAL':<7} {total_before/1024:7.0f}K {total_full/1024:7.0f}K "
          f"{total_lite/1024:7.0f}K {100*(1-total_lite/total_before):6.0f}%")


if __name__ == "__main__":
    main()
