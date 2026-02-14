from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataPoint:
    date: str
    value: float


@dataclass(frozen=True)
class Program:
    name: str
    description: str
    country: str
    region: str
    sector: str
    start_date: str
    end_date: str
    budget: float
    currency: str
    beneficiary_count: int


@dataclass(frozen=True)
class Indicator:
    name: str
    level: str
    unit: str
    baseline: float
    target: float
    actual: float
    period: str


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
class Benchmark:
    source: str
    indicator: str
    value: float
    unit: str
    geography: str
    period: str
    url: str


@dataclass(frozen=True)
class EconomicSeries:
    series_id: str
    title: str
    values: tuple[DataPoint, ...]
    source: str
    unit: str
    frequency: str


@dataclass(frozen=True)
class HealthIndicator:
    indicator_code: str
    indicator_name: str
    country: str
    year: int
    value: float
    unit: str
