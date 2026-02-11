from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.investigation.domain.investigation import Investigation


class InvestigationRepository(ABC):
    @abstractmethod
    async def save(self, investigation: Investigation) -> None: ...

    @abstractmethod
    async def get_by_id(self, investigation_id: str) -> Investigation | None: ...

    @abstractmethod
    async def list_all(self) -> list[Investigation]: ...

    @abstractmethod
    async def update(self, investigation: Investigation) -> None: ...

    @abstractmethod
    async def save_event(self, investigation_id: str, event_type: str, event_data: str) -> None: ...

    @abstractmethod
    async def get_events(self, investigation_id: str) -> list[dict[str, str]]: ...
