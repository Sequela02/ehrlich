from __future__ import annotations

import pytest

from ehrlich.investigation.domain.domain_config import (
    DomainConfig,
    ScoreDefinition,
    merge_domain_configs,
)
from ehrlich.investigation.domain.domain_registry import DomainRegistry


def _make_config(
    name: str,
    *,
    categories: tuple[str, ...] = (),
    tool_tags: frozenset[str] | None = None,
    score_defs: tuple[ScoreDefinition, ...] = (),
    attrs: tuple[str, ...] = (),
    hypothesis_types: tuple[str, ...] = (),
    director_examples: str = "",
    experiment_examples: str = "",
) -> DomainConfig:
    return DomainConfig(
        name=name,
        display_name=name.title(),
        identifier_type="smiles",
        identifier_label="SMILES",
        candidate_label="Compound",
        tool_tags=tool_tags or frozenset(),
        score_definitions=score_defs,
        attribute_keys=attrs,
        valid_domain_categories=categories,
        hypothesis_types=hypothesis_types,
        director_examples=director_examples,
        experiment_examples=experiment_examples,
    )


_MOLECULAR = _make_config(
    "molecular_science",
    categories=("drug_discovery", "antimicrobial", "toxicology"),
    tool_tags=frozenset({"chemistry", "analysis", "prediction"}),
    score_defs=(ScoreDefinition(key="probability", label="Prob", format_spec=".2f"),),
    attrs=("mechanism",),
    hypothesis_types=("mechanistic", "correlational"),
    director_examples="<example>MRSA</example>",
    experiment_examples="<experiment>dock</experiment>",
)

_SPORTS = _make_config(
    "sports_science",
    categories=("training", "recovery", "supplements"),
    tool_tags=frozenset({"sports"}),
    score_defs=(ScoreDefinition(key="effect_size", label="ES", format_spec=".2f"),),
    attrs=("population",),
    hypothesis_types=("correlational",),
    director_examples="<example>HIIT</example>",
)


class TestDomainRegistryDetect:
    def test_single_category_returns_one_config(self) -> None:
        reg = DomainRegistry()
        reg.register(_MOLECULAR)
        reg.register(_SPORTS)

        result = reg.detect(["drug_discovery"])
        assert len(result) == 1
        assert result[0].name == "molecular_science"

    def test_multiple_categories_same_domain_deduplicates(self) -> None:
        reg = DomainRegistry()
        reg.register(_MOLECULAR)

        result = reg.detect(["drug_discovery", "antimicrobial"])
        assert len(result) == 1
        assert result[0].name == "molecular_science"

    def test_cross_domain_returns_both(self) -> None:
        reg = DomainRegistry()
        reg.register(_MOLECULAR)
        reg.register(_SPORTS)

        result = reg.detect(["drug_discovery", "training"])
        assert len(result) == 2
        names = {c.name for c in result}
        assert names == {"molecular_science", "sports_science"}

    def test_unknown_category_falls_back_to_first(self) -> None:
        reg = DomainRegistry()
        reg.register(_MOLECULAR)
        reg.register(_SPORTS)

        result = reg.detect(["astrophysics"])
        assert len(result) == 1

    def test_empty_registry_raises(self) -> None:
        reg = DomainRegistry()
        with pytest.raises(ValueError, match="No domain configs registered"):
            reg.detect(["anything"])

    def test_preserves_order_from_input(self) -> None:
        reg = DomainRegistry()
        reg.register(_MOLECULAR)
        reg.register(_SPORTS)

        result = reg.detect(["training", "drug_discovery"])
        assert result[0].name == "sports_science"
        assert result[1].name == "molecular_science"


class TestMergeDomainConfigs:
    def test_single_config_returns_same(self) -> None:
        result = merge_domain_configs([_MOLECULAR])
        assert result is _MOLECULAR

    def test_merged_name_alphabetical(self) -> None:
        result = merge_domain_configs([_SPORTS, _MOLECULAR])
        assert result.name == "molecular_science + sports_science"

    def test_merged_tool_tags_union(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        assert result.tool_tags == frozenset({"chemistry", "analysis", "prediction", "sports"})

    def test_merged_score_definitions_concatenated(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        keys = [sd.key for sd in result.score_definitions]
        assert "probability" in keys
        assert "effect_size" in keys

    def test_merged_attribute_keys_deduplicated(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        assert "mechanism" in result.attribute_keys
        assert "population" in result.attribute_keys

    def test_merged_hypothesis_types_deduplicated(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        assert result.hypothesis_types.count("correlational") == 1

    def test_merged_director_examples_joined(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        assert "<example>MRSA</example>" in result.director_examples
        assert "<example>HIIT</example>" in result.director_examples

    def test_source_configs_preserved(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        assert len(result.source_configs) == 2
        names = {c.name for c in result.source_configs}
        assert names == {"molecular_science", "sports_science"}

    def test_to_display_dict_includes_domains(self) -> None:
        result = merge_domain_configs([_MOLECULAR, _SPORTS])
        d = result.to_display_dict()
        assert "domains" in d
        domains = d["domains"]
        assert isinstance(domains, list)
        assert len(domains) == 2

    def test_single_config_display_dict_no_domains(self) -> None:
        d = _MOLECULAR.to_display_dict()
        assert "domains" not in d
