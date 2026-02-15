"""Tool registry, domain registry, and MCP config construction.

Single source of truth for what tools and domains exist.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from ehrlich.analysis.tools import (
    analyze_substructures,
    assess_threats,
    compute_cost_effectiveness,
    compute_properties,
    estimate_did,
    estimate_psm,
    estimate_rdd,
    estimate_synthetic_control,
    explore_dataset,
    run_categorical_test,
    run_statistical_test,
    search_bioactivity,
    search_compounds,
    search_pharmacology,
)
from ehrlich.chemistry.tools import (
    compute_descriptors,
    compute_fingerprint,
    generate_3d,
    substructure_match,
    tanimoto_similarity,
    validate_smiles,
)
from ehrlich.impact.tools import (
    compare_programs,
    fetch_benchmark,
    search_economic_indicators,
    search_education_data,
    search_health_indicators,
    search_housing_data,
    search_open_data,
    search_spending_data,
)
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.domain_registry import DomainRegistry
from ehrlich.investigation.domain.domains.impact import IMPACT_EVALUATION
from ehrlich.investigation.domain.domains.molecular import MOLECULAR_SCIENCE
from ehrlich.investigation.domain.domains.nutrition import NUTRITION_SCIENCE
from ehrlich.investigation.domain.domains.training import TRAINING_SCIENCE
from ehrlich.investigation.domain.mcp_config import MCPServerConfig
from ehrlich.investigation.tools import (
    conclude_investigation,
    design_experiment,
    evaluate_hypothesis,
    propose_hypothesis,
    query_uploaded_data,
    record_finding,
    record_negative_control,
    search_prior_research,
)
from ehrlich.investigation.tools_viz import (
    render_admet_radar,
    render_binding_scatter,
    render_causal_diagram,
    render_dose_response,
    render_evidence_matrix,
    render_forest_plot,
    render_funnel_plot,
    render_geographic_comparison,
    render_muscle_heatmap,
    render_nutrient_adequacy,
    render_nutrient_comparison,
    render_parallel_trends,
    render_performance_chart,
    render_program_dashboard,
    render_rdd_plot,
    render_therapeutic_window,
    render_training_timeline,
)
from ehrlich.literature.tools import get_reference, search_citations, search_literature
from ehrlich.nutrition.tools import (
    analyze_nutrient_ratios,
    assess_nutrient_adequacy,
    check_intake_safety,
    check_interactions,
    compare_nutrients,
    compute_inflammatory_index,
    search_nutrient_data,
    search_supplement_evidence,
    search_supplement_labels,
    search_supplement_safety,
)
from ehrlich.prediction.tools import (
    cluster_compounds,
    cluster_data,
    predict_candidates,
    predict_scores,
    train_classifier,
    train_model,
)
from ehrlich.simulation.tools import (
    assess_resistance,
    dock_against_target,
    fetch_toxicity_profile,
    get_protein_annotation,
    predict_admet,
    search_disease_targets,
    search_protein_targets,
)
from ehrlich.training.tools import (
    analyze_training_evidence,
    assess_injury_risk,
    compare_protocols,
    compute_dose_response,
    compute_performance_model,
    compute_training_metrics,
    plan_periodization,
    search_clinical_trials,
    search_exercise_database,
    search_pubmed_training,
    search_training_literature,
)


@lru_cache(maxsize=1)
def build_tool_registry() -> ToolRegistry:
    """Build the tool registry (singleton — immutable after construction)."""
    registry = ToolRegistry()

    _chem = frozenset({"chemistry"})
    _lit = frozenset({"literature"})
    _analysis = frozenset({"analysis"})
    _pred = frozenset({"prediction"})
    _sim = frozenset({"simulation"})
    _training = frozenset({"training"})
    _training_clinical = frozenset({"training", "clinical"})
    _training_exercise = frozenset({"training", "exercise"})
    _nutrition = frozenset({"nutrition"})
    _nutrition_safety = frozenset({"nutrition", "safety"})
    _impact = frozenset({"impact"})
    _causal = frozenset({"causal"})
    _ml = frozenset({"ml"})
    _viz = frozenset({"visualization"})
    _chem_viz = frozenset({"chemistry", "visualization"})
    _sim_viz = frozenset({"simulation", "visualization"})
    _training_viz = frozenset({"training", "visualization"})
    _nutrition_viz = frozenset({"nutrition", "visualization"})
    _impact_viz = frozenset({"impact", "visualization"})
    _causal_viz = frozenset({"causal", "visualization"})

    tagged_tools: list[tuple[str, Callable[..., Any], frozenset[str] | None]] = [
        # Chemistry (6)
        ("validate_smiles", validate_smiles, _chem),
        ("compute_descriptors", compute_descriptors, _chem),
        ("compute_fingerprint", compute_fingerprint, _chem),
        ("tanimoto_similarity", tanimoto_similarity, _chem),
        ("generate_3d", generate_3d, _chem),
        ("substructure_match", substructure_match, _chem),
        # Literature (3)
        ("search_literature", search_literature, _lit),
        ("get_reference", get_reference, _lit),
        ("search_citations", search_citations, _lit),
        # Analysis (6)
        ("explore_dataset", explore_dataset, _analysis),
        ("search_compounds", search_compounds, _analysis),
        ("search_bioactivity", search_bioactivity, _analysis),
        ("analyze_substructures", analyze_substructures, _analysis),
        ("compute_properties", compute_properties, _analysis),
        ("search_pharmacology", search_pharmacology, _analysis),
        # Prediction (3) -- molecular-specific
        ("train_model", train_model, _pred),
        ("predict_candidates", predict_candidates, _pred),
        ("cluster_compounds", cluster_compounds, _pred),
        # ML (3) -- domain-agnostic
        ("train_classifier", train_classifier, _ml),
        ("predict_scores", predict_scores, _ml),
        ("cluster_data", cluster_data, _ml),
        # Simulation (7)
        ("search_protein_targets", search_protein_targets, _sim),
        ("dock_against_target", dock_against_target, _sim),
        ("predict_admet", predict_admet, _sim),
        ("fetch_toxicity_profile", fetch_toxicity_profile, _sim),
        ("assess_resistance", assess_resistance, _sim),
        ("get_protein_annotation", get_protein_annotation, _sim),
        ("search_disease_targets", search_disease_targets, _sim),
        # Training Science (11)
        ("search_training_literature", search_training_literature, _training),
        ("analyze_training_evidence", analyze_training_evidence, _training),
        ("compare_protocols", compare_protocols, _training),
        ("assess_injury_risk", assess_injury_risk, _training),
        ("compute_training_metrics", compute_training_metrics, _training),
        ("search_clinical_trials", search_clinical_trials, _training_clinical),
        ("search_pubmed_training", search_pubmed_training, _training),
        ("search_exercise_database", search_exercise_database, _training_exercise),
        ("compute_performance_model", compute_performance_model, _training),
        ("compute_dose_response", compute_dose_response, _training),
        ("plan_periodization", plan_periodization, _training_exercise),
        # Nutrition Science (10)
        ("search_supplement_evidence", search_supplement_evidence, _nutrition),
        ("search_supplement_labels", search_supplement_labels, _nutrition),
        ("search_nutrient_data", search_nutrient_data, _nutrition),
        ("search_supplement_safety", search_supplement_safety, _nutrition_safety),
        ("compare_nutrients", compare_nutrients, _nutrition),
        ("assess_nutrient_adequacy", assess_nutrient_adequacy, _nutrition),
        ("check_intake_safety", check_intake_safety, _nutrition_safety),
        ("check_interactions", check_interactions, _nutrition_safety),
        ("analyze_nutrient_ratios", analyze_nutrient_ratios, _nutrition),
        ("compute_inflammatory_index", compute_inflammatory_index, _nutrition),
        # Impact Evaluation (8)
        ("search_economic_indicators", search_economic_indicators, _impact),
        ("search_health_indicators", search_health_indicators, _impact),
        ("fetch_benchmark", fetch_benchmark, _impact),
        ("compare_programs", compare_programs, _impact),
        ("search_spending_data", search_spending_data, _impact),
        ("search_education_data", search_education_data, _impact),
        ("search_housing_data", search_housing_data, _impact),
        ("search_open_data", search_open_data, _impact),
        # Causal Inference (6) -- domain-agnostic
        ("estimate_did", estimate_did, _causal),
        ("estimate_psm", estimate_psm, _causal),
        ("estimate_rdd", estimate_rdd, _causal),
        ("estimate_synthetic_control", estimate_synthetic_control, _causal),
        ("assess_threats", assess_threats, _causal),
        ("compute_cost_effectiveness", compute_cost_effectiveness, _causal),
        # Visualization (17)
        ("render_binding_scatter", render_binding_scatter, _chem_viz),
        ("render_admet_radar", render_admet_radar, _sim_viz),
        ("render_training_timeline", render_training_timeline, _training_viz),
        ("render_muscle_heatmap", render_muscle_heatmap, _training_viz),
        ("render_forest_plot", render_forest_plot, _viz),
        ("render_evidence_matrix", render_evidence_matrix, _viz),
        ("render_performance_chart", render_performance_chart, _training_viz),
        ("render_funnel_plot", render_funnel_plot, _viz),
        ("render_dose_response", render_dose_response, _training_viz),
        ("render_nutrient_comparison", render_nutrient_comparison, _nutrition_viz),
        ("render_nutrient_adequacy", render_nutrient_adequacy, _nutrition_viz),
        ("render_therapeutic_window", render_therapeutic_window, _nutrition_viz),
        ("render_program_dashboard", render_program_dashboard, _impact_viz),
        ("render_geographic_comparison", render_geographic_comparison, _impact_viz),
        ("render_parallel_trends", render_parallel_trends, _impact_viz),
        ("render_rdd_plot", render_rdd_plot, _causal_viz),
        ("render_causal_diagram", render_causal_diagram, _causal_viz),
        # Statistics (2) -- universal, no tags
        ("run_statistical_test", run_statistical_test, None),
        ("run_categorical_test", run_categorical_test, None),
        # Investigation control (8) -- universal, no tags
        ("record_finding", record_finding, None),
        ("conclude_investigation", conclude_investigation, None),
        ("propose_hypothesis", propose_hypothesis, None),
        ("design_experiment", design_experiment, None),
        ("evaluate_hypothesis", evaluate_hypothesis, None),
        ("record_negative_control", record_negative_control, None),
        ("search_prior_research", search_prior_research, None),
        ("query_uploaded_data", query_uploaded_data, None),
    ]
    for name, func, tags in tagged_tools:
        registry.register(name, func, tags)
    return registry


@lru_cache(maxsize=1)
def build_domain_registry() -> DomainRegistry:
    """Build the domain registry (singleton — immutable after construction)."""
    domain_registry = DomainRegistry()
    domain_registry.register(MOLECULAR_SCIENCE)
    domain_registry.register(TRAINING_SCIENCE)
    domain_registry.register(NUTRITION_SCIENCE)
    domain_registry.register(IMPACT_EVALUATION)
    return domain_registry


def build_mcp_configs() -> list[MCPServerConfig]:
    """Build MCP server configs from environment. Currently supports Excalidraw."""
    configs: list[MCPServerConfig] = []
    if os.environ.get("EHRLICH_MCP_EXCALIDRAW", "").lower() in ("1", "true"):
        configs.append(
            MCPServerConfig(
                name="excalidraw",
                transport="stdio",
                command="npx",
                args=("-y", "@anthropic/claude-code-mcp", "excalidraw"),
                tags=frozenset({"visualization"}),
            )
        )
    return configs
