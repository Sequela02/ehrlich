from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.prediction.domain.trained_model import TrainedModel


class ModelRepository(ABC):
    @abstractmethod
    async def save(self, model: TrainedModel, artifact: object) -> str: ...

    @abstractmethod
    async def load(self, model_id: str) -> tuple[TrainedModel, object]: ...

    @abstractmethod
    async def list_models(self) -> list[TrainedModel]: ...
