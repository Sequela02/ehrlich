from ehrlich.kernel.types import SMILES
from ehrlich.prediction.domain.prediction_result import PredictionResult
from ehrlich.prediction.domain.trained_model import TrainedModel


class PredictionService:
    async def train(self, target: str, model_type: str = "xgboost") -> TrainedModel:
        raise NotImplementedError

    async def predict(self, smiles_list: list[SMILES], model_id: str) -> list[PredictionResult]:
        raise NotImplementedError

    async def ensemble(self, smiles_list: list[SMILES]) -> list[PredictionResult]:
        raise NotImplementedError

    async def cluster(
        self, smiles_list: list[SMILES], n_clusters: int = 5
    ) -> dict[int, list[SMILES]]:
        raise NotImplementedError
