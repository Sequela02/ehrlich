from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.investigation.domain.candidate import Candidate
    from ehrlich.investigation.domain.experiment import Experiment
    from ehrlich.investigation.domain.finding import Finding
    from ehrlich.investigation.domain.hypothesis import Hypothesis
    from ehrlich.investigation.domain.negative_control import NegativeControl


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
    hypotheses: list[Hypothesis] = field(default_factory=list)
    experiments: list[Experiment] = field(default_factory=list)
    current_hypothesis_id: str = ""
    current_experiment_id: str = ""
    findings: list[Finding] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    negative_controls: list[NegativeControl] = field(default_factory=list)
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

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.hypotheses.append(hypothesis)

    def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                return h
        return None

    def add_experiment(self, experiment: Experiment) -> None:
        self.experiments.append(experiment)

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        for e in self.experiments:
            if e.id == experiment_id:
                return e
        return None

    def add_negative_control(self, control: NegativeControl) -> None:
        self.negative_controls.append(control)
