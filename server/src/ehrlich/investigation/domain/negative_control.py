from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NegativeControl:
    smiles: str
    name: str
    prediction_score: float
    expected_inactive: bool = True
    source: str = ""

    @property
    def correctly_classified(self) -> bool:
        return self.prediction_score < 0.5
