from ehrlich.analysis.domain.dataset import Dataset


class Tox21Loader:
    async def load(self, assay: str) -> Dataset:
        raise NotImplementedError

    async def cross_reference(self, dataset: Dataset) -> Dataset:
        raise NotImplementedError
