import json

from ehrlich.analysis.application.analysis_service import AnalysisService
from ehrlich.analysis.application.statistics_service import StatisticsService
from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader
from ehrlich.analysis.infrastructure.gtopdb_client import GtoPdbClient
from ehrlich.analysis.infrastructure.pubchem_client import PubChemClient
from ehrlich.kernel.exceptions import ExternalServiceError

_loader = ChEMBLLoader()
_pubchem = PubChemClient()
_gtopdb = GtoPdbClient()
_service = AnalysisService(repository=_loader, compound_repo=_pubchem)
_pharmacology = _gtopdb
_stats = StatisticsService()


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
