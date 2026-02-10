from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from ehrlich.prediction.domain.trained_model import TrainedModel
from ehrlich.prediction.infrastructure.model_store import ModelStore


@pytest.fixture
def store(tmp_path: Path) -> ModelStore:
    return ModelStore(models_dir=tmp_path)


def _make_model(model_id: str = "test_model_001") -> TrainedModel:
    return TrainedModel(
        model_id=model_id,
        model_type="xgboost",
        target="Staphylococcus aureus",
        metrics={"auroc": 0.85, "f1": 0.78},
        feature_importance={"bit_42": 0.15, "bit_7": 0.12},
        is_trained=True,
        n_train=100,
        n_test=25,
        created_at="2026-02-10T12:00:00",
    )


class TestSaveLoad:
    @pytest.mark.asyncio
    async def test_roundtrip(self, store: ModelStore) -> None:
        original = _make_model()
        artifact = {"dummy": "model_data"}

        model_id = await store.save(original, artifact)
        assert model_id == "test_model_001"

        loaded_model, loaded_artifact = await store.load(model_id)
        assert loaded_model.model_id == original.model_id
        assert loaded_model.model_type == original.model_type
        assert loaded_model.target == original.target
        assert loaded_model.metrics == original.metrics
        assert loaded_model.is_trained is True
        assert loaded_model.n_train == 100
        assert loaded_model.n_test == 25
        assert loaded_artifact == artifact

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises(self, store: ModelStore) -> None:
        with pytest.raises(FileNotFoundError, match="Model not found"):
            await store.load("nonexistent_model")


class TestListModels:
    @pytest.mark.asyncio
    async def test_list_empty(self, store: ModelStore) -> None:
        models = await store.list_models()
        assert models == []

    @pytest.mark.asyncio
    async def test_list_multiple(self, store: ModelStore) -> None:
        for i in range(3):
            model = _make_model(f"model_{i:03d}")
            await store.save(model, {"data": i})

        models = await store.list_models()
        assert len(models) == 3
        assert [m.model_id for m in models] == ["model_000", "model_001", "model_002"]
