from __future__ import annotations

from pathlib import Path

from ehrlich.kernel.exceptions import TargetNotFoundError
from ehrlich.simulation.domain.protein_target import ProteinTarget

_PROTEINS_DIR = Path(__file__).resolve().parents[5] / "data" / "proteins"

# Pre-configured MRSA targets with approximate active-site centers
_TARGETS: dict[str, ProteinTarget] = {
    "1VQQ": ProteinTarget(
        pdb_id="1VQQ",
        name="PBP2a",
        organism="Staphylococcus aureus (MRSA)",
        center_x=26.0,
        center_y=13.0,
        center_z=60.0,
        box_size=22.0,
    ),
    "1AD4": ProteinTarget(
        pdb_id="1AD4",
        name="DHPS",
        organism="Staphylococcus aureus",
        center_x=42.0,
        center_y=34.0,
        center_z=36.0,
        box_size=20.0,
    ),
    "2XCT": ProteinTarget(
        pdb_id="2XCT",
        name="DNA Gyrase",
        organism="Staphylococcus aureus",
        center_x=19.0,
        center_y=-5.0,
        center_z=38.0,
        box_size=22.0,
    ),
    "1UAE": ProteinTarget(
        pdb_id="1UAE",
        name="MurA",
        organism="Escherichia coli",
        center_x=34.0,
        center_y=30.0,
        center_z=22.0,
        box_size=20.0,
    ),
    "3SPU": ProteinTarget(
        pdb_id="3SPU",
        name="NDM-1",
        organism="Klebsiella pneumoniae",
        center_x=14.0,
        center_y=-10.0,
        center_z=5.0,
        box_size=22.0,
    ),
}


class ProteinStore:
    def __init__(self, proteins_dir: Path | None = None) -> None:
        self._dir = proteins_dir or _PROTEINS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def get_target(self, pdb_id: str) -> ProteinTarget:
        target = _TARGETS.get(pdb_id.upper())
        if target is None:
            raise TargetNotFoundError(pdb_id)
        return target

    async def get_pdbqt(self, pdb_id: str) -> str:
        target = self.get_target(pdb_id)
        pdbqt_path = self._dir / f"{target.pdb_id}.pdbqt"
        if not pdbqt_path.exists():
            raise FileNotFoundError(
                f"PDBQT file not found for {target.pdb_id} ({target.name}). "
                f"Expected at: {pdbqt_path}"
            )
        return str(pdbqt_path)

    async def list_targets(self) -> list[ProteinTarget]:
        return list(_TARGETS.values())
