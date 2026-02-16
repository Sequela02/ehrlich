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
    from ehrlich.investigation.domain.positive_control import PositiveControl
    from ehrlich.investigation.domain.uploaded_file import UploadedFile


class InvestigationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, current: InvestigationStatus, target: InvestigationStatus) -> None:
        super().__init__(f"Cannot transition from '{current}' to '{target}'")
        self.current = current
        self.target = target


_VALID_TRANSITIONS: dict[InvestigationStatus, frozenset[InvestigationStatus]] = {
    InvestigationStatus.PENDING: frozenset({
        InvestigationStatus.RUNNING,
        InvestigationStatus.CANCELLED,
    }),
    InvestigationStatus.RUNNING: frozenset({
        InvestigationStatus.AWAITING_APPROVAL,
        InvestigationStatus.PAUSED,
        InvestigationStatus.COMPLETED,
        InvestigationStatus.FAILED,
        InvestigationStatus.CANCELLED,
    }),
    InvestigationStatus.AWAITING_APPROVAL: frozenset({
        InvestigationStatus.RUNNING,
        InvestigationStatus.CANCELLED,
    }),
    InvestigationStatus.PAUSED: frozenset({
        InvestigationStatus.RUNNING,
        InvestigationStatus.CANCELLED,
    }),
    # Terminal states — no transitions allowed
    InvestigationStatus.COMPLETED: frozenset(),
    InvestigationStatus.FAILED: frozenset(),
    InvestigationStatus.CANCELLED: frozenset(),
}


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
    positive_controls: list[PositiveControl] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    summary: str = ""
    domain: str = ""
    iteration: int = 0
    error: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    trained_model_ids: list[str] = field(default_factory=list)
    cost_data: dict[str, object] = field(default_factory=dict)
    uploaded_files: list[UploadedFile] = field(default_factory=list)

    def transition_to(self, new_status: InvestigationStatus) -> None:
        """Transition to a new status, enforcing valid state transitions."""
        allowed = _VALID_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise InvalidTransitionError(self.status, new_status)
        self.status = new_status

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

    def add_positive_control(self, control: PositiveControl) -> None:
        self.positive_controls.append(control)
