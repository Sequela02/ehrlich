from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper


@dataclass(frozen=True)
class CoreReferenceSet:
    papers: tuple[Paper, ...] = field(default_factory=tuple)

    def find_by_doi(self, doi: str) -> Paper | None:
        return next((p for p in self.papers if p.doi == doi), None)

    def __len__(self) -> int:
        return len(self.papers)
