"""Ports (ABCs) for causal inference estimators.

ISP: one port per method, following prediction/domain/ports.py pattern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.analysis.domain.causal import CausalEstimate


class DiDEstimatorPort(ABC):
    """Difference-in-differences estimator."""

    @abstractmethod
    def estimate(
        self,
        treatment_pre: list[float],
        treatment_post: list[float],
        control_pre: list[float],
        control_post: list[float],
    ) -> CausalEstimate: ...


class PSMEstimatorPort(ABC):
    """Propensity score matching estimator."""

    @abstractmethod
    def estimate(
        self,
        treated_outcomes: list[float],
        control_outcomes: list[float],
        treated_covariates: list[list[float]],
        control_covariates: list[list[float]],
    ) -> CausalEstimate: ...


class RDDEstimatorPort(ABC):
    """Regression discontinuity design estimator."""

    @abstractmethod
    def estimate(
        self,
        running_variable: list[float],
        outcome: list[float],
        cutoff: float,
        bandwidth: float | None = None,
        design: str = "sharp",
    ) -> CausalEstimate: ...


class SyntheticControlPort(ABC):
    """Synthetic control method estimator."""

    @abstractmethod
    def estimate(
        self,
        treated_series: list[float],
        donor_matrix: list[list[float]],
        treatment_period: int,
    ) -> CausalEstimate: ...
