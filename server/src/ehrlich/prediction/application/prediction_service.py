from __future__ import annotations

import datetime
import logging
import uuid
from typing import TYPE_CHECKING

import numpy as np

from ehrlich.prediction.domain.prediction_result import PredictionResult
from ehrlich.prediction.domain.trained_model import TrainedModel

if TYPE_CHECKING:
    from ehrlich.prediction.domain.ports import Clusterer, DataSplitter
    from ehrlich.prediction.domain.repository import ModelRepository
    from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(
        self,
        model_repo: ModelRepository,
        xgboost: XGBoostAdapter,
    ) -> None:
        self._model_repo = model_repo
        self._xgboost = xgboost

    async def train(
        self,
        features: list[list[float]],
        labels: list[float],
        identifiers: list[str],
        target_name: str,
        splitter: DataSplitter,
        comparison_splitter: DataSplitter,
        feature_names: list[str] | None = None,
    ) -> TrainedModel:
        if len(features) < 10:
            raise ValueError(f"Dataset too small for training: {len(features)} samples")

        x = np.array(features, dtype=np.float64)
        y = np.array(labels, dtype=np.float64)

        train_idx, test_idx = splitter.split(features, labels, identifiers)
        x_train, y_train = x[train_idx], y[train_idx]
        x_test, y_test = x[test_idx], y[test_idx]

        model_artifact, metrics, feature_importance = await self._xgboost.train(
            x_train, y_train, x_test, y_test, feature_names=feature_names
        )

        # Comparison split for generalizability assessment
        comp_train_idx, comp_test_idx = comparison_splitter.split(features, labels, identifiers)
        _, random_metrics, _ = await self._xgboost.train(
            x[comp_train_idx],
            y[comp_train_idx],
            x[comp_test_idx],
            y[comp_test_idx],
        )
        metrics["random_auroc"] = random_metrics["auroc"]
        metrics["random_auprc"] = random_metrics["auprc"]
        metrics["random_accuracy"] = random_metrics["accuracy"]
        metrics["random_f1"] = random_metrics["f1"]

        # Permutation significance (Y-scrambling)
        metrics["permutation_p_value"] = self._xgboost.permutation_test(
            x_train, y_train, x_test, y_test, metrics["auroc"]
        )

        safe_target = target_name.lower().replace(" ", "_") if target_name else "generic"
        model_id = f"xgboost_{safe_target}_{uuid.uuid4().hex[:8]}"
        trained_model = TrainedModel(
            model_id=model_id,
            model_type="xgboost",
            target=target_name,
            metrics=metrics,
            feature_importance=feature_importance,
            is_trained=True,
            n_train=len(y_train),
            n_test=len(y_test),
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )

        await self._model_repo.save(trained_model, model_artifact)
        return trained_model

    async def predict(
        self,
        features: list[list[float]],
        identifiers: list[str],
        model_id: str,
    ) -> list[PredictionResult]:
        trained_model, artifact = await self._model_repo.load(model_id)

        if not features:
            return []

        x = np.array(features, dtype=np.float64)
        probas = await self._xgboost.predict(x, artifact)

        results = [
            PredictionResult(
                identifier=identifier,
                probability=prob,
                model_type=trained_model.model_type,
            )
            for identifier, prob in zip(identifiers, probas, strict=True)
        ]
        results.sort(key=lambda r: r.probability, reverse=True)

        return [
            PredictionResult(
                identifier=r.identifier,
                probability=r.probability,
                rank=i + 1,
                model_type=r.model_type,
            )
            for i, r in enumerate(results)
        ]

    async def cluster(
        self,
        features: list[list[float]],
        identifiers: list[str],
        n_clusters: int,
        clusterer: Clusterer,
    ) -> dict[int, list[str]]:
        if not features:
            return {}
        return clusterer.cluster(features, identifiers, n_clusters)
