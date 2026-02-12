"""Visualization tools for the investigation engine.

6 tools that generate structured chart payloads for the frontend:
binding scatter, ADMET radar, training timeline, muscle heatmap,
forest plot, and evidence matrix.
"""

from __future__ import annotations

import json
from typing import Any

_KNOWN_MUSCLES_FRONT = frozenset({
    "chest", "pectorals", "deltoids", "biceps", "forearms",
    "quadriceps", "hip_flexors", "tibialis_anterior", "abdominals",
    "obliques", "adductors",
})

_KNOWN_MUSCLES_BACK = frozenset({
    "trapezius", "rhomboids", "latissimus_dorsi", "lats",
    "erector_spinae", "lower_back", "triceps", "rear_deltoids",
    "hamstrings", "glutes", "gluteus_maximus", "calves",
    "gastrocnemius", "soleus",
})

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

    return json.dumps({
        "viz_type": "binding_scatter",
        "title": title,
        "data": {
            "points": points,
            "x_label": x_property,
            "y_label": y_property,
        },
        "config": {"domain": "molecular"},
    })


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
    axes = [
        {"axis": k, "value": max(0.0, min(1.0, float(v)))}
        for k, v in properties.items()
    ]

    return json.dumps({
        "viz_type": "admet_radar",
        "title": title or f"ADMET Profile: {compound_name}",
        "data": {
            "compound": compound_name,
            "properties": axes,
        },
        "config": {"domain": "molecular"},
    })


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
        acwr_series.append({
            "date": timeline[i]["date"] if i < len(timeline) else "",
            "acwr": round(ratio, 3),
        })

    return json.dumps({
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
    })


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
        validated.append({
            "muscle": muscle,
            "intensity": intensity,
            "known": known,
        })

    return json.dumps({
        "viz_type": "muscle_heatmap",
        "title": title,
        "data": {
            "muscles": validated,
            "view": view if view in ("front", "back") else "front",
        },
        "config": {"domain": "training", "color_scale": "intensity"},
    })


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
        processed.append({
            "name": s.get("name", ""),
            "effect_size": effect,
            "ci_lower": float(s.get("ci_lower", 0.0)),
            "ci_upper": float(s.get("ci_upper", 0.0)),
            "weight": weight,
        })

    pooled_effect = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Pooled CI: simple weighted average of CI widths
    pooled_lower = 0.0
    pooled_upper = 0.0
    if total_weight > 0:
        pooled_lower = sum(
            float(s.get("ci_lower", 0.0)) * float(s.get("weight", 0.0))
            for s in studies
        ) / total_weight
        pooled_upper = sum(
            float(s.get("ci_upper", 0.0)) * float(s.get("weight", 0.0))
            for s in studies
        ) / total_weight

    return json.dumps({
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
    })


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
    clamped = [
        [max(-1.0, min(1.0, float(v))) for v in row]
        for row in matrix
    ]

    return json.dumps({
        "viz_type": "evidence_matrix",
        "title": title,
        "data": {
            "rows": hypotheses,
            "cols": evidence_sources,
            "values": clamped,
        },
        "config": {"color_scale": "diverging"},
    })
