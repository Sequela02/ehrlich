"""Data preparation script for Ehrlich.

Downloads and prepares datasets for antimicrobial discovery:
- ChEMBL bioactivity data for key antimicrobial targets
- Protein structures (PDB/PDBQT) for docking
- Tox21 toxicity data for safety filtering

Usage:
    python data/scripts/prepare_data.py --chembl
    python data/scripts/prepare_data.py --proteins
    python data/scripts/prepare_data.py --all
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent
DATASETS_DIR = DATA_DIR / "datasets"
PROTEINS_DIR = DATA_DIR / "proteins"

# Key antimicrobial targets in ChEMBL
TARGETS = {
    "ecoli_gyrase": {"chembl_id": "CHEMBL1927", "organism": "Escherichia coli"},
    "sa_dhfr": {"chembl_id": "CHEMBL2366", "organism": "Staphylococcus aureus"},
    "mtb_inha": {"chembl_id": "CHEMBL1849", "organism": "Mycobacterium tuberculosis"},
    "pa_lpxc": {"chembl_id": "CHEMBL3885882", "organism": "Pseudomonas aeruginosa"},
}

# Protein structures for docking
PROTEIN_TARGETS = {
    "1KZN": "E. coli DNA gyrase B",
    "3FRB": "S. aureus DHFR",
    "4TZK": "M. tuberculosis InhA",
}


def prepare_chembl() -> None:
    """Download ChEMBL bioactivity data for antimicrobial targets."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    print("ChEMBL data preparation:")
    for name, info in TARGETS.items():
        output = DATASETS_DIR / f"{name}.csv"
        if output.exists():
            print(f"  [skip] {name} already exists")
            continue
        print(f"  [todo] {name} ({info['chembl_id']}) - {info['organism']}")
        # TODO: Implement ChEMBL API download
    print("Done. Implement ChEMBL API calls to download bioactivity data.")


def prepare_proteins() -> None:
    """Download protein structures for molecular docking."""
    PROTEINS_DIR.mkdir(parents=True, exist_ok=True)
    print("Protein structure preparation:")
    for pdb_id, description in PROTEIN_TARGETS.items():
        output = PROTEINS_DIR / f"{pdb_id}.pdbqt"
        if output.exists():
            print(f"  [skip] {pdb_id} already exists")
            continue
        print(f"  [todo] {pdb_id} - {description}")
        # TODO: Download PDB, convert to PDBQT with Meeko
    print("Done. Implement PDB download and PDBQT conversion.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare data for Ehrlich")
    parser.add_argument("--chembl", action="store_true", help="Download ChEMBL data")
    parser.add_argument("--proteins", action="store_true", help="Download protein structures")
    parser.add_argument("--all", action="store_true", help="Download everything")
    args = parser.parse_args()

    if args.all or args.chembl:
        prepare_chembl()
    if args.all or args.proteins:
        prepare_proteins()
    if not (args.all or args.chembl or args.proteins):
        parser.print_help()


if __name__ == "__main__":
    main()
