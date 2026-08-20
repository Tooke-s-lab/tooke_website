#!/usr/bin/env bash
# Downloads all PDB structures deposited by Tooke, C.L. on RCSB.
# Run this from Claude Code (or any machine with internet access) — it won't
# work in the claude.ai sandbox, which doesn't have network access to RCSB.
#
# Usage:
#   chmod +x download-structures.sh
#   ./download-structures.sh
#
# Produces a `source/structures/` folder with both .pdb and .cif for each entry.

set -e

STRUCTURES=(
  # --- 2019: relebactam inhibitor study (Antimicrob Agents Chemother) ---
  "6QW7:L2_relebactam_16h"
  "6QW8:CTXM15_relebactam_16h"
  "6QW9:KPC2_relebactam_16h"
  "6QWA:KPC3_relebactam_16h"
  "6QWB:KPC4_relebactam_16h"
  "6QWC:KPC4_relebactam_1h"
  "6QWD:KPC3_apo"
  "6QWE:KPC4_apo"

  # --- 2020: boronate inhibitors (RSC Med Chem) ---
  "6TD0:KPC2_vaborbactam"
  "6TD1:KPC2_taniborbactam"

  # --- 2020: acyl-enzyme dynamics (J Biol Chem) ---
  "6Z21:KPC2_E166Q_apo"
  "6Z23:KPC2_E166Q_cefotaxime_acylenzyme"
  "6Z24:KPC2_E166Q_ceftazidime_acylenzyme"
  "6Z25:KPC4_E166Q_ceftazidime_acylenzyme"

  # --- 2025: unpublished, most recent ---
  "9F0V:KPC2_benzoxaborole_AK63"
  "9FBT:KPC2_benzoxaborole_AK431"
)

mkdir -p source/structures/pdb source/structures/cif

echo "Downloading ${#STRUCTURES[@]} structures..."

for entry in "${STRUCTURES[@]}"; do
  id="${entry%%:*}"
  label="${entry##*:}"

  echo "  ${id}  (${label})"

  curl -sf "https://files.rcsb.org/download/${id}.pdb" \
    -o "source/structures/pdb/${id}_${label}.pdb" \
    || echo "    ! ${id}.pdb not available (large structures may lack legacy PDB format — .cif will still work)"

  curl -sf "https://files.rcsb.org/download/${id}.cif" \
    -o "source/structures/cif/${id}_${label}.cif" \
    || echo "    ! ${id}.cif failed"
done

echo "Done. Files are in source/structures/pdb/ and source/structures/cif/"
