"""Sports Science tools for the investigation engine.

6 tools that enable evidence-based sports science research:
literature search, training evidence analysis, protocol comparison,
injury risk assessment, training metrics computation, and
supplement evidence search.
"""

from __future__ import annotations

import json
import math

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient

_client = SemanticScholarClient()


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
    sports_query = f"sports science {query}"
    papers = await _client.search(sports_query, limit=limit)
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

    n = len(studies)
    effect_sizes = [s.get("effect_size", 0.0) for s in studies]
    sample_sizes = [s.get("sample_size", 20) for s in studies]
    quality_scores = [s.get("quality_score", 0.5) for s in studies]

    # Weighted mean effect size (weighted by sample size)
    total_weight = sum(sample_sizes)
    pooled_effect = (
        sum(e * w for e, w in zip(effect_sizes, sample_sizes, strict=True)) / total_weight
        if total_weight > 0
        else 0.0
    )

    # Simplified I-squared (heterogeneity)
    if n > 1:
        mean_effect = sum(effect_sizes) / n
        q_stat = sum((e - mean_effect) ** 2 for e in effect_sizes)
        df = n - 1
        i_squared = max(0.0, (q_stat - df) / q_stat * 100) if q_stat > 0 else 0.0
    else:
        i_squared = 0.0

    avg_quality = sum(quality_scores) / n

    # Evidence grade
    if n >= 5 and avg_quality >= 0.7 and i_squared < 50:
        grade = "A"
        grade_label = "Strong evidence"
    elif n >= 3 and avg_quality >= 0.5:
        grade = "B"
        grade_label = "Moderate evidence"
    elif n >= 2:
        grade = "C"
        grade_label = "Limited evidence"
    else:
        grade = "D"
        grade_label = "Very limited evidence"

    # Effect size interpretation
    abs_effect = abs(pooled_effect)
    if abs_effect >= 0.8:
        magnitude = "large"
    elif abs_effect >= 0.5:
        magnitude = "medium"
    elif abs_effect >= 0.2:
        magnitude = "small"
    else:
        magnitude = "trivial"

    return json.dumps(
        {
            "intervention": intervention,
            "outcome": outcome,
            "study_count": n,
            "pooled_effect_size": round(pooled_effect, 3),
            "effect_magnitude": magnitude,
            "i_squared": round(i_squared, 1),
            "heterogeneity": (
                "low" if i_squared < 25 else "moderate" if i_squared < 75 else "high"
            ),
            "average_quality": round(avg_quality, 2),
            "evidence_grade": grade,
            "evidence_label": grade_label,
            "total_sample_size": sum(sample_sizes),
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

    scored: list[dict[str, str | float | int]] = []
    for p in protocols:
        name = str(p.get("name", "Unknown"))
        effect = float(p.get("effect_size", 0.0))
        quality = float(p.get("evidence_quality", 0.5))
        risk = float(p.get("injury_risk", 0.3))
        adherence = float(p.get("adherence_rate", 0.7))

        # Composite score: effectiveness * quality * safety * adherence
        composite = effect * quality * (1 - risk) * adherence

        scored.append(
            {
                "name": name,
                "effect_size": round(effect, 3),
                "evidence_quality": round(quality, 2),
                "injury_risk": round(risk, 2),
                "adherence_rate": round(adherence, 2),
                "composite_score": round(composite, 3),
            }
        )

    scored.sort(key=lambda x: float(x["composite_score"]), reverse=True)

    for i, s in enumerate(scored):
        s["rank"] = i + 1

    return json.dumps(
        {
            "outcome": outcome,
            "protocol_count": len(scored),
            "protocols": scored,
            "recommended": scored[0]["name"] if scored else None,
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
    # Base risk by sport category
    sport_risk: dict[str, float] = {
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
    base = sport_risk.get(sport.lower(), 0.3)

    # Training load factor (ACWR-inspired)
    if training_load > 1.5:
        load_factor = 0.3
    elif training_load > 1.3:
        load_factor = 0.15
    elif training_load > 0.8:
        load_factor = 0.0  # sweet spot
    else:
        load_factor = 0.1  # too low = detraining risk

    # Injury history factor
    history_factor = min(0.3, len(previous_injuries) * 0.1)

    # Age factor
    if age > 35:
        age_factor = 0.1
    elif age < 18:
        age_factor = 0.05
    else:
        age_factor = 0.0

    # Experience factor (less experience = higher risk)
    exp_factor = max(0.0, 0.15 - training_history_years * 0.03)

    total_risk = min(1.0, base + load_factor + history_factor + age_factor + exp_factor)

    if total_risk >= 0.6:
        risk_level = "high"
    elif total_risk >= 0.35:
        risk_level = "moderate"
    else:
        risk_level = "low"

    recommendations = []
    if load_factor > 0.1:
        recommendations.append("Reduce training load to ACWR 0.8-1.3 range")
    if history_factor > 0.1:
        recommendations.append(
            "Implement targeted prehab for previous injury sites"
        )
    if age_factor > 0:
        recommendations.append("Include adequate recovery and mobility work")
    if exp_factor > 0:
        recommendations.append("Progress training volume gradually (10% rule)")

    return json.dumps(
        {
            "sport": sport,
            "training_load": training_load,
            "risk_score": round(total_risk, 3),
            "risk_level": risk_level,
            "contributing_factors": {
                "base_sport_risk": round(base, 2),
                "training_load": round(load_factor, 2),
                "injury_history": round(history_factor, 2),
                "age": round(age_factor, 2),
                "experience": round(exp_factor, 2),
            },
            "previous_injuries": previous_injuries,
            "recommendations": recommendations,
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

    # Acute load (last 7 days)
    acute = daily_loads[-7:]
    acute_sum = sum(acute)
    acute_avg = acute_sum / 7

    # Chronic load (last 28 days or available)
    chronic_window = min(28, len(daily_loads))
    chronic = daily_loads[-chronic_window:]
    chronic_avg = sum(chronic) / chronic_window

    # ACWR
    acwr = acute_avg / chronic_avg if chronic_avg > 0 else 0.0

    # Monotony (mean / std dev of 7-day block)
    if len(acute) > 1:
        mean_7 = acute_avg
        variance = sum((x - mean_7) ** 2 for x in acute) / (len(acute) - 1)
        std_7 = math.sqrt(variance) if variance > 0 else 0.001
        monotony = mean_7 / std_7
    else:
        monotony = 0.0

    # Strain
    strain = acute_sum * monotony

    # ACWR zone
    if 0.8 <= acwr <= 1.3:
        acwr_zone = "optimal"
    elif acwr > 1.5:
        acwr_zone = "danger"
    elif acwr > 1.3:
        acwr_zone = "caution"
    else:
        acwr_zone = "undertrained"

    result: dict[str, object] = {
        "days_analyzed": len(daily_loads),
        "acute_load_7d": round(acute_sum, 1),
        "chronic_load_avg": round(chronic_avg, 1),
        "acwr": round(acwr, 2),
        "acwr_zone": acwr_zone,
        "monotony": round(monotony, 2),
        "strain": round(strain, 1),
    }

    if rpe_values and len(rpe_values) == len(daily_loads):
        avg_rpe = sum(rpe_values[-7:]) / 7
        session_rpe_load = sum(
            d * r for d, r in zip(daily_loads[-7:], rpe_values[-7:], strict=True)
        )
        result["avg_rpe_7d"] = round(avg_rpe, 1)
        result["session_rpe_load_7d"] = round(session_rpe_load, 1)

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
    query = f"{supplement} {outcome} meta-analysis systematic review sports"
    papers = await _client.search(query, limit=limit)

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
