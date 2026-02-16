from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ehrlich.api.auth import get_optional_user
from ehrlich.chemistry.application.chemistry_service import ChemistryService
from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.types import SMILES
from ehrlich.simulation.infrastructure.protein_store import ProteinStore

router = APIRouter(tags=["molecule"])

_chemistry = ChemistryService()
_protein_store = ProteinStore()
_optional_user = Depends(get_optional_user)

_ERROR_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
  <rect width="100%" height="100%" fill="#1a1e1a" rx="8"/>
  <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle"
        font-family="monospace" font-size="11" fill="#666">Invalid SMILES</text>
</svg>"""


@router.get("/molecule/depict")
async def depict(
    smiles: str = Query(..., description="SMILES string", max_length=500),
    w: int = Query(300, ge=50, le=1000),
    h: int = Query(200, ge=50, le=1000),
    _user: dict[str, Any] | None = _optional_user,
) -> Response:
    try:
        svg = _chemistry.depict_2d(SMILES(smiles), width=w, height=h)
    except (InvalidSMILESError, Exception):
        svg = _ERROR_SVG.format(w=w, h=h)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/molecule/conformer")
async def conformer(
    smiles: str = Query(..., description="SMILES string", max_length=500),
    _user: dict[str, Any] | None = _optional_user,
) -> dict[str, Any]:
    try:
        conf = _chemistry.generate_conformer(SMILES(smiles))
        return {"mol_block": conf.mol_block, "energy": conf.energy, "num_atoms": conf.num_atoms}
    except InvalidSMILESError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/molecule/descriptors")
async def descriptors(
    smiles: str = Query(..., description="SMILES string", max_length=500),
    _user: dict[str, Any] | None = _optional_user,
) -> dict[str, Any]:
    try:
        desc = _chemistry.compute_descriptors(SMILES(smiles))
        result = asdict(desc)
        result["passes_lipinski"] = desc.passes_lipinski
        return result
    except InvalidSMILESError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/targets")
async def list_targets(
    _user: dict[str, Any] | None = _optional_user,
) -> list[dict[str, str]]:
    targets = await _protein_store.list_targets()
    return [{"pdb_id": t.pdb_id, "name": t.name, "organism": t.organism} for t in targets]
