from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.investigation.domain.candidate import Candidate
    from ehrlich.investigation.domain.finding import Finding


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Investigation:
    prompt: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: InvestigationStatus = InvestigationStatus.PENDING
    phases: list[str] = field(default_factory=list)
    current_phase: str = ""
    findings: list[Finding] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    summary: str = ""
    iteration: int = 0
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    cost_data: dict[str, object] = field(default_factory=dict)

    def record_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def set_candidates(self, candidates: list[Candidate], citations: list[str]) -> None:
        self.candidates = candidates
        self.citations = citations

    def start_phase(self, phase: str) -> None:
        self.current_phase = phase
        if phase not in self.phases:
            self.phases.append(phase)
