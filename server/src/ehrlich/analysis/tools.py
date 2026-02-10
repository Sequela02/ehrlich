import json

from ehrlich.analysis.application.analysis_service import AnalysisService
from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader

_loader = ChEMBLLoader()
_service = AnalysisService(repository=_loader)


async def explore_dataset(target: str, threshold: float = 1.0) -> str:
    """Load and explore a bioactivity dataset for the given target organism."""
    dataset = await _service.explore(target, threshold)
    return json.dumps(
        {
            "name": dataset.name,
            "target": dataset.target,
            "size": dataset.size,
            "active_count": dataset.active_count,
            "inactive_count": dataset.size - dataset.active_count,
            "active_ratio": round(dataset.active_count / dataset.size, 4)
            if dataset.size > 0
            else 0,
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
                "p_value": r.p_value,
                "odds_ratio": round(r.odds_ratio, 4),
                "active_count": r.active_count,
                "total_count": r.total_count,
                "significant": r.p_value < 0.05,
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
