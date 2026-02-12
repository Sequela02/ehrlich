from __future__ import annotations

import json

from ehrlich.analysis.infrastructure.chembl_loader import ChEMBLLoader
from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES
from ehrlich.prediction.application.prediction_service import PredictionService
from ehrlich.prediction.infrastructure.model_store import ModelStore
from ehrlich.prediction.infrastructure.xgboost_adapter import XGBoostAdapter

_rdkit: RDKitAdapter = RDKitAdapter()
_xgboost = XGBoostAdapter()
_model_store = ModelStore()
_dataset_repo = ChEMBLLoader()
_service = PredictionService(
    model_repo=_model_store,
    dataset_repo=_dataset_repo,
    rdkit=_rdkit,
    xgboost=_xgboost,
)


async def train_model(target: str, model_type: str = "xgboost") -> str:
    """Train an ML model for bioactivity prediction."""
    try:
        trained = await _service.train(target, model_type)
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
    """Predict bioactivity for a list of SMILES."""
    typed_smiles = [SMILES(s) for s in smiles_list]
    try:
        results = await _service.predict(typed_smiles, model_id)
    except (FileNotFoundError, KeyError) as e:
        return json.dumps({"error": f"Model not found: {model_id}", "detail": str(e)})
    return json.dumps(
        {
            "model_id": model_id,
            "count": len(results),
            "predictions": [
                {
                    "rank": r.rank,
                    "smiles": str(r.smiles),
                    "probability": round(r.probability, 4),
                    "model_type": r.model_type,
                }
                for r in results
            ],
        }
    )


async def cluster_compounds(smiles_list: list[str], n_clusters: int = 5) -> str:
    """Cluster compounds by structural similarity using Butina clustering."""
    typed_smiles = [SMILES(s) for s in smiles_list]
    clusters = await _service.cluster(typed_smiles, n_clusters)
    return json.dumps(
        {
            "n_clusters": len(clusters),
            "clusters": {
                str(k): {
                    "size": len(v),
                    "smiles": [str(s) for s in v],
                }
                for k, v in clusters.items()
            },
        }
    )
