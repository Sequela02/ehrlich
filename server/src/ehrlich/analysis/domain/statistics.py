from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatisticalResult:
    """Result of a statistical hypothesis test."""

    test_name: str
    test_statistic: float
    p_value: float
    effect_size: float
    effect_size_type: str
    ci_lower: float
    ci_upper: float
    sample_size_a: int
    sample_size_b: int
    significant: bool
    alpha: float = 0.05
    interpretation: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.p_value <= 1.0:
            msg = f"p_value must be in [0, 1], got {self.p_value}"
            raise ValueError(msg)
        if self.sample_size_a <= 0 or self.sample_size_b <= 0:
            msg = "Sample sizes must be positive"
            raise ValueError(msg)
