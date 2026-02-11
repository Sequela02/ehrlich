from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetAssociation:
    target_id: str
    target_name: str
    disease_name: str
    association_score: float
    evidence_count: int = 0
    tractability: str = ""
    known_drugs: list[str] = field(default_factory=list)
