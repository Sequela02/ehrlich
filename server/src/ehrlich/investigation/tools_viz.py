"""Visualization tools for the investigation engine.

17 tools that generate structured chart payloads for the frontend:
binding scatter, ADMET radar, training timeline, muscle heatmap,
forest plot, evidence matrix, performance chart, funnel plot,
dose-response curve, nutrient comparison, nutrient adequacy,
therapeutic window, program dashboard, geographic comparison,
parallel trends, RDD plot, and causal diagram.
"""

from __future__ import annotations

import json
from typing import Any

_KNOWN_MUSCLES_FRONT = frozenset(
    {
        "chest",
        "pectorals",
        "deltoids",
        "biceps",
        "forearms",
        "quadriceps",
        "hip_flexors",
        "tibialis_anterior",
        "abdominals",
        "obliques",
        "adductors",
    }
)

_KNOWN_MUSCLES_BACK = frozenset(
    {
        "trapezius",
        "rhomboids",
        "latissimus_dorsi",
        "lats",
        "erector_spinae",
        "lower_back",
        "triceps",
        "rear_deltoids",
        "hamstrings",
        "glutes",
        "gluteus_maximus",
        "calves",
        "gastrocnemius",
        "soleus",
    }
)

_ALL_KNOWN_MUSCLES = _KNOWN_MUSCLES_FRONT | _KNOWN_MUSCLES_BACK


async def render_binding_scatter(
    compounds: list[dict[str, Any]],
    x_property: str = "molecular_weight",
    y_property: str = "binding_affinity",
    title: str = "Binding Affinity Landscape",
) -> str:
    """Render an interactive scatter plot of compound binding affinities.

    Args:
        compounds: List of dicts with 'name', 'smiles', and numeric properties
        x_property: Property for x-axis (e.g., molecular_weight, logp, tpsa)
        y_property: Property for y-axis (e.g., binding_affinity, ic50, ki)
        title: Chart title
    """
    points = []
    for c in compounds:
        point: dict[str, Any] = {
            "name": c.get("name", ""),
            "smiles": c.get("smiles", ""),
            "x": float(c.get(x_property, 0.0)),
            "y": float(c.get(y_property, 0.0)),
        }
        points.append(point)

    return json.dumps(
        {
            "viz_type": "binding_scatter",
            "title": title,
            "data": {
                "points": points,
                "x_label": x_property,
                "y_label": y_property,
            },
            "config": {"domain": "molecular"},
        }
    )


async def render_admet_radar(
    compound_name: str,
    properties: dict[str, float],
    title: str = "",
) -> str:
    """Render a radar chart of ADMET/drug-likeness properties for a compound.

    Args:
        compound_name: Name or identifier of the compound
        properties: Dict of property_name -> normalized_value (0-1 scale).
                   Common keys: absorption, distribution, metabolism,
                   excretion, toxicity, qed, lipinski
        title: Chart title (defaults to compound name)
    """
    axes = [{"axis": k, "value": max(0.0, min(1.0, float(v)))} for k, v in properties.items()]

    return json.dumps(
        {
            "viz_type": "admet_radar",
            "title": title or f"ADMET Profile: {compound_name}",
            "data": {
                "compound": compound_name,
                "properties": axes,
            },
            "config": {"domain": "molecular"},
        }
    )


async def render_training_timeline(
    daily_loads: list[dict[str, Any]],
    title: str = "Training Load Timeline",
) -> str:
    """Render a training load timeline with ACWR danger zones.

    Args:
        daily_loads: List of dicts with 'date', 'load', 'rpe' (optional), 'duration_min' (optional)
        title: Chart title
    """
    timeline = []
    loads_only: list[float] = []
    for entry in daily_loads:
        load = float(entry.get("load", 0.0))
        loads_only.append(load)
        item: dict[str, Any] = {
            "date": entry.get("date", ""),
            "load": load,
        }
        if "rpe" in entry:
            item["rpe"] = float(entry["rpe"])
        if "duration_min" in entry:
            item["duration_min"] = float(entry["duration_min"])
        timeline.append(item)

    # Compute rolling ACWR (7-day acute / 28-day chronic)
    acwr_series: list[dict[str, Any]] = []
    for i in range(len(loads_only)):
        acute_start = max(0, i - 6)
        acute = sum(loads_only[acute_start : i + 1]) / min(7, i - acute_start + 1)

        chronic_start = max(0, i - 27)
        chronic_window = loads_only[chronic_start : i + 1]
        chronic = sum(chronic_window) / len(chronic_window) if chronic_window else 0.0

        ratio = acute / chronic if chronic > 0 else 0.0
        acwr_series.append(
            {
                "date": timeline[i]["date"] if i < len(timeline) else "",
                "acwr": round(ratio, 3),
            }
        )

    return json.dumps(
        {
            "viz_type": "training_timeline",
            "title": title,
            "data": {
                "timeline": timeline,
                "acwr": acwr_series,
                "danger_zones": [
                    {"min": 1.3, "max": 2.0, "label": "High Risk"},
                    {"min": 0.0, "max": 0.8, "label": "Undertraining"},
                ],
            },
            "config": {"domain": "training"},
        }
    )


async def render_muscle_heatmap(
    muscle_data: list[dict[str, Any]],
    title: str = "Muscle Activation Map",
    view: str = "front",
) -> str:
    """Render an anatomical body diagram with color-coded muscle activation or injury risk.

    Args:
        muscle_data: List of dicts with 'muscle' (e.g., 'quadriceps',
                    'hamstring', 'chest') and 'intensity' (0-1 scale)
        title: Chart title
        view: 'front' or 'back' body view
    """
    validated: list[dict[str, Any]] = []
    for entry in muscle_data:
        muscle = entry.get("muscle", "").lower().strip()
        intensity = max(0.0, min(1.0, float(entry.get("intensity", 0.0))))
        known = muscle in _ALL_KNOWN_MUSCLES
        validated.append(
            {
                "muscle": muscle,
                "intensity": intensity,
                "known": known,
            }
        )

    return json.dumps(
        {
            "viz_type": "muscle_heatmap",
            "title": title,
            "data": {
                "muscles": validated,
                "view": view if view in ("front", "back") else "front",
            },
            "config": {"domain": "training", "color_scale": "intensity"},
        }
    )


async def render_forest_plot(
    studies: list[dict[str, Any]],
    title: str = "Forest Plot",
    effect_measure: str = "SMD",
) -> str:
    """Render a forest plot for meta-analysis results.

    Args:
        studies: List of dicts with 'name', 'effect_size', 'ci_lower', 'ci_upper', 'weight' (0-1)
        title: Chart title
        effect_measure: Label for effect measure axis (SMD, OR, RR, MD)
    """
    processed: list[dict[str, Any]] = []
    total_weight = 0.0
    weighted_sum = 0.0
    for s in studies:
        weight = float(s.get("weight", 0.0))
        effect = float(s.get("effect_size", 0.0))
        total_weight += weight
        weighted_sum += effect * weight
        processed.append(
            {
                "name": s.get("name", ""),
                "effect_size": effect,
                "ci_lower": float(s.get("ci_lower", 0.0)),
                "ci_upper": float(s.get("ci_upper", 0.0)),
                "weight": weight,
            }
        )

    pooled_effect = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Pooled CI: simple weighted average of CI widths
    pooled_lower = 0.0
    pooled_upper = 0.0
    if total_weight > 0:
        pooled_lower = (
            sum(float(s.get("ci_lower", 0.0)) * float(s.get("weight", 0.0)) for s in studies)
            / total_weight
        )
        pooled_upper = (
            sum(float(s.get("ci_upper", 0.0)) * float(s.get("weight", 0.0)) for s in studies)
            / total_weight
        )

    return json.dumps(
        {
            "viz_type": "forest_plot",
            "title": title,
            "data": {
                "studies": processed,
                "pooled": {
                    "effect_size": round(pooled_effect, 4),
                    "ci_lower": round(pooled_lower, 4),
                    "ci_upper": round(pooled_upper, 4),
                },
                "effect_measure": effect_measure,
            },
            "config": {},
        }
    )


async def render_evidence_matrix(
    hypotheses: list[str],
    evidence_sources: list[str],
    matrix: list[list[float]],
    title: str = "Evidence Matrix",
) -> str:
    """Render a hypothesis-by-evidence heatmap showing support/contradiction strength.

    Args:
        hypotheses: Row labels (hypothesis statements, truncated)
        evidence_sources: Column labels (data source names)
        matrix: 2D array of values (-1 to 1, negative=contradicting, positive=supporting)
        title: Chart title
    """
    # Clamp values to [-1, 1]
    clamped = [[max(-1.0, min(1.0, float(v))) for v in row] for row in matrix]

    return json.dumps(
        {
            "viz_type": "evidence_matrix",
            "title": title,
            "data": {
                "rows": hypotheses,
                "cols": evidence_sources,
                "values": clamped,
            },
            "config": {"color_scale": "diverging"},
        }
    )


async def render_performance_chart(
    daily_data: list[dict[str, Any]],
    title: str = "Performance Management Chart",
) -> str:
    """Render a Banister fitness-fatigue performance chart (CTL/ATL/TSB).

    Shows fitness (chronic training load), fatigue (acute training load),
    and form (training stress balance) over time.

    Args:
        daily_data: List of dicts with 'day' (int), 'fitness' (float),
                   'fatigue' (float), 'form' (float)
        title: Chart title
    """
    points: list[dict[str, Any]] = []
    for entry in daily_data:
        points.append(
            {
                "day": int(entry.get("day", 0)),
                "fitness": round(float(entry.get("fitness", 0.0)), 2),
                "fatigue": round(float(entry.get("fatigue", 0.0)), 2),
                "form": round(float(entry.get("form", 0.0)), 2),
            }
        )

    form_values = [p["form"] for p in points]
    peak_form = max(form_values) if form_values else 0.0

    return json.dumps(
        {
            "viz_type": "performance_chart",
            "title": title,
            "data": {
                "points": points,
                "peak_form": round(peak_form, 2),
                "form_zones": [
                    {"min": 15, "max": 25, "label": "Peak Performance"},
                    {"min": -30, "max": -10, "label": "Overreaching Risk"},
                ],
            },
            "config": {"domain": "training"},
        }
    )


async def render_funnel_plot(
    studies: list[dict[str, Any]],
    title: str = "Funnel Plot",
    effect_measure: str = "SMD",
) -> str:
    """Render a funnel plot for publication bias assessment.

    Plots study effect sizes against their precision (1/SE).
    Asymmetry suggests publication bias.

    Args:
        studies: List of dicts with 'name', 'effect_size', 'se' (standard error),
                'sample_size' (optional, for display)
        title: Chart title
        effect_measure: Label for effect measure (SMD, OR, RR, MD)
    """
    processed: list[dict[str, Any]] = []
    all_effects: list[float] = []
    total_weight = 0.0
    weighted_sum = 0.0

    for s in studies:
        effect = float(s.get("effect_size", 0.0))
        se = max(0.001, float(s.get("se", 0.1)))
        precision = 1.0 / se
        weight = precision**2
        total_weight += weight
        weighted_sum += effect * weight
        all_effects.append(effect)
        processed.append(
            {
                "name": s.get("name", ""),
                "effect_size": effect,
                "se": se,
                "precision": round(precision, 3),
                "sample_size": int(s.get("sample_size", 0)),
            }
        )

    pooled_effect = weighted_sum / total_weight if total_weight > 0 else 0.0

    max_precision = max((p["precision"] for p in processed), default=1.0)
    funnel_bounds: list[dict[str, float]] = []
    for prec_frac in [0.1, 0.25, 0.5, 0.75, 1.0]:
        precision = max_precision * prec_frac
        se_at_level = 1.0 / precision if precision > 0 else 1.0
        funnel_bounds.append(
            {
                "precision": round(precision, 3),
                "ci_lower": round(pooled_effect - 1.96 * se_at_level, 4),
                "ci_upper": round(pooled_effect + 1.96 * se_at_level, 4),
            }
        )

    return json.dumps(
        {
            "viz_type": "funnel_plot",
            "title": title,
            "data": {
                "studies": processed,
                "pooled_effect": round(pooled_effect, 4),
                "funnel_bounds": funnel_bounds,
                "effect_measure": effect_measure,
            },
            "config": {},
        }
    )


async def render_dose_response(
    data_points: list[dict[str, Any]],
    title: str = "Dose-Response Curve",
    dose_label: str = "Dose",
    effect_label: str = "Effect",
) -> str:
    """Render a dose-response curve for exercise interventions.

    Shows the relationship between exercise dose and health/performance
    outcomes with confidence intervals.

    Args:
        data_points: List of dicts with 'dose', 'effect', 'ci_lower', 'ci_upper'
        title: Chart title
        dose_label: Label for dose axis (e.g. 'MET-hours/week', 'Sets/week')
        effect_label: Label for effect axis (e.g. 'Hazard Ratio', 'Effect Size')
    """
    processed: list[dict[str, Any]] = []
    for entry in data_points:
        processed.append(
            {
                "dose": float(entry.get("dose", 0.0)),
                "effect": float(entry.get("effect", 0.0)),
                "ci_lower": float(entry.get("ci_lower", 0.0)),
                "ci_upper": float(entry.get("ci_upper", 0.0)),
            }
        )
    processed.sort(key=lambda p: p["dose"])

    return json.dumps(
        {
            "viz_type": "dose_response",
            "title": title,
            "data": {
                "points": processed,
                "dose_label": dose_label,
                "effect_label": effect_label,
            },
            "config": {"domain": "training"},
        }
    )


async def render_nutrient_comparison(
    foods: list[dict[str, Any]],
    nutrients: list[str] | None = None,
    title: str = "Nutrient Comparison",
) -> str:
    """Render grouped bar chart comparing nutrient profiles across foods.

    Args:
        foods: List of dicts with 'name' and 'nutrients' (list of {name, amount, unit, pct_rda})
        nutrients: Optional filter for specific nutrients to compare
        title: Chart title
    """
    nutrient_filter = set(nutrients) if nutrients else None
    processed_foods: list[dict[str, Any]] = []
    all_labels: set[str] = set()

    for food in foods:
        food_entry: dict[str, Any] = {"name": food.get("name", "")}
        nutrient_list: list[dict[str, Any]] = []
        for n in food.get("nutrients", []):
            n_name = n.get("name", "")
            if nutrient_filter and n_name not in nutrient_filter:
                continue
            all_labels.add(n_name)
            nutrient_list.append(
                {
                    "name": n_name,
                    "amount": float(n.get("amount", 0.0)),
                    "unit": n.get("unit", ""),
                    "pct_rda": float(n.get("pct_rda", 0.0)),
                }
            )
        food_entry["nutrients"] = nutrient_list
        processed_foods.append(food_entry)

    return json.dumps(
        {
            "viz_type": "nutrient_comparison",
            "title": title,
            "data": {
                "foods": processed_foods,
                "nutrient_labels": sorted(all_labels),
            },
            "config": {"domain": "nutrition"},
        }
    )


async def render_nutrient_adequacy(
    nutrient_data: list[dict[str, Any]],
    title: str = "Nutrient Adequacy",
) -> str:
    """Render horizontal bar chart showing % of RDA achieved per nutrient.

    Args:
        nutrient_data: List of dicts with 'name', 'pct_rda', 'intake', 'rda', 'unit'
        title: Chart title
    """
    processed: list[dict[str, Any]] = []
    mar_sum = 0.0

    for n in nutrient_data:
        pct_rda = float(n.get("pct_rda", 0.0))
        mar_sum += min(pct_rda, 1.0)

        if pct_rda < 0.5:
            status = "deficient"
        elif pct_rda < 0.8:
            status = "inadequate"
        else:
            status = "adequate"

        processed.append(
            {
                "name": n.get("name", ""),
                "pct_rda": pct_rda,
                "status": status,
                "intake": float(n.get("intake", 0.0)),
                "rda": float(n.get("rda", 0.0)),
                "unit": n.get("unit", ""),
            }
        )

    mar_score = mar_sum / len(nutrient_data) if nutrient_data else 0.0

    return json.dumps(
        {
            "viz_type": "nutrient_adequacy",
            "title": title,
            "data": {
                "nutrients": processed,
                "mar_score": round(mar_score, 4),
            },
            "config": {"domain": "nutrition"},
        }
    )


async def render_therapeutic_window(
    nutrients: list[dict[str, Any]],
    title: str = "Therapeutic Window",
) -> str:
    """Render range chart showing safety zones (EAR-RDA-UL) per nutrient.

    Args:
        nutrients: List of dicts with 'name', 'ear', 'rda', 'ul', 'current_intake', 'unit'
        title: Chart title
    """
    processed: list[dict[str, Any]] = []

    for n in nutrients:
        ear = float(n.get("ear", 0.0))
        rda = float(n.get("rda", 0.0))
        ul = float(n.get("ul", 0.0))
        intake = float(n.get("current_intake", 0.0))

        if intake < ear:
            zone = "deficient"
        elif intake < rda:
            zone = "inadequate"
        elif ul > 0 and intake >= ul:
            zone = "excessive"
        else:
            zone = "adequate"

        processed.append(
            {
                "name": n.get("name", ""),
                "ear": ear,
                "rda": rda,
                "ul": ul,
                "current_intake": intake,
                "unit": n.get("unit", ""),
                "zone": zone,
            }
        )

    return json.dumps(
        {
            "viz_type": "therapeutic_window",
            "title": title,
            "data": {"nutrients": processed},
            "config": {"domain": "nutrition"},
        }
    )


async def render_program_dashboard(
    indicators: list[dict[str, Any]],
    program_name: str = "Program",
    title: str = "",
) -> str:
    """Render a multi-indicator KPI dashboard for a social program.

    Shows baseline, target, and actual values for each indicator with
    progress coloring (green >= 80%, yellow 50-80%, red < 50%).

    Args:
        indicators: List of dicts with 'name', 'baseline', 'target',
                   'actual', 'unit'
        program_name: Name of the program
        title: Chart title (defaults to program name)
    """
    processed: list[dict[str, Any]] = []
    for ind in indicators:
        baseline = float(ind.get("baseline", 0.0))
        target = float(ind.get("target", 0.0))
        actual = float(ind.get("actual", 0.0))

        pct_target = actual / target if target != 0 else 0.0
        if pct_target >= 0.8:
            status = "on_track"
        elif pct_target >= 0.5:
            status = "at_risk"
        else:
            status = "off_track"

        processed.append(
            {
                "name": ind.get("name", ""),
                "baseline": round(baseline, 2),
                "target": round(target, 2),
                "actual": round(actual, 2),
                "unit": ind.get("unit", ""),
                "pct_target": round(pct_target, 4),
                "status": status,
            }
        )

    return json.dumps(
        {
            "viz_type": "program_dashboard",
            "title": title or f"{program_name} Dashboard",
            "data": {
                "program_name": program_name,
                "indicators": processed,
            },
            "config": {"domain": "impact"},
        }
    )


async def render_geographic_comparison(
    regions: list[dict[str, Any]],
    metric_name: str = "Value",
    benchmark: float | None = None,
    title: str = "Geographic Comparison",
) -> str:
    """Render a bar chart comparing regions with optional benchmark line.

    Args:
        regions: List of dicts with 'name' and 'value'
        metric_name: Label for the metric axis
        benchmark: Optional benchmark value shown as reference line
        title: Chart title
    """
    processed: list[dict[str, Any]] = []
    for r in regions:
        processed.append(
            {
                "name": r.get("name", ""),
                "value": round(float(r.get("value", 0.0)), 2),
            }
        )

    return json.dumps(
        {
            "viz_type": "geographic_comparison",
            "title": title,
            "data": {
                "regions": processed,
                "metric_name": metric_name,
                "benchmark": round(benchmark, 2) if benchmark is not None else None,
            },
            "config": {"domain": "impact"},
        }
    )


async def render_parallel_trends(
    treatment_series: list[dict[str, Any]],
    control_series: list[dict[str, Any]],
    treatment_start: str = "",
    title: str = "Parallel Trends",
) -> str:
    """Render a DiD parallel trends chart (treatment vs control over time).

    Shows two line series with a vertical reference line at treatment
    start and shaded pre/post regions.

    Args:
        treatment_series: List of dicts with 'period' and 'value'
        control_series: List of dicts with 'period' and 'value'
        treatment_start: Period label where treatment begins
        title: Chart title
    """
    treatment = [
        {"period": t.get("period", ""), "value": round(float(t.get("value", 0.0)), 2)}
        for t in treatment_series
    ]
    control = [
        {"period": c.get("period", ""), "value": round(float(c.get("value", 0.0)), 2)}
        for c in control_series
    ]

    return json.dumps(
        {
            "viz_type": "parallel_trends",
            "title": title,
            "data": {
                "treatment": treatment,
                "control": control,
                "treatment_start": treatment_start,
            },
            "config": {"domain": "impact"},
        }
    )


async def render_rdd_plot(
    observations: list[dict[str, Any]],
    cutoff: float,
    fitted_left: list[dict[str, float]] | None = None,
    fitted_right: list[dict[str, float]] | None = None,
    title: str = "Regression Discontinuity",
) -> str:
    """Render an RDD scatter plot with fitted lines and cutoff reference.

    Shows observations colored by side of cutoff, vertical dashed cutoff
    line, and optional fitted regression lines on each side.

    Args:
        observations: List of dicts with 'x' (running variable) and 'y' (outcome)
        cutoff: Cutoff threshold value (vertical reference line)
        fitted_left: Optional fitted points for left side [{x, y}, ...]
        fitted_right: Optional fitted points for right side [{x, y}, ...]
        title: Chart title
    """
    points: list[dict[str, Any]] = []
    for obs in observations:
        x_val = float(obs.get("x", 0.0))
        points.append(
            {
                "x": x_val,
                "y": float(obs.get("y", 0.0)),
                "side": "right" if x_val >= cutoff else "left",
            }
        )

    left_fit = [
        {"x": float(p.get("x", 0.0)), "y": float(p.get("y", 0.0))} for p in (fitted_left or [])
    ]
    right_fit = [
        {"x": float(p.get("x", 0.0)), "y": float(p.get("y", 0.0))} for p in (fitted_right or [])
    ]

    return json.dumps(
        {
            "viz_type": "rdd_plot",
            "title": title,
            "data": {
                "observations": points,
                "cutoff": cutoff,
                "fitted_left": left_fit,
                "fitted_right": right_fit,
            },
            "config": {"domain": "causal"},
        }
    )


async def render_causal_diagram(
    nodes: list[dict[str, str]],
    edges: list[dict[str, str]],
    title: str = "Causal Diagram",
) -> str:
    """Render a directed acyclic graph (DAG) for causal analysis.

    Shows treatment, outcome, and confounder nodes with directed edges
    representing causal relationships and associations.

    Args:
        nodes: List of dicts with 'id', 'label', and 'type'
               (type: 'treatment', 'outcome', 'confounder', 'mediator', 'instrument')
        edges: List of dicts with 'source', 'target', and 'type'
               (type: 'causal', 'association', 'instrument')
        title: Chart title
    """
    valid_node_types = {"treatment", "outcome", "confounder", "mediator", "instrument"}
    processed_nodes: list[dict[str, str]] = []
    for node in nodes:
        node_type = node.get("type", "confounder")
        if node_type not in valid_node_types:
            node_type = "confounder"
        processed_nodes.append(
            {
                "id": node.get("id", ""),
                "label": node.get("label", ""),
                "type": node_type,
            }
        )

    processed_edges: list[dict[str, str]] = []
    for edge in edges:
        edge_type = edge.get("type", "causal")
        if edge_type not in ("causal", "association", "instrument"):
            edge_type = "causal"
        processed_edges.append(
            {
                "source": edge.get("source", ""),
                "target": edge.get("target", ""),
                "type": edge_type,
            }
        )

    return json.dumps(
        {
            "viz_type": "causal_diagram",
            "title": title,
            "data": {
                "nodes": processed_nodes,
                "edges": processed_edges,
            },
            "config": {"domain": "causal"},
        }
    )
