from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProteinTarget:
    pdb_id: str
    name: str
    organism: str = ""
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    box_size: float = 20.0
