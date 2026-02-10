from ehrlich.prediction.domain.repository import ModelRepository
from ehrlich.prediction.domain.trained_model import TrainedModel


class ModelStore(ModelRepository):
    async def save(self, model: TrainedModel, artifact: object) -> str:
        raise NotImplementedError

    async def load(self, model_id: str) -> tuple[TrainedModel, object]:
        raise NotImplementedError

    async def list_models(self) -> list[TrainedModel]:
        raise NotImplementedError
