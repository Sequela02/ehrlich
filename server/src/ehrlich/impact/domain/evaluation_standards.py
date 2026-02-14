"""Evidence grading standards for impact evaluation.

Based on What Works Clearinghouse (WWC) evidence tiers,
CONEVAL MIR (Matriz de Indicadores para Resultados) levels,
and CREMAA quality criteria.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.impact.domain.entities import ThreatToValidity

WWC_TIERS: dict[str, str] = {
    "strong": (
        "Well-designed RCT or quasi-experimental study with no "
        "serious threats to validity (low attrition, verified equivalence)"
    ),
    "moderate": (
        "Quasi-experimental design with some threats to validity "
        "that are partially addressed (e.g., PSM with sensitivity analysis)"
    ),
    "promising": (
        "Correlational study with statistical controls or pre-post "
        "comparison with a plausible comparison group"
    ),
    "rationale": ("Theory-based or descriptive evidence only; no causal identification strategy"),
}

CONEVAL_MIR_LEVELS: dict[str, str] = {
    "fin": "Long-term societal goal the program contributes to",
    "proposito": "Direct outcome expected for the target population",
    "componente": "Goods or services delivered by the program",
    "actividad": "Key activities required to produce components",
}

CREMAA_CRITERIA: dict[str, str] = {
    "claridad": "Indicator is clear and unambiguous",
    "relevancia": "Indicator is relevant to the program objective",
    "economia": "Data collection is cost-effective",
    "monitoreable": "Indicator can be tracked systematically",
    "adecuado": "Indicator is appropriate for the level it measures",
    "aportacion_marginal": "Indicator adds unique information not captured elsewhere",
}


def classify_evidence_tier(method: str, threats: list[ThreatToValidity]) -> str:
    """Classify evidence strength based on method and threats.

    Returns one of: strong, moderate, promising, rationale.
    """
    strong_methods = {"rct", "randomized_controlled_trial"}
    moderate_methods = {
        "did",
        "difference_in_differences",
        "psm",
        "propensity_score_matching",
        "rdd",
        "regression_discontinuity",
        "synthetic_control",
    }
    promising_methods = {"iv", "instrumental_variables", "fixed_effects", "panel_regression"}

    method_lower = method.lower().replace("-", "_").replace(" ", "_")

    severe_threats = [t for t in threats if t.severity == "high"]

    if method_lower in strong_methods:
        if len(severe_threats) >= 2:
            return "moderate"
        if len(severe_threats) == 1:
            return "moderate"
        return "strong"

    if method_lower in moderate_methods:
        if len(severe_threats) >= 2:
            return "promising"
        return "moderate"

    if method_lower in promising_methods:
        if len(severe_threats) >= 1:
            return "rationale"
        return "promising"

    return "rationale"
