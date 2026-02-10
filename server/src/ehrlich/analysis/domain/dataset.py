from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES


@dataclass
class Dataset:
    name: str
    target: str
    smiles_list: list[SMILES] = field(default_factory=list)
    activities: list[float] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.smiles_list)

    @property
    def active_count(self) -> int:
        return sum(1 for a in self.activities if a >= 0.5)
