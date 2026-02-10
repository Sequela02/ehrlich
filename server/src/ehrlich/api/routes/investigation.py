from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ehrlich.analysis.tools import analyze_substructures, compute_properties, explore_dataset
from ehrlich.api.sse import domain_event_to_sse
from ehrlich.chemistry.tools import (
    compute_descriptors,
    compute_fingerprint,
    generate_3d,
    modify_molecule,
    substructure_match,
    tanimoto_similarity,
    validate_smiles,
)
from ehrlich.config import get_settings
from ehrlich.investigation.application.orchestrator import Orchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.investigation import Investigation
from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
from ehrlich.investigation.tools import conclude_investigation, record_finding
from ehrlich.literature.tools import get_reference, search_literature
from ehrlich.prediction.tools import cluster_compounds, predict_candidates, train_model
from ehrlich.simulation.tools import assess_resistance, dock_against_target, predict_admet

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

router = APIRouter(tags=["investigation"])

_investigations: dict[str, Investigation] = {}


class InvestigateRequest(BaseModel):
    prompt: str


class InvestigateResponse(BaseModel):
    id: str
    status: str


def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    tools: dict[str, Any] = {
        "validate_smiles": validate_smiles,
        "compute_descriptors": compute_descriptors,
        "compute_fingerprint": compute_fingerprint,
        "tanimoto_similarity": tanimoto_similarity,
        "generate_3d": generate_3d,
        "substructure_match": substructure_match,
        "modify_molecule": modify_molecule,
        "search_literature": search_literature,
        "get_reference": get_reference,
        "explore_dataset": explore_dataset,
        "analyze_substructures": analyze_substructures,
        "compute_properties": compute_properties,
        "train_model": train_model,
        "predict_candidates": predict_candidates,
        "cluster_compounds": cluster_compounds,
        "dock_against_target": dock_against_target,
        "predict_admet": predict_admet,
        "assess_resistance": assess_resistance,
        "record_finding": record_finding,
        "conclude_investigation": conclude_investigation,
    }
    for name, func in tools.items():
        registry.register(name, func)
    return registry


@router.post("/investigate")
async def start_investigation(request: InvestigateRequest) -> InvestigateResponse:
    investigation = Investigation(prompt=request.prompt)
    _investigations[investigation.id] = investigation
    return InvestigateResponse(id=investigation.id, status=investigation.status.value)


@router.get("/investigate/{investigation_id}/stream")
async def stream_investigation(investigation_id: str) -> EventSourceResponse:
    investigation = _investigations.get(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if investigation.status != "pending":
        raise HTTPException(status_code=409, detail="Investigation already started")

    settings = get_settings()
    client = AnthropicClientAdapter(model=settings.anthropic_model)
    registry = _build_registry()
    orchestrator = Orchestrator(
        client=client,
        registry=registry,
        max_iterations=settings.max_iterations,
    )

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async for domain_event in orchestrator.run(investigation):
            sse_event = domain_event_to_sse(domain_event)
            if sse_event is not None:
                yield {"event": sse_event.event.value, "data": sse_event.format()}

    return EventSourceResponse(event_generator())
