from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnrichmentResult:
    substructure: str
    p_value: float
    odds_ratio: float
    active_count: int
    total_count: int
    description: str = ""
