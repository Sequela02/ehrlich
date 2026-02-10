from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fingerprint:
    bits: tuple[int, ...]
    fp_type: str = "morgan"
    radius: int = 2
    n_bits: int = 2048
