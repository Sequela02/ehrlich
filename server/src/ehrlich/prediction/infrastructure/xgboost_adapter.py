from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)


class XGBoostAdapter:
    async def train(
        self,
        x_train: np.ndarray[Any, np.dtype[np.float64]],
        y_train: np.ndarray[Any, np.dtype[np.float64]],
        x_test: np.ndarray[Any, np.dtype[np.float64]],
        y_test: np.ndarray[Any, np.dtype[np.float64]],
    ) -> tuple[XGBClassifier, dict[str, float], dict[str, float]]:
        n_pos = int(y_train.sum())
        n_neg = len(y_train) - n_pos
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)

        metrics = self._compute_metrics(model, x_test, y_test)
        feature_importance = self._extract_feature_importance(model)

        return model, metrics, feature_importance

    async def predict(
        self,
        x: np.ndarray[Any, np.dtype[np.float64]],
        model: Any,
    ) -> list[float]:
        probas: np.ndarray[Any, np.dtype[np.float64]] = model.predict_proba(x)
        if probas.shape[1] == 1:
            return [float(p) for p in probas[:, 0]]
        return [float(p) for p in probas[:, 1]]

    @staticmethod
    def _compute_metrics(
        model: XGBClassifier,
        x_test: np.ndarray[Any, np.dtype[np.float64]],
        y_test: np.ndarray[Any, np.dtype[np.float64]],
    ) -> dict[str, float]:
        probas: np.ndarray[Any, np.dtype[np.float64]] = model.predict_proba(x_test)
        y_pred_proba = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]
        y_pred = (y_pred_proba >= 0.5).astype(int)

        try:
            auroc = float(roc_auc_score(y_test, y_pred_proba))
        except ValueError:
            auroc = 0.0

        try:
            auprc = float(average_precision_score(y_test, y_pred_proba))
        except ValueError:
            auprc = 0.0

        return {
            "auroc": auroc,
            "auprc": auprc,
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0.0)),
        }

    @staticmethod
    def _extract_feature_importance(model: XGBClassifier) -> dict[str, float]:
        importances: np.ndarray[Any, np.dtype[np.float64]] = model.feature_importances_
        top_indices = np.argsort(importances)[-20:][::-1]
        return {f"bit_{i}": float(importances[i]) for i in top_indices if importances[i] > 0}
