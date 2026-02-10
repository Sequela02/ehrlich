from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ADMETProfile:
    absorption: float = 0.0
    distribution_vd: float = 0.0
    metabolism_cyp_inhibitor: bool = False
    excretion_clearance: float = 0.0
    toxicity_ld50: float = 0.0
    toxicity_ames: bool = False
    herg_inhibitor: bool = False
    bbb_permeant: bool = False

    @property
    def has_toxicity_flags(self) -> bool:
        return self.toxicity_ames or self.herg_inhibitor
