from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResistanceAssessment:
    target_id: str
    mutations: dict[str, str] = field(default_factory=dict)
    risk_level: str = "unknown"
    explanation: str = ""
