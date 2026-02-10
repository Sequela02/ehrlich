from __future__ import annotations

import numpy as np
import pytest

from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter


@pytest.fixture
def adapter() -> XGBoostAdapter:
    return XGBoostAdapter()


@pytest.fixture
def synthetic_data() -> tuple[
    np.ndarray[..., np.dtype[np.float64]],
    np.ndarray[..., np.dtype[np.float64]],
    np.ndarray[..., np.dtype[np.float64]],
    np.ndarray[..., np.dtype[np.float64]],
]:
    rng = np.random.RandomState(42)
    n_train, n_test, n_features = 80, 20, 64
    x_train = rng.randint(0, 2, size=(n_train, n_features)).astype(np.float64)
    x_test = rng.randint(0, 2, size=(n_test, n_features)).astype(np.float64)
    # Activity correlated with first few bits
    y_train = (x_train[:, :3].sum(axis=1) >= 2).astype(np.float64)
    y_test = (x_test[:, :3].sum(axis=1) >= 2).astype(np.float64)
    return x_train, y_train, x_test, y_test


class TestTrain:
    @pytest.mark.asyncio
    async def test_returns_model_and_metrics(
        self,
        adapter: XGBoostAdapter,
        synthetic_data: tuple[
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
        ],
    ) -> None:
        x_train, y_train, x_test, y_test = synthetic_data
        model, metrics, importance = await adapter.train(x_train, y_train, x_test, y_test)
        assert model is not None
        assert isinstance(metrics, dict)
        assert isinstance(importance, dict)

    @pytest.mark.asyncio
    async def test_metrics_have_expected_keys(
        self,
        adapter: XGBoostAdapter,
        synthetic_data: tuple[
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
        ],
    ) -> None:
        x_train, y_train, x_test, y_test = synthetic_data
        _, metrics, _ = await adapter.train(x_train, y_train, x_test, y_test)
        assert "auroc" in metrics
        assert "auprc" in metrics
        assert "accuracy" in metrics
        assert "f1" in metrics
        assert all(0.0 <= v <= 1.0 for v in metrics.values())

    @pytest.mark.asyncio
    async def test_feature_importance_populated(
        self,
        adapter: XGBoostAdapter,
        synthetic_data: tuple[
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
        ],
    ) -> None:
        x_train, y_train, x_test, y_test = synthetic_data
        _, _, importance = await adapter.train(x_train, y_train, x_test, y_test)
        assert len(importance) > 0
        assert all(v > 0 for v in importance.values())


class TestPredict:
    @pytest.mark.asyncio
    async def test_returns_probabilities(
        self,
        adapter: XGBoostAdapter,
        synthetic_data: tuple[
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
        ],
    ) -> None:
        x_train, y_train, x_test, y_test = synthetic_data
        model, _, _ = await adapter.train(x_train, y_train, x_test, y_test)
        probas = await adapter.predict(x_test, model)
        assert len(probas) == len(x_test)
        assert all(0.0 <= p <= 1.0 for p in probas)

    @pytest.mark.asyncio
    async def test_probabilities_are_floats(
        self,
        adapter: XGBoostAdapter,
        synthetic_data: tuple[
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
            np.ndarray[..., np.dtype[np.float64]],
        ],
    ) -> None:
        x_train, y_train, x_test, y_test = synthetic_data
        model, _, _ = await adapter.train(x_train, y_train, x_test, y_test)
        probas = await adapter.predict(x_test, model)
        assert all(isinstance(p, float) for p in probas)
