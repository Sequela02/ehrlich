from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    title: str
    detail: str
    evidence: str = ""
    phase: str = ""
    confidence: float = 0.0
