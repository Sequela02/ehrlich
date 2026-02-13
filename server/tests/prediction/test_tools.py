"""Tests for prediction tools (molecular + generic)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.kernel.types import SMILES

# -- Molecular tools -----------------------------------------------------------

_ACTIVE_SMILES = [
    SMILES("c1ccc(cc1)O"),
    SMILES("c1ccc(cc1)N"),
    SMILES("CC(=O)Oc1ccccc1C(=O)O"),
    SMILES("c1ccncc1"),
    SMILES("c1ccc2[nH]ccc2c1"),
    SMILES("OC(=O)c1ccccc1"),
    SMILES("c1ccc2c(c1)cccc2"),
]

_INACTIVE_SMILES = [
    SMILES("CCCCCC"),
    SMILES("CCCCCCCCCC"),
    SMILES("C1CCCCC1"),
    SMILES("CC(C)CC"),
    SMILES("CCOC(=O)CC"),
    SMILES("CCC(=O)C"),
    SMILES("CCCCCCCCC"),
]


def _mock_dataset() -> Dataset:
    return Dataset(
        name="ChEMBL Test",
        target="Staphylococcus aureus",
        smiles_list=_ACTIVE_SMILES + _INACTIVE_SMILES,
        activities=[1.0] * len(_ACTIVE_SMILES) + [0.0] * len(_INACTIVE_SMILES),
        metadata={"source": "test"},
    )


class TestTrainModel:
    @pytest.mark.asyncio
    async def test_returns_json_with_metrics(self) -> None:
        from ehrlich.prediction import tools

        with patch.object(tools._dataset_repo, "load", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_dataset()
            result = json.loads(await tools.train_model("Staphylococcus aureus"))
            assert "model_id" in result
            assert "metrics" in result
            assert "auroc" in result["metrics"]
            assert result["n_train"] > 0
            assert result["n_test"] > 0


class TestPredictCandidates:
    @pytest.mark.asyncio
    async def test_returns_ranked_predictions(self) -> None:
        from ehrlich.prediction import tools

        with patch.object(tools._dataset_repo, "load", new_callable=AsyncMock) as mock:
            mock.return_value = _mock_dataset()
            train_result = json.loads(await tools.train_model("Staphylococcus aureus"))
            model_id = train_result["model_id"]

        result = json.loads(
            await tools.predict_candidates(["c1ccccc1", "CCO", "c1ccncc1"], model_id)
        )
        assert result["count"] == 3
        assert result["predictions"][0]["rank"] == 1
        assert all(0.0 <= p["probability"] <= 1.0 for p in result["predictions"])
        assert result["model_id"] == model_id


class TestClusterCompounds:
    @pytest.mark.asyncio
    async def test_returns_clusters(self) -> None:
        from ehrlich.prediction import tools

        smiles = [str(s) for s in _ACTIVE_SMILES + _INACTIVE_SMILES]
        result = json.loads(await tools.cluster_compounds(smiles, n_clusters=20))
        assert result["n_clusters"] > 0
        total = sum(c["size"] for c in result["clusters"].values())
        assert total == len(smiles)


# -- Generic ML tools ---------------------------------------------------------


def _make_flat_features() -> tuple[list[str], list[float], list[float]]:
    """Generate synthetic flat feature data for generic tools."""
    rng = np.random.RandomState(42)
    n_samples, n_features = 20, 8
    x = rng.rand(n_samples, n_features)
    labels = (x[:, 0] + x[:, 1] > 1.0).astype(float).tolist()
    feature_names = [f"f{i}" for i in range(n_features)]
    feature_values = x.flatten().tolist()
    return feature_names, feature_values, labels


class TestTrainClassifier:
    @pytest.mark.asyncio
    async def test_returns_trained_model(self) -> None:
        from ehrlich.prediction import tools

        names, values, labels = _make_flat_features()
        result = json.loads(
            await tools.train_classifier(names, values, labels, target_name="test_target")
        )
        assert "model_id" in result
        assert "metrics" in result
        assert "auroc" in result["metrics"]
        assert result["n_train"] > 0

    @pytest.mark.asyncio
    async def test_empty_feature_names_error(self) -> None:
        from ehrlich.prediction import tools

        result = json.loads(await tools.train_classifier([], [1.0], [1.0]))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mismatched_dimensions_error(self) -> None:
        from ehrlich.prediction import tools

        result = json.loads(await tools.train_classifier(["a", "b"], [1.0, 2.0, 3.0], [1.0]))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_custom_identifiers(self) -> None:
        from ehrlich.prediction import tools

        names, values, labels = _make_flat_features()
        ids = ",".join(f"sample_{i}" for i in range(20))
        result = json.loads(await tools.train_classifier(names, values, labels, identifiers=ids))
        assert "model_id" in result


class TestPredictScores:
    @pytest.mark.asyncio
    async def test_returns_predictions(self) -> None:
        from ehrlich.prediction import tools

        names, values, labels = _make_flat_features()
        train_result = json.loads(
            await tools.train_classifier(names, values, labels, target_name="test")
        )
        model_id = train_result["model_id"]

        # Predict on 3 samples
        pred_values = values[: 3 * len(names)]
        result = json.loads(await tools.predict_scores(names, pred_values, model_id))
        assert result["count"] == 3
        assert result["predictions"][0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_model_not_found(self) -> None:
        from ehrlich.prediction import tools

        result = json.loads(await tools.predict_scores(["a"], [1.0], "nonexistent_model"))
        assert "error" in result


class TestClusterData:
    @pytest.mark.asyncio
    async def test_returns_clusters(self) -> None:
        from ehrlich.prediction import tools

        rng = np.random.RandomState(42)
        n_samples, n_features = 15, 4
        names = [f"f{i}" for i in range(n_features)]
        values = rng.rand(n_samples, n_features).flatten().tolist()
        ids = ",".join(f"item_{i}" for i in range(n_samples))
        result = json.loads(await tools.cluster_data(names, values, n_clusters=3, identifiers=ids))
        assert result["n_clusters"] == 3
        total = sum(c["size"] for c in result["clusters"].values())
        assert total == n_samples

    @pytest.mark.asyncio
    async def test_empty_feature_names_error(self) -> None:
        from ehrlich.prediction import tools

        result = json.loads(await tools.cluster_data([], [1.0]))
        assert "error" in result
