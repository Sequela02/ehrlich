from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VisualizationPayload:
    """Structured payload for a visualization rendered by a tool."""

    viz_type: str
    title: str
    data: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    domain: str = ""
