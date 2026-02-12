from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.nutrition.domain.entities import (
        AdverseEvent,
        NutrientProfile,
        SupplementLabel,
    )


class SupplementRepository(ABC):
    @abstractmethod
    async def search_labels(
        self, ingredient: str, max_results: int
    ) -> list[SupplementLabel]: ...


class NutrientRepository(ABC):
    @abstractmethod
    async def search(
        self, query: str, max_results: int
    ) -> list[NutrientProfile]: ...


class AdverseEventRepository(ABC):
    @abstractmethod
    async def search(
        self, product_name: str, max_results: int
    ) -> list[AdverseEvent]: ...
