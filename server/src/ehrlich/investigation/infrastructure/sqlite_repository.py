from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.repository import InvestigationRepository

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    phases TEXT NOT NULL DEFAULT '[]',
    current_phase TEXT NOT NULL DEFAULT '',
    findings TEXT NOT NULL DEFAULT '[]',
    candidates TEXT NOT NULL DEFAULT '[]',
    citations TEXT NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    iteration INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    cost_data TEXT NOT NULL DEFAULT '{}'
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
            await db.commit()
        logger.info("SQLite repository initialized at %s", self._db_path)

    async def save(self, investigation: Investigation) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO investigations
                   (id, prompt, status, phases, current_phase, findings, candidates,
                    citations, summary, iteration, error, created_at, cost_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                   status=?, phases=?, current_phase=?, findings=?, candidates=?,
                   citations=?, summary=?, iteration=?, error=?, cost_data=?
                   WHERE id=?""",
                (
                    investigation.status.value,
                    json.dumps(investigation.phases),
                    investigation.current_phase,
                    json.dumps([_finding_to_dict(f) for f in investigation.findings]),
                    json.dumps([_candidate_to_dict(c) for c in investigation.candidates]),
                    json.dumps(investigation.citations),
                    investigation.summary,
                    investigation.iteration,
                    investigation.error,
                    json.dumps(investigation.cost_data),
                    investigation.id,
                ),
            )
            await db.commit()


def _to_row(inv: Investigation) -> tuple[Any, ...]:
    return (
        inv.id,
        inv.prompt,
        inv.status.value,
        json.dumps(inv.phases),
        inv.current_phase,
        json.dumps([_finding_to_dict(f) for f in inv.findings]),
        json.dumps([_candidate_to_dict(c) for c in inv.candidates]),
        json.dumps(inv.citations),
        inv.summary,
        inv.iteration,
        inv.error,
        inv.created_at.isoformat(),
        json.dumps(inv.cost_data),
    )


def _finding_to_dict(f: Finding) -> dict[str, Any]:
    return {
        "title": f.title,
        "detail": f.detail,
        "evidence": f.evidence,
        "phase": f.phase,
        "confidence": f.confidence,
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
    findings_raw = json.loads(row["findings"])
    findings = [
        Finding(
            title=f["title"],
            detail=f["detail"],
            evidence=f.get("evidence", ""),
            phase=f.get("phase", ""),
            confidence=f.get("confidence", 0.0),
        )
        for f in findings_raw
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
        phases=json.loads(row["phases"]),
        current_phase=row["current_phase"],
        findings=findings,
        candidates=candidates,
        citations=json.loads(row["citations"]),
        summary=row["summary"],
        iteration=row["iteration"],
        error=row["error"],
        created_at=created_at,
        cost_data=json.loads(row["cost_data"]),
    )
