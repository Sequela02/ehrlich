from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from ehrlich.api.auth import get_current_user, get_current_user_sse
from ehrlich.api.schemas.investigation import (
    ApproveRequest,
    CreditBalanceResponse,
    InvestigateRequest,
    InvestigateResponse,
    InvestigationDetail,
    InvestigationSummary,
    serialize_candidates,
    serialize_findings,
    serialize_hypotheses,
    serialize_negative_controls,
    to_detail,
)
from ehrlich.api.sse import SSEEventType, domain_event_to_sse
from ehrlich.config import get_settings
from ehrlich.investigation.application.orchestrator_factory import create_orchestrator
from ehrlich.investigation.application.registry_factory import (
    build_domain_registry,
    build_mcp_configs,
    build_tool_registry,
)
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge
from ehrlich.investigation.infrastructure.repository import InvestigationRepository

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator

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


def _broadcast_event(investigation_id: str, event: dict[str, str]) -> None:
    for queue in _subscribers.get(investigation_id, []):
        queue.put_nowait(event)


def _end_broadcast(investigation_id: str) -> None:
    for queue in _subscribers.get(investigation_id, []):
        queue.put_nowait(None)
    _subscribers.pop(investigation_id, None)


# ── Route Handlers ──────────────────────────────────────────────────────


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
    return to_detail(investigation)


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
    registry = build_tool_registry()
    domain_registry = build_domain_registry()
    mcp_configs = build_mcp_configs()
    mcp_bridge = MCPBridge() if mcp_configs else None

    # BYOK: check for user-provided API key
    api_key_override = request.headers.get("X-Anthropic-Key") or None

    # Read tier from investigation meta (set during POST /investigate)
    meta = _investigation_meta.get(investigation.id, {})
    tier = meta.get("tier", "opus")
    director_model_override = TIER_MODELS.get(tier)

    _active_investigations[investigation.id] = investigation
    _subscribers[investigation.id] = []

    orchestrator = create_orchestrator(
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


# ── SSE Helpers ─────────────────────────────────────────────────────────


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

        data = json.dumps(
            {
                "event": SSEEventType.COMPLETED.value,
                "data": {
                    "investigation_id": investigation.id,
                    "candidate_count": len(investigation.candidates),
                    "summary": investigation.summary,
                    "cost": investigation.cost_data,
                    "candidates": serialize_candidates(investigation),
                    "findings": serialize_findings(investigation),
                    "hypotheses": serialize_hypotheses(investigation),
                    "negative_controls": serialize_negative_controls(investigation),
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
