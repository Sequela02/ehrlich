from __future__ import annotations

from typing import TYPE_CHECKING

from ehrlich.simulation.domain.admet_profile import ADMETProfile

if TYPE_CHECKING:
    from ehrlich.kernel.chemistry_port import ChemistryPort
    from ehrlich.kernel.descriptors import MolecularDescriptors
    from ehrlich.kernel.types import SMILES

# Mutagenic substructure alerts (SMARTS)
_MUTAGENIC_ALERTS = (
    "[NX3](=O)=O",  # nitro group (uncharged)
    "[N+](=O)[O-]",  # nitro group (charge-separated)
    "[N]=[N]=[N]",  # azide
    "O=C1C=CC(=O)C=C1",  # quinone
)

# Hepatotoxicity substructure alerts
_HEPATOTOX_ALERTS = (
    "C(=O)Cl",  # acyl chloride
    "[SX2]C(=O)",  # thioester
)


class PkCSMClient:
    """ADMET prediction using RDKit molecular descriptors.

    Named PkCSMClient for interface compatibility; uses local RDKit computation
    as the primary (and currently only) implementation.
    """

    def __init__(self, rdkit: ChemistryPort) -> None:
        self._rdkit = rdkit

    async def predict(self, smiles: SMILES) -> ADMETProfile:
        desc = self._rdkit.compute_descriptors(smiles)
        lipinski = self._count_lipinski_violations(desc)
        ames = self._check_mutagenic_alerts(smiles)
        hepatotox = self._check_hepatotoxicity(desc, smiles)
        herg = desc.logp > 3.7 and desc.molecular_weight > 350
        bbb = desc.tpsa < 90 and desc.molecular_weight < 400 and 0 < desc.logp < 3
        absorption = max(0.0, min(100.0, 100.0 - lipinski * 25.0))
        distribution_vd = round(0.04 + 0.1 * max(0.0, desc.logp), 3)
        cyp_inhibitor = desc.logp > 3.0 and desc.num_rings >= 2
        clearance = round(max(0.1, 30.0 - desc.molecular_weight * 0.04), 3)
        ld50 = round(max(50.0, 500.0 * desc.qed), 1)

        return ADMETProfile(
            absorption=absorption,
            distribution_vd=distribution_vd,
            metabolism_cyp_inhibitor=cyp_inhibitor,
            excretion_clearance=clearance,
            toxicity_ld50=ld50,
            toxicity_ames=ames,
            herg_inhibitor=herg,
            bbb_permeant=bbb,
            hepatotoxicity=hepatotox,
            lipinski_violations=lipinski,
            qed=round(desc.qed, 4),
        )

    def _check_mutagenic_alerts(self, smiles: SMILES) -> bool:
        for pattern in _MUTAGENIC_ALERTS:
            matched, _ = self._rdkit.substructure_match(smiles, pattern)
            if matched:
                return True
        return False

    def _check_hepatotoxicity(self, desc: MolecularDescriptors, smiles: SMILES) -> bool:
        if desc.logp > 3.5 and desc.molecular_weight > 400:
            return True
        for pattern in _HEPATOTOX_ALERTS:
            matched, _ = self._rdkit.substructure_match(smiles, pattern)
            if matched:
                return True
        return False

    @staticmethod
    def _count_lipinski_violations(desc: MolecularDescriptors) -> int:
        violations = 0
        if desc.molecular_weight > 500:
            violations += 1
        if desc.logp > 5:
            violations += 1
        if desc.hbd > 5:
            violations += 1
        if desc.hba > 10:
            violations += 1
        return violations
