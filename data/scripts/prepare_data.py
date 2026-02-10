"""Data preparation script for Ehrlich.

Downloads and prepares datasets for antimicrobial discovery:
- ChEMBL bioactivity data for key antimicrobial targets
- Protein structures (PDB) for docking

Usage:
    uv run python data/scripts/prepare_data.py --chembl
    uv run python data/scripts/prepare_data.py --proteins
    uv run python data/scripts/prepare_data.py --all
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add server/src to path so we can import ehrlich modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "server" / "src"))

DATA_DIR = Path(__file__).parent.parent
DATASETS_DIR = DATA_DIR / "datasets"
PROTEINS_DIR = DATA_DIR / "proteins"

# Key antimicrobial targets -- organism names matching ChEMBL API
TARGETS = [
    "Staphylococcus aureus",
    "Escherichia coli",
    "Pseudomonas aeruginosa",
    "Mycobacterium tuberculosis",
    "Acinetobacter baumannii",
]

# Protein structures for docking
PROTEIN_TARGETS = {
    "1KZN": "E. coli DNA gyrase B",
    "3FRB": "S. aureus DHFR",
    "4TZK": "M. tuberculosis InhA",
}

_PDB_URL = "https://files.rcsb.org/download"


async def prepare_chembl() -> None:
    """Download ChEMBL bioactivity data using the existing ChEMBLLoader."""
    from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader

    loader = ChEMBLLoader(cache_dir=DATASETS_DIR)
    print("ChEMBL data preparation:")
    for organism in TARGETS:
        cache_key = f"chembl_{organism.replace(' ', '_').lower()}"
        cache_file = DATASETS_DIR / f"{cache_key}.parquet"
        if cache_file.exists():
            print(f"  [cached] {organism} ({cache_file.name})")
            continue
        print(f"  [downloading] {organism} ...")
        try:
            dataset = await loader.load(organism, threshold=1.0)
            if dataset.size > 0:
                print(f"  [done] {organism}: {dataset.size} compounds, {dataset.active_count} active")
            else:
                print(f"  [warn] {organism}: no data returned from ChEMBL")
        except Exception as e:
            print(f"  [error] {organism}: {e}")
    print("ChEMBL preparation complete.")


async def prepare_proteins() -> None:
    """Download protein structures from RCSB PDB."""
    import httpx

    PROTEINS_DIR.mkdir(parents=True, exist_ok=True)
    print("Protein structure preparation:")
    async with httpx.AsyncClient(timeout=30.0) as client:
        for pdb_id, description in PROTEIN_TARGETS.items():
            output = PROTEINS_DIR / f"{pdb_id}.pdb"
            if output.exists():
                print(f"  [cached] {pdb_id} - {description}")
                continue
            url = f"{_PDB_URL}/{pdb_id}.pdb"
            print(f"  [downloading] {pdb_id} - {description} ...")
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                output.write_bytes(resp.content)
                print(f"  [done] {pdb_id} ({len(resp.content)} bytes)")
            except Exception as e:
                print(f"  [error] {pdb_id}: {e}")
    print("Protein preparation complete.")


async def async_main(args: argparse.Namespace) -> None:
    if args.all or args.chembl:
        await prepare_chembl()
    if args.all or args.proteins:
        await prepare_proteins()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare data for Ehrlich")
    parser.add_argument("--chembl", action="store_true", help="Download ChEMBL bioactivity data")
    parser.add_argument("--proteins", action="store_true", help="Download PDB protein structures")
    parser.add_argument("--all", action="store_true", help="Download everything")
    args = parser.parse_args()

    if not (args.all or args.chembl or args.proteins):
        parser.print_help()
        return

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
