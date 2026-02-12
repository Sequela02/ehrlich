from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.training.domain.entities import ClinicalTrial


class ClinicalTrialRepository(ABC):
    @abstractmethod
    async def search(
        self, condition: str, intervention: str, max_results: int
    ) -> list[ClinicalTrial]: ...
