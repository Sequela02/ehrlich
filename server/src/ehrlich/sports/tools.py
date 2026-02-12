"""Sports Science tools for the investigation engine.

6 tools that enable evidence-based sports science research:
literature search, training evidence analysis, protocol comparison,
injury risk assessment, training metrics computation, and
supplement evidence search.
"""

from __future__ import annotations

import json

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient
from ehrlich.sports.application.sports_service import SportsService

_client = SemanticScholarClient()
_service = SportsService(paper_repo=_client)


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
