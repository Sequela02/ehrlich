from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ehrlich.analysis.tools import (
    analyze_substructures,
    assess_threats,
    compute_cost_effectiveness,
    compute_properties,
    estimate_did,
    estimate_psm,
    estimate_rdd,
    estimate_synthetic_control,
    explore_dataset,
    run_categorical_test,
    run_statistical_test,
    search_bioactivity,
    search_compounds,
    search_pharmacology,
)
from ehrlich.api.auth import get_current_user, get_current_user_sse
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
from ehrlich.impact.tools import (
    compare_programs,
    fetch_benchmark,
    search_economic_indicators,
)
from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.application.tool_registry import ToolRegistry
from ehrlich.investigation.domain.domain_registry import DomainRegistry
from ehrlich.investigation.domain.domains.impact import IMPACT_EVALUATION
from ehrlich.investigation.domain.domains.molecular import MOLECULAR_SCIENCE
from ehrlich.investigation.domain.domains.nutrition import NUTRITION_SCIENCE
from ehrlich.investigation.domain.domains.training import TRAINING_SCIENCE
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.mcp_config import MCPServerConfig
from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge
from ehrlich.investigation.infrastructure.repository import InvestigationRepository
from ehrlich.investigation.tools import (
    conclude_investigation,
    design_experiment,
    evaluate_hypothesis,
    propose_hypothesis,
    query_uploaded_data,
    record_finding,
    record_negative_control,
    search_prior_research,
)
from ehrlich.investigation.tools_viz import (
    render_admet_radar,
    render_binding_scatter,
    render_causal_diagram,
    render_dose_response,
    render_evidence_matrix,
    render_forest_plot,
    render_funnel_plot,
    render_geographic_comparison,
    render_muscle_heatmap,
    render_nutrient_adequacy,
    render_nutrient_comparison,
    render_parallel_trends,
    render_performance_chart,
    render_program_dashboard,
    render_rdd_plot,
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
from ehrlich.prediction.tools import (
    cluster_compounds,
    cluster_data,
    predict_candidates,
    predict_scores,
    train_classifier,
    train_model,
)
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

_require_user = Depends(get_current_user)
_require_user_sse = Depends(get_current_user_sse)

TIER_MODELS: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-5-20250929",
    "opus": "claude-opus-4-6",
}

TIER_CREDITS: dict[str, int] = {
    "haiku": 1,
    "sonnet": 3,
    "opus": 5,
}

_repository: InvestigationRepository | None = None
_active_investigations: dict[str, Investigation] = {}
_active_orchestrators: dict[str, MultiModelOrchestrator] = {}
_subscribers: dict[str, list[asyncio.Queue[dict[str, str] | None]]] = {}
# Transient per-investigation metadata (tier, credit cost, refund info)
_investigation_meta: dict[str, dict[str, Any]] = {}


class InvestigateRequest(BaseModel):
    prompt: str
    director_tier: str = "opus"
    file_ids: list[str] = []


class CreditBalanceResponse(BaseModel):
    credits: int
    is_byok: bool


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


async def init_repository(database_url: str) -> None:
    global _repository  # noqa: PLW0603
    repo = InvestigationRepository(database_url)
    await repo.initialize()
    _repository = repo


async def close_repository() -> None:
    if _repository is not None:
        await _repository.close()


def _get_repository() -> InvestigationRepository:
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
    _impact = frozenset({"impact"})
    _causal = frozenset({"causal"})
    _ml = frozenset({"ml"})
    _viz = frozenset({"visualization"})
    _chem_viz = frozenset({"chemistry", "visualization"})
    _sim_viz = frozenset({"simulation", "visualization"})
    _training_viz = frozenset({"training", "visualization"})
    _nutrition_viz = frozenset({"nutrition", "visualization"})
    _impact_viz = frozenset({"impact", "visualization"})
    _causal_viz = frozenset({"causal", "visualization"})

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
        # Prediction (3) -- molecular-specific
        ("train_model", train_model, _pred),
        ("predict_candidates", predict_candidates, _pred),
        ("cluster_compounds", cluster_compounds, _pred),
        # ML (3) -- domain-agnostic
        ("train_classifier", train_classifier, _ml),
        ("predict_scores", predict_scores, _ml),
        ("cluster_data", cluster_data, _ml),
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
        # Impact Evaluation (3)
        ("search_economic_indicators", search_economic_indicators, _impact),
        ("fetch_benchmark", fetch_benchmark, _impact),
        ("compare_programs", compare_programs, _impact),
        # Causal Inference (6) -- domain-agnostic
        ("estimate_did", estimate_did, _causal),
        ("estimate_psm", estimate_psm, _causal),
        ("estimate_rdd", estimate_rdd, _causal),
        ("estimate_synthetic_control", estimate_synthetic_control, _causal),
        ("assess_threats", assess_threats, _causal),
        ("compute_cost_effectiveness", compute_cost_effectiveness, _causal),
        # Visualization (17)
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
        ("render_program_dashboard", render_program_dashboard, _impact_viz),
        ("render_geographic_comparison", render_geographic_comparison, _impact_viz),
        ("render_parallel_trends", render_parallel_trends, _impact_viz),
        ("render_rdd_plot", render_rdd_plot, _causal_viz),
        ("render_causal_diagram", render_causal_diagram, _causal_viz),
        # Statistics (2) -- universal, no tags
        ("run_statistical_test", run_statistical_test, None),
        ("run_categorical_test", run_categorical_test, None),
        # Investigation control (7) -- universal, no tags
        ("record_finding", record_finding, None),
        ("conclude_investigation", conclude_investigation, None),
        ("propose_hypothesis", propose_hypothesis, None),
        ("design_experiment", design_experiment, None),
        ("evaluate_hypothesis", evaluate_hypothesis, None),
        ("record_negative_control", record_negative_control, None),
        ("search_prior_research", search_prior_research, None),
        ("query_uploaded_data", query_uploaded_data, None),
    ]
    for name, func, tags in tagged_tools:
        registry.register(name, func, tags)
    return registry


def _build_domain_registry() -> DomainRegistry:
    domain_registry = DomainRegistry()
    domain_registry.register(MOLECULAR_SCIENCE)
    domain_registry.register(TRAINING_SCIENCE)
    domain_registry.register(NUTRITION_SCIENCE)
    domain_registry.register(IMPACT_EVALUATION)
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
async def list_investigations(
    user: dict[str, Any] = _require_user,
) -> list[InvestigationSummary]:
    repo = _get_repository()
    db_user = await repo.get_or_create_user(user["workos_id"], user["email"])
    investigations = await repo.list_by_user(str(db_user["id"]))
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


@router.get("/credits/balance")
async def get_credit_balance(
    request: Request,
    user: dict[str, Any] = _require_user,
) -> CreditBalanceResponse:
    repo = _get_repository()
    credits = await repo.get_user_credits(user["workos_id"])
    is_byok = bool(request.headers.get("X-Anthropic-Key"))
    return CreditBalanceResponse(credits=credits, is_byok=is_byok)


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
async def start_investigation(
    request: InvestigateRequest,
    http_request: Request,
    user: dict[str, Any] = _require_user,
) -> InvestigateResponse:
    tier = request.director_tier
    if tier not in TIER_CREDITS:
        raise HTTPException(status_code=400, detail=f"Invalid director tier: {tier}")

    is_byok = bool(http_request.headers.get("X-Anthropic-Key"))
    credit_cost = TIER_CREDITS[tier]

    investigation = Investigation(prompt=request.prompt)
    repo = _get_repository()
    db_user = await repo.get_or_create_user(user["workos_id"], user["email"])

    # Save investigation first (credit_transactions FK references investigations)
    await repo.save(investigation, user_id=str(db_user["id"]))

    # Attach uploaded files
    if request.file_ids:
        from ehrlich.api.routes.upload import get_pending_upload

        for fid in request.file_ids:
            uploaded = get_pending_upload(fid)
            if uploaded:
                investigation.uploaded_files.append(uploaded)
                await repo.save_uploaded_file(investigation.id, uploaded)

    if not is_byok:
        deducted = await repo.deduct_credits(user["workos_id"], credit_cost, investigation.id)
        if not deducted:
            raise HTTPException(status_code=402, detail="Insufficient credits")

    _investigation_meta[investigation.id] = {
        "tier": tier,
        "credit_cost": credit_cost if not is_byok else 0,
        "workos_id": user["workos_id"],
        "is_byok": is_byok,
    }

    return InvestigateResponse(id=investigation.id, status=investigation.status.value)


class ApproveRequest(BaseModel):
    approved_ids: list[str]
    rejected_ids: list[str] = []


@router.post("/investigate/{investigation_id}/approve")
async def approve_hypotheses(
    investigation_id: str,
    request: ApproveRequest,
    user: dict[str, Any] = _require_user,
) -> dict[str, str]:
    orchestrator = _active_orchestrators.get(investigation_id)
    if orchestrator is None:
        raise HTTPException(status_code=404, detail="No active orchestrator")
    orchestrator.approve_hypotheses(request.approved_ids, request.rejected_ids)
    return {"status": "approved"}


@router.get("/investigate/{investigation_id}/stream")
async def stream_investigation(
    investigation_id: str,
    request: Request,
    user: dict[str, Any] = _require_user_sse,
) -> EventSourceResponse:
    repo = _get_repository()
    investigation = _active_investigations.get(investigation_id)
    if investigation is None:
        investigation = await repo.get_by_id(investigation_id)
        if investigation is not None:
            investigation.uploaded_files = await repo.get_uploaded_files(investigation.id)
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

    # BYOK: check for user-provided API key
    api_key_override = request.headers.get("X-Anthropic-Key") or None

    # Read tier from investigation meta (set during POST /investigate)
    meta = _investigation_meta.get(investigation.id, {})
    tier = meta.get("tier", "opus")
    director_model_override = TIER_MODELS.get(tier)

    _active_investigations[investigation.id] = investigation
    _subscribers[investigation.id] = []

    orchestrator = _create_orchestrator(
        settings,
        registry,
        repo,
        domain_registry,
        mcp_bridge,
        mcp_configs,
        api_key_override=api_key_override,
        director_model_override=director_model_override,
    )
    _active_orchestrators[investigation.id] = orchestrator

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        failed = False
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
        except Exception:
            failed = True
            raise
        finally:
            _end_broadcast(investigation.id)
            await repo.update(investigation)
            _active_investigations.pop(investigation.id, None)
            _active_orchestrators.pop(investigation.id, None)

            # Refund credits on failure (not for BYOK)
            if failed or investigation.status == InvestigationStatus.FAILED:
                credit_cost = meta.get("credit_cost", 0)
                workos_id = meta.get("workos_id")
                if credit_cost > 0 and workos_id:
                    await repo.refund_credits(workos_id, credit_cost, investigation.id)

            _investigation_meta.pop(investigation.id, None)

    return EventSourceResponse(event_generator())


def _create_orchestrator(
    settings: Any,
    registry: ToolRegistry,
    repository: InvestigationRepository,
    domain_registry: DomainRegistry | None = None,
    mcp_bridge: MCPBridge | None = None,
    mcp_configs: list[MCPServerConfig] | None = None,
    api_key_override: str | None = None,
    director_model_override: str | None = None,
) -> MultiModelOrchestrator:
    api_key = api_key_override or settings.anthropic_api_key or None

    director_model = director_model_override or settings.director_model

    # effort is only supported by Opus models (4.5+)
    director_effort = settings.director_effort if "opus" in director_model else None

    thinking = None
    if settings.director_thinking == "enabled":
        thinking = {
            "type": "enabled",
            "budget_tokens": settings.director_thinking_budget,
        }

    director = AnthropicClientAdapter(
        model=director_model,
        api_key=api_key,
        max_tokens=32768,
        effort=director_effort,
        thinking=thinking,
    )
    researcher = AnthropicClientAdapter(
        model=settings.researcher_model,
        api_key=api_key,
    )
    summarizer = AnthropicClientAdapter(
        model=settings.summarizer_model,
        api_key=api_key,
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
