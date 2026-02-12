from abc import ABC, abstractmethod

from ehrlich.analysis.domain.compound import CompoundSearchResult
from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.analysis.domain.pharmacology import PharmacologyEntry


class DatasetRepository(ABC):
    @abstractmethod
    async def load(self, target: str, threshold: float = 1.0) -> Dataset: ...

    @abstractmethod
    async def search_bioactivity(
        self,
        target: str,
        assay_types: list[str] | None = None,
        threshold: float = 1.0,
    ) -> Dataset: ...

    @abstractmethod
    async def list_targets(self) -> list[str]: ...


class CompoundSearchRepository(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[CompoundSearchResult]: ...

    @abstractmethod
    async def search_by_similarity(
        self, smiles: str, threshold: float = 0.8, limit: int = 10
    ) -> list[CompoundSearchResult]: ...


class PharmacologyRepository(ABC):
    @abstractmethod
    async def search(self, target: str, family: str = "") -> list[PharmacologyEntry]: ...
