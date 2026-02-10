import json
from dataclasses import asdict

from ehrlich.chemistry.application.chemistry_service import ChemistryService
from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.types import SMILES

_service = ChemistryService()


async def validate_smiles(smiles: str) -> str:
    """Validate whether a SMILES string represents a valid molecule."""
    valid = _service.validate_smiles(SMILES(smiles))
    return json.dumps({"smiles": smiles, "valid": valid})


async def compute_descriptors(smiles: str) -> str:
    """Compute molecular descriptors (MW, LogP, TPSA, HBD, HBA, QED, etc.) for a SMILES."""
    try:
        desc = _service.compute_descriptors(SMILES(smiles))
        data = asdict(desc)
        data["passes_lipinski"] = desc.passes_lipinski
        return json.dumps({"smiles": smiles, **data})
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles})


async def compute_fingerprint(smiles: str, fp_type: str = "morgan") -> str:
    """Compute molecular fingerprint (Morgan/ECFP or MACCS) for a SMILES."""
    try:
        fp = _service.compute_fingerprint(SMILES(smiles), fp_type)
        return json.dumps(
            {
                "smiles": smiles,
                "fp_type": fp.fp_type,
                "n_bits": fp.n_bits,
                "on_bits_count": len(fp.bits),
                "on_bits": list(fp.bits),
            }
        )
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles})


async def tanimoto_similarity(smiles1: str, smiles2: str) -> str:
    """Compute Tanimoto similarity between two molecules (0.0-1.0)."""
    try:
        fp1 = _service.compute_fingerprint(SMILES(smiles1))
        fp2 = _service.compute_fingerprint(SMILES(smiles2))
        sim = _service.tanimoto_similarity(fp1, fp2)
        return json.dumps({"smiles1": smiles1, "smiles2": smiles2, "similarity": sim})
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e)})


async def generate_3d(smiles: str) -> str:
    """Generate a 3D conformer for the given SMILES. Returns MolBlock + energy."""
    try:
        conf = _service.generate_conformer(SMILES(smiles))
        return json.dumps(
            {
                "smiles": smiles,
                "mol_block": str(conf.mol_block),
                "energy_kcal": round(conf.energy, 4),
                "num_atoms": conf.num_atoms,
            }
        )
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles})


async def substructure_match(smiles: str, pattern: str) -> str:
    """Check if a molecule contains the given substructure pattern (SMARTS or SMILES)."""
    try:
        matched, atoms = _service.substructure_match(SMILES(smiles), pattern)
        return json.dumps(
            {
                "smiles": smiles,
                "pattern": pattern,
                "matched": matched,
                "matching_atoms": list(atoms),
            }
        )
    except InvalidSMILESError as e:
        return json.dumps({"error": str(e), "smiles": smiles, "pattern": pattern})


async def modify_molecule(smiles: str, modification: str) -> str:
    """Apply a chemical modification to the molecule (R-group enumeration)."""
    return json.dumps(
        {
            "status": "not_implemented",
            "smiles": smiles,
            "modification": modification,
            "message": "R-group enumeration is a stretch goal",
        }
    )
