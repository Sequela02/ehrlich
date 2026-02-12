from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper
    from ehrlich.literature.domain.repository import PaperSearchRepository
    from ehrlich.nutrition.domain.entities import (
        AdverseEvent,
        NutrientProfile,
        SupplementLabel,
    )
    from ehrlich.nutrition.domain.repository import (
        AdverseEventRepository,
        NutrientRepository,
        SupplementRepository,
    )


class NutritionService:
    def __init__(
        self,
        paper_repo: PaperSearchRepository,
        supplements: SupplementRepository | None = None,
        nutrients: NutrientRepository | None = None,
        adverse_events: AdverseEventRepository | None = None,
    ) -> None:
        self._papers = paper_repo
        self._supplements = supplements
        self._nutrients = nutrients
        self._adverse_events = adverse_events

    async def search_supplement_evidence(
        self, supplement: str, outcome: str = "performance", limit: int = 8
    ) -> list[Paper]:
        query = f"{supplement} {outcome} meta-analysis systematic review"
        return await self._papers.search(query, limit=limit)

    async def search_supplement_labels(
        self, ingredient: str, max_results: int = 10
    ) -> list[SupplementLabel]:
        if not self._supplements:
            return []
        return await self._supplements.search_labels(ingredient, max_results)

    async def search_nutrient_data(
        self, query: str, max_results: int = 5
    ) -> list[NutrientProfile]:
        if not self._nutrients:
            return []
        return await self._nutrients.search(query, max_results)

    async def search_supplement_safety(
        self, product_name: str, max_results: int = 10
    ) -> list[AdverseEvent]:
        if not self._adverse_events:
            return []
        return await self._adverse_events.search(product_name, max_results)
