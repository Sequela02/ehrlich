from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.analysis.domain.repository import DatasetRepository


class ChEMBLLoader(DatasetRepository):
    async def load(self, target: str, threshold: float = 1.0) -> Dataset:
        raise NotImplementedError

    async def list_targets(self) -> list[str]:
        raise NotImplementedError
