from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ehrlich.simulation.domain.docking_result import DockingResult
from ehrlich.simulation.domain.resistance_assessment import MutationRisk, ResistanceAssessment
from ehrlich.simulation.infrastructure.vina_adapter import VinaAdapter, interpret_energy

if TYPE_CHECKING:
    from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
    from ehrlich.kernel.types import SMILES
    from ehrlich.simulation.domain.admet_profile import ADMETProfile
    from ehrlich.simulation.infrastructure.pkcsm_client import PkCSMClient
    from ehrlich.simulation.infrastructure.protein_store import ProteinStore

logger = logging.getLogger(__name__)

# Known resistance mutations per target
_KNOWN_MUTATIONS: dict[str, list[tuple[str, str, str]]] = {
    "1VQQ": [
        ("S403A", "HIGH", "Reduced beta-lactam binding affinity at active site"),
        ("N146K", "MODERATE", "Altered active site geometry affecting drug orientation"),
    ],
    "1AD4": [
        ("F17L", "HIGH", "Sulfonamide resistance via altered DHPS binding pocket"),
    ],
    "2XCT": [
        ("S84L", "HIGH", "Fluoroquinolone resistance via DNA gyrase QRDR mutation"),
    ],
    "1UAE": [
        ("C115D", "MODERATE", "Fosfomycin resistance via altered MurA active site cysteine"),
    ],
    "3SPU": [
        ("V73_ins", "HIGH", "Extended-spectrum resistance via NDM-1 loop insertion"),
        ("M154L", "MODERATE", "Altered zinc coordination in metallo-beta-lactamase"),
    ],
}

# Compound class patterns -> affected targets
_RESISTANCE_PATTERNS: dict[str, list[str]] = {
    "C1C(C(=O)N1)S": ["1VQQ"],  # beta-lactam ring -> PBP2a
    "c1cc2c(cc1F)c(=O)c(cn2)C(=O)O": ["2XCT"],  # fluoroquinolone -> DNA Gyrase
    "NS(=O)(=O)": ["1AD4"],  # sulfonamide -> DHPS
}


class SimulationService:
    def __init__(
        self,
        protein_store: ProteinStore,
        rdkit: RDKitAdapter,
        vina: VinaAdapter,
        admet_client: PkCSMClient,
    ) -> None:
        self._proteins = protein_store
        self._rdkit = rdkit
        self._vina = vina
        self._admet = admet_client

    async def dock(self, smiles: SMILES, target_id: str) -> DockingResult:
        target = self._proteins.get_target(target_id)

        if VinaAdapter.is_available():
            try:
                pdbqt = await self._proteins.get_pdbqt(target_id)
                conformer = self._rdkit.generate_conformer(smiles)
                center = (target.center_x, target.center_y, target.center_z)
                result = await self._vina.dock(
                    str(conformer.mol_block), pdbqt, center, target.box_size
                )
                energy = result.get("energy", 0.0)
                rmsd = result.get("rmsd", 0.0)
                return DockingResult(
                    smiles=smiles,
                    target_id=target_id,
                    binding_energy=energy,
                    pose_rmsd=rmsd,
                    interactions={"interpretation": [interpret_energy(energy)]},
                )
            except (FileNotFoundError, NotImplementedError):
                logger.info("Vina docking unavailable for %s, using estimate", target_id)

        return self._estimate_docking(smiles, target_id)

    async def predict_admet(self, smiles: SMILES) -> ADMETProfile:
        return await self._admet.predict(smiles)

    async def assess_resistance(self, smiles: SMILES, target_id: str) -> ResistanceAssessment:
        target = self._proteins.get_target(target_id)
        mutations_config = _KNOWN_MUTATIONS.get(target_id.upper(), [])

        if not mutations_config:
            return ResistanceAssessment(
                target_id=target_id,
                target_name=target.name,
                risk_level="LOW",
                explanation=f"No known resistance mutations catalogued for {target.name}",
            )

        compound_risk = self._assess_compound_class_risk(smiles, target_id)

        mutation_risks: list[MutationRisk] = []
        mutations_dict: dict[str, str] = {}
        for mutation, base_risk, mechanism in mutations_config:
            effective_risk = "HIGH" if compound_risk == "HIGH" else base_risk
            mutation_risks.append(
                MutationRisk(
                    mutation=mutation,
                    risk_level=effective_risk,
                    mechanism=mechanism,
                )
            )
            mutations_dict[mutation] = effective_risk

        risk_levels = [mr.risk_level for mr in mutation_risks]
        if "HIGH" in risk_levels:
            overall = "HIGH"
        elif "MODERATE" in risk_levels:
            overall = "MODERATE"
        else:
            overall = "LOW"

        return ResistanceAssessment(
            target_id=target_id,
            target_name=target.name,
            risk_level=overall,
            mutation_risks=tuple(mutation_risks),
            mutations=mutations_dict,
            explanation=(
                f"Assessment for {target.name}: {len(mutation_risks)} known resistance "
                f"mutation(s). Overall risk: {overall}."
            ),
        )

    def _estimate_docking(self, smiles: SMILES, target_id: str) -> DockingResult:
        desc = self._rdkit.compute_descriptors(smiles)
        energy = round(-1.0 * (desc.qed * 7.0 + min(desc.logp, 5.0) * 0.6 + 1.5), 2)
        energy = max(-12.0, min(-2.0, energy))
        return DockingResult(
            smiles=smiles,
            target_id=target_id,
            binding_energy=energy,
            pose_rmsd=0.0,
            interactions={
                "method": ["rdkit_estimate"],
                "interpretation": [interpret_energy(energy)],
                "note": ["Estimated from molecular descriptors (Vina unavailable)"],
            },
        )

    def _assess_compound_class_risk(self, smiles: SMILES, target_id: str) -> str:
        for pattern, affected_targets in _RESISTANCE_PATTERNS.items():
            if target_id.upper() in affected_targets:
                matched, _ = self._rdkit.substructure_match(smiles, pattern)
                if matched:
                    return "HIGH"
        return "MODERATE"
