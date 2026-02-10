from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


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
    error: str = ""
