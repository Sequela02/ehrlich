from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionResult:
    identifier: str
    probability: float
    rank: int = 0
    model_type: str = ""
