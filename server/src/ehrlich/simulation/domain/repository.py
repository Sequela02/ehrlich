from abc import ABC, abstractmethod

from ehrlich.simulation.domain.protein_annotation import ProteinAnnotation
from ehrlich.simulation.domain.protein_target import ProteinTarget
from ehrlich.simulation.domain.target_association import TargetAssociation
from ehrlich.simulation.domain.toxicity_profile import ToxicityProfile


class ProteinTargetRepository(ABC):
    @abstractmethod
    async def search(
        self, query: str, organism: str = "", limit: int = 10
    ) -> list[ProteinTarget]: ...


class ToxicityRepository(ABC):
    @abstractmethod
    async def fetch(self, identifier: str) -> ToxicityProfile | None: ...


class ProteinAnnotationRepository(ABC):
    @abstractmethod
    async def search(
        self, query: str, organism: str = "", limit: int = 5
    ) -> list[ProteinAnnotation]: ...


class TargetAssociationRepository(ABC):
    @abstractmethod
    async def search(self, disease: str, limit: int = 10) -> list[TargetAssociation]: ...
