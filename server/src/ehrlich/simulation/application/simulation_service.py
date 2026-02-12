from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from ehrlich.simulation.domain.docking_result import DockingResult
from ehrlich.simulation.domain.resistance_assessment import MutationRisk, ResistanceAssessment
from ehrlich.simulation.infrastructure.vina_adapter import VinaAdapter, interpret_energy

if TYPE_CHECKING:
    from ehrlich.kernel.chemistry_port import ChemistryPort
    from ehrlich.kernel.types import SMILES
    from ehrlich.simulation.domain.admet_profile import ADMETProfile
    from ehrlich.simulation.domain.protein_annotation import ProteinAnnotation
    from ehrlich.simulation.domain.protein_target import ProteinTarget
    from ehrlich.simulation.domain.repository import (
        ProteinAnnotationRepository,
        ProteinTargetRepository,
        TargetAssociationRepository,
        ToxicityRepository,
    )
    from ehrlich.simulation.domain.target_association import TargetAssociation
    from ehrlich.simulation.domain.toxicity_profile import ToxicityProfile
    from ehrlich.simulation.infrastructure.pkcsm_client import PkCSMClient
    from ehrlich.simulation.infrastructure.protein_store import ProteinStore

logger = logging.getLogger(__name__)

_RESISTANCE_YAML = Path(__file__).resolve().parents[5] / "data" / "resistance" / "default.yaml"


def _load_resistance_data(
    yaml_path: Path,
) -> tuple[dict[str, list[tuple[str, str, str]]], dict[str, list[str]]]:
    if not yaml_path.exists():
        logger.warning("Resistance YAML not found: %s", yaml_path)
        return {}, {}
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    mutations: dict[str, list[tuple[str, str, str]]] = {}
    for target_id, entries in data.get("mutations", {}).items():
        mutations[target_id] = [
            (str(e["mutation"]), str(e["risk"]), str(e["mechanism"])) for e in entries
        ]
    patterns: dict[str, list[str]] = {}
    for smarts, info in data.get("patterns", {}).items():
        patterns[str(smarts)] = [str(t) for t in info.get("targets", [])]
    return mutations, patterns


class SimulationService:
    def __init__(
        self,
        protein_store: ProteinStore,
        rdkit: ChemistryPort,
        vina: VinaAdapter,
        admet_client: PkCSMClient,
        rcsb_client: ProteinTargetRepository | None = None,
        comptox_client: ToxicityRepository | None = None,
        annotation_repo: ProteinAnnotationRepository | None = None,
        association_repo: TargetAssociationRepository | None = None,
        resistance_yaml: Path | None = None,
    ) -> None:
        self._proteins = protein_store
        self._rdkit = rdkit
        self._vina = vina
        self._admet = admet_client
        self._rcsb = rcsb_client
        self._comptox = comptox_client
        self._annotations = annotation_repo
        self._associations = association_repo
        mutations, patterns = _load_resistance_data(resistance_yaml or _RESISTANCE_YAML)
        self._known_mutations = mutations
        self._resistance_patterns = patterns

    async def search_targets(
        self, query: str, organism: str = "", limit: int = 10
    ) -> list[ProteinTarget]:
        return await self._proteins.search(query, organism, limit)

    async def list_targets(self) -> list[ProteinTarget]:
        return await self._proteins.list_targets()

    async def get_protein_annotation(
        self, query: str, organism: str = ""
    ) -> list[ProteinAnnotation]:
        if self._annotations is None:
            return []
        return await self._annotations.search(query, organism)

    async def search_disease_targets(
        self, disease: str, limit: int = 10
    ) -> list[TargetAssociation]:
        if self._associations is None:
            return []
        return await self._associations.search(disease, limit)

    async def fetch_toxicity(self, identifier: str) -> ToxicityProfile | None:
        if self._comptox is None:
            return None
        return await self._comptox.fetch(identifier)

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
        mutations_config = self._known_mutations.get(target_id.upper(), [])

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
        for pattern, affected_targets in self._resistance_patterns.items():
            if target_id.upper() in affected_targets:
                matched, _ = self._rdkit.substructure_match(smiles, pattern)
                if matched:
                    return "HIGH"
        return "MODERATE"
