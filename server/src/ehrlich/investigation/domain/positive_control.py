from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositiveControl:
    identifier: str
    identifier_type: str = ""
    name: str = ""
    known_activity: str = ""
    source: str = ""
    score: float = 0.0
    expected_active: bool = True

    @property
    def correctly_classified(self) -> bool:
        return self.score >= 0.5
