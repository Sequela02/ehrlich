from __future__ import annotations

import json

from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader
from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES
from ehrlich.prediction.application.prediction_service import PredictionService
from ehrlich.prediction.infrastructure.generic_adapters import (
    DistanceClusterer,
    RandomSplitter,
)
from ehrlich.prediction.infrastructure.model_store import ModelStore
from ehrlich.prediction.infrastructure.molecular_adapters import (
    MolecularClusterer,
    MolecularFeatureExtractor,
    ScaffoldSplitter,
)
from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter

_rdkit: RDKitAdapter = RDKitAdapter()
_xgboost = XGBoostAdapter()
_model_store = ModelStore()
_dataset_repo = ChEMBLLoader()

_mol_features = MolecularFeatureExtractor(_rdkit)
_scaffold_splitter = ScaffoldSplitter(_rdkit)
_mol_clusterer = MolecularClusterer(_rdkit)
_random_splitter = RandomSplitter()
_distance_clusterer = DistanceClusterer()

_service = PredictionService(
    model_repo=_model_store,
    xgboost=_xgboost,
)


# ---------------------------------------------------------------------------
# Molecular tools (domain-specific, tagged "prediction")
# ---------------------------------------------------------------------------


async def train_model(target: str, model_type: str = "xgboost") -> str:
    """Train an ML model for bioactivity prediction.

    Args:
        target: Target organism or protein name (e.g. "Staphylococcus aureus")
        model_type: ML algorithm to use (default: xgboost)
    """
    try:
        dataset = await _dataset_repo.load(target)
        if dataset.size < 10:
            raise ValueError(f"Dataset too small for training: {dataset.size} compounds")

        smiles_strs = [str(s) for s in dataset.smiles_list]
        features, valid_ids = _mol_features.extract(smiles_strs)

        # Match labels to valid identifiers preserving order
        smiles_to_idx = {str(s): i for i, s in enumerate(dataset.smiles_list)}
        labels = [dataset.activities[smiles_to_idx[vid]] for vid in valid_ids]

        trained = await _service.train(
            features,
            labels,
            valid_ids,
            target,
            splitter=_scaffold_splitter,
            comparison_splitter=_random_splitter,
        )
    except ValueError as e:
        return json.dumps({"error": str(e), "target": target, "model_type": model_type})
    return json.dumps(
        {
            "model_id": trained.model_id,
            "model_type": trained.model_type,
            "target": trained.target,
            "metrics": trained.metrics,
            "feature_importance": dict(list(trained.feature_importance.items())[:10]),
            "n_train": trained.n_train,
            "n_test": trained.n_test,
            "created_at": trained.created_at,
        }
    )


async def predict_candidates(smiles_list: list[str], model_id: str) -> str:
    """Predict bioactivity for a list of SMILES.

    Args:
        smiles_list: List of SMILES strings to score
        model_id: ID of trained model to use
    """
    typed_smiles = [SMILES(s) for s in smiles_list]
    smiles_strs = [str(s) for s in typed_smiles]
    features, valid_ids = _mol_features.extract(smiles_strs)
    try:
        results = await _service.predict(features, valid_ids, model_id)
    except (FileNotFoundError, KeyError) as e:
        return json.dumps({"error": f"Model not found: {model_id}", "detail": str(e)})
    return json.dumps(
        {
            "model_id": model_id,
            "count": len(results),
            "predictions": [
                {
                    "rank": r.rank,
                    "smiles": r.identifier,
                    "probability": round(r.probability, 4),
                    "model_type": r.model_type,
                }
                for r in results
            ],
        }
    )


async def cluster_compounds(smiles_list: list[str], n_clusters: int = 5) -> str:
    """Cluster compounds by structural similarity using Butina clustering.

    Args:
        smiles_list: List of SMILES strings to cluster
        n_clusters: Maximum number of clusters
    """
    smiles_strs = [str(SMILES(s)) for s in smiles_list]
    features, valid_ids = _mol_features.extract(smiles_strs)
    clusters = await _service.cluster(features, valid_ids, n_clusters, _mol_clusterer)
    return json.dumps(
        {
            "n_clusters": len(clusters),
            "clusters": {
                str(k): {
                    "size": len(v),
                    "smiles": v,
                }
                for k, v in clusters.items()
            },
        }
    )


# ---------------------------------------------------------------------------
# Generic ML tools (domain-agnostic, tagged "ml")
# ---------------------------------------------------------------------------


async def train_classifier(
    feature_names: list[str],
    feature_values: list[float],
    labels: list[float],
    target_name: str = "",
    identifiers: str = "",
    model_type: str = "xgboost",
) -> str:
    """Train a binary classifier on tabular feature data.

    Accepts a flat feature matrix (row-major) with labels for binary
    classification. Returns model metrics including AUROC, F1, and
    permutation p-value.

    Args:
        feature_names: Column names for the feature matrix
        feature_values: Flattened row-major feature matrix (length = n_samples * n_features)
        labels: Binary labels (0.0 or 1.0) for each sample
        target_name: Optional name for the prediction target
        identifiers: Comma-separated sample identifiers (auto-generated if empty)
        model_type: ML algorithm (default: xgboost)
    """
    n_features = len(feature_names)
    if n_features == 0:
        return json.dumps({"error": "feature_names cannot be empty"})

    n_samples = len(labels)
    if n_samples == 0:
        return json.dumps({"error": "labels cannot be empty"})

    expected_len = n_samples * n_features
    if len(feature_values) != expected_len:
        return json.dumps(
            {
                "error": f"feature_values length {len(feature_values)} != "
                f"n_samples ({n_samples}) * n_features ({n_features}) = {expected_len}"
            }
        )

    features = [feature_values[i * n_features : (i + 1) * n_features] for i in range(n_samples)]
    ids = (
        [s.strip() for s in identifiers.split(",")]
        if identifiers
        else [f"sample_{i}" for i in range(n_samples)]
    )

    try:
        trained = await _service.train(
            features,
            labels,
            ids,
            target_name,
            splitter=_random_splitter,
            comparison_splitter=_random_splitter,
            feature_names=feature_names,
        )
    except ValueError as e:
        return json.dumps({"error": str(e), "target_name": target_name, "model_type": model_type})

    return json.dumps(
        {
            "model_id": trained.model_id,
            "model_type": trained.model_type,
            "target": trained.target,
            "metrics": trained.metrics,
            "feature_importance": dict(list(trained.feature_importance.items())[:10]),
            "n_train": trained.n_train,
            "n_test": trained.n_test,
            "created_at": trained.created_at,
        }
    )


async def predict_scores(
    feature_names: list[str],
    feature_values: list[float],
    model_id: str,
    identifiers: str = "",
) -> str:
    """Score samples using a trained classifier.

    Accepts a flat feature matrix and returns ranked predictions with
    probabilities.

    Args:
        feature_names: Column names (must match training features)
        feature_values: Flattened row-major feature matrix
        model_id: ID of the trained model
        identifiers: Comma-separated sample identifiers (auto-generated if empty)
    """
    n_features = len(feature_names)
    if n_features == 0:
        return json.dumps({"error": "feature_names cannot be empty"})

    n_samples = len(feature_values) // n_features if n_features else 0
    if n_features and len(feature_values) % n_features != 0:
        return json.dumps(
            {
                "error": f"feature_values length {len(feature_values)} is not "
                f"divisible by n_features ({n_features})"
            }
        )

    features = [feature_values[i * n_features : (i + 1) * n_features] for i in range(n_samples)]
    ids = (
        [s.strip() for s in identifiers.split(",")]
        if identifiers
        else [f"sample_{i}" for i in range(n_samples)]
    )

    try:
        results = await _service.predict(features, ids, model_id)
    except (FileNotFoundError, KeyError) as e:
        return json.dumps({"error": f"Model not found: {model_id}", "detail": str(e)})

    return json.dumps(
        {
            "model_id": model_id,
            "count": len(results),
            "predictions": [
                {
                    "rank": r.rank,
                    "identifier": r.identifier,
                    "probability": round(r.probability, 4),
                    "model_type": r.model_type,
                }
                for r in results
            ],
        }
    )


async def cluster_data(
    feature_names: list[str],
    feature_values: list[float],
    n_clusters: int = 5,
    identifiers: str = "",
) -> str:
    """Cluster samples by feature similarity using hierarchical clustering.

    Accepts a flat feature matrix and groups samples into clusters using
    Ward linkage.

    Args:
        feature_names: Column names for the feature matrix
        feature_values: Flattened row-major feature matrix
        n_clusters: Number of clusters to create
        identifiers: Comma-separated sample identifiers (auto-generated if empty)
    """
    n_features = len(feature_names)
    if n_features == 0:
        return json.dumps({"error": "feature_names cannot be empty"})

    n_samples = len(feature_values) // n_features if n_features else 0
    if n_features and len(feature_values) % n_features != 0:
        return json.dumps(
            {
                "error": f"feature_values length {len(feature_values)} is not "
                f"divisible by n_features ({n_features})"
            }
        )

    features = [feature_values[i * n_features : (i + 1) * n_features] for i in range(n_samples)]
    ids = (
        [s.strip() for s in identifiers.split(",")]
        if identifiers
        else [f"sample_{i}" for i in range(n_samples)]
    )

    clusters = await _service.cluster(features, ids, n_clusters, _distance_clusterer)
    return json.dumps(
        {
            "n_clusters": len(clusters),
            "clusters": {
                str(k): {
                    "size": len(v),
                    "identifiers": v,
                }
                for k, v in clusters.items()
            },
        }
    )
