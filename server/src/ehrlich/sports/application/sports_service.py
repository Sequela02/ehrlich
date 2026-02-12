from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ehrlich.sports.domain.entities import (
    AdverseEvent,
    ClinicalTrial,
    EvidenceAnalysis,
    EvidenceGrade,
    InjuryRiskAssessment,
    NutrientProfile,
    ProtocolComparison,
    SupplementLabel,
    WorkloadMetrics,
)

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper
    from ehrlich.literature.domain.repository import PaperSearchRepository
    from ehrlich.sports.domain.repository import (
        AdverseEventRepository,
        ClinicalTrialRepository,
        NutrientRepository,
        SupplementRepository,
    )

_SPORT_BASE_RISK: dict[str, float] = {
    "running": 0.3,
    "soccer": 0.4,
    "basketball": 0.35,
    "football": 0.5,
    "swimming": 0.15,
    "cycling": 0.25,
    "weightlifting": 0.3,
    "tennis": 0.3,
    "gymnastics": 0.45,
    "crossfit": 0.4,
}


class SportsService:
    def __init__(
        self,
        paper_repo: PaperSearchRepository,
        clinical_trials: ClinicalTrialRepository | None = None,
        supplements: SupplementRepository | None = None,
        nutrients: NutrientRepository | None = None,
        adverse_events: AdverseEventRepository | None = None,
    ) -> None:
        self._papers = paper_repo
        self._clinical_trials = clinical_trials
        self._supplements = supplements
        self._nutrients = nutrients
        self._adverse_events = adverse_events

    async def search_literature(self, query: str, limit: int = 10) -> list[Paper]:
        sports_query = f"sports science {query}"
        return await self._papers.search(sports_query, limit=limit)

    async def search_supplement_evidence(
        self, supplement: str, outcome: str = "performance", limit: int = 8
    ) -> list[Paper]:
        query = f"{supplement} {outcome} meta-analysis systematic review sports"
        return await self._papers.search(query, limit=limit)

    def analyze_training_evidence(
        self,
        intervention: str,
        outcome: str,
        studies: list[dict[str, float]],
    ) -> EvidenceAnalysis:
        n = len(studies)
        effect_sizes = [s.get("effect_size", 0.0) for s in studies]
        sample_sizes = [s.get("sample_size", 20) for s in studies]
        quality_scores = [s.get("quality_score", 0.5) for s in studies]

        total_weight = sum(sample_sizes)
        pooled_effect = (
            sum(e * w for e, w in zip(effect_sizes, sample_sizes, strict=True)) / total_weight
            if total_weight > 0
            else 0.0
        )

        if n > 1:
            mean_effect = sum(effect_sizes) / n
            q_stat = sum((e - mean_effect) ** 2 for e in effect_sizes)
            df = n - 1
            i_squared = max(0.0, (q_stat - df) / q_stat * 100) if q_stat > 0 else 0.0
        else:
            i_squared = 0.0

        avg_quality = sum(quality_scores) / n

        if n >= 5 and avg_quality >= 0.7 and i_squared < 50:
            grade = EvidenceGrade.A
        elif n >= 3 and avg_quality >= 0.5:
            grade = EvidenceGrade.B
        elif n >= 2:
            grade = EvidenceGrade.C
        else:
            grade = EvidenceGrade.D

        abs_effect = abs(pooled_effect)
        if abs_effect >= 0.8:
            magnitude = "large"
        elif abs_effect >= 0.5:
            magnitude = "medium"
        elif abs_effect >= 0.2:
            magnitude = "small"
        else:
            magnitude = "trivial"

        heterogeneity = "low" if i_squared < 25 else "moderate" if i_squared < 75 else "high"

        return EvidenceAnalysis(
            intervention=intervention,
            outcome=outcome,
            study_count=n,
            pooled_effect_size=round(pooled_effect, 3),
            effect_magnitude=magnitude,
            i_squared=round(i_squared, 1),
            heterogeneity=heterogeneity,
            average_quality=round(avg_quality, 2),
            evidence_grade=grade.name,
            evidence_label=grade.value,
            total_sample_size=sum(int(s) for s in sample_sizes),
        )

    def compare_protocols(
        self,
        protocols: list[dict[str, float | str]],
        outcome: str,
    ) -> tuple[list[ProtocolComparison], str | None]:
        scored: list[ProtocolComparison] = []
        for p in protocols:
            name = str(p.get("name", "Unknown"))
            effect = float(p.get("effect_size", 0.0))
            quality = float(p.get("evidence_quality", 0.5))
            risk = float(p.get("injury_risk", 0.3))
            adherence = float(p.get("adherence_rate", 0.7))
            composite = effect * quality * (1 - risk) * adherence

            scored.append(
                ProtocolComparison(
                    name=name,
                    effect_size=round(effect, 3),
                    evidence_quality=round(quality, 2),
                    injury_risk=round(risk, 2),
                    adherence_rate=round(adherence, 2),
                    composite_score=round(composite, 3),
                )
            )

        scored.sort(key=lambda x: x.composite_score, reverse=True)
        ranked = [
            ProtocolComparison(
                name=s.name,
                effect_size=s.effect_size,
                evidence_quality=s.evidence_quality,
                injury_risk=s.injury_risk,
                adherence_rate=s.adherence_rate,
                composite_score=s.composite_score,
                rank=i + 1,
            )
            for i, s in enumerate(scored)
        ]

        recommended = ranked[0].name if ranked else None
        return ranked, recommended

    def assess_injury_risk(
        self,
        sport: str,
        training_load: float,
        previous_injuries: list[str],
        age: int = 25,
        training_history_years: float = 3.0,
    ) -> InjuryRiskAssessment:
        base = _SPORT_BASE_RISK.get(sport.lower(), 0.3)

        if training_load > 1.5:
            load_factor = 0.3
        elif training_load > 1.3:
            load_factor = 0.15
        elif training_load > 0.8:
            load_factor = 0.0
        else:
            load_factor = 0.1

        history_factor = min(0.3, len(previous_injuries) * 0.1)

        if age > 35:
            age_factor = 0.1
        elif age < 18:
            age_factor = 0.05
        else:
            age_factor = 0.0

        exp_factor = max(0.0, 0.15 - training_history_years * 0.03)

        total_risk = min(1.0, base + load_factor + history_factor + age_factor + exp_factor)

        if total_risk >= 0.6:
            risk_level = "high"
        elif total_risk >= 0.35:
            risk_level = "moderate"
        else:
            risk_level = "low"

        recommendations: list[str] = []
        if load_factor > 0.1:
            recommendations.append("Reduce training load to ACWR 0.8-1.3 range")
        if history_factor > 0.1:
            recommendations.append("Implement targeted prehab for previous injury sites")
        if age_factor > 0:
            recommendations.append("Include adequate recovery and mobility work")
        if exp_factor > 0:
            recommendations.append("Progress training volume gradually (10% rule)")

        return InjuryRiskAssessment(
            sport=sport,
            training_load=training_load,
            risk_score=round(total_risk, 3),
            risk_level=risk_level,
            contributing_factors={
                "base_sport_risk": round(base, 2),
                "training_load": round(load_factor, 2),
                "injury_history": round(history_factor, 2),
                "age": round(age_factor, 2),
                "experience": round(exp_factor, 2),
            },
            previous_injuries=tuple(previous_injuries),
            recommendations=tuple(recommendations),
        )

    def compute_training_metrics(
        self,
        daily_loads: list[float],
        rpe_values: list[float] | None = None,
    ) -> WorkloadMetrics:
        acute = daily_loads[-7:]
        acute_sum = sum(acute)
        acute_avg = acute_sum / 7

        chronic_window = min(28, len(daily_loads))
        chronic = daily_loads[-chronic_window:]
        chronic_avg = sum(chronic) / chronic_window

        acwr = acute_avg / chronic_avg if chronic_avg > 0 else 0.0

        if len(acute) > 1:
            mean_7 = acute_avg
            variance = sum((x - mean_7) ** 2 for x in acute) / (len(acute) - 1)
            std_7 = math.sqrt(variance) if variance > 0 else 0.001
            monotony = mean_7 / std_7
        else:
            monotony = 0.0

        strain = acute_sum * monotony

        if 0.8 <= acwr <= 1.3:
            acwr_zone = "optimal"
        elif acwr > 1.5:
            acwr_zone = "danger"
        elif acwr > 1.3:
            acwr_zone = "caution"
        else:
            acwr_zone = "undertrained"

        avg_rpe: float | None = None
        session_rpe_load: float | None = None
        if rpe_values and len(rpe_values) == len(daily_loads):
            avg_rpe = round(sum(rpe_values[-7:]) / 7, 1)
            session_rpe_load = round(
                sum(d * r for d, r in zip(daily_loads[-7:], rpe_values[-7:], strict=True)), 1
            )

        return WorkloadMetrics(
            days_analyzed=len(daily_loads),
            acute_load_7d=round(acute_sum, 1),
            chronic_load_avg=round(chronic_avg, 1),
            acwr=round(acwr, 2),
            acwr_zone=acwr_zone,
            monotony=round(monotony, 2),
            strain=round(strain, 1),
            avg_rpe_7d=avg_rpe,
            session_rpe_load_7d=session_rpe_load,
        )

    async def search_clinical_trials(
        self, condition: str, intervention: str = "", max_results: int = 10
    ) -> list[ClinicalTrial]:
        if not self._clinical_trials:
            return []
        return await self._clinical_trials.search(condition, intervention, max_results)

    async def search_supplement_labels(
        self, ingredient: str, max_results: int = 10
    ) -> list[SupplementLabel]:
        if not self._supplements:
            return []
        return await self._supplements.search_labels(ingredient, max_results)

    async def search_nutrient_data(
        self, query: str, max_results: int = 5
    ) -> list[NutrientProfile]:
        if not self._nutrients:
            return []
        return await self._nutrients.search(query, max_results)

    async def search_supplement_safety(
        self, product_name: str, max_results: int = 10
    ) -> list[AdverseEvent]:
        if not self._adverse_events:
            return []
        return await self._adverse_events.search(product_name, max_results)
