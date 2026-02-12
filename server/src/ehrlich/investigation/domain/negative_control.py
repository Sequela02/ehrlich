from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NegativeControl:
    identifier: str
    identifier_type: str = ""
    name: str = ""
    score: float = 0.0
    threshold: float = 0.5
    expected_inactive: bool = True
    source: str = ""

    @property
    def correctly_classified(self) -> bool:
        return self.score < self.threshold
