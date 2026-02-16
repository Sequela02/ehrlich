from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ehrlich.training.domain.entities import (
    ClinicalTrial,
    DoseResponsePoint,
    EvidenceAnalysis,
    EvidenceGrade,
    Exercise,
    InjuryRiskAssessment,
    PerformanceModelPoint,
    PeriodizationBlock,
    PeriodizationPlan,
    ProtocolComparison,
    PubMedArticle,
    WorkloadMetrics,
)

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper
    from ehrlich.literature.domain.repository import PaperSearchRepository
    from ehrlich.training.domain.repository import (
        ClinicalTrialRepository,
        ExerciseRepository,
        PubMedRepository,
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


def _compute_i_squared(effect_sizes: list[float], sample_sizes: list[float]) -> float:
    """Compute I-squared heterogeneity statistic using inverse-variance weighting.

    I-squared quantifies the percentage of total variation across studies due to
    heterogeneity rather than chance. Based on Cochran's Q statistic with
    inverse-variance weights (approximated by sample sizes).

    Args:
        effect_sizes: Effect sizes from individual studies
        sample_sizes: Sample sizes from individual studies (used as weights)

    Returns:
        I-squared percentage (0-100), where 0% = no heterogeneity,
        100% = all variation is heterogeneity
    """
    n = len(effect_sizes)
    if n <= 1:
        return 0.0

    # Use sample sizes as inverse-variance weights
    weights = sample_sizes
    total_weight = sum(weights)

    if total_weight <= 0:
        return 0.0

    # Compute weighted mean
    weighted_mean = sum(w * e for w, e in zip(weights, effect_sizes, strict=True)) / total_weight

    # Compute Cochran's Q statistic (weighted sum of squared deviations)
    q_stat = sum(w * (e - weighted_mean) ** 2 for w, e in zip(weights, effect_sizes, strict=True))

    # Degrees of freedom
    df = n - 1

    # I-squared = max(0, (Q - df) / Q * 100)
    if q_stat > 0:
        return max(0.0, (q_stat - df) / q_stat * 100)
    return 0.0


class TrainingService:
    def __init__(
        self,
        paper_repo: PaperSearchRepository,
        clinical_trials: ClinicalTrialRepository | None = None,
        pubmed: PubMedRepository | None = None,
        exercises: ExerciseRepository | None = None,
    ) -> None:
        self._papers = paper_repo
        self._clinical_trials = clinical_trials
        self._pubmed = pubmed
        self._exercises = exercises

    async def search_literature(self, query: str, limit: int = 10) -> list[Paper]:
        mesh_expansion = {
            "hiit": "high intensity interval training",
            "strength": "resistance training",
            "cardio": "cardiovascular exercise",
            "flexibility": "stretching exercise",
            "power": "plyometric training",
            "endurance": "aerobic exercise",
        }

        query_lower = query.lower()
        expanded_terms = [query]
        for short, full in mesh_expansion.items():
            if short in query_lower and full not in query_lower:
                expanded_terms.append(full)

        expanded_query = " ".join(expanded_terms)
        training_query = f"training science {expanded_query}"

        # Fetch extra papers to compensate for filtering
        papers = await self._papers.search(training_query, limit=limit * 2)

        # Filter out non-human studies
        non_human_keywords = {
            "mice",
            "rats",
            "rat",
            "murine",
            "in vitro",
            "cell culture",
            "drosophila",
            "zebrafish",
        }
        human_papers = [
            p for p in papers if not any(kw in p.title.lower() for kw in non_human_keywords)
        ]

        # Sort by study type rank, then year descending
        def get_study_type_rank(paper: Paper) -> int:
            text = (paper.title + " " + paper.abstract).lower()
            if "meta-analysis" in text or "systematic review" in text:
                return 0
            if "rct" in text or "randomized" in text:
                return 1
            if "cohort" in text or "longitudinal" in text:
                return 2
            return 3

        human_papers.sort(key=lambda p: (get_study_type_rank(p), -p.year))

        return human_papers[:limit]

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

        i_squared = _compute_i_squared(effect_sizes, sample_sizes)

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

    async def assess_injury_risk(
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

        epidemiological_context: tuple[dict[str, str], ...] = ()
        if self._pubmed:
            articles = await self._pubmed.search(
                f"injury incidence {sport} systematic review", max_results=3
            )
            epidemiological_context = tuple(
                {
                    "pmid": a.pmid,
                    "title": a.title,
                    "year": str(a.year),
                    "relevance_note": f"Systematic review on {sport} injury epidemiology",
                }
                for a in articles
            )

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
            epidemiological_context=epidemiological_context,
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

    async def search_pubmed(
        self, query: str, mesh_terms: list[str] | None = None, max_results: int = 10
    ) -> list[PubMedArticle]:
        if not self._pubmed:
            return []
        return await self._pubmed.search(query, mesh_terms, max_results)

    async def search_exercises(
        self, muscle_group: str = "", equipment: str = "", category: str = "", limit: int = 20
    ) -> list[Exercise]:
        if not self._exercises:
            return []
        return await self._exercises.search(muscle_group, equipment, category, limit)

    def compute_performance_model(
        self, daily_loads: list[float], fitness_tau: int = 42, fatigue_tau: int = 7
    ) -> list[PerformanceModelPoint]:
        """Banister fitness-fatigue model using EWMA."""
        points: list[PerformanceModelPoint] = []
        fitness = 0.0
        fatigue = 0.0
        alpha_f = 2.0 / (fitness_tau + 1)
        alpha_a = 2.0 / (fatigue_tau + 1)
        for i, load in enumerate(daily_loads):
            fitness = alpha_f * load + (1 - alpha_f) * fitness
            fatigue = alpha_a * load + (1 - alpha_a) * fatigue
            points.append(
                PerformanceModelPoint(
                    day=i + 1,
                    fitness=round(fitness, 2),
                    fatigue=round(fatigue, 2),
                    form=round(fitness - fatigue, 2),
                )
            )
        return points

    def compute_dose_response(
        self,
        dose_levels: list[float],
        effect_sizes: list[float],
        ci_lower: list[float],
        ci_upper: list[float],
    ) -> list[DoseResponsePoint]:
        """Build dose-response curve from dose-effect pairs."""
        n = min(len(dose_levels), len(effect_sizes), len(ci_lower), len(ci_upper))
        points = [
            DoseResponsePoint(
                dose=round(dose_levels[i], 3),
                effect=round(effect_sizes[i], 4),
                ci_lower=round(ci_lower[i], 4),
                ci_upper=round(ci_upper[i], 4),
            )
            for i in range(n)
        ]
        return sorted(points, key=lambda p: p.dose)

    def plan_periodization(
        self,
        goal: str,
        total_weeks: int,
        model: str,
        training_days_per_week: int,
    ) -> PeriodizationPlan | dict[str, str]:
        """Generate an evidence-based periodization plan.

        Implements linear (Rhea 2003), undulating/DUP (Miranda 2011),
        and block (Issurin 2010) periodization models.
        """
        if total_weeks < 4:
            return {"error": "total_weeks must be >= 4"}
        if model not in ("linear", "undulating", "block"):
            return {"error": f"Unknown model '{model}'. Use 'linear', 'undulating', or 'block'."}
        if not 2 <= training_days_per_week <= 7:
            return {"error": "training_days_per_week must be between 2 and 7"}

        freq = training_days_per_week

        if model == "linear":
            blocks, progression, rationale = self._plan_linear(goal, total_weeks, freq)
        elif model == "undulating":
            blocks, progression, rationale = self._plan_undulating(goal, total_weeks, freq)
        else:
            blocks, progression, rationale = self._plan_block(goal, total_weeks, freq)

        return PeriodizationPlan(
            goal=goal,
            total_weeks=total_weeks,
            model=model,
            blocks=tuple(blocks),
            rationale=rationale,
            weekly_load_progression=tuple(round(v, 2) for v in progression),
        )

    def _plan_linear(
        self, goal: str, total_weeks: int, freq: int
    ) -> tuple[list[PeriodizationBlock], list[float], str]:
        """Linear periodization (Rhea 2003): progressive overload across phases."""
        phase_specs = [
            ("Hypertrophy", "accumulation", (0.65, 0.75), (12, 20), "High-volume hypertrophy"),
            ("Strength", "transmutation", (0.75, 0.85), (9, 15), "Moderate-volume strength"),
            ("Peaking", "realization", (0.85, 0.95), (6, 10), "Low-volume peaking"),
        ]
        base_weeks = total_weeks // 3
        remainder = total_weeks % 3
        blocks: list[PeriodizationBlock] = []
        for i, (name, phase_type, intensity, volume, focus) in enumerate(phase_specs):
            weeks = base_weeks + (1 if i < remainder else 0)
            blocks.append(
                PeriodizationBlock(
                    name=name,
                    phase_type=phase_type,
                    weeks=weeks,
                    intensity_range=intensity,
                    volume_range=volume,
                    frequency=freq,
                    focus=f"{focus} for {goal}",
                )
            )

        progression = self._generate_progression(blocks)
        rationale = (
            "Linear periodization (Rhea 2003): systematic progression from high-volume/"
            "low-intensity to low-volume/high-intensity across sequential phases."
        )
        return blocks, progression, rationale

    def _plan_undulating(
        self, goal: str, total_weeks: int, freq: int
    ) -> tuple[list[PeriodizationBlock], list[float], str]:
        """Undulating/DUP periodization (Miranda 2011): daily variation within weeks."""
        blocks = [
            PeriodizationBlock(
                name="Undulating",
                phase_type="accumulation",
                weeks=total_weeks,
                intensity_range=(0.60, 0.82),
                volume_range=(8, 20),
                frequency=freq,
                focus=f"Daily undulating variation for {goal}",
            )
        ]

        cycle = [0.70, 0.82, 0.60]  # moderate, heavy, light
        progression: list[float] = []
        for week in range(total_weeks):
            if (week + 1) % 4 == 0:
                progression.append(0.50)  # deload
            else:
                base = cycle[week % len(cycle)]
                ramp = min(0.10, week * 0.02)
                progression.append(min(1.0, base + ramp))

        rationale = (
            "Daily undulating periodization (Miranda 2011): intensity varies within "
            "each week (moderate/heavy/light rotation) with deload every 4th week."
        )
        return blocks, progression, rationale

    def _plan_block(
        self, goal: str, total_weeks: int, freq: int
    ) -> tuple[list[PeriodizationBlock], list[float], str]:
        """Block periodization (Issurin 2010): concentrated loads in sequential mesocycles."""
        accum_weeks = max(1, round(total_weeks * 0.4))
        trans_weeks = max(1, round(total_weeks * 0.3))
        real_weeks = max(1, total_weeks - accum_weeks - trans_weeks - 1)
        recov_weeks = total_weeks - accum_weeks - trans_weeks - real_weeks

        blocks_specs = [
            (
                "Accumulation",
                "accumulation",
                (0.60, 0.75),
                (15, 25),
                accum_weeks,
                "High-volume work capacity",
            ),
            (
                "Transmutation",
                "transmutation",
                (0.75, 0.85),
                (10, 15),
                trans_weeks,
                "Sport-specific strength transfer",
            ),
            (
                "Realization",
                "realization",
                (0.85, 0.95),
                (6, 10),
                real_weeks,
                "Competition readiness / peak performance",
            ),
        ]
        if recov_weeks > 0:
            blocks_specs.append(
                (
                    "Recovery",
                    "recovery",
                    (0.40, 0.55),
                    (4, 8),
                    recov_weeks,
                    "Active recovery and regeneration",
                )
            )

        blocks: list[PeriodizationBlock] = []
        for name, phase_type, intensity, volume, weeks, focus in blocks_specs:
            blocks.append(
                PeriodizationBlock(
                    name=name,
                    phase_type=phase_type,
                    weeks=weeks,
                    intensity_range=intensity,
                    volume_range=volume,
                    frequency=freq,
                    focus=f"{focus} for {goal}",
                )
            )

        progression = self._generate_progression(blocks)
        rationale = (
            "Block periodization (Issurin 2010): concentrated training loads in sequential "
            "mesocycles -- accumulation (volume), transmutation (intensity), "
            "realization (peaking)."
        )
        return blocks, progression, rationale

    @staticmethod
    def _generate_progression(blocks: list[PeriodizationBlock]) -> list[float]:
        """Generate weekly load progression with deload every 4th week."""
        progression: list[float] = []
        global_week = 0
        for block in blocks:
            base = (block.intensity_range[0] + block.intensity_range[1]) / 2
            for w in range(block.weeks):
                global_week += 1
                if global_week % 4 == 0:
                    progression.append(round(base * 0.55, 2))  # deload: ~45% reduction
                else:
                    ramp_frac = w / max(1, block.weeks - 1) if block.weeks > 1 else 0.5
                    load = base + ramp_frac * 0.10
                    progression.append(round(min(1.0, load), 2))
        return progression
