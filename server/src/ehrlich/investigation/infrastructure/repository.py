from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import asyncpg

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.domain.repository import InvestigationRepository as _Base

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workos_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    credits INTEGER NOT NULL DEFAULT 5,
    encrypted_api_key BYTEA,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    domain TEXT NOT NULL DEFAULT '',
    hypotheses JSONB NOT NULL DEFAULT '[]',
    experiments JSONB NOT NULL DEFAULT '[]',
    current_hypothesis_id TEXT NOT NULL DEFAULT '',
    current_experiment_id TEXT NOT NULL DEFAULT '',
    findings JSONB NOT NULL DEFAULT '[]',
    candidates JSONB NOT NULL DEFAULT '[]',
    negative_controls JSONB NOT NULL DEFAULT '[]',
    citations JSONB NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    iteration INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    cost_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id),
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    type TEXT NOT NULL,
    investigation_id TEXT REFERENCES investigations(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$ BEGIN
    ALTER TABLE investigations ADD COLUMN IF NOT EXISTS findings_search tsvector;
EXCEPTION WHEN others THEN NULL;
END $$;

CREATE INDEX IF NOT EXISTS idx_findings_fts ON investigations USING GIN(findings_search);
CREATE INDEX IF NOT EXISTS idx_investigations_user ON investigations(user_id);
CREATE INDEX IF NOT EXISTS idx_events_investigation ON events(investigation_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user ON credit_transactions(user_id);
"""


class InvestigationRepository(_Base):
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: asyncpg.Pool[asyncpg.Record] | None = None

    async def initialize(self) -> None:
        await self._ensure_database()
        self._pool = await asyncpg.create_pool(self._database_url, min_size=2, max_size=10)
        async with self._pool.acquire() as conn:
            await conn.execute(_SCHEMA)
        logger.info("PostgreSQL repository initialized")

    async def _ensure_database(self) -> None:
        """Create the database if it doesn't exist."""
        from urllib.parse import urlparse

        parsed = urlparse(self._database_url)
        db_name = parsed.path.lstrip("/")
        maintenance_url = self._database_url.rsplit("/", 1)[0] + "/postgres"

        try:
            conn = await asyncpg.connect(maintenance_url)
            try:
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info("Created database %s", db_name)
            except asyncpg.DuplicateDatabaseError:
                pass
            finally:
                await conn.close()
        except Exception:
            logger.debug("Could not auto-create database, assuming it exists")

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _get_pool(self) -> asyncpg.Pool[asyncpg.Record]:
        if self._pool is None:
            msg = "PostgreSQL pool not initialized"
            raise RuntimeError(msg)
        return self._pool

    async def save(self, investigation: Investigation, *, user_id: str | None = None) -> None:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO investigations
                   (id, user_id, prompt, status, hypotheses, experiments,
                    current_hypothesis_id, current_experiment_id,
                    findings, candidates, negative_controls,
                    citations, summary, domain, iteration, error, created_at, cost_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                           $11, $12, $13, $14, $15, $16, $17, $18)""",
                investigation.id,
                user_id,
                investigation.prompt,
                investigation.status.value,
                json.dumps([_hypothesis_to_dict(h) for h in investigation.hypotheses]),
                json.dumps([_experiment_to_dict(e) for e in investigation.experiments]),
                investigation.current_hypothesis_id,
                investigation.current_experiment_id,
                json.dumps([_finding_to_dict(f) for f in investigation.findings]),
                json.dumps([_candidate_to_dict(c) for c in investigation.candidates]),
                json.dumps(
                    [_negative_control_to_dict(nc) for nc in investigation.negative_controls]
                ),
                json.dumps(investigation.citations),
                investigation.summary,
                investigation.domain,
                investigation.iteration,
                investigation.error,
                investigation.created_at,
                json.dumps(investigation.cost_data),
            )

    async def get_by_id(self, investigation_id: str) -> Investigation | None:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM investigations WHERE id = $1", investigation_id
            )
            if row is None:
                return None
            return _from_row(row)

    async def list_all(self) -> list[Investigation]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM investigations ORDER BY created_at DESC")
            return [_from_row(row) for row in rows]

    async def list_by_user(self, user_id: str) -> list[Investigation]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM investigations WHERE user_id = $1 ORDER BY created_at DESC",
                user_id,
            )
            return [_from_row(row) for row in rows]

    async def update(self, investigation: Investigation) -> None:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE investigations SET
                   status=$1, hypotheses=$2, experiments=$3,
                   current_hypothesis_id=$4, current_experiment_id=$5,
                   findings=$6, candidates=$7, negative_controls=$8,
                   citations=$9, summary=$10, domain=$11, iteration=$12,
                   error=$13, cost_data=$14
                   WHERE id=$15""",
                investigation.status.value,
                json.dumps([_hypothesis_to_dict(h) for h in investigation.hypotheses]),
                json.dumps([_experiment_to_dict(e) for e in investigation.experiments]),
                investigation.current_hypothesis_id,
                investigation.current_experiment_id,
                json.dumps([_finding_to_dict(f) for f in investigation.findings]),
                json.dumps([_candidate_to_dict(c) for c in investigation.candidates]),
                json.dumps(
                    [_negative_control_to_dict(nc) for nc in investigation.negative_controls]
                ),
                json.dumps(investigation.citations),
                investigation.summary,
                investigation.domain,
                investigation.iteration,
                investigation.error,
                json.dumps(investigation.cost_data),
                investigation.id,
            )
            if investigation.status == InvestigationStatus.COMPLETED:
                await self._rebuild_fts(conn, investigation)

    async def save_event(self, investigation_id: str, event_type: str, event_data: str) -> None:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO events (investigation_id, event_type, event_data) VALUES ($1, $2, $3)",
                investigation_id,
                event_type,
                event_data,
            )

    async def get_events(self, investigation_id: str) -> list[dict[str, str]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT event_type, event_data FROM events "
                "WHERE investigation_id = $1 ORDER BY id ASC",
                investigation_id,
            )
            return [
                {
                    "event_type": row["event_type"],
                    "event_data": (
                        row["event_data"]
                        if isinstance(row["event_data"], str)
                        else json.dumps(row["event_data"])
                    ),
                }
                for row in rows
            ]

    async def search_findings(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, prompt, findings, hypotheses,
                          ts_rank(findings_search, plainto_tsquery('english', $1)) AS rank
                   FROM investigations
                   WHERE findings_search @@ plainto_tsquery('english', $1)
                   ORDER BY rank DESC
                   LIMIT $2""",
                query,
                limit,
            )
            results: list[dict[str, Any]] = []
            for row in rows:
                findings_data = row["findings"]
                if isinstance(findings_data, str):
                    findings_data = json.loads(findings_data)
                hypotheses_data = row["hypotheses"]
                if isinstance(hypotheses_data, str):
                    hypotheses_data = json.loads(hypotheses_data)
                hyp_map = {h["id"]: h for h in hypotheses_data}
                for f in findings_data:
                    hyp = hyp_map.get(f.get("hypothesis_id", ""), {})
                    results.append(
                        {
                            "investigation_id": row["id"],
                            "investigation_prompt": row["prompt"],
                            "finding_title": f.get("title", ""),
                            "finding_detail": f.get("detail", ""),
                            "evidence_type": f.get("evidence_type", ""),
                            "hypothesis_statement": hyp.get("statement", ""),
                            "hypothesis_status": hyp.get("status", ""),
                            "source_type": f.get("source_type", ""),
                            "source_id": f.get("source_id", ""),
                            "rank": row["rank"],
                        }
                    )
            return results[:limit]

    # -- User management (PostgreSQL-specific, not on ABC) -------------------------

    async def get_or_create_user(self, workos_id: str, email: str) -> dict[str, Any]:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, workos_id, email, credits, created_at FROM users WHERE workos_id = $1",
                workos_id,
            )
            if row is not None:
                return dict(row)
            row = await conn.fetchrow(
                "INSERT INTO users (workos_id, email) VALUES ($1, $2) "
                "RETURNING id, workos_id, email, credits, created_at",
                workos_id,
                email,
            )
            assert row is not None  # noqa: S101
            return dict(row)

    async def get_user_credits(self, workos_id: str) -> int:
        pool = self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT credits FROM users WHERE workos_id = $1", workos_id)
            if row is None:
                return 0
            return int(row["credits"])

    async def deduct_credits(self, workos_id: str, amount: int, investigation_id: str) -> bool:
        pool = self._get_pool()
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                "UPDATE users SET credits = credits - $1 "
                "WHERE workos_id = $2 AND credits >= $1 "
                "RETURNING id",
                amount,
                workos_id,
            )
            if row is None:
                return False
            await conn.execute(
                "INSERT INTO credit_transactions "
                "(user_id, amount, type, investigation_id) "
                "VALUES ($1, $2, $3, $4)",
                row["id"],
                -amount,
                "deduction",
                investigation_id,
            )
            return True

    async def refund_credits(self, workos_id: str, amount: int, investigation_id: str) -> None:
        pool = self._get_pool()
        async with pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                "UPDATE users SET credits = credits + $1 WHERE workos_id = $2 RETURNING id",
                amount,
                workos_id,
            )
            if row is not None:
                await conn.execute(
                    "INSERT INTO credit_transactions "
                    "(user_id, amount, type, investigation_id) "
                    "VALUES ($1, $2, $3, $4)",
                    row["id"],
                    amount,
                    "refund",
                    investigation_id,
                )

    # -- Private helpers -----------------------------------------------------------

    async def _rebuild_fts(
        self, conn: asyncpg.Connection[asyncpg.Record], investigation: Investigation
    ) -> None:
        hypothesis_map = {h.id: h for h in investigation.hypotheses}
        parts: list[str] = []
        for finding in investigation.findings:
            hyp = hypothesis_map.get(finding.hypothesis_id)
            parts.extend(
                [
                    finding.title,
                    finding.detail,
                    finding.evidence_type,
                    hyp.statement if hyp else "",
                    hyp.status.value if hyp else "",
                    finding.source_type,
                    finding.source_id,
                ]
            )
        text = " ".join(parts)
        await conn.execute(
            "UPDATE investigations SET findings_search = to_tsvector('english', $1) WHERE id = $2",
            text,
            investigation.id,
        )


def _hypothesis_to_dict(h: Hypothesis) -> dict[str, Any]:
    return {
        "id": h.id,
        "statement": h.statement,
        "rationale": h.rationale,
        "prediction": h.prediction,
        "null_prediction": h.null_prediction,
        "success_criteria": h.success_criteria,
        "failure_criteria": h.failure_criteria,
        "scope": h.scope,
        "hypothesis_type": h.hypothesis_type,
        "prior_confidence": h.prior_confidence,
        "status": h.status.value,
        "parent_id": h.parent_id,
        "confidence": h.confidence,
        "certainty_of_evidence": h.certainty_of_evidence,
        "supporting_evidence": h.supporting_evidence,
        "contradicting_evidence": h.contradicting_evidence,
    }


def _experiment_to_dict(e: Experiment) -> dict[str, Any]:
    return {
        "id": e.id,
        "hypothesis_id": e.hypothesis_id,
        "description": e.description,
        "tool_plan": e.tool_plan,
        "status": e.status.value,
        "result_summary": e.result_summary,
        "supports_hypothesis": e.supports_hypothesis,
        "independent_variable": e.independent_variable,
        "dependent_variable": e.dependent_variable,
        "controls": e.controls,
        "confounders": e.confounders,
        "analysis_plan": e.analysis_plan,
        "success_criteria": e.success_criteria,
        "failure_criteria": e.failure_criteria,
    }


def _finding_to_dict(f: Finding) -> dict[str, Any]:
    return {
        "title": f.title,
        "detail": f.detail,
        "evidence": f.evidence,
        "hypothesis_id": f.hypothesis_id,
        "evidence_type": f.evidence_type,
        "confidence": f.confidence,
        "source_type": f.source_type,
        "source_id": f.source_id,
        "evidence_level": f.evidence_level,
    }


def _negative_control_to_dict(nc: NegativeControl) -> dict[str, Any]:
    return {
        "identifier": nc.identifier,
        "identifier_type": nc.identifier_type,
        "name": nc.name,
        "score": nc.score,
        "threshold": nc.threshold,
        "expected_inactive": nc.expected_inactive,
        "source": nc.source,
    }


def _candidate_to_dict(c: Candidate) -> dict[str, Any]:
    return {
        "identifier": c.identifier,
        "identifier_type": c.identifier_type,
        "name": c.name,
        "rank": c.rank,
        "notes": c.notes,
        "scores": c.scores,
        "attributes": c.attributes,
    }


def _from_row(row: asyncpg.Record) -> Investigation:
    hypotheses_raw = row["hypotheses"]
    if isinstance(hypotheses_raw, str):
        hypotheses_raw = json.loads(hypotheses_raw)
    hypotheses = [
        Hypothesis(
            statement=h["statement"],
            rationale=h.get("rationale", ""),
            id=h["id"],
            status=HypothesisStatus(h.get("status", "proposed")),
            parent_id=h.get("parent_id", ""),
            prediction=h.get("prediction", ""),
            null_prediction=h.get("null_prediction", ""),
            success_criteria=h.get("success_criteria", ""),
            failure_criteria=h.get("failure_criteria", ""),
            scope=h.get("scope", ""),
            hypothesis_type=h.get("hypothesis_type", ""),
            prior_confidence=h.get("prior_confidence", 0.0),
            confidence=h.get("confidence", 0.0),
            certainty_of_evidence=h.get("certainty_of_evidence", ""),
            supporting_evidence=h.get("supporting_evidence", []),
            contradicting_evidence=h.get("contradicting_evidence", []),
        )
        for h in hypotheses_raw
    ]

    experiments_raw = row["experiments"]
    if isinstance(experiments_raw, str):
        experiments_raw = json.loads(experiments_raw)
    experiments = [
        Experiment(
            hypothesis_id=e["hypothesis_id"],
            description=e["description"],
            id=e["id"],
            tool_plan=e.get("tool_plan", []),
            status=ExperimentStatus(e.get("status", "planned")),
            result_summary=e.get("result_summary", ""),
            supports_hypothesis=e.get("supports_hypothesis"),
            independent_variable=e.get("independent_variable", ""),
            dependent_variable=e.get("dependent_variable", ""),
            controls=e.get("controls", []),
            confounders=e.get("confounders", []),
            analysis_plan=e.get("analysis_plan", ""),
            success_criteria=e.get("success_criteria", ""),
            failure_criteria=e.get("failure_criteria", ""),
        )
        for e in experiments_raw
    ]

    findings_raw = row["findings"]
    if isinstance(findings_raw, str):
        findings_raw = json.loads(findings_raw)
    findings = [
        Finding(
            title=f["title"],
            detail=f["detail"],
            evidence=f.get("evidence", ""),
            hypothesis_id=f.get("hypothesis_id", ""),
            evidence_type=f.get("evidence_type", "neutral"),
            confidence=f.get("confidence", 0.0),
            source_type=f.get("source_type", ""),
            source_id=f.get("source_id", ""),
            evidence_level=f.get("evidence_level", 0),
        )
        for f in findings_raw
    ]

    negative_controls_raw = row["negative_controls"]
    if isinstance(negative_controls_raw, str):
        negative_controls_raw = json.loads(negative_controls_raw)
    negative_controls = [
        NegativeControl(
            identifier=nc["identifier"],
            identifier_type=nc.get("identifier_type", ""),
            name=nc.get("name", ""),
            score=nc.get("score", 0.0),
            threshold=nc.get("threshold", 0.5),
            expected_inactive=nc.get("expected_inactive", True),
            source=nc.get("source", ""),
        )
        for nc in negative_controls_raw
    ]

    candidates_raw = row["candidates"]
    if isinstance(candidates_raw, str):
        candidates_raw = json.loads(candidates_raw)
    candidates = [
        Candidate(
            identifier=c["identifier"],
            identifier_type=c.get("identifier_type", ""),
            name=c.get("name", ""),
            rank=c.get("rank", 0),
            notes=c.get("notes", ""),
            scores=c.get("scores", {}),
            attributes=c.get("attributes", {}),
        )
        for c in candidates_raw
    ]

    citations_raw = row["citations"]
    if isinstance(citations_raw, str):
        citations_raw = json.loads(citations_raw)

    cost_data_raw = row["cost_data"]
    if isinstance(cost_data_raw, str):
        cost_data_raw = json.loads(cost_data_raw)

    created_at = row["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    return Investigation(
        id=row["id"],
        prompt=row["prompt"],
        status=InvestigationStatus(row["status"]),
        hypotheses=hypotheses,
        experiments=experiments,
        current_hypothesis_id=row["current_hypothesis_id"],
        current_experiment_id=row["current_experiment_id"],
        findings=findings,
        candidates=candidates,
        negative_controls=negative_controls,
        citations=citations_raw,
        summary=row["summary"],
        domain=row["domain"],
        iteration=row["iteration"],
        error=row["error"],
        created_at=created_at,
        cost_data=cost_data_raw,
    )
