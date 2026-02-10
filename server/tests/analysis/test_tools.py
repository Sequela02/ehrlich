import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.kernel.types import SMILES


def _mock_dataset() -> Dataset:
    return Dataset(
        name="ChEMBL Test",
        target="Staphylococcus aureus",
        smiles_list=[
            SMILES("c1ccccc1O"),
            SMILES("c1ccccc1N"),
            SMILES("CCCCCC"),
            SMILES("CCCCCCCC"),
        ],
        activities=[1.0, 1.0, 0.0, 0.0],
        metadata={"source": "ChEMBL", "size": "4"},
    )


class TestExploreDataset:
    @pytest.mark.asyncio
    async def test_returns_stats(self) -> None:
        from ehrlich.analysis import tools

        with patch.object(tools._service, "explore", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_dataset()
            result = json.loads(await tools.explore_dataset("Staphylococcus aureus"))
            assert result["size"] == 4
            assert result["active_count"] == 2
            assert result["active_ratio"] == 0.5


class TestAnalyzeSubstructures:
    @pytest.mark.asyncio
    async def test_returns_enrichments(self) -> None:
        from ehrlich.analysis import tools

        dataset = _mock_dataset()
        with (
            patch.object(tools._service, "explore", new_callable=AsyncMock) as mock_explore,
            patch.object(
                tools._service, "analyze_substructures", new_callable=AsyncMock
            ) as mock_analyze,
        ):
            from ehrlich.analysis.domain.enrichment import EnrichmentResult

            mock_explore.return_value = dataset
            mock_analyze.return_value = [
                EnrichmentResult(
                    substructure="benzene",
                    p_value=0.01,
                    odds_ratio=5.0,
                    active_count=2,
                    total_count=2,
                    description="Benzene ring",
                )
            ]
            result = json.loads(await tools.analyze_substructures("Staphylococcus aureus"))
            assert result["significant_count"] == 1
            assert len(result["enrichments"]) == 1
            assert result["enrichments"][0]["substructure"] == "benzene"


class TestComputeProperties:
    @pytest.mark.asyncio
    async def test_returns_properties(self) -> None:
        from ehrlich.analysis import tools

        dataset = _mock_dataset()
        with (
            patch.object(tools._service, "explore", new_callable=AsyncMock) as mock_explore,
            patch.object(
                tools._service, "compute_properties", new_callable=AsyncMock
            ) as mock_props,
        ):
            mock_explore.return_value = dataset
            mock_props.return_value = {
                "total": 4,
                "active_count": 2,
                "inactive_count": 2,
                "molecular_weight": {
                    "active_mean": 100.0,
                    "active_std": 10.0,
                    "inactive_mean": 90.0,
                    "inactive_std": 5.0,
                },
            }
            result = json.loads(await tools.compute_properties("Staphylococcus aureus"))
            assert result["total"] == 4
            assert "molecular_weight" in result
