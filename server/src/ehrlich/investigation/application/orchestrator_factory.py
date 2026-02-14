"""Orchestrator construction with Anthropic adapter wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.multi_orchestrator import MultiModelOrchestrator
from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

if TYPE_CHECKING:
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_registry import DomainRegistry
    from ehrlich.investigation.domain.mcp_config import MCPServerConfig
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge
    from ehrlich.investigation.infrastructure.repository import InvestigationRepository


def create_orchestrator(
    settings: Any,
    registry: ToolRegistry,
    repository: InvestigationRepository,
    domain_registry: DomainRegistry | None = None,
    mcp_bridge: MCPBridge | None = None,
    mcp_configs: list[MCPServerConfig] | None = None,
    api_key_override: str | None = None,
    director_model_override: str | None = None,
) -> MultiModelOrchestrator:
    """Wire up Anthropic adapters and build a MultiModelOrchestrator."""
    api_key = api_key_override or settings.anthropic_api_key or None

    director_model = director_model_override or settings.director_model

    # effort is only supported by Opus models (4.5+)
    director_effort = settings.director_effort if "opus" in director_model else None

    thinking = None
    if settings.director_thinking == "enabled":
        thinking = {
            "type": "enabled",
            "budget_tokens": settings.director_thinking_budget,
        }

    director = AnthropicClientAdapter(
        model=director_model,
        api_key=api_key,
        max_tokens=32768,
        effort=director_effort,
        thinking=thinking,
    )
    researcher = AnthropicClientAdapter(
        model=settings.researcher_model,
        api_key=api_key,
    )
    summarizer = AnthropicClientAdapter(
        model=settings.summarizer_model,
        api_key=api_key,
    )
    return MultiModelOrchestrator(
        director=director,
        researcher=researcher,
        summarizer=summarizer,
        registry=registry,
        max_iterations_per_experiment=settings.max_iterations_per_experiment,
        summarizer_threshold=settings.summarizer_threshold,
        require_approval=True,
        repository=repository,
        domain_registry=domain_registry,
        mcp_bridge=mcp_bridge,
        mcp_configs=mcp_configs,
    )
