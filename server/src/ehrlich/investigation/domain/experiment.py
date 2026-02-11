from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class ExperimentStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Experiment:
    hypothesis_id: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_plan: list[str] = field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.PLANNED
    result_summary: str = ""
    supports_hypothesis: bool | None = None

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            msg = "Experiment must reference a hypothesis"
            raise ValueError(msg)
        if not self.description:
            msg = "Experiment description cannot be empty"
            raise ValueError(msg)
