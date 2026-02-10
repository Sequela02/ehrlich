from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrainedModel:
    model_id: str
    model_type: str
    target: str
    metrics: dict[str, float] = field(default_factory=dict)
    feature_importance: dict[str, float] = field(default_factory=dict)
    is_trained: bool = False
