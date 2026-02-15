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


@dataclass(frozen=True)
class SpendingRecord:
    award_id: str
    recipient_name: str
    amount: float
    agency: str
    description: str
    period: str
    award_type: str


@dataclass(frozen=True)
class EducationRecord:
    school_id: str
    name: str
    state: str
    student_size: int
    net_price: float
    completion_rate: float
    earnings_median: float


@dataclass(frozen=True)
class HousingData:
    area_name: str
    state: str
    fmr_0br: float
    fmr_1br: float
    fmr_2br: float
    fmr_3br: float
    fmr_4br: float
    median_income: float
    year: int


@dataclass(frozen=True)
class DatasetMetadata:
    dataset_id: str
    title: str
    organization: str
    description: str
    tags: tuple[str, ...]
    resource_count: int
    modified: str
