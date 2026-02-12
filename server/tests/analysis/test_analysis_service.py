import pytest

from ehrlich.analysis.application.analysis_service import AnalysisService
from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.analysis.domain.repository import DatasetRepository
from ehrlich.kernel.types import SMILES


class MockDatasetRepository(DatasetRepository):
    def __init__(self, dataset: Dataset | None = None) -> None:
        self._dataset = dataset

    async def load(self, target: str, threshold: float = 1.0) -> Dataset:
        if self._dataset:
            return self._dataset
        return Dataset(name="mock", target=target)

    async def search_bioactivity(
        self,
        target: str,
        assay_types: list[str] | None = None,
        threshold: float = 1.0,
    ) -> Dataset:
        return await self.load(target, threshold)

    async def list_targets(self) -> list[str]:
        return ["mock_target"]


def _make_dataset() -> Dataset:
    active_smiles = [
        SMILES("c1ccccc1O"),  # phenol (active)
        SMILES("c1ccccc1N"),  # aniline (active)
        SMILES("c1ccc(cc1)C(=O)O"),  # benzoic acid (active)
        SMILES("c1ccccc1CC(=O)O"),  # phenylacetic acid (active)
    ]
    inactive_smiles = [
        SMILES("CCCCCCCC"),  # octane (inactive)
        SMILES("CCCCCC"),  # hexane (inactive)
        SMILES("CC(C)CC"),  # isopentane (inactive)
        SMILES("CCCCCCCCCC"),  # decane (inactive)
    ]
    return Dataset(
        name="test",
        target="test_organism",
        smiles_list=active_smiles + inactive_smiles,
        activities=[1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    )


class TestAnalyzeSubstructures:
    @pytest.mark.asyncio
    async def test_finds_enrichment(self) -> None:
        dataset = _make_dataset()
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        results = await service.analyze_substructures(dataset)
        assert len(results) > 0
        benzene = next((r for r in results if r.substructure == "benzene"), None)
        assert benzene is not None
        assert benzene.active_count == 4  # all active have benzene
        assert benzene.odds_ratio > 1.0  # enriched in active

    @pytest.mark.asyncio
    async def test_empty_dataset(self) -> None:
        dataset = Dataset(name="empty", target="test")
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        results = await service.analyze_substructures(dataset)
        assert results == []

    @pytest.mark.asyncio
    async def test_all_active_returns_empty(self) -> None:
        dataset = Dataset(
            name="all_active",
            target="test",
            smiles_list=[SMILES("CCO"), SMILES("CCCO")],
            activities=[1.0, 1.0],
        )
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        results = await service.analyze_substructures(dataset)
        assert results == []


class TestComputeProperties:
    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        dataset = _make_dataset()
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        props = await service.compute_properties(dataset)
        assert props["total"] == 8
        assert props["active_count"] == 4
        assert props["inactive_count"] == 4
        assert "molecular_weight" in props
        mw = props["molecular_weight"]
        assert isinstance(mw, dict)
        assert mw["active_mean"] > 0

    @pytest.mark.asyncio
    async def test_empty_dataset(self) -> None:
        dataset = Dataset(name="empty", target="test")
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        props = await service.compute_properties(dataset)
        assert "error" in props


class TestExplore:
    @pytest.mark.asyncio
    async def test_delegates_to_repo(self) -> None:
        dataset = _make_dataset()
        repo = MockDatasetRepository(dataset)
        service = AnalysisService(repository=repo)
        result = await service.explore("test_organism")
        assert result.name == "test"
        assert result.size == 8
