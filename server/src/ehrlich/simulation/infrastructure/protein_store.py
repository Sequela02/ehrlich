from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ehrlich.kernel.exceptions import TargetNotFoundError
from ehrlich.simulation.domain.protein_target import ProteinTarget

if TYPE_CHECKING:
    from ehrlich.simulation.domain.repository import ProteinTargetRepository

logger = logging.getLogger(__name__)

_PROTEINS_DIR = Path(__file__).resolve().parents[5] / "data" / "proteins"
_TARGETS_YAML = Path(__file__).resolve().parents[5] / "data" / "targets" / "default.yaml"


def _load_targets_from_yaml(yaml_path: Path) -> dict[str, ProteinTarget]:
    if not yaml_path.exists():
        logger.warning("Targets YAML not found: %s", yaml_path)
        return {}
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    targets: dict[str, ProteinTarget] = {}
    for entry in data.get("targets", []):
        pdb_id = str(entry["pdb_id"]).upper()
        targets[pdb_id] = ProteinTarget(
            pdb_id=pdb_id,
            name=str(entry["name"]),
            organism=str(entry.get("organism", "")),
            center_x=float(entry.get("center_x", 0.0)),
            center_y=float(entry.get("center_y", 0.0)),
            center_z=float(entry.get("center_z", 0.0)),
            box_size=float(entry.get("box_size", 20.0)),
        )
    return targets


class ProteinStore:
    def __init__(
        self,
        proteins_dir: Path | None = None,
        yaml_path: Path | None = None,
        rcsb_client: ProteinTargetRepository | None = None,
    ) -> None:
        self._dir = proteins_dir or _PROTEINS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._targets = _load_targets_from_yaml(yaml_path or _TARGETS_YAML)
        self._rcsb = rcsb_client

    def get_target(self, pdb_id: str) -> ProteinTarget:
        target = self._targets.get(pdb_id.upper())
        if target is None:
            raise TargetNotFoundError(pdb_id)
        return target

    async def search(self, query: str, organism: str = "", limit: int = 10) -> list[ProteinTarget]:
        if self._rcsb is not None:
            return await self._rcsb.search(query, organism, limit)
        results = [
            t
            for t in self._targets.values()
            if query.lower() in t.name.lower() or query.lower() in t.organism.lower()
        ]
        return results[:limit]

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
        return list(self._targets.values())
