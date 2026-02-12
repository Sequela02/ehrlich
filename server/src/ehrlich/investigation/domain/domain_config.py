from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreDefinition:
    """Defines how a score column should be displayed and evaluated."""

    key: str
    label: str
    format_spec: str
    higher_is_better: bool = True
    good_threshold: float = 0.7
    ok_threshold: float = 0.4


@dataclass(frozen=True)
class DomainConfig:
    """Configuration for a scientific domain that drives tool filtering,
    prompt adaptation, and frontend display."""

    name: str
    display_name: str
    identifier_type: str
    identifier_label: str
    candidate_label: str
    tool_tags: frozenset[str]
    score_definitions: tuple[ScoreDefinition, ...]
    attribute_keys: tuple[str, ...]
    negative_control_threshold: float = 0.5
    visualization_type: str = "molecular"
    hypothesis_types: tuple[str, ...] = ()
    valid_domain_categories: tuple[str, ...] = ()
    template_prompts: tuple[dict[str, str], ...] = ()
    director_examples: str = ""
    experiment_examples: str = ""
    synthesis_scoring_instructions: str = ""

    def to_display_dict(self) -> dict[str, object]:
        """Return a serializable dict for SSE/frontend consumption."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "identifier_type": self.identifier_type,
            "identifier_label": self.identifier_label,
            "candidate_label": self.candidate_label,
            "visualization_type": self.visualization_type,
            "score_columns": [
                {
                    "key": sd.key,
                    "label": sd.label,
                    "format_spec": sd.format_spec,
                    "higher_is_better": sd.higher_is_better,
                    "good_threshold": sd.good_threshold,
                    "ok_threshold": sd.ok_threshold,
                }
                for sd in self.score_definitions
            ],
            "attribute_keys": list(self.attribute_keys),
        }
