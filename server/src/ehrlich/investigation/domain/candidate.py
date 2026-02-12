from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candidate:
    identifier: str
    identifier_type: str = ""
    name: str = ""
    rank: int = 0
    notes: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)
