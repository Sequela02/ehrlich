from abc import ABC, abstractmethod

from ehrlich.analysis.domain.dataset import Dataset


class DatasetRepository(ABC):
    @abstractmethod
    async def load(self, target: str, threshold: float = 1.0) -> Dataset: ...

    @abstractmethod
    async def list_targets(self) -> list[str]: ...
