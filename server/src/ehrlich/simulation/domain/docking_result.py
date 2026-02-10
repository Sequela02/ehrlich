from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES


@dataclass(frozen=True)
class DockingResult:
    smiles: SMILES
    target_id: str
    binding_energy: float
    pose_rmsd: float = 0.0
    interactions: dict[str, list[str]] = field(default_factory=dict)
