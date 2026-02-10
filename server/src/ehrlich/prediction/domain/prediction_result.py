from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES


@dataclass(frozen=True)
class PredictionResult:
    smiles: SMILES
    probability: float
    rank: int = 0
    model_type: str = ""
