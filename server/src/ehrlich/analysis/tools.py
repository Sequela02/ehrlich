import json

from ehrlich.analysis.application.analysis_service import AnalysisService
from ehrlich.analysis.application.causal_service import CausalService
from ehrlich.analysis.application.statistics_service import StatisticsService
from ehrlich.analysis.domain.causal import CausalEstimate
from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader
from ehrlich.analysis.infrastructure.did_estimator import DiDEstimator
from ehrlich.analysis.infrastructure.gtopdb_client import GtoPdbClient
from ehrlich.analysis.infrastructure.psm_estimator import PSMEstimator
from ehrlich.analysis.infrastructure.pubchem_client import PubChemClient
from ehrlich.analysis.infrastructure.rdd_estimator import RDDEstimator
from ehrlich.analysis.infrastructure.synthetic_control_estimator import SyntheticControlEstimator
from ehrlich.kernel.exceptions import ExternalServiceError

_loader = ChEMBLLoader()
_pubchem = PubChemClient()
_gtopdb = GtoPdbClient()
_service = AnalysisService(repository=_loader, compound_repo=_pubchem)
_pharmacology = _gtopdb
_stats = StatisticsService()
_did = DiDEstimator()
_psm = PSMEstimator()
_rdd = RDDEstimator()
_sc = SyntheticControlEstimator()
_causal = CausalService()


async def explore_dataset(target: str, threshold: float = 1.0) -> str:
    """Load and explore a bioactivity dataset for the given target organism."""
    try:
        dataset = await _service.explore(target, threshold)
    except ExternalServiceError as e:
        return json.dumps({"error": f"ChEMBL API error: {e.detail}", "target": target})
    if dataset.size == 0:
        return json.dumps(
            {
                "name": dataset.name,
                "target": dataset.target,
                "size": 0,
                "active_count": 0,
                "message": f"No bioactivity data found for '{target}'. "
                "Try a different organism name.",
            }
        )
    return json.dumps(
        {
            "name": dataset.name,
            "target": dataset.target,
            "size": dataset.size,
            "active_count": dataset.active_count,
            "inactive_count": dataset.size - dataset.active_count,
            "active_ratio": round(dataset.active_count / dataset.size, 4),
            "metadata": dataset.metadata,
        }
    )


async def search_compounds(query: str, search_type: str = "name", limit: int = 10) -> str:
    """Search for compounds by name or SMILES similarity via PubChem."""
    try:
        if search_type == "similarity":
            results = await _service.search_by_similarity(query, threshold=0.8, limit=limit)
        else:
            results = await _service.search_compounds(query, limit=limit)
    except ExternalServiceError as e:
        return json.dumps({"error": f"PubChem error: {e.detail}", "query": query})
    return json.dumps(
        {
            "query": query,
            "search_type": search_type,
            "count": len(results),
            "compounds": [
                {
                    "cid": c.cid,
                    "smiles": c.smiles,
                    "iupac_name": c.iupac_name,
                    "molecular_formula": c.molecular_formula,
                    "molecular_weight": c.molecular_weight,
                    "source": c.source,
                }
                for c in results
            ],
        }
    )


async def search_bioactivity(
    target: str, assay_types: str = "MIC,IC50", threshold: float = 1.0
) -> str:
    """Search ChEMBL bioactivity data with flexible assay types."""
    types_list = [t.strip() for t in assay_types.split(",")]
    try:
        dataset = await _service.search_bioactivity(target, types_list, threshold)
    except ExternalServiceError as e:
        return json.dumps({"error": f"ChEMBL API error: {e.detail}", "target": target})
    if dataset.size == 0:
        return json.dumps(
            {
                "target": target,
                "assay_types": types_list,
                "size": 0,
                "message": f"No bioactivity data for '{target}' with types {types_list}.",
            }
        )
    return json.dumps(
        {
            "target": target,
            "assay_types": types_list,
            "size": dataset.size,
            "active_count": dataset.active_count,
            "inactive_count": dataset.size - dataset.active_count,
            "active_ratio": round(dataset.active_count / dataset.size, 4),
            "metadata": dataset.metadata,
        }
    )


async def analyze_substructures(target: str, threshold: float = 1.0) -> str:
    """Analyze enriched substructures in active vs inactive compounds for a target."""
    dataset = await _service.explore(target, threshold)
    results = await _service.analyze_substructures(dataset)
    enrichments = []
    for r in results:
        enrichments.append(
            {
                "substructure": r.substructure,
                "description": r.description,
                "p_value": float(r.p_value),
                "odds_ratio": round(float(r.odds_ratio), 4),
                "active_count": r.active_count,
                "total_count": r.total_count,
                "significant": bool(r.p_value < 0.05),
            }
        )
    return json.dumps(
        {
            "target": target,
            "dataset_size": dataset.size,
            "enrichments": enrichments,
            "significant_count": sum(1 for e in enrichments if e["significant"]),
        }
    )


async def compute_properties(target: str, threshold: float = 1.0) -> str:
    """Compute molecular property distributions for active vs inactive compounds."""
    dataset = await _service.explore(target, threshold)
    props = await _service.compute_properties(dataset)
    return json.dumps({"target": target, **{k: v for k, v in props.items()}})


async def search_pharmacology(target: str, family: str = "") -> str:
    """Search pharmacological data from Guide to Pharmacology."""
    try:
        entries = await _pharmacology.search(target, family)
    except ExternalServiceError as e:
        return json.dumps({"error": f"GtoPdb search failed: {e.detail}", "target": target})
    return json.dumps(
        {
            "target": target,
            "count": len(entries),
            "interactions": [
                {
                    "target_name": e.target_name,
                    "target_family": e.target_family,
                    "ligand_name": e.ligand_name,
                    "ligand_smiles": e.ligand_smiles,
                    "affinity_type": e.affinity_type,
                    "affinity_value": e.affinity_value,
                    "action": e.action,
                    "approved": e.approved,
                }
                for e in entries
            ],
        }
    )


async def run_statistical_test(
    group_a: list[float],
    group_b: list[float],
    test: str = "auto",
    alpha: float = 0.05,
) -> str:
    """Run a statistical hypothesis test comparing two groups of numeric data.

    Returns test statistic, p-value, effect size (Cohen's d) with 95% CI,
    and interpretation. Auto-selects the appropriate test (t-test, Welch's t,
    Mann-Whitney U) based on normality and variance homogeneity.

    Args:
        group_a: First group of numeric values
        group_b: Second group of numeric values
        test: Test type: auto, t_test, welch_t, or mann_whitney
        alpha: Significance level (default 0.05)
    """
    try:
        result = _stats.run_test(group_a, group_b, test, alpha)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(
        {
            "test_name": result.test_name,
            "test_statistic": round(result.test_statistic, 4),
            "p_value": round(result.p_value, 6),
            "effect_size": round(result.effect_size, 4),
            "effect_size_type": result.effect_size_type,
            "ci_95_lower": round(result.ci_lower, 4),
            "ci_95_upper": round(result.ci_upper, 4),
            "sample_size_a": result.sample_size_a,
            "sample_size_b": result.sample_size_b,
            "significant": result.significant,
            "alpha": result.alpha,
            "interpretation": result.interpretation,
        }
    )


async def run_categorical_test(
    table: list[list[int]],
    test: str = "auto",
    alpha: float = 0.05,
) -> str:
    """Run a statistical test on categorical/count data (contingency table).

    Auto-selects Fisher's exact test (small samples) or chi-squared test.
    Returns test statistic, p-value, effect size (odds ratio for 2x2 tables
    or Cramer's V for larger tables), and interpretation.

    Args:
        table: 2D contingency table as list of lists (e.g. [[10, 5], [3, 12]])
        test: Test type: auto, chi_squared, or fisher_exact
        alpha: Significance level (default 0.05)
    """
    try:
        result = _stats.run_categorical_test(table, test, alpha)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(
        {
            "test_name": result.test_name,
            "test_statistic": round(result.test_statistic, 4),
            "p_value": round(result.p_value, 6),
            "effect_size": round(result.effect_size, 4),
            "effect_size_type": result.effect_size_type,
            "sample_size_a": result.sample_size_a,
            "sample_size_b": result.sample_size_b,
            "significant": result.significant,
            "alpha": result.alpha,
            "interpretation": result.interpretation,
        }
    )


def _causal_estimate_to_dict(estimate: CausalEstimate) -> dict[str, object]:
    """Convert a CausalEstimate to a JSON-serializable dict."""
    return {
        "method": estimate.method,
        "effect_size": estimate.effect_size,
        "standard_error": estimate.standard_error,
        "confidence_interval": list(estimate.confidence_interval),
        "p_value": estimate.p_value,
        "n_treatment": estimate.n_treatment,
        "n_control": estimate.n_control,
        "covariates": list(estimate.covariates),
        "assumptions": list(estimate.assumptions),
        "threats": [
            {
                "type": t.type,
                "severity": t.severity,
                "description": t.description,
                "mitigation": t.mitigation,
            }
            for t in estimate.threats
        ],
        "evidence_tier": estimate.evidence_tier,
    }


async def estimate_did(
    treatment_pre: str,
    treatment_post: str,
    control_pre: str,
    control_post: str,
) -> str:
    """Estimate causal effect using difference-in-differences (DiD).

    Computes the DiD estimator with standard error, p-value, Cohen's d,
    95% confidence interval, parallel trends test, and automated threat
    assessment. Returns evidence tier classification (WWC standards).

    Args:
        treatment_pre: JSON array of pre-intervention treatment values
            (e.g. '[85.2, 87.1, 86.5]')
        treatment_post: JSON array of post-intervention treatment values
            (e.g. '[92.3, 94.1, 93.5]')
        control_pre: JSON array of pre-intervention control values
            (e.g. '[84.0, 85.2, 84.8]')
        control_post: JSON array of post-intervention control values
            (e.g. '[85.1, 85.8, 85.3]')
    """
    try:
        t_pre = [float(x) for x in json.loads(treatment_pre)]
        t_post = [float(x) for x in json.loads(treatment_post)]
        c_pre = [float(x) for x in json.loads(control_pre)]
        c_post = [float(x) for x in json.loads(control_post)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON arrays. Provide numeric arrays."})

    if not all([t_pre, t_post, c_pre, c_post]):
        return json.dumps({"error": "All four groups must have at least one value."})

    estimate = _causal.estimate_did(t_pre, t_post, c_pre, c_post, estimator=_did)
    return json.dumps(_causal_estimate_to_dict(estimate))


async def estimate_psm(
    treated_outcomes: str,
    control_outcomes: str,
    treated_covariates: str,
    control_covariates: str,
) -> str:
    """Estimate causal effect using propensity score matching (PSM).

    Computes ATT via nearest-neighbor caliper matching on logistic
    propensity scores. Returns effect size, SE, p-value, balance
    diagnostics, and automated threat assessment.

    Args:
        treated_outcomes: JSON array of treatment group outcome values
            (e.g. '[92.3, 94.1, 93.5]')
        control_outcomes: JSON array of control group outcome values
            (e.g. '[85.1, 85.8, 85.3]')
        treated_covariates: JSON 2D array of treatment covariates
            (e.g. '[[1.2, 3.4], [2.1, 4.5]]')
        control_covariates: JSON 2D array of control covariates
            (e.g. '[[1.0, 3.2], [2.3, 4.1]]')
    """
    try:
        t_out = [float(x) for x in json.loads(treated_outcomes)]
        c_out = [float(x) for x in json.loads(control_outcomes)]
        t_cov = [[float(v) for v in row] for row in json.loads(treated_covariates)]
        c_cov = [[float(v) for v in row] for row in json.loads(control_covariates)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON. Provide numeric arrays."})

    if not t_out or not c_out or not t_cov or not c_cov:
        return json.dumps({"error": "All groups must have at least one value."})

    estimate = _causal.estimate_psm(t_out, c_out, t_cov, c_cov, estimator=_psm)
    return json.dumps(_causal_estimate_to_dict(estimate))


async def estimate_rdd(
    running_variable: str,
    outcome: str,
    cutoff: float,
    bandwidth: float | None = None,
    design: str = "sharp",
) -> str:
    """Estimate causal effect using regression discontinuity design (RDD).

    Computes local linear regression on each side of the cutoff.
    Supports sharp and fuzzy designs. Returns effect size, SE, p-value,
    bandwidth, and automated threat assessment.

    Args:
        running_variable: JSON array of running variable values
            (e.g. '[45, 48, 50, 52, 55]')
        outcome: JSON array of outcome values (same length as running_variable)
            (e.g. '[70, 72, 80, 82, 85]')
        cutoff: Cutoff threshold value
        bandwidth: Optional bandwidth (auto-calculated via IK method if None)
        design: 'sharp' or 'fuzzy'
    """
    try:
        rv = [float(x) for x in json.loads(running_variable)]
        y = [float(x) for x in json.loads(outcome)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON arrays. Provide numeric arrays."})

    if not rv or not y:
        return json.dumps({"error": "Running variable and outcome must have values."})
    if len(rv) != len(y):
        return json.dumps({"error": "Running variable and outcome must have same length."})

    estimate = _causal.estimate_rdd(
        rv,
        y,
        cutoff,
        estimator=_rdd,
        bandwidth=bandwidth,
        design=design,
    )
    return json.dumps(_causal_estimate_to_dict(estimate))


async def estimate_synthetic_control(
    treated_series: str,
    donor_matrix: str,
    treatment_period: int,
) -> str:
    """Estimate causal effect using synthetic control method.

    Constructs a synthetic counterfactual from weighted donor units via
    constrained optimization (SLSQP). Returns effect size, SE, p-value,
    pre-treatment fit quality, and automated threat assessment.

    Args:
        treated_series: JSON array of treated unit time series
            (e.g. '[10, 11, 12, 20, 22, 25]')
        donor_matrix: JSON 2D array where each row is a donor unit time series
            (e.g. '[[10, 11, 12, 13, 14, 15], [9, 10, 11, 12, 13, 14]]')
        treatment_period: Index (0-based) where treatment begins
            (e.g. 3 means first 3 periods are pre-treatment)
    """
    try:
        treated = [float(x) for x in json.loads(treated_series)]
        donors = [[float(v) for v in row] for row in json.loads(donor_matrix)]
    except (json.JSONDecodeError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON. Provide numeric arrays."})

    if not treated or not donors:
        return json.dumps({"error": "Treated series and donor matrix must have values."})

    estimate = _causal.estimate_synthetic_control(treated, donors, treatment_period, estimator=_sc)
    return json.dumps(_causal_estimate_to_dict(estimate))


async def assess_threats(
    method: str,
    sample_sizes: str,
    parallel_trends_p: float | None = None,
    effect_size: float | None = None,
) -> str:
    """Assess validity threats for a causal inference method.

    Knowledge-based threat assessment that identifies potential biases
    and suggests mitigations for different causal methods (DiD, PSM,
    RDD, SC, RCT, IV).

    Args:
        method: Causal method name ('did', 'psm', 'rdd', 'sc', 'rct', 'iv')
        sample_sizes: JSON object mapping group names to sizes
            (e.g. '{{"treatment": 50, "control": 45}}')
        parallel_trends_p: p-value from parallel trends test (DiD only)
        effect_size: Cohen's d or standardized effect size
    """
    try:
        sizes = json.loads(sample_sizes)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in sample_sizes parameter"})

    if not isinstance(sizes, dict):
        return json.dumps({"error": "sample_sizes must be a JSON object"})

    parsed_sizes = {str(k): int(v) for k, v in sizes.items()}
    threats = _causal.assess_threats(method, parsed_sizes, parallel_trends_p, effect_size)
    return json.dumps(
        {
            "method": method,
            "threat_count": len(threats),
            "threats": [
                {
                    "type": t.type,
                    "severity": t.severity,
                    "description": t.description,
                    "mitigation": t.mitigation,
                }
                for t in threats
            ],
        }
    )


async def compute_cost_effectiveness(
    program_name: str,
    total_cost: float,
    total_effect: float,
    currency: str = "USD",
    effect_unit: str = "units",
    comparison_cost: float | None = None,
    comparison_effect: float | None = None,
) -> str:
    """Compute cost-effectiveness ratio and optional ICER.

    Calculates cost per unit of effect for a program, and optionally
    the Incremental Cost-Effectiveness Ratio (ICER) when a comparison
    program is provided.

    Args:
        program_name: Name of the program
        total_cost: Total program cost
        total_effect: Total measured effect (e.g. QALYs, enrollment change)
        currency: Currency code (default: USD)
        effect_unit: Unit of effect measurement (e.g. 'QALYs', 'pp enrollment')
        comparison_cost: Cost of comparison program (for ICER calculation)
        comparison_effect: Effect of comparison program (for ICER calculation)
    """
    result = _causal.compute_cost_effectiveness(
        program_name,
        total_cost,
        total_effect,
        currency,
        effect_unit,
        comparison_cost,
        comparison_effect,
    )
    return json.dumps(
        {
            "program_name": result.program_name,
            "total_cost": result.total_cost,
            "total_effect": result.total_effect,
            "cost_per_unit": result.cost_per_unit,
            "currency": result.currency,
            "effect_unit": result.effect_unit,
            "icer": result.icer,
        }
    )
