from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    REVISED = "revised"
    REJECTED = "rejected"


class HypothesisType(StrEnum):
    MECHANISTIC = "mechanistic"
    STRUCTURAL = "structural"
    PHARMACOLOGICAL = "pharmacological"
    TOXICOLOGICAL = "toxicological"
    OTHER = "other"


@dataclass
class Hypothesis:
    statement: str
    rationale: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    parent_id: str = ""
    prediction: str = ""
    null_prediction: str = ""
    success_criteria: str = ""
    failure_criteria: str = ""
    scope: str = ""
    hypothesis_type: str = ""
    prior_confidence: float = 0.0
    confidence: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.statement:
            msg = "Hypothesis statement cannot be empty"
            raise ValueError(msg)
        if not 0.0 <= self.confidence <= 1.0:
            msg = f"Confidence must be 0.0-1.0, got {self.confidence}"
            raise ValueError(msg)
        if not 0.0 <= self.prior_confidence <= 1.0:
            msg = f"Prior confidence must be 0.0-1.0, got {self.prior_confidence}"
            raise ValueError(msg)
