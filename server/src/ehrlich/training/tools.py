"""Training Science tools for the investigation engine.

11 tools that enable evidence-based training science research:
literature search (Semantic Scholar + PubMed), exercise database,
training evidence analysis, protocol comparison, injury risk
assessment, training metrics computation, clinical trial search,
performance modeling, dose-response analysis, and periodization planning.
"""

from __future__ import annotations

import json

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient
from ehrlich.training.application.training_service import TrainingService
from ehrlich.training.infrastructure.clinicaltrials_client import ClinicalTrialsClient
from ehrlich.training.infrastructure.pubmed_client import PubMedClient
from ehrlich.training.infrastructure.wger_client import WgerClient

_client = SemanticScholarClient()
_ct_client = ClinicalTrialsClient()
_pubmed_client = PubMedClient()
_wger_client = WgerClient()
_service = TrainingService(
    paper_repo=_client,
    clinical_trials=_ct_client,
    pubmed=_pubmed_client,
    exercises=_wger_client,
)


async def search_training_literature(
    query: str,
    limit: int = 10,
) -> str:
    """Search scientific literature for training science papers.

    Searches Semantic Scholar with training science context.
    Returns papers with title, authors, year, DOI, abstract, and citation count.

    Args:
        query: Search query (e.g. 'HIIT VO2max improvement meta-analysis')
        limit: Maximum number of papers to return (default: 10)
    """
    papers = await _service.search_literature(query, limit=limit)
    results = []
    for p in papers:
        results.append(
            {
                "title": p.title,
                "authors": ", ".join(p.authors),
                "year": p.year,
                "doi": p.doi,
                "abstract": p.abstract[:500] if p.abstract else "",
                "citations": p.citations,
            }
        )
    return json.dumps({"query": query, "count": len(results), "papers": results})


async def analyze_training_evidence(
    intervention: str,
    outcome: str,
    studies: list[dict[str, float]],
) -> str:
    """Analyze evidence quality for a training intervention.

    Computes pooled effect size (Cohen's d), heterogeneity (I-squared),
    and assigns an evidence grade (A-D) based on the number and quality
    of studies.

    Args:
        intervention: Training intervention name (e.g. 'HIIT', 'plyometrics')
        outcome: Outcome measure (e.g. 'VO2max', 'sprint time')
        studies: List of study dicts with keys: effect_size (Cohen's d),
                 sample_size, quality_score (0-1)
    """
    if not studies:
        return json.dumps({"error": "No studies provided", "intervention": intervention})

    analysis = _service.analyze_training_evidence(intervention, outcome, studies)
    return json.dumps(
        {
            "intervention": analysis.intervention,
            "outcome": analysis.outcome,
            "study_count": analysis.study_count,
            "pooled_effect_size": analysis.pooled_effect_size,
            "effect_magnitude": analysis.effect_magnitude,
            "i_squared": analysis.i_squared,
            "heterogeneity": analysis.heterogeneity,
            "average_quality": analysis.average_quality,
            "evidence_grade": analysis.evidence_grade,
            "evidence_label": analysis.evidence_label,
            "total_sample_size": analysis.total_sample_size,
        }
    )


async def compare_protocols(
    protocols: list[dict[str, float | str]],
    outcome: str,
) -> str:
    """Compare training protocols using evidence-weighted scoring.

    Each protocol should include name, effect_size, evidence_quality (0-1),
    injury_risk (0-1), and adherence_rate (0-1).

    Args:
        protocols: List of protocol dicts with keys: name, effect_size,
                   evidence_quality (0-1), injury_risk (0-1), adherence_rate (0-1)
        outcome: Outcome being compared (e.g. 'VO2max improvement')
    """
    if not protocols:
        return json.dumps({"error": "No protocols provided"})

    ranked, recommended = _service.compare_protocols(protocols, outcome)
    return json.dumps(
        {
            "outcome": outcome,
            "protocol_count": len(ranked),
            "protocols": [
                {
                    "name": p.name,
                    "effect_size": p.effect_size,
                    "evidence_quality": p.evidence_quality,
                    "injury_risk": p.injury_risk,
                    "adherence_rate": p.adherence_rate,
                    "composite_score": p.composite_score,
                    "rank": p.rank,
                }
                for p in ranked
            ],
            "recommended": recommended,
        }
    )


async def assess_injury_risk(
    sport: str,
    training_load: float,
    previous_injuries: list[str],
    age: int = 25,
    training_history_years: float = 3.0,
) -> str:
    """Assess injury risk based on training parameters.

    Uses knowledge-based scoring considering sport type, training load,
    injury history, age, and training experience.

    Args:
        sport: Sport name (e.g. 'running', 'soccer', 'weightlifting')
        training_load: Weekly training load in arbitrary units (ACWR-style)
        previous_injuries: List of previous injury types
        age: Athlete age in years (default: 25)
        training_history_years: Years of structured training (default: 3.0)
    """
    assessment = await _service.assess_injury_risk(
        sport, training_load, previous_injuries, age, training_history_years
    )
    return json.dumps(
        {
            "sport": assessment.sport,
            "training_load": assessment.training_load,
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "contributing_factors": assessment.contributing_factors,
            "previous_injuries": list(assessment.previous_injuries),
            "recommendations": list(assessment.recommendations),
            "epidemiological_context": list(assessment.epidemiological_context),
        }
    )


async def compute_training_metrics(
    daily_loads: list[float],
    rpe_values: list[float] | None = None,
) -> str:
    """Compute training monitoring metrics from daily load data.

    Calculates ACWR (acute:chronic workload ratio), monotony, strain,
    and training impulse (TRIMP) equivalents.

    Args:
        daily_loads: List of daily training loads (at least 7 days,
                     ideally 28+ days). Most recent day last.
        rpe_values: Optional list of daily RPE values (1-10 scale),
                    same length as daily_loads.
    """
    if len(daily_loads) < 7:
        return json.dumps({"error": "Need at least 7 days of data for meaningful metrics"})

    metrics = _service.compute_training_metrics(daily_loads, rpe_values)
    result: dict[str, object] = {
        "days_analyzed": metrics.days_analyzed,
        "acute_load_7d": metrics.acute_load_7d,
        "chronic_load_avg": metrics.chronic_load_avg,
        "acwr": metrics.acwr,
        "acwr_zone": metrics.acwr_zone,
        "monotony": metrics.monotony,
        "strain": metrics.strain,
    }

    if metrics.avg_rpe_7d is not None:
        result["avg_rpe_7d"] = metrics.avg_rpe_7d
        result["session_rpe_load_7d"] = metrics.session_rpe_load_7d

    return json.dumps(result)


async def search_clinical_trials(
    condition: str,
    intervention: str = "",
    max_results: int = 10,
) -> str:
    """Search ClinicalTrials.gov for exercise and training RCTs.

    Finds registered clinical trials related to exercise, training, and
    training interventions. Returns trial ID, status, phase, enrollment,
    conditions, interventions, and primary outcomes.

    Args:
        condition: Medical condition or topic (e.g. 'exercise', 'obesity', 'knee injury')
        intervention: Training intervention filter (e.g. 'HIIT', 'resistance training')
        max_results: Maximum number of trials to return (default: 10)
    """
    trials = await _service.search_clinical_trials(condition, intervention, max_results)
    return json.dumps(
        {
            "condition": condition,
            "intervention": intervention,
            "count": len(trials),
            "trials": [
                {
                    "nct_id": t.nct_id,
                    "title": t.title,
                    "status": t.status,
                    "phase": t.phase,
                    "enrollment": t.enrollment,
                    "conditions": list(t.conditions),
                    "interventions": list(t.interventions),
                    "primary_outcomes": list(t.primary_outcomes),
                    "study_type": t.study_type,
                    "start_date": t.start_date,
                }
                for t in trials
            ],
        }
    )


async def search_pubmed_training(
    query: str,
    mesh_terms: list[str] | None = None,
    max_results: int = 10,
) -> str:
    """Search PubMed for exercise and training science papers.

    Searches PubMed via E-utilities with MeSH term support for precise
    biomedical literature retrieval. Complements Semantic Scholar with
    structured medical vocabulary.

    Args:
        query: Search query (e.g. 'resistance training muscle hypertrophy')
        mesh_terms: Optional MeSH terms for precise filtering
                   (e.g. ['Resistance Training', 'Muscle Strength'])
        max_results: Maximum number of papers to return (default: 10)
    """
    articles = await _service.search_pubmed(query, mesh_terms, max_results)
    return json.dumps(
        {
            "query": query,
            "count": len(articles),
            "articles": [
                {
                    "pmid": a.pmid,
                    "title": a.title,
                    "abstract": a.abstract[:500] if a.abstract else "",
                    "authors": ", ".join(a.authors),
                    "journal": a.journal,
                    "year": a.year,
                    "doi": a.doi,
                    "mesh_terms": list(a.mesh_terms),
                    "publication_type": a.publication_type,
                }
                for a in articles
            ],
        }
    )


async def search_exercise_database(
    muscle_group: str = "",
    equipment: str = "",
    category: str = "",
) -> str:
    """Search exercise database for exercises by muscle group, equipment, or category.

    Queries the wger exercise database for structured exercise data including
    primary and secondary muscles, equipment requirements, and descriptions.

    Args:
        muscle_group: Filter by muscle group (e.g. 'chest', 'quadriceps', 'back')
        equipment: Filter by equipment (e.g. 'barbell', 'dumbbell', 'bodyweight')
        category: Filter by category (e.g. 'arms', 'legs', 'chest')
    """
    exercises = await _service.search_exercises(muscle_group, equipment, category)
    return json.dumps(
        {
            "muscle_group": muscle_group,
            "equipment": equipment,
            "category": category,
            "count": len(exercises),
            "exercises": [
                {
                    "id": e.id,
                    "name": e.name,
                    "category": e.category,
                    "muscles_primary": list(e.muscles_primary),
                    "muscles_secondary": list(e.muscles_secondary),
                    "equipment": list(e.equipment),
                    "description": e.description[:300] if e.description else "",
                }
                for e in exercises
            ],
        }
    )


async def compute_performance_model(
    daily_loads: list[float],
    fitness_tau: int = 42,
    fatigue_tau: int = 7,
) -> str:
    """Compute Banister fitness-fatigue performance model (CTL/ATL/TSB).

    Uses exponentially weighted moving averages to model fitness (CTL, 42-day),
    fatigue (ATL, 7-day), and form (TSB = fitness - fatigue).

    Args:
        daily_loads: List of daily training stress scores (at least 14 days).
                     Most recent day last.
        fitness_tau: Fitness time constant in days (default: 42)
        fatigue_tau: Fatigue time constant in days (default: 7)
    """
    if len(daily_loads) < 14:
        return json.dumps({"error": "Need at least 14 days of data for performance modeling"})

    points = _service.compute_performance_model(daily_loads, fitness_tau, fatigue_tau)
    return json.dumps(
        {
            "days": len(points),
            "fitness_tau": fitness_tau,
            "fatigue_tau": fatigue_tau,
            "model": [
                {
                    "day": p.day,
                    "fitness": p.fitness,
                    "fatigue": p.fatigue,
                    "form": p.form,
                }
                for p in points
            ],
            "peak_form_day": max(points, key=lambda p: p.form).day if points else 0,
            "current_form": points[-1].form if points else 0.0,
        }
    )


async def compute_dose_response(
    dose_levels: list[float],
    effect_sizes: list[float],
    ci_lower: list[float],
    ci_upper: list[float],
) -> str:
    """Compute dose-response relationship for exercise interventions.

    Builds a dose-response curve from dose-effect data points, useful for
    determining minimum effective dose and optimal exercise volume.

    Args:
        dose_levels: Exercise doses (e.g. MET-hours/week, sets/week)
        effect_sizes: Effect sizes at each dose level (SMD, RR, or HR)
        ci_lower: Lower confidence interval bounds
        ci_upper: Upper confidence interval bounds
    """
    if len(dose_levels) < 2:
        return json.dumps({"error": "Need at least 2 dose levels for dose-response analysis"})

    points = _service.compute_dose_response(dose_levels, effect_sizes, ci_lower, ci_upper)
    return json.dumps(
        {
            "point_count": len(points),
            "dose_range": [points[0].dose, points[-1].dose] if points else [],
            "points": [
                {
                    "dose": p.dose,
                    "effect": p.effect,
                    "ci_lower": p.ci_lower,
                    "ci_upper": p.ci_upper,
                }
                for p in points
            ],
        }
    )


async def plan_periodization(
    goal: str,
    total_weeks: int = 12,
    model: str = "block",
    training_days_per_week: int = 4,
) -> str:
    """Plan a periodized training program with macro/meso/micro cycles.

    Generates an evidence-based periodization plan with block structure,
    intensity/volume prescriptions, and weekly load progression.

    Args:
        goal: Training goal (e.g. 'strength', 'hypertrophy', 'power', 'general fitness')
        total_weeks: Total program duration in weeks (minimum 4, default: 12)
        model: Periodization model: 'linear', 'undulating', or 'block' (default: 'block')
        training_days_per_week: Training sessions per week (2-7, default: 4)
    """
    plan = _service.plan_periodization(goal, total_weeks, model, training_days_per_week)
    if isinstance(plan, dict):
        return json.dumps(plan)
    return json.dumps(
        {
            "goal": plan.goal,
            "total_weeks": plan.total_weeks,
            "model": plan.model,
            "rationale": plan.rationale,
            "blocks": [
                {
                    "name": b.name,
                    "phase_type": b.phase_type,
                    "weeks": b.weeks,
                    "intensity_range": list(b.intensity_range),
                    "volume_range": list(b.volume_range),
                    "frequency": b.frequency,
                    "focus": b.focus,
                }
                for b in plan.blocks
            ],
            "weekly_load_progression": list(plan.weekly_load_progression),
        }
    )
