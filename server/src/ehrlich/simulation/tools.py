from __future__ import annotations

import json

from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.exceptions import InvalidSMILESError, TargetNotFoundError
from ehrlich.kernel.types import SMILES
from ehrlich.simulation.application.simulation_service import SimulationService
from ehrlich.simulation.infrastructure.pkcsm_client import PkCSMClient
from ehrlich.simulation.infrastructure.protein_store import ProteinStore
from ehrlich.simulation.infrastructure.vina_adapter import VinaAdapter

_rdkit = RDKitAdapter()
_protein_store = ProteinStore()
_vina = VinaAdapter()
_admet_client = PkCSMClient(rdkit=_rdkit)
_service = SimulationService(
    protein_store=_protein_store,
    rdkit=_rdkit,
    vina=_vina,
    admet_client=_admet_client,
)


async def dock_against_target(smiles: str, target_id: str) -> str:
    """Dock a molecule against a protein target."""
    try:
        result = await _service.dock(SMILES(smiles), target_id)
    except TargetNotFoundError:
        available = await _protein_store.list_targets()
        ids = [t.pdb_id for t in available]
        return json.dumps({"error": f"Unknown target: {target_id}", "available_targets": ids})
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles})
    return json.dumps(
        {
            "smiles": str(result.smiles),
            "target_id": result.target_id,
            "binding_energy": result.binding_energy,
            "pose_rmsd": result.pose_rmsd,
            "interactions": result.interactions,
        }
    )


async def predict_admet(smiles: str) -> str:
    """Predict ADMET properties for a molecule."""
    profile = await _service.predict_admet(SMILES(smiles))
    return json.dumps(
        {
            "smiles": smiles,
            "absorption": profile.absorption,
            "distribution_vd": profile.distribution_vd,
            "metabolism_cyp_inhibitor": profile.metabolism_cyp_inhibitor,
            "excretion_clearance": profile.excretion_clearance,
            "toxicity_ld50": profile.toxicity_ld50,
            "toxicity_ames": profile.toxicity_ames,
            "herg_inhibitor": profile.herg_inhibitor,
            "bbb_permeant": profile.bbb_permeant,
            "hepatotoxicity": profile.hepatotoxicity,
            "lipinski_violations": profile.lipinski_violations,
            "qed": profile.qed,
            "has_toxicity_flags": profile.has_toxicity_flags,
        }
    )


async def assess_resistance(smiles: str, target_id: str) -> str:
    """Assess resistance mutation risk for a molecule-target pair."""
    try:
        result = await _service.assess_resistance(SMILES(smiles), target_id)
    except TargetNotFoundError:
        available = await _protein_store.list_targets()
        ids = [t.pdb_id for t in available]
        return json.dumps({"error": f"Unknown target: {target_id}", "available_targets": ids})
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles})
    return json.dumps(
        {
            "smiles": smiles,
            "target_id": result.target_id,
            "target_name": result.target_name,
            "risk_level": result.risk_level,
            "mutations": result.mutations,
            "mutation_details": [
                {
                    "mutation": mr.mutation,
                    "risk_level": mr.risk_level,
                    "mechanism": mr.mechanism,
                }
                for mr in result.mutation_risks
            ],
            "explanation": result.explanation,
        }
    )
