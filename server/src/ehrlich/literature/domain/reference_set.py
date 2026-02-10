from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper


@dataclass(frozen=True)
class CoreReferenceSet:
    papers: tuple[Paper, ...] = field(default_factory=tuple)
    _key_index: dict[str, Paper] = field(default_factory=dict, repr=False, compare=False)

    def find_by_doi(self, doi: str) -> Paper | None:
        return next((p for p in self.papers if p.doi == doi), None)

    def find_by_key(self, key: str) -> Paper | None:
        return self._key_index.get(key)

    def __len__(self) -> int:
        return len(self.papers)
