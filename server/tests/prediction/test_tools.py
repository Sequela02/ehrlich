from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.kernel.types import SMILES
from ehrlich.prediction.domain.prediction_result import PredictionResult
from ehrlich.prediction.domain.trained_model import TrainedModel


class TestTrainModel:
    @pytest.mark.asyncio
    async def test_returns_json_with_metrics(self) -> None:
        from ehrlich.prediction import tools

        mock_model = TrainedModel(
            model_id="xgboost_test_001",
            model_type="xgboost",
            target="Staphylococcus aureus",
            metrics={"auroc": 0.88, "f1": 0.75},
            feature_importance={"bit_1": 0.2, "bit_5": 0.15},
            is_trained=True,
            n_train=800,
            n_test=200,
            created_at="2026-02-10T12:00:00",
        )
        with patch.object(tools._service, "train", new_callable=AsyncMock) as mock:
            mock.return_value = mock_model
            result = json.loads(await tools.train_model("Staphylococcus aureus"))
            assert result["model_id"] == "xgboost_test_001"
            assert result["metrics"]["auroc"] == 0.88
            assert result["n_train"] == 800
            assert result["n_test"] == 200


class TestPredictCandidates:
    @pytest.mark.asyncio
    async def test_returns_ranked_predictions(self) -> None:
        from ehrlich.prediction import tools

        mock_results = [
            PredictionResult(
                smiles=SMILES("c1ccccc1"), probability=0.95, rank=1, model_type="xgboost"
            ),
            PredictionResult(smiles=SMILES("CCO"), probability=0.30, rank=2, model_type="xgboost"),
        ]
        with patch.object(tools._service, "predict", new_callable=AsyncMock) as mock:
            mock.return_value = mock_results
            result = json.loads(await tools.predict_candidates(["c1ccccc1", "CCO"], "model_001"))
            assert result["count"] == 2
            assert result["predictions"][0]["rank"] == 1
            assert result["predictions"][0]["probability"] == 0.95
            assert result["model_id"] == "model_001"


class TestClusterCompounds:
    @pytest.mark.asyncio
    async def test_returns_clusters(self) -> None:
        from ehrlich.prediction import tools

        mock_clusters = {
            0: [SMILES("c1ccccc1"), SMILES("c1ccc(cc1)O")],
            1: [SMILES("CCCCCC")],
        }
        with patch.object(tools._service, "cluster", new_callable=AsyncMock) as mock:
            mock.return_value = mock_clusters
            result = json.loads(
                await tools.cluster_compounds(["c1ccccc1", "c1ccc(cc1)O", "CCCCCC"])
            )
            assert result["n_clusters"] == 2
            assert result["clusters"]["0"]["size"] == 2
            assert result["clusters"]["1"]["size"] == 1
