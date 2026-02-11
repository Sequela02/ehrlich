from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PharmacologyEntry:
    target_name: str
    target_family: str = ""
    ligand_name: str = ""
    ligand_smiles: str = ""
    affinity_type: str = ""
    affinity_value: float = 0.0
    action: str = ""
    approved: bool = False
