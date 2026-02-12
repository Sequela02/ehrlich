from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.investigation.domain.domain_config import DomainConfig


class DomainRegistry:
    """Registry of scientific domain configurations."""

    def __init__(self) -> None:
        self._configs: dict[str, DomainConfig] = {}
        self._category_map: dict[str, str] = {}

    def register(self, config: DomainConfig) -> None:
        self._configs[config.name] = config
        for category in config.valid_domain_categories:
            self._category_map[category] = config.name

    def get(self, name: str) -> DomainConfig | None:
        return self._configs.get(name)

    def detect(self, classified_category: str) -> DomainConfig:
        """Map a classified domain category to its DomainConfig.

        Falls back to the first registered config if no match.
        """
        domain_name = self._category_map.get(classified_category)
        if domain_name and domain_name in self._configs:
            return self._configs[domain_name]
        # Fallback to first registered
        if self._configs:
            return next(iter(self._configs.values()))
        msg = "No domain configs registered"
        raise ValueError(msg)

    def all_categories(self) -> frozenset[str]:
        return frozenset(self._category_map.keys())

    def all_template_prompts(self) -> list[dict[str, str]]:
        prompts: list[dict[str, str]] = []
        for config in self._configs.values():
            for tp in config.template_prompts:
                prompts.append({**tp, "domain": config.name})
        return prompts

    def all_configs(self) -> list[DomainConfig]:
        return list(self._configs.values())
