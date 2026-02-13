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
from ehrlich.investigation.domain.domain_registry import DomainRegistry
from ehrlich.investigation.domain.domains.molecular import MOLECULAR_SCIENCE
from ehrlich.investigation.domain.domains.nutrition import NUTRITION_SCIENCE
from ehrlich.investigation.domain.domains.training import TRAINING_SCIENCE
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.mcp_config import MCPServerConfig
from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge
from ehrlich.investigation.infrastructure.sqlite_repository import SqliteInvestigationRepository
from ehrlich.investigation.tools import (
    conclude_investigation,
    design_experiment,
    evaluate_hypothesis,
    propose_hypothesis,
    record_finding,
    record_negative_control,
    search_prior_research,
)
from ehrlich.investigation.tools_viz import (
    render_admet_radar,
    render_binding_scatter,
    render_dose_response,
    render_evidence_matrix,
    render_forest_plot,
    render_funnel_plot,
    render_muscle_heatmap,
    render_nutrient_adequacy,
    render_nutrient_comparison,
    render_performance_chart,
    render_therapeutic_window,
    render_training_timeline,
)
from ehrlich.literature.tools import get_reference, search_citations, search_literature
from ehrlich.nutrition.tools import (
    analyze_nutrient_ratios,
    assess_nutrient_adequacy,
    check_intake_safety,
    check_interactions,
    compare_nutrients,
    compute_inflammatory_index,
    search_nutrient_data,
    search_supplement_evidence,
    search_supplement_labels,
    search_supplement_safety,
)
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
from ehrlich.training.tools import (
    analyze_training_evidence,
    assess_injury_risk,
    compare_protocols,
    compute_dose_response,
    compute_performance_model,
    compute_training_metrics,
    plan_periodization,
    search_clinical_trials,
    search_exercise_database,
    search_pubmed_training,
    search_training_literature,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["investigation"])

_repository: SqliteInvestigationRepository | None = None
_active_investigations: dict[str, Investigation] = {}
_active_orchestrators: dict[str, MultiModelOrchestrator] = {}
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
    _chem = frozenset({"chemistry"})
    _lit = frozenset({"literature"})
    _analysis = frozenset({"analysis"})
    _pred = frozenset({"prediction"})
    _sim = frozenset({"simulation"})
    _training = frozenset({"training"})
    _training_clinical = frozenset({"training", "clinical"})
    _training_exercise = frozenset({"training", "exercise"})
    _nutrition = frozenset({"nutrition"})
    _nutrition_safety = frozenset({"nutrition", "safety"})
    _viz = frozenset({"visualization"})
    _chem_viz = frozenset({"chemistry", "visualization"})
    _sim_viz = frozenset({"simulation", "visualization"})
    _training_viz = frozenset({"training", "visualization"})
    _nutrition_viz = frozenset({"nutrition", "visualization"})

    tagged_tools: list[tuple[str, Any, frozenset[str] | None]] = [
        # Chemistry (6)
        ("validate_smiles", validate_smiles, _chem),
        ("compute_descriptors", compute_descriptors, _chem),
        ("compute_fingerprint", compute_fingerprint, _chem),
        ("tanimoto_similarity", tanimoto_similarity, _chem),
        ("generate_3d", generate_3d, _chem),
        ("substructure_match", substructure_match, _chem),
        # Literature (3)
        ("search_literature", search_literature, _lit),
        ("get_reference", get_reference, _lit),
        ("search_citations", search_citations, _lit),
        # Analysis (6)
        ("explore_dataset", explore_dataset, _analysis),
        ("search_compounds", search_compounds, _analysis),
        ("search_bioactivity", search_bioactivity, _analysis),
        ("analyze_substructures", analyze_substructures, _analysis),
        ("compute_properties", compute_properties, _analysis),
        ("search_pharmacology", search_pharmacology, _analysis),
        # Prediction (3)
        ("train_model", train_model, _pred),
        ("predict_candidates", predict_candidates, _pred),
        ("cluster_compounds", cluster_compounds, _pred),
        # Simulation (7)
        ("search_protein_targets", search_protein_targets, _sim),
        ("dock_against_target", dock_against_target, _sim),
        ("predict_admet", predict_admet, _sim),
        ("fetch_toxicity_profile", fetch_toxicity_profile, _sim),
        ("assess_resistance", assess_resistance, _sim),
        ("get_protein_annotation", get_protein_annotation, _sim),
        ("search_disease_targets", search_disease_targets, _sim),
        # Training Science (11)
        ("search_training_literature", search_training_literature, _training),
        ("analyze_training_evidence", analyze_training_evidence, _training),
        ("compare_protocols", compare_protocols, _training),
        ("assess_injury_risk", assess_injury_risk, _training),
        ("compute_training_metrics", compute_training_metrics, _training),
        ("search_clinical_trials", search_clinical_trials, _training_clinical),
        ("search_pubmed_training", search_pubmed_training, _training),
        ("search_exercise_database", search_exercise_database, _training_exercise),
        ("compute_performance_model", compute_performance_model, _training),
        ("compute_dose_response", compute_dose_response, _training),
        ("plan_periodization", plan_periodization, _training_exercise),
        # Nutrition Science (10)
        ("search_supplement_evidence", search_supplement_evidence, _nutrition),
        ("search_supplement_labels", search_supplement_labels, _nutrition),
        ("search_nutrient_data", search_nutrient_data, _nutrition),
        ("search_supplement_safety", search_supplement_safety, _nutrition_safety),
        ("compare_nutrients", compare_nutrients, _nutrition),
        ("assess_nutrient_adequacy", assess_nutrient_adequacy, _nutrition),
        ("check_intake_safety", check_intake_safety, _nutrition_safety),
        ("check_interactions", check_interactions, _nutrition_safety),
        ("analyze_nutrient_ratios", analyze_nutrient_ratios, _nutrition),
        ("compute_inflammatory_index", compute_inflammatory_index, _nutrition),
        # Visualization (12)
        ("render_binding_scatter", render_binding_scatter, _chem_viz),
        ("render_admet_radar", render_admet_radar, _sim_viz),
        ("render_training_timeline", render_training_timeline, _training_viz),
        ("render_muscle_heatmap", render_muscle_heatmap, _training_viz),
        ("render_forest_plot", render_forest_plot, _viz),
        ("render_evidence_matrix", render_evidence_matrix, _viz),
        ("render_performance_chart", render_performance_chart, _training_viz),
        ("render_funnel_plot", render_funnel_plot, _viz),
        ("render_dose_response", render_dose_response, _training_viz),
        ("render_nutrient_comparison", render_nutrient_comparison, _nutrition_viz),
        ("render_nutrient_adequacy", render_nutrient_adequacy, _nutrition_viz),
        ("render_therapeutic_window", render_therapeutic_window, _nutrition_viz),
        # Investigation control (7) -- universal, no tags
        ("record_finding", record_finding, None),
        ("conclude_investigation", conclude_investigation, None),
        ("propose_hypothesis", propose_hypothesis, None),
        ("design_experiment", design_experiment, None),
        ("evaluate_hypothesis", evaluate_hypothesis, None),
        ("record_negative_control", record_negative_control, None),
        ("search_prior_research", search_prior_research, None),
    ]
    for name, func, tags in tagged_tools:
        registry.register(name, func, tags)
    return registry


def _build_domain_registry() -> DomainRegistry:
    domain_registry = DomainRegistry()
    domain_registry.register(MOLECULAR_SCIENCE)
    domain_registry.register(TRAINING_SCIENCE)
    domain_registry.register(NUTRITION_SCIENCE)
    return domain_registry


def _build_mcp_configs() -> list[MCPServerConfig]:
    """Build MCP server configs from environment. Currently supports Excalidraw."""
    import os

    configs: list[MCPServerConfig] = []
    if os.environ.get("EHRLICH_MCP_EXCALIDRAW", "").lower() in ("1", "true"):
        configs.append(
            MCPServerConfig(
                name="excalidraw",
                transport="stdio",
                command="npx",
                args=("-y", "@anthropic/claude-code-mcp", "excalidraw"),
                tags=frozenset({"visualization"}),
            )
        )
    return configs


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


class ApproveRequest(BaseModel):
    approved_ids: list[str]
    rejected_ids: list[str] = []


@router.post("/investigate/{investigation_id}/approve")
async def approve_hypotheses(
    investigation_id: str,
    request: ApproveRequest,
) -> dict[str, str]:
    orchestrator = _active_orchestrators.get(investigation_id)
    if orchestrator is None:
        raise HTTPException(status_code=404, detail="No active orchestrator")
    orchestrator.approve_hypotheses(request.approved_ids, request.rejected_ids)
    return {"status": "approved"}


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
    domain_registry = _build_domain_registry()
    mcp_configs = _build_mcp_configs()
    mcp_bridge = MCPBridge() if mcp_configs else None

    _active_investigations[investigation.id] = investigation
    _subscribers[investigation.id] = []

    orchestrator = _create_orchestrator(
        settings,
        registry,
        repo,
        domain_registry,
        mcp_bridge,
        mcp_configs,
    )
    _active_orchestrators[investigation.id] = orchestrator

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
                        SSEEventType.HYPOTHESIS_APPROVAL_REQUESTED,
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
            _active_orchestrators.pop(investigation.id, None)

    return EventSourceResponse(event_generator())


def _create_orchestrator(
    settings: Any,
    registry: ToolRegistry,
    repository: SqliteInvestigationRepository,
    domain_registry: DomainRegistry | None = None,
    mcp_bridge: MCPBridge | None = None,
    mcp_configs: list[MCPServerConfig] | None = None,
) -> MultiModelOrchestrator:
    api_key = settings.anthropic_api_key or None

    thinking = None
    if settings.director_thinking == "enabled":
        thinking = {
            "type": "enabled",
            "budget_tokens": settings.director_thinking_budget,
        }

    director = AnthropicClientAdapter(
        model=settings.director_model,
        api_key=api_key,
        max_tokens=32768,
        effort=settings.director_effort,
        thinking=thinking,
    )
    researcher = AnthropicClientAdapter(
        model=settings.researcher_model,
        api_key=api_key,
        effort=settings.researcher_effort,
    )
    summarizer = AnthropicClientAdapter(
        model=settings.summarizer_model,
        api_key=api_key,
        effort=settings.summarizer_effort,
    )
    return MultiModelOrchestrator(
        director=director,
        researcher=researcher,
        summarizer=summarizer,
        registry=registry,
        max_iterations_per_experiment=settings.max_iterations_per_experiment,
        summarizer_threshold=settings.summarizer_threshold,
        require_approval=True,
        repository=repository,
        domain_registry=domain_registry,
        mcp_bridge=mcp_bridge,
        mcp_configs=mcp_configs,
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
                "identifier": c.identifier,
                "identifier_type": c.identifier_type,
                "name": c.name,
                "rank": c.rank,
                "notes": c.notes,
                "scores": c.scores,
                "attributes": c.attributes,
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
                "identifier": nc.identifier,
                "identifier_type": nc.identifier_type,
                "name": nc.name,
                "score": nc.score,
                "threshold": nc.threshold,
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
            "identifier": c.identifier,
            "identifier_type": c.identifier_type,
            "name": c.name,
            "rank": c.rank,
            "notes": c.notes,
            "scores": c.scores,
            "attributes": c.attributes,
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
            "identifier": nc.identifier,
            "identifier_type": nc.identifier_type,
            "name": nc.name,
            "score": nc.score,
            "threshold": nc.threshold,
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
