from __future__ import annotations

from dataclasses import dataclass, field

from ehrlich.kernel.types import SMILES, InChIKey


@dataclass
class Compound:
    smiles: SMILES
    name: str = ""
    inchi_key: InChIKey = InChIKey("")
    metadata: dict[str, str] = field(default_factory=dict)
