from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ehrlich.kernel.exceptions import InvalidSMILESError

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES


@dataclass(frozen=True)
class Molecule:
    smiles: SMILES

    def __post_init__(self) -> None:
        if not self.smiles or not self.smiles.strip():
            raise InvalidSMILESError(self.smiles, "SMILES string cannot be empty")
        if not re.match(r"^[A-Za-z0-9@+\-\[\]\(\)\\\/=#$:.%]+$", self.smiles):
            raise InvalidSMILESError(self.smiles, "SMILES contains invalid characters")
