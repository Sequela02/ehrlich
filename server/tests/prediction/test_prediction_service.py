from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES
from ehrlich.prediction.application.prediction_service import PredictionService
from ehrlich.prediction.infrastructure.model_store import ModelStore
from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter

# Diverse molecules for realistic fingerprints
_ACTIVE_SMILES = [
    SMILES("c1ccc(cc1)O"),  # phenol
    SMILES("c1ccc(cc1)N"),  # aniline
    SMILES("CC(=O)Oc1ccccc1C(=O)O"),  # aspirin
    SMILES("c1ccncc1"),  # pyridine
    SMILES("c1ccc2[nH]ccc2c1"),  # indole
    SMILES("OC(=O)c1ccccc1"),  # benzoic acid
    SMILES("c1ccc2c(c1)cccc2"),  # naphthalene
]

_INACTIVE_SMILES = [
    SMILES("CCCCCC"),  # hexane
    SMILES("CCCCCCCCCC"),  # decane
    SMILES("C1CCCCC1"),  # cyclohexane
    SMILES("CC(C)CC"),  # isopentane
    SMILES("CCOC(=O)CC"),  # ethyl propanoate
    SMILES("CCC(=O)C"),  # butanone
    SMILES("CCCCCCCCC"),  # nonane
]


def _mock_dataset() -> Dataset:
    return Dataset(
        name="ChEMBL Test",
        target="Staphylococcus aureus",
        smiles_list=_ACTIVE_SMILES + _INACTIVE_SMILES,
        activities=[1.0] * len(_ACTIVE_SMILES) + [0.0] * len(_INACTIVE_SMILES),
        metadata={"source": "test"},
    )


@pytest.fixture
def service(tmp_path: object) -> PredictionService:
    dataset_repo = AsyncMock()
    dataset_repo.load.return_value = _mock_dataset()
    return PredictionService(
        model_repo=ModelStore(models_dir=tmp_path),  # type: ignore[arg-type]
        dataset_repo=dataset_repo,
        rdkit=RDKitAdapter(),
        xgboost=XGBoostAdapter(),
    )


class TestTrain:
    @pytest.mark.asyncio
    async def test_train_returns_trained_model(self, service: PredictionService) -> None:
        result = await service.train("Staphylococcus aureus")
        assert result.is_trained is True
        assert result.model_type == "xgboost"
        assert result.target == "Staphylococcus aureus"
        assert result.n_train > 0
        assert result.n_test > 0
        assert "auroc" in result.metrics
        assert "f1" in result.metrics

    @pytest.mark.asyncio
    async def test_train_dataset_too_small(self, service: PredictionService) -> None:
        service._dataset_repo.load.return_value = Dataset(  # type: ignore[union-attr]
            name="Tiny",
            target="Test",
            smiles_list=[SMILES("CCO")] * 3,
            activities=[1.0, 0.0, 1.0],
        )
        with pytest.raises(ValueError, match="too small"):
            await service.train("Test")

    @pytest.mark.asyncio
    async def test_train_includes_random_metrics(self, service: PredictionService) -> None:
        result = await service.train("Staphylococcus aureus")
        assert "random_auroc" in result.metrics
        assert "random_auprc" in result.metrics
        assert "random_accuracy" in result.metrics
        assert "random_f1" in result.metrics
        assert all(0.0 <= result.metrics[k] <= 1.0 for k in ("random_auroc", "random_auprc"))

    @pytest.mark.asyncio
    async def test_train_includes_permutation_p_value(self, service: PredictionService) -> None:
        result = await service.train("Staphylococcus aureus")
        assert "permutation_p_value" in result.metrics
        assert 0.0 < result.metrics["permutation_p_value"] <= 1.0


class TestPredict:
    @pytest.mark.asyncio
    async def test_predict_returns_ranked_results(self, service: PredictionService) -> None:
        trained = await service.train("Staphylococcus aureus")
        candidates = [SMILES("c1ccccc1"), SMILES("CCO"), SMILES("c1ccncc1")]
        results = await service.predict(candidates, trained.model_id)
        assert len(results) == 3
        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3
        assert all(0.0 <= r.probability <= 1.0 for r in results)

    @pytest.mark.asyncio
    async def test_predict_empty_returns_empty(self, service: PredictionService) -> None:
        trained = await service.train("Staphylococcus aureus")
        results = await service.predict([], trained.model_id)
        assert results == []


class TestCluster:
    @pytest.mark.asyncio
    async def test_cluster_returns_groups(self, service: PredictionService) -> None:
        smiles = _ACTIVE_SMILES + _INACTIVE_SMILES
        clusters = await service.cluster(smiles, n_clusters=20)
        assert len(clusters) > 0
        all_smiles_in_clusters = [s for group in clusters.values() for s in group]
        assert len(all_smiles_in_clusters) == len(smiles)

    @pytest.mark.asyncio
    async def test_cluster_empty_returns_empty(self, service: PredictionService) -> None:
        clusters = await service.cluster([], n_clusters=5)
        assert clusters == {}


class TestScaffoldSplit:
    def test_split_preserves_total(self) -> None:
        import numpy as np

        x = np.random.RandomState(42).rand(20, 10)
        y = np.array([1.0] * 10 + [0.0] * 10)
        scaffolds = [f"scaffold_{i % 5}" for i in range(20)]
        x_tr, y_tr, x_te, y_te = PredictionService._scaffold_split(x, y, scaffolds)
        assert len(y_tr) + len(y_te) == 20

    def test_fallback_on_single_scaffold(self) -> None:
        import numpy as np

        x = np.random.RandomState(42).rand(20, 10)
        y = np.array([1.0] * 10 + [0.0] * 10)
        scaffolds = ["same"] * 20
        x_tr, y_tr, x_te, y_te = PredictionService._scaffold_split(x, y, scaffolds)
        assert len(y_tr) + len(y_te) == 20
        assert len(y_te) > 0
