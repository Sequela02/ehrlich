"""Sports Science tools for the investigation engine.

10 tools that enable evidence-based sports science research:
literature search, training evidence analysis, protocol comparison,
injury risk assessment, training metrics computation, supplement
evidence search, clinical trial search, supplement label search,
nutrient data search, and supplement safety search.
"""

from __future__ import annotations

import json

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient
from ehrlich.sports.application.sports_service import SportsService
from ehrlich.sports.infrastructure.clinicaltrials_client import ClinicalTrialsClient
from ehrlich.sports.infrastructure.dsld_client import DSLDClient
from ehrlich.sports.infrastructure.fooddata_client import FoodDataClient
from ehrlich.sports.infrastructure.openfda_client import OpenFDAClient

_client = SemanticScholarClient()
_ct_client = ClinicalTrialsClient()
_dsld_client = DSLDClient()
_food_client = FoodDataClient()
_fda_client = OpenFDAClient()
_service = SportsService(
    paper_repo=_client,
    clinical_trials=_ct_client,
    supplements=_dsld_client,
    nutrients=_food_client,
    adverse_events=_fda_client,
)


async def search_sports_literature(
    query: str,
    limit: int = 10,
) -> str:
    """Search scientific literature for sports science papers.

    Searches Semantic Scholar with sports science context.
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
        return json.dumps(
            {"error": "No studies provided", "intervention": intervention}
        )

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
    assessment = _service.assess_injury_risk(
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
        return json.dumps(
            {"error": "Need at least 7 days of data for meaningful metrics"}
        )

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


async def search_supplement_evidence(
    supplement: str,
    outcome: str = "performance",
    limit: int = 8,
) -> str:
    """Search for evidence on supplement efficacy for sports performance.

    Queries Semantic Scholar for meta-analyses and systematic reviews
    on supplement effects.

    Args:
        supplement: Supplement name (e.g. 'creatine', 'caffeine', 'beta-alanine')
        outcome: Performance outcome (e.g. 'strength', 'endurance', 'recovery')
        limit: Maximum papers to return (default: 8)
    """
    papers = await _service.search_supplement_evidence(supplement, outcome, limit)

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

    return json.dumps(
        {
            "supplement": supplement,
            "outcome": outcome,
            "count": len(results),
            "papers": results,
        }
    )


async def search_clinical_trials(
    condition: str,
    intervention: str = "",
    max_results: int = 10,
) -> str:
    """Search ClinicalTrials.gov for exercise and training RCTs.

    Finds registered clinical trials related to exercise, training, and
    sports interventions. Returns trial ID, status, phase, enrollment,
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


async def search_supplement_labels(
    ingredient: str,
    max_results: int = 10,
) -> str:
    """Search NIH DSLD for supplement products containing an ingredient.

    Queries the NIH Dietary Supplement Label Database for commercial
    supplement products. Returns product name, brand, ingredient list
    with amounts and daily value percentages, and serving size.

    Args:
        ingredient: Ingredient name (e.g. 'creatine', 'caffeine', 'vitamin D')
        max_results: Maximum number of products to return (default: 10)
    """
    labels = await _service.search_supplement_labels(ingredient, max_results)
    return json.dumps(
        {
            "ingredient": ingredient,
            "count": len(labels),
            "products": [
                {
                    "report_id": lb.report_id,
                    "product_name": lb.product_name,
                    "brand": lb.brand,
                    "serving_size": lb.serving_size,
                    "ingredients": [
                        {
                            "name": ing.name,
                            "amount": ing.amount,
                            "unit": ing.unit,
                            "daily_value_pct": ing.daily_value_pct,
                        }
                        for ing in lb.ingredients
                    ],
                }
                for lb in labels
            ],
        }
    )


async def search_nutrient_data(
    food_query: str,
    max_results: int = 5,
) -> str:
    """Search USDA FoodData Central for nutrient profiles.

    Queries the USDA FoodData Central database for food nutrient
    information including macronutrients, vitamins, and minerals.

    Args:
        food_query: Food search query (e.g. 'chicken breast', 'whey protein', 'salmon')
        max_results: Maximum number of food items to return (default: 5)
    """
    profiles = await _service.search_nutrient_data(food_query, max_results)
    return json.dumps(
        {
            "query": food_query,
            "count": len(profiles),
            "foods": [
                {
                    "fdc_id": p.fdc_id,
                    "description": p.description,
                    "brand": p.brand,
                    "category": p.category,
                    "nutrients": [
                        {
                            "name": n.name,
                            "amount": n.amount,
                            "unit": n.unit,
                            "nutrient_number": n.nutrient_number,
                        }
                        for n in p.nutrients
                    ],
                }
                for p in profiles
            ],
        }
    )


async def search_supplement_safety(
    product_name: str,
    max_results: int = 10,
) -> str:
    """Search OpenFDA CAERS for supplement adverse event reports.

    Queries the FDA Center for Food Safety adverse event reporting
    system for supplement-related adverse events. Returns report date,
    products involved, reactions, outcomes, and consumer demographics.

    Args:
        product_name: Supplement product name (e.g. 'creatine', 'pre-workout', 'fat burner')
        max_results: Maximum number of reports to return (default: 10)
    """
    events = await _service.search_supplement_safety(product_name, max_results)
    return json.dumps(
        {
            "product_name": product_name,
            "count": len(events),
            "adverse_events": [
                {
                    "report_id": e.report_id,
                    "date": e.date,
                    "products": list(e.products),
                    "reactions": list(e.reactions),
                    "outcomes": list(e.outcomes),
                    "consumer_age": e.consumer_age,
                    "consumer_gender": e.consumer_gender,
                }
                for e in events
            ],
        }
    )
