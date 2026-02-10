from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MutationRisk:
    mutation: str
    risk_level: str
    mechanism: str
    delta_energy: float = 0.0


@dataclass(frozen=True)
class ResistanceAssessment:
    target_id: str
    target_name: str = ""
    risk_level: str = "UNKNOWN"
    mutation_risks: tuple[MutationRisk, ...] = ()
    explanation: str = ""
    mutations: dict[str, str] = field(default_factory=dict)
