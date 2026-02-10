from __future__ import annotations

import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any

import numpy as np

from ehrlich.prediction.domain.prediction_result import PredictionResult
from ehrlich.prediction.domain.trained_model import TrainedModel

if TYPE_CHECKING:
    from ehrlich.analysis.domain.repository import DatasetRepository
    from ehrlich.chemistry.domain.fingerprint import Fingerprint
    from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
    from ehrlich.kernel.types import SMILES
    from ehrlich.prediction.domain.repository import ModelRepository
    from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(
        self,
        model_repo: ModelRepository,
        dataset_repo: DatasetRepository,
        rdkit: RDKitAdapter,
        xgboost: XGBoostAdapter,
    ) -> None:
        self._model_repo = model_repo
        self._dataset_repo = dataset_repo
        self._rdkit = rdkit
        self._xgboost = xgboost

    async def train(self, target: str, model_type: str = "xgboost") -> TrainedModel:
        dataset = await self._dataset_repo.load(target)
        if dataset.size < 10:
            raise ValueError(f"Dataset too small for training: {dataset.size} compounds")

        fingerprints: list[list[int]] = []
        scaffolds: list[str] = []
        valid_activities: list[float] = []

        for i, smiles in enumerate(dataset.smiles_list):
            try:
                fp = self._rdkit.compute_fingerprint(smiles)
                dense = self._fingerprint_to_dense(fp)
                scaffold = self._safe_murcko_scaffold(smiles)
                fingerprints.append(dense)
                scaffolds.append(scaffold)
                valid_activities.append(dataset.activities[i])
            except Exception:
                continue

        if len(fingerprints) < 10:
            raise ValueError(f"Too few valid fingerprints for training: {len(fingerprints)}")

        x = np.array(fingerprints, dtype=np.float64)
        y = np.array(valid_activities, dtype=np.float64)

        x_train, y_train, x_test, y_test = self._scaffold_split(x, y, scaffolds)

        model_artifact, metrics, feature_importance = await self._xgboost.train(
            x_train, y_train, x_test, y_test
        )

        model_id = f"xgboost_{target.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        trained_model = TrainedModel(
            model_id=model_id,
            model_type=model_type,
            target=target,
            metrics=metrics,
            feature_importance=feature_importance,
            is_trained=True,
            n_train=len(y_train),
            n_test=len(y_test),
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )

        await self._model_repo.save(trained_model, model_artifact)
        return trained_model

    async def predict(self, smiles_list: list[SMILES], model_id: str) -> list[PredictionResult]:
        trained_model, artifact = await self._model_repo.load(model_id)

        fingerprints: list[list[int]] = []
        valid_smiles: list[SMILES] = []
        for smiles in smiles_list:
            try:
                fp = self._rdkit.compute_fingerprint(smiles)
                dense = self._fingerprint_to_dense(fp)
                fingerprints.append(dense)
                valid_smiles.append(smiles)
            except Exception:
                continue

        if not fingerprints:
            return []

        x = np.array(fingerprints, dtype=np.float64)
        probas = await self._xgboost.predict(x, artifact)

        results = [
            PredictionResult(
                smiles=smiles,
                probability=prob,
                model_type=trained_model.model_type,
            )
            for smiles, prob in zip(valid_smiles, probas, strict=True)
        ]
        results.sort(key=lambda r: r.probability, reverse=True)

        return [
            PredictionResult(
                smiles=r.smiles,
                probability=r.probability,
                rank=i + 1,
                model_type=r.model_type,
            )
            for i, r in enumerate(results)
        ]

    async def cluster(
        self, smiles_list: list[SMILES], n_clusters: int = 5
    ) -> dict[int, list[SMILES]]:
        fingerprints: list[Fingerprint] = []
        valid_smiles: list[SMILES] = []
        for smiles in smiles_list:
            try:
                fp = self._rdkit.compute_fingerprint(smiles)
                fingerprints.append(fp)
                valid_smiles.append(smiles)
            except Exception:
                continue

        if not fingerprints:
            return {}

        clusters_indices = self._rdkit.butina_cluster(fingerprints, cutoff=0.35)

        result: dict[int, list[SMILES]] = {}
        for cluster_id, indices in enumerate(clusters_indices):
            if cluster_id >= n_clusters:
                break
            result[cluster_id] = [valid_smiles[i] for i in indices]
        return result

    async def ensemble(self, smiles_list: list[SMILES]) -> list[PredictionResult]:
        models = await self._model_repo.list_models()
        trained = [m for m in models if m.is_trained]
        if not trained:
            raise ValueError("No trained models available for ensemble")

        all_probas: dict[SMILES, list[float]] = {s: [] for s in smiles_list}

        for model in trained:
            predictions = await self.predict(smiles_list, model.model_id)
            for pred in predictions:
                all_probas[pred.smiles].append(pred.probability)

        results: list[PredictionResult] = []
        for smiles in smiles_list:
            probas = all_probas.get(smiles, [])
            if probas:
                avg_prob = sum(probas) / len(probas)
                results.append(
                    PredictionResult(
                        smiles=smiles,
                        probability=avg_prob,
                        model_type="ensemble",
                    )
                )

        results.sort(key=lambda r: r.probability, reverse=True)
        return [
            PredictionResult(
                smiles=r.smiles,
                probability=r.probability,
                rank=i + 1,
                model_type=r.model_type,
            )
            for i, r in enumerate(results)
        ]

    def _safe_murcko_scaffold(self, smiles: SMILES) -> str:
        try:
            return self._rdkit.murcko_scaffold(smiles)
        except Exception:
            return "unknown"

    @staticmethod
    def _fingerprint_to_dense(fp: Fingerprint) -> list[int]:
        dense = [0] * fp.n_bits
        for bit in fp.bits:
            dense[bit] = 1
        return dense

    @staticmethod
    def _scaffold_split(
        x: np.ndarray[Any, np.dtype[np.float64]],
        y: np.ndarray[Any, np.dtype[np.float64]],
        scaffolds: list[str],
        test_size: float = 0.2,
    ) -> tuple[
        np.ndarray[Any, np.dtype[np.float64]],
        np.ndarray[Any, np.dtype[np.float64]],
        np.ndarray[Any, np.dtype[np.float64]],
        np.ndarray[Any, np.dtype[np.float64]],
    ]:
        unique_scaffolds = list(set(scaffolds))
        rng = np.random.RandomState(42)
        rng.shuffle(unique_scaffolds)

        n_test_scaffolds = max(1, int(len(unique_scaffolds) * test_size))
        test_scaffolds = set(unique_scaffolds[:n_test_scaffolds])

        train_idx = [i for i, s in enumerate(scaffolds) if s not in test_scaffolds]
        test_idx = [i for i, s in enumerate(scaffolds) if s in test_scaffolds]

        if not test_idx or not train_idx:
            all_idx = np.arange(len(y))
            rng.shuffle(all_idx)
            split = int(len(all_idx) * (1 - test_size))
            train_idx = all_idx[:split].tolist()
            test_idx = all_idx[split:].tolist()

        return x[train_idx], y[train_idx], x[test_idx], y[test_idx]
