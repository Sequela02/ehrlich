"""Pydantic request/response schemas and serialization helpers for investigation routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from ehrlich.investigation.domain.investigation import Investigation


# ── Request/Response Models ─────────────────────────────────────────────


class InvestigateRequest(BaseModel):
    prompt: str
    director_tier: str = "opus"
    file_ids: list[str] = []


class InvestigateResponse(BaseModel):
    id: str
    status: str


class CreditBalanceResponse(BaseModel):
    credits: int
    is_byok: bool


class ApproveRequest(BaseModel):
    approved_ids: list[str]
    rejected_ids: list[str] = []


class InvestigationSummary(BaseModel):
    id: str
    prompt: str
    status: str
    created_at: str
    candidate_count: int


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


# ── Serialization Helpers ───────────────────────────────────────────────
# Used by both _to_detail() and _replay_final() to eliminate duplication.


def serialize_candidates(investigation: Investigation) -> list[dict[str, Any]]:
    return [
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


def serialize_findings(investigation: Investigation) -> list[dict[str, Any]]:
    return [
        {
            "title": f.title,
            "detail": f.detail,
            "hypothesis_id": f.hypothesis_id,
            "evidence_type": f.evidence_type,
            "evidence": f.evidence,
        }
        for f in investigation.findings
    ]


def serialize_hypotheses(investigation: Investigation) -> list[dict[str, Any]]:
    return [
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


def serialize_negative_controls(investigation: Investigation) -> list[dict[str, Any]]:
    return [
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


def serialize_experiments(investigation: Investigation) -> list[dict[str, Any]]:
    return [
        {
            "id": e.id,
            "hypothesis_id": e.hypothesis_id,
            "description": e.description,
            "tool_plan": e.tool_plan,
            "status": e.status.value,
        }
        for e in investigation.experiments
    ]


def to_detail(investigation: Investigation) -> InvestigationDetail:
    """Convert an Investigation entity to an InvestigationDetail response."""
    return InvestigationDetail(
        id=investigation.id,
        prompt=investigation.prompt,
        status=investigation.status.value,
        hypotheses=serialize_hypotheses(investigation),
        experiments=serialize_experiments(investigation),
        current_hypothesis_id=investigation.current_hypothesis_id,
        current_experiment_id=investigation.current_experiment_id,
        findings=serialize_findings(investigation),
        candidates=serialize_candidates(investigation),
        negative_controls=serialize_negative_controls(investigation),
        citations=investigation.citations,
        summary=investigation.summary,
        created_at=investigation.created_at.isoformat(),
        cost_data=investigation.cost_data,
    )
