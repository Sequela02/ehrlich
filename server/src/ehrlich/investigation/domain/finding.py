from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    title: str
    detail: str
    evidence: str = ""
    hypothesis_id: str = ""
    evidence_type: str = "neutral"
    confidence: float = 0.0
    source_type: str = ""
    source_id: str = ""
