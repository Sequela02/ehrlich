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
    epidemiological_context: tuple[dict[str, str], ...] = ()


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


@dataclass(frozen=True)
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    authors: tuple[str, ...]
    journal: str
    year: int
    doi: str
    mesh_terms: tuple[str, ...]
    publication_type: str


@dataclass(frozen=True)
class Exercise:
    id: int
    name: str
    category: str
    muscles_primary: tuple[str, ...]
    muscles_secondary: tuple[str, ...]
    equipment: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class PerformanceModelPoint:
    day: int
    fitness: float
    fatigue: float
    form: float


@dataclass(frozen=True)
class DoseResponsePoint:
    dose: float
    effect: float
    ci_lower: float
    ci_upper: float


@dataclass(frozen=True)
class PeriodizationBlock:
    """A mesocycle block within a periodization plan."""

    name: str
    phase_type: str  # "accumulation", "transmutation", "realization", "recovery"
    weeks: int
    intensity_range: tuple[float, float]  # %1RM range, e.g. (0.65, 0.75)
    volume_range: tuple[int, int]  # sets per muscle group per week
    frequency: int  # sessions per week
    focus: str


@dataclass(frozen=True)
class PeriodizationPlan:
    """Complete periodization plan with blocks and load progression."""

    goal: str
    total_weeks: int
    model: str  # "linear", "undulating", "block"
    blocks: tuple[PeriodizationBlock, ...]
    rationale: str
    weekly_load_progression: tuple[float, ...]  # relative load per week (0.0-1.0)
