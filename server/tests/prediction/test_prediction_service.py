"""Tests for PredictionService (real implementations, no mocks)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ehrlich.prediction.application.prediction_service import PredictionService
from ehrlich.prediction.infrastructure.generic_adapters import (
    DistanceClusterer,
    RandomSplitter,
)
from ehrlich.prediction.infrastructure.model_store import ModelStore
from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter


def _make_synthetic_features() -> tuple[list[list[float]], list[float], list[str]]:
    """Generate synthetic binary features with a clear signal in the first 3 bits."""
    rng = np.random.RandomState(42)
    n_samples, n_features = 20, 64
    x = rng.randint(0, 2, size=(n_samples, n_features)).astype(float)
    # Labels correlated with first 3 features
    labels = (x[:, :3].sum(axis=1) >= 2).astype(float).tolist()
    features = x.tolist()
    identifiers = [f"sample_{i}" for i in range(n_samples)]
    return features, labels, identifiers


@pytest.fixture
def service(tmp_path: Path) -> PredictionService:
    return PredictionService(
        model_repo=ModelStore(models_dir=tmp_path),
        xgboost=XGBoostAdapter(),
    )


@pytest.fixture
def splitter() -> RandomSplitter:
    return RandomSplitter()


class TestTrain:
    @pytest.mark.asyncio
    async def test_train_returns_trained_model(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        result = await service.train(
            features,
            labels,
            ids,
            "synthetic_target",
            splitter=splitter,
            comparison_splitter=splitter,
        )
        assert result.is_trained is True
        assert result.model_type == "xgboost"
        assert result.target == "synthetic_target"
        assert result.n_train > 0
        assert result.n_test > 0
        assert "auroc" in result.metrics
        assert "f1" in result.metrics

    @pytest.mark.asyncio
    async def test_train_dataset_too_small(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features = [[1.0] * 10] * 3
        labels = [1.0, 0.0, 1.0]
        ids = ["a", "b", "c"]
        with pytest.raises(ValueError, match="too small"):
            await service.train(
                features,
                labels,
                ids,
                "test",
                splitter=splitter,
                comparison_splitter=splitter,
            )

    @pytest.mark.asyncio
    async def test_train_includes_random_metrics(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        result = await service.train(
            features,
            labels,
            ids,
            "synthetic_target",
            splitter=splitter,
            comparison_splitter=splitter,
        )
        assert "random_auroc" in result.metrics
        assert "random_auprc" in result.metrics
        assert "random_accuracy" in result.metrics
        assert "random_f1" in result.metrics
        assert all(0.0 <= result.metrics[k] <= 1.0 for k in ("random_auroc", "random_auprc"))

    @pytest.mark.asyncio
    async def test_train_includes_permutation_p_value(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        result = await service.train(
            features,
            labels,
            ids,
            "synthetic_target",
            splitter=splitter,
            comparison_splitter=splitter,
        )
        assert "permutation_p_value" in result.metrics
        assert 0.0 < result.metrics["permutation_p_value"] <= 1.0

    @pytest.mark.asyncio
    async def test_train_with_feature_names(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        names = [f"feat_{i}" for i in range(64)]
        result = await service.train(
            features,
            labels,
            ids,
            "named_target",
            splitter=splitter,
            comparison_splitter=splitter,
            feature_names=names,
        )
        # Feature importance keys should use custom names
        for key in result.feature_importance:
            assert key.startswith("feat_")


class TestPredict:
    @pytest.mark.asyncio
    async def test_predict_returns_ranked_results(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        trained = await service.train(
            features,
            labels,
            ids,
            "target",
            splitter=splitter,
            comparison_splitter=splitter,
        )
        # Predict on a subset
        pred_features = features[:3]
        pred_ids = ids[:3]
        results = await service.predict(pred_features, pred_ids, trained.model_id)
        assert len(results) == 3
        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3
        assert all(0.0 <= r.probability <= 1.0 for r in results)

    @pytest.mark.asyncio
    async def test_predict_empty_returns_empty(
        self, service: PredictionService, splitter: RandomSplitter
    ) -> None:
        features, labels, ids = _make_synthetic_features()
        trained = await service.train(
            features,
            labels,
            ids,
            "target",
            splitter=splitter,
            comparison_splitter=splitter,
        )
        results = await service.predict([], [], trained.model_id)
        assert results == []


class TestCluster:
    @pytest.mark.asyncio
    async def test_cluster_returns_groups(self) -> None:
        service = PredictionService(
            model_repo=ModelStore(models_dir=Path("/tmp/unused")),
            xgboost=XGBoostAdapter(),
        )
        rng = np.random.RandomState(42)
        features = rng.rand(14, 4).tolist()
        ids = [f"item_{i}" for i in range(14)]
        clusters = await service.cluster(features, ids, 3, DistanceClusterer())
        assert len(clusters) == 3
        all_items = [s for group in clusters.values() for s in group]
        assert len(all_items) == 14

    @pytest.mark.asyncio
    async def test_cluster_empty_returns_empty(self) -> None:
        service = PredictionService(
            model_repo=ModelStore(models_dir=Path("/tmp/unused")),
            xgboost=XGBoostAdapter(),
        )
        clusters = await service.cluster([], [], 5, DistanceClusterer())
        assert clusters == {}
