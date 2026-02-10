from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from ehrlich.prediction.domain.repository import ModelRepository
from ehrlich.prediction.domain.trained_model import TrainedModel

_MODELS_DIR = Path(__file__).resolve().parents[5] / "data" / "models"


class ModelStore(ModelRepository):
    def __init__(self, models_dir: Path | None = None) -> None:
        self._dir = models_dir or _MODELS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    async def save(self, model: TrainedModel, artifact: object) -> str:
        model_dir = self._dir / model.model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "model_id": model.model_id,
            "model_type": model.model_type,
            "target": model.target,
            "metrics": model.metrics,
            "feature_importance": model.feature_importance,
            "is_trained": model.is_trained,
            "n_train": model.n_train,
            "n_test": model.n_test,
            "created_at": model.created_at,
        }
        (model_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
        joblib.dump(artifact, model_dir / "model.joblib")

        return model.model_id

    async def load(self, model_id: str) -> tuple[TrainedModel, Any]:
        model_dir = self._dir / model_id
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_id}")

        meta = json.loads((model_dir / "metadata.json").read_text())
        trained_model = self._meta_to_model(meta)
        artifact: Any = joblib.load(model_dir / "model.joblib")

        return trained_model, artifact

    async def list_models(self) -> list[TrainedModel]:
        models: list[TrainedModel] = []
        if not self._dir.exists():
            return models
        for model_dir in sorted(self._dir.iterdir()):
            meta_path = model_dir / "metadata.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            models.append(self._meta_to_model(meta))
        return models

    @staticmethod
    def _meta_to_model(meta: dict[str, Any]) -> TrainedModel:
        return TrainedModel(
            model_id=meta["model_id"],
            model_type=meta["model_type"],
            target=meta["target"],
            metrics=meta.get("metrics", {}),
            feature_importance=meta.get("feature_importance", {}),
            is_trained=meta.get("is_trained", False),
            n_train=meta.get("n_train", 0),
            n_test=meta.get("n_test", 0),
            created_at=meta.get("created_at", ""),
        )
