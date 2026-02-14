from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.impact.domain.entities import (
        Benchmark,
        EconomicSeries,
        HealthIndicator,
    )


class EconomicDataRepository(ABC):
    @abstractmethod
    async def search_series(self, query: str, limit: int = 10) -> list[EconomicSeries]: ...

    @abstractmethod
    async def get_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None: ...


class HealthDataRepository(ABC):
    @abstractmethod
    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[HealthIndicator]: ...


class DevelopmentDataRepository(ABC):
    @abstractmethod
    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[Benchmark]: ...

    @abstractmethod
    async def get_countries(self) -> list[dict[str, str]]: ...
