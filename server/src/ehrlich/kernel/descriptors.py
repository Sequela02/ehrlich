from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MolecularDescriptors:
    molecular_weight: float = 0.0
    logp: float = 0.0
    tpsa: float = 0.0
    hbd: int = 0
    hba: int = 0
    rotatable_bonds: int = 0
    qed: float = 0.0
    num_rings: int = 0

    @property
    def passes_lipinski(self) -> bool:
        violations = sum(
            [
                self.molecular_weight > 500,
                self.logp > 5,
                self.hbd > 5,
                self.hba > 10,
            ]
        )
        return violations <= 1
