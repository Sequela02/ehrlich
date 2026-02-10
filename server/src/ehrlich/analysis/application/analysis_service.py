from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.analysis.domain.enrichment import EnrichmentResult
from ehrlich.analysis.domain.repository import DatasetRepository


class AnalysisService:
    def __init__(self, repository: DatasetRepository) -> None:
        self._repository = repository

    async def explore(self, target: str, threshold: float = 1.0) -> Dataset:
        return await self._repository.load(target, threshold)

    async def analyze_substructures(self, dataset: Dataset) -> list[EnrichmentResult]:
        raise NotImplementedError

    async def compute_properties(self, dataset: Dataset) -> dict[str, float]:
        raise NotImplementedError
