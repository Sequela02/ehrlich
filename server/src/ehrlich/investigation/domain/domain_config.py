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
    source_configs: tuple[DomainConfig, ...] = ()

    def to_display_dict(self) -> dict[str, object]:
        """Return a serializable dict for SSE/frontend consumption."""
        result: dict[str, object] = {
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
        if self.source_configs:
            result["domains"] = [c.to_display_dict() for c in self.source_configs]
        return result


def merge_domain_configs(configs: list[DomainConfig]) -> DomainConfig:
    """Merge multiple domain configs into a single synthetic config.

    Combines tool tags, score definitions, examples, and other fields
    from all provided configs for cross-domain investigations.
    """
    if len(configs) == 1:
        return configs[0]

    sorted_configs = sorted(configs, key=lambda c: c.name)
    merged_name = " + ".join(c.name for c in sorted_configs)

    # Deduplicate tuples preserving order
    seen_attrs: set[str] = set()
    attrs: list[str] = []
    for c in sorted_configs:
        for a in c.attribute_keys:
            if a not in seen_attrs:
                seen_attrs.add(a)
                attrs.append(a)

    seen_hyp: set[str] = set()
    hyp_types: list[str] = []
    for c in sorted_configs:
        for h in c.hypothesis_types:
            if h not in seen_hyp:
                seen_hyp.add(h)
                hyp_types.append(h)

    first = sorted_configs[0]
    return DomainConfig(
        name=merged_name,
        display_name=merged_name,
        identifier_type=first.identifier_type,
        identifier_label=first.identifier_label,
        candidate_label=first.candidate_label,
        tool_tags=frozenset().union(*(c.tool_tags for c in sorted_configs)),
        score_definitions=tuple(sd for c in sorted_configs for sd in c.score_definitions),
        attribute_keys=tuple(attrs),
        negative_control_threshold=first.negative_control_threshold,
        visualization_type=first.visualization_type,
        hypothesis_types=tuple(hyp_types),
        valid_domain_categories=tuple(
            cat for c in sorted_configs for cat in c.valid_domain_categories
        ),
        template_prompts=tuple(tp for c in sorted_configs for tp in c.template_prompts),
        director_examples="\n\n".join(
            c.director_examples for c in sorted_configs if c.director_examples
        ),
        experiment_examples="\n\n".join(
            c.experiment_examples for c in sorted_configs if c.experiment_examples
        ),
        synthesis_scoring_instructions="\n\n".join(
            c.synthesis_scoring_instructions
            for c in sorted_configs
            if c.synthesis_scoring_instructions
        ),
        source_configs=tuple(sorted_configs),
    )
