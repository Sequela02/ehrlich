"""Domain entities for causal inference."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatToValidity:
    type: str
    severity: str
    description: str
    mitigation: str


@dataclass(frozen=True)
class CausalEstimate:
    method: str
    effect_size: float
    standard_error: float
    confidence_interval: tuple[float, float]
    p_value: float
    n_treatment: int
    n_control: int
    covariates: tuple[str, ...]
    assumptions: tuple[str, ...]
    threats: tuple[ThreatToValidity, ...]
    evidence_tier: str


@dataclass(frozen=True)
class CostEffectivenessResult:
    program_name: str
    total_cost: float
    total_effect: float
    cost_per_unit: float
    currency: str
    effect_unit: str
    icer: float | None
