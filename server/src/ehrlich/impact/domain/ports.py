"""Ports (ABCs) for impact evaluation causal inference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.impact.domain.entities import CausalEstimate


class CausalEstimator(ABC):
    """Abstract base class for causal inference estimators."""

    @abstractmethod
    def estimate_did(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
    ) -> CausalEstimate:
        """Estimate causal effect using difference-in-differences.

        Args:
            treatment_pre: Pre-intervention outcomes for treatment group
            treatment_post: Post-intervention outcomes for treatment group
            control_pre: Pre-intervention outcomes for control group
            control_post: Post-intervention outcomes for control group

        Returns:
            CausalEstimate with effect size, significance, and threats
        """
        ...
