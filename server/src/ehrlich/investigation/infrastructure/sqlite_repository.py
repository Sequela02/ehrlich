from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.domain.repository import InvestigationRepository

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    hypotheses TEXT NOT NULL DEFAULT '[]',
    experiments TEXT NOT NULL DEFAULT '[]',
    current_hypothesis_id TEXT NOT NULL DEFAULT '',
    current_experiment_id TEXT NOT NULL DEFAULT '',
    findings TEXT NOT NULL DEFAULT '[]',
    candidates TEXT NOT NULL DEFAULT '[]',
    negative_controls TEXT NOT NULL DEFAULT '[]',
    citations TEXT NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    domain TEXT NOT NULL DEFAULT '',
    iteration INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    cost_data TEXT NOT NULL DEFAULT '{}'
)
"""

_CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id)
)
"""


class SqliteInvestigationRepository(InvestigationRepository):
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def initialize(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute(_CREATE_TABLE)
            await db.execute(_CREATE_EVENTS_TABLE)
            await db.commit()
        logger.info("SQLite repository initialized at %s", self._db_path)

    async def save(self, investigation: Investigation) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO investigations
                   (id, prompt, status, hypotheses, experiments,
                    current_hypothesis_id, current_experiment_id,
                    findings, candidates, negative_controls,
                    citations, summary, domain, iteration, error, created_at, cost_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                _to_row(investigation),
            )
            await db.commit()

    async def get_by_id(self, investigation_id: str) -> Investigation | None:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM investigations WHERE id = ?", (investigation_id,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return _from_row(row)

    async def list_all(self) -> list[Investigation]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM investigations ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [_from_row(row) for row in rows]

    async def update(self, investigation: Investigation) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """UPDATE investigations SET
                   status=?, hypotheses=?, experiments=?,
                   current_hypothesis_id=?, current_experiment_id=?,
                   findings=?, candidates=?, negative_controls=?,
                   citations=?, summary=?, domain=?, iteration=?, error=?, cost_data=?
                   WHERE id=?""",
                (
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
                ),
            )
            await db.commit()

    async def save_event(self, investigation_id: str, event_type: str, event_data: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO events (investigation_id, event_type, event_data) VALUES (?, ?, ?)",
                (investigation_id, event_type, event_data),
            )
            await db.commit()

    async def get_events(self, investigation_id: str) -> list[dict[str, str]]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT event_type, event_data FROM events "
                "WHERE investigation_id = ? ORDER BY id ASC",
                (investigation_id,),
            )
            rows = await cursor.fetchall()
            return [
                {"event_type": row["event_type"], "event_data": row["event_data"]} for row in rows
            ]


def _to_row(inv: Investigation) -> tuple[Any, ...]:
    return (
        inv.id,
        inv.prompt,
        inv.status.value,
        json.dumps([_hypothesis_to_dict(h) for h in inv.hypotheses]),
        json.dumps([_experiment_to_dict(e) for e in inv.experiments]),
        inv.current_hypothesis_id,
        inv.current_experiment_id,
        json.dumps([_finding_to_dict(f) for f in inv.findings]),
        json.dumps([_candidate_to_dict(c) for c in inv.candidates]),
        json.dumps([_negative_control_to_dict(nc) for nc in inv.negative_controls]),
        json.dumps(inv.citations),
        inv.summary,
        inv.domain,
        inv.iteration,
        inv.error,
        inv.created_at.isoformat(),
        json.dumps(inv.cost_data),
    )


def _hypothesis_to_dict(h: Hypothesis) -> dict[str, Any]:
    return {
        "id": h.id,
        "statement": h.statement,
        "rationale": h.rationale,
        "status": h.status.value,
        "parent_id": h.parent_id,
        "confidence": h.confidence,
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
    }


def _negative_control_to_dict(nc: NegativeControl) -> dict[str, Any]:
    return {
        "smiles": nc.smiles,
        "name": nc.name,
        "prediction_score": nc.prediction_score,
        "expected_inactive": nc.expected_inactive,
        "source": nc.source,
    }


def _candidate_to_dict(c: Candidate) -> dict[str, Any]:
    return {
        "smiles": c.smiles,
        "name": c.name,
        "prediction_score": c.prediction_score,
        "docking_score": c.docking_score,
        "admet_score": c.admet_score,
        "resistance_risk": c.resistance_risk,
        "rank": c.rank,
        "notes": c.notes,
    }


def _from_row(row: Any) -> Investigation:
    hypotheses_raw = json.loads(row["hypotheses"])
    hypotheses = [
        Hypothesis(
            statement=h["statement"],
            rationale=h.get("rationale", ""),
            id=h["id"],
            status=HypothesisStatus(h.get("status", "proposed")),
            parent_id=h.get("parent_id", ""),
            confidence=h.get("confidence", 0.0),
            supporting_evidence=h.get("supporting_evidence", []),
            contradicting_evidence=h.get("contradicting_evidence", []),
        )
        for h in hypotheses_raw
    ]

    experiments_raw = json.loads(row["experiments"])
    experiments = [
        Experiment(
            hypothesis_id=e["hypothesis_id"],
            description=e["description"],
            id=e["id"],
            tool_plan=e.get("tool_plan", []),
            status=ExperimentStatus(e.get("status", "planned")),
            result_summary=e.get("result_summary", ""),
            supports_hypothesis=e.get("supports_hypothesis"),
        )
        for e in experiments_raw
    ]

    findings_raw = json.loads(row["findings"])
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
        )
        for f in findings_raw
    ]

    negative_controls_raw = json.loads(row["negative_controls"])
    negative_controls = [
        NegativeControl(
            smiles=nc["smiles"],
            name=nc.get("name", ""),
            prediction_score=nc.get("prediction_score", 0.0),
            expected_inactive=nc.get("expected_inactive", True),
            source=nc.get("source", ""),
        )
        for nc in negative_controls_raw
    ]

    candidates_raw = json.loads(row["candidates"])
    candidates = [
        Candidate(
            smiles=c["smiles"],
            name=c.get("name", ""),
            prediction_score=c.get("prediction_score", 0.0),
            docking_score=c.get("docking_score", 0.0),
            admet_score=c.get("admet_score", 0.0),
            resistance_risk=c.get("resistance_risk", "unknown"),
            rank=c.get("rank", 0),
            notes=c.get("notes", ""),
        )
        for c in candidates_raw
    ]

    created_at_str = row["created_at"]
    created_at = datetime.fromisoformat(created_at_str)
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
        citations=json.loads(row["citations"]),
        summary=row["summary"],
        domain=row["domain"],
        iteration=row["iteration"],
        error=row["error"],
        created_at=created_at,
        cost_data=json.loads(row["cost_data"]),
    )
