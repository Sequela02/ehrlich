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
