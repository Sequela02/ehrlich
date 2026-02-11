from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ehrlich.analysis.tools import (
    analyze_substructures,
    compute_properties,
    explore_dataset,
    search_bioactivity,
    search_compounds,
    search_pharmacology,
)
from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.chemistry.tools import (
    compute_descriptors,
    compute_fingerprint,
    generate_3d,
    substructure_match,
    tanimoto_similarity,
    validate_smiles,
)
from ehrlich.config import get_settings
from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
from ehrlich.investigation.infrastructure.sqlite_repository import SqliteInvestigationRepository
from ehrlich.investigation.tools import (
    conclude_investigation,
    design_experiment,
    evaluate_hypothesis,
    propose_hypothesis,
    record_finding,
    record_negative_control,
)
from ehrlich.literature.tools import get_reference, search_literature
from ehrlich.prediction.tools import cluster_compounds, predict_candidates, train_model
from ehrlich.simulation.tools import (
    assess_resistance,
    dock_against_target,
    fetch_toxicity_profile,
    get_protein_annotation,
    predict_admet,
    search_disease_targets,
    search_protein_targets,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["investigation"])

_repository: SqliteInvestigationRepository | None = None
_active_investigations: dict[str, Investigation] = {}
_subscribers: dict[str, list[asyncio.Queue[dict[str, str] | None]]] = {}


class InvestigateRequest(BaseModel):
    prompt: str


class InvestigateResponse(BaseModel):
    id: str
    status: str


class InvestigationDetail(BaseModel):
    id: str
    prompt: str
    status: str
    hypotheses: list[dict[str, Any]]
    experiments: list[dict[str, Any]]
    current_hypothesis_id: str
    current_experiment_id: str
    findings: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    negative_controls: list[dict[str, Any]]
    citations: list[str]
    summary: str
    created_at: str
    cost_data: dict[str, object]


class InvestigationSummary(BaseModel):
    id: str
    prompt: str
    status: str
    created_at: str
    candidate_count: int


async def init_repository(db_path: str) -> None:
    global _repository  # noqa: PLW0603
    _repository = SqliteInvestigationRepository(db_path)
    await _repository.initialize()


def _get_repository() -> SqliteInvestigationRepository:
    if _repository is None:
        msg = "Repository not initialized"
        raise RuntimeError(msg)
    return _repository


def _build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    tools: dict[str, Any] = {
        "validate_smiles": validate_smiles,
        "compute_descriptors": compute_descriptors,
        "compute_fingerprint": compute_fingerprint,
        "tanimoto_similarity": tanimoto_similarity,
        "generate_3d": generate_3d,
        "substructure_match": substructure_match,
        "search_literature": search_literature,
        "get_reference": get_reference,
        "explore_dataset": explore_dataset,
        "search_compounds": search_compounds,
        "search_bioactivity": search_bioactivity,
        "analyze_substructures": analyze_substructures,
        "compute_properties": compute_properties,
        "train_model": train_model,
        "predict_candidates": predict_candidates,
        "cluster_compounds": cluster_compounds,
        "search_protein_targets": search_protein_targets,
        "dock_against_target": dock_against_target,
        "predict_admet": predict_admet,
        "fetch_toxicity_profile": fetch_toxicity_profile,
        "assess_resistance": assess_resistance,
        "get_protein_annotation": get_protein_annotation,
        "search_disease_targets": search_disease_targets,
        "search_pharmacology": search_pharmacology,
        "record_finding": record_finding,
        "conclude_investigation": conclude_investigation,
        "propose_hypothesis": propose_hypothesis,
        "design_experiment": design_experiment,
        "evaluate_hypothesis": evaluate_hypothesis,
        "record_negative_control": record_negative_control,
    }
    for name, func in tools.items():
        registry.register(name, func)
    return registry


def _broadcast_event(investigation_id: str, event: dict[str, str]) -> None:
    for queue in _subscribers.get(investigation_id, []):
        queue.put_nowait(event)


def _end_broadcast(investigation_id: str) -> None:
    for queue in _subscribers.get(investigation_id, []):
        queue.put_nowait(None)
    _subscribers.pop(investigation_id, None)


@router.get("/investigate")
async def list_investigations() -> list[InvestigationSummary]:
    repo = _get_repository()
    investigations = await repo.list_all()
    return [
        InvestigationSummary(
            id=inv.id,
            prompt=inv.prompt,
            status=inv.status.value,
            created_at=inv.created_at.isoformat(),
            candidate_count=len(inv.candidates),
        )
        for inv in investigations
    ]


@router.get("/investigate/{investigation_id}")
async def get_investigation(investigation_id: str) -> InvestigationDetail:
    repo = _get_repository()
    # Check active first (in-flight data is more current)
    investigation = _active_investigations.get(investigation_id)
    if investigation is None:
        investigation = await repo.get_by_id(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return _to_detail(investigation)


@router.post("/investigate")
async def start_investigation(request: InvestigateRequest) -> InvestigateResponse:
    investigation = Investigation(prompt=request.prompt)
    repo = _get_repository()
    await repo.save(investigation)
    return InvestigateResponse(id=investigation.id, status=investigation.status.value)


@router.get("/investigate/{investigation_id}/stream")
async def stream_investigation(investigation_id: str) -> EventSourceResponse:
    repo = _get_repository()
    investigation = _active_investigations.get(investigation_id)
    if investigation is None:
        investigation = await repo.get_by_id(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    status = investigation.status

    # Completed or failed -- replay final status
    if status in (InvestigationStatus.COMPLETED, InvestigationStatus.FAILED):
        return EventSourceResponse(_replay_final(investigation))

    # Running -- subscribe to live events if broadcast is active
    if status == InvestigationStatus.RUNNING:
        if investigation.id in _subscribers:
            return EventSourceResponse(_subscribe(investigation))
        raise HTTPException(
            status_code=409,
            detail="Investigation is running but stream is not available for reconnection",
        )

    # Pending -- start the investigation and stream
    settings = get_settings()
    registry = _build_registry()

    _active_investigations[investigation.id] = investigation
    _subscribers[investigation.id] = []

    orchestrator = _create_orchestrator(settings, registry)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            async for domain_event in orchestrator.run(investigation):
                sse_event = domain_event_to_sse(domain_event)
                if sse_event is not None:
                    event = {
                        "event": sse_event.event.value,
                        "data": sse_event.format(),
                    }
                    # Skip completed/error (replayed from state) and cost_update (transient)
                    if sse_event.event not in (
                        SSEEventType.COMPLETED,
                        SSEEventType.ERROR,
                        SSEEventType.COST_UPDATE,
                    ):
                        await repo.save_event(
                            investigation.id,
                            sse_event.event.value,
                            sse_event.format(),
                        )
                    _broadcast_event(investigation.id, event)
                    yield event
        finally:
            _end_broadcast(investigation.id)
            await repo.update(investigation)
            _active_investigations.pop(investigation.id, None)

    return EventSourceResponse(event_generator())


def _create_orchestrator(settings: Any, registry: ToolRegistry) -> MultiModelOrchestrator:
    api_key = settings.anthropic_api_key or None
    director = AnthropicClientAdapter(model=settings.director_model, api_key=api_key)
    researcher = AnthropicClientAdapter(model=settings.researcher_model, api_key=api_key)
    summarizer = AnthropicClientAdapter(model=settings.summarizer_model, api_key=api_key)
    return MultiModelOrchestrator(
        director=director,
        researcher=researcher,
        summarizer=summarizer,
        registry=registry,
        max_iterations_per_experiment=settings.max_iterations_per_experiment,
        summarizer_threshold=settings.summarizer_threshold,
    )


async def _subscribe(
    investigation: Investigation,
) -> AsyncGenerator[dict[str, str], None]:
    queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()
    subs = _subscribers.setdefault(investigation.id, [])
    subs.append(queue)
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        subs = _subscribers.get(investigation.id, [])
        if queue in subs:
            subs.remove(queue)


async def _replay_final(
    investigation: Investigation,
) -> AsyncGenerator[dict[str, str], None]:
    repo = _get_repository()

    if investigation.status == InvestigationStatus.COMPLETED:
        # Replay all stored events first (full timeline)
        stored_events = await repo.get_events(investigation.id)
        for ev in stored_events:
            yield {"event": ev["event_type"], "data": ev["event_data"]}

        candidates = [
            {
                "smiles": c.smiles,
                "name": c.name,
                "rank": c.rank,
                "notes": c.notes,
                "prediction_score": c.prediction_score,
                "docking_score": c.docking_score,
                "admet_score": c.admet_score,
                "resistance_risk": c.resistance_risk,
            }
            for c in investigation.candidates
        ]
        findings = [
            {
                "title": f.title,
                "detail": f.detail,
                "hypothesis_id": f.hypothesis_id,
                "evidence_type": f.evidence_type,
                "evidence": f.evidence,
            }
            for f in investigation.findings
        ]
        hypotheses = [
            {
                "id": h.id,
                "statement": h.statement,
                "rationale": h.rationale,
                "status": h.status.value,
                "parent_id": h.parent_id,
                "confidence": h.confidence,
                "supporting_evidence": h.supporting_evidence,
                "contradicting_evidence": h.contradicting_evidence,
            }
            for h in investigation.hypotheses
        ]
        negative_controls = [
            {
                "smiles": nc.smiles,
                "name": nc.name,
                "prediction_score": nc.prediction_score,
                "correctly_classified": nc.correctly_classified,
                "source": nc.source,
            }
            for nc in investigation.negative_controls
        ]
        data = json.dumps(
            {
                "event": SSEEventType.COMPLETED.value,
                "data": {
                    "investigation_id": investigation.id,
                    "candidate_count": len(investigation.candidates),
                    "summary": investigation.summary,
                    "cost": investigation.cost_data,
                    "candidates": candidates,
                    "findings": findings,
                    "hypotheses": hypotheses,
                    "negative_controls": negative_controls,
                    "prompt": investigation.prompt,
                },
            }
        )
        yield {"event": SSEEventType.COMPLETED.value, "data": data}
    elif investigation.status == InvestigationStatus.FAILED:
        data = json.dumps(
            {
                "event": SSEEventType.ERROR.value,
                "data": {
                    "error": investigation.error,
                    "investigation_id": investigation.id,
                },
            }
        )
        yield {"event": SSEEventType.ERROR.value, "data": data}


def _to_detail(inv: Investigation) -> InvestigationDetail:
    findings = [
        {
            "title": f.title,
            "detail": f.detail,
            "hypothesis_id": f.hypothesis_id,
            "evidence_type": f.evidence_type,
            "evidence": f.evidence,
        }
        for f in inv.findings
    ]
    candidates = [
        {
            "smiles": c.smiles,
            "name": c.name,
            "rank": c.rank,
            "notes": c.notes,
            "prediction_score": c.prediction_score,
            "docking_score": c.docking_score,
            "admet_score": c.admet_score,
            "resistance_risk": c.resistance_risk,
        }
        for c in inv.candidates
    ]
    hypotheses = [
        {
            "id": h.id,
            "statement": h.statement,
            "rationale": h.rationale,
            "status": h.status.value,
            "parent_id": h.parent_id,
            "confidence": h.confidence,
            "supporting_evidence": h.supporting_evidence,
            "contradicting_evidence": h.contradicting_evidence,
        }
        for h in inv.hypotheses
    ]
    experiments = [
        {
            "id": e.id,
            "hypothesis_id": e.hypothesis_id,
            "description": e.description,
            "tool_plan": e.tool_plan,
            "status": e.status.value,
        }
        for e in inv.experiments
    ]
    negative_controls = [
        {
            "smiles": nc.smiles,
            "name": nc.name,
            "prediction_score": nc.prediction_score,
            "correctly_classified": nc.correctly_classified,
            "source": nc.source,
        }
        for nc in inv.negative_controls
    ]
    return InvestigationDetail(
        id=inv.id,
        prompt=inv.prompt,
        status=inv.status.value,
        hypotheses=hypotheses,
        experiments=experiments,
        current_hypothesis_id=inv.current_hypothesis_id,
        current_experiment_id=inv.current_experiment_id,
        findings=findings,
        candidates=candidates,
        negative_controls=negative_controls,
        citations=inv.citations,
        summary=inv.summary,
        created_at=inv.created_at.isoformat(),
        cost_data=inv.cost_data,
    )
