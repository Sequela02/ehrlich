from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.training.domain.entities import ClinicalTrial, Exercise, PubMedArticle


class ClinicalTrialRepository(ABC):
    @abstractmethod
    async def search(
        self, condition: str, intervention: str, max_results: int
    ) -> list[ClinicalTrial]: ...


class PubMedRepository(ABC):
    @abstractmethod
    async def search(
        self, query: str, mesh_terms: list[str] | None = None, max_results: int = 10
    ) -> list[PubMedArticle]: ...


class ExerciseRepository(ABC):
    @abstractmethod
    async def search(
        self, muscle_group: str = "", equipment: str = "", category: str = "", limit: int = 20
    ) -> list[Exercise]: ...
