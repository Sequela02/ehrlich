from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import MolBlock


@dataclass(frozen=True)
class Conformer3D:
    mol_block: MolBlock
    energy: float = 0.0
    num_atoms: int = 0
