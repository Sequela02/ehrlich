from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES


@dataclass
class Candidate:
    smiles: SMILES
    name: str = ""
    prediction_score: float = 0.0
    docking_score: float = 0.0
    admet_score: float = 0.0
    resistance_risk: str = "unknown"
    rank: int = 0
    notes: str = ""
