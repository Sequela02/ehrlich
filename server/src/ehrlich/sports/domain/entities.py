from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EvidenceGrade(Enum):
    A = "Strong evidence"
    B = "Moderate evidence"
    C = "Limited evidence"
    D = "Very limited evidence"


@dataclass(frozen=True)
class StudyResult:
    effect_size: float = 0.0
    sample_size: int = 20
    quality_score: float = 0.5


@dataclass(frozen=True)
class EvidenceAnalysis:
    intervention: str
    outcome: str
    study_count: int
    pooled_effect_size: float
    effect_magnitude: str
    i_squared: float
    heterogeneity: str
    average_quality: float
    evidence_grade: str
    evidence_label: str
    total_sample_size: int


@dataclass(frozen=True)
class TrainingProtocol:
    name: str
    effect_size: float = 0.0
    evidence_quality: float = 0.5
    injury_risk: float = 0.3
    adherence_rate: float = 0.7


@dataclass(frozen=True)
class ProtocolComparison:
    name: str
    effect_size: float
    evidence_quality: float
    injury_risk: float
    adherence_rate: float
    composite_score: float
    rank: int = 0


@dataclass(frozen=True)
class InjuryRiskAssessment:
    sport: str
    training_load: float
    risk_score: float
    risk_level: str
    contributing_factors: dict[str, float] = field(default_factory=dict)
    previous_injuries: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkloadMetrics:
    days_analyzed: int
    acute_load_7d: float
    chronic_load_avg: float
    acwr: float
    acwr_zone: str
    monotony: float
    strain: float
    avg_rpe_7d: float | None = None
    session_rpe_load_7d: float | None = None


# --- Clinical Trials ---


@dataclass(frozen=True)
class ClinicalTrial:
    nct_id: str
    title: str
    status: str
    phase: str
    enrollment: int
    conditions: tuple[str, ...]
    interventions: tuple[str, ...]
    primary_outcomes: tuple[str, ...]
    study_type: str
    start_date: str


# --- Supplement Labels (NIH DSLD) ---


@dataclass(frozen=True)
class IngredientEntry:
    name: str
    amount: str
    unit: str
    daily_value_pct: float | None = None


@dataclass(frozen=True)
class SupplementLabel:
    report_id: str
    product_name: str
    brand: str
    ingredients: tuple[IngredientEntry, ...]
    serving_size: str


# --- Nutrient Profiles (USDA FoodData Central) ---


@dataclass(frozen=True)
class NutrientEntry:
    name: str
    amount: float
    unit: str
    nutrient_number: str


@dataclass(frozen=True)
class NutrientProfile:
    fdc_id: int
    description: str
    brand: str
    category: str
    nutrients: tuple[NutrientEntry, ...]


# --- Adverse Events (OpenFDA CAERS) ---


@dataclass(frozen=True)
class AdverseEvent:
    report_id: str
    date: str
    products: tuple[str, ...]
    reactions: tuple[str, ...]
    outcomes: tuple[str, ...]
    consumer_age: str
    consumer_gender: str
