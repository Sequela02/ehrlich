from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.literature_survey import run_literature_survey
from ehrlich.investigation.application.phase_runner import (
    _DirectorResult,
    run_classification_phase,
    run_controls_phase,
    run_formulation_phase,
    run_hypothesis_testing_phase,
    run_synthesis_phase,
)
from ehrlich.investigation.application.prompts.builders import (
    build_uploaded_data_context,
)
from ehrlich.investigation.application.prompts.constants import (
    RESEARCHER_EXPERIMENT_PROMPT,
)
from ehrlich.investigation.application.tool_cache import ToolCache
from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
from ehrlich.investigation.domain.events import (
    CostUpdate,
    DomainEvent,
    InvestigationError,
    PhaseChanged,
    Thinking,
)
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.application.tree_manager import TreeManager
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.domain_registry import DomainRegistry
    from ehrlich.investigation.domain.mcp_config import MCPServerConfig
    from ehrlich.investigation.domain.repository import InvestigationRepository
    from ehrlich.investigation.domain.uploaded_file import UploadedFile
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge


def _build_output_config(schema: dict[str, Any]) -> dict[str, Any]:
    return {"format": {"type": "json_schema", "schema": schema}}


logger = logging.getLogger(__name__)


class MultiModelOrchestrator:
    def __init__(
        self,
        director: AnthropicClientAdapter,
        researcher: AnthropicClientAdapter,
        summarizer: AnthropicClientAdapter,
        registry: ToolRegistry,
        max_iterations_per_experiment: int = 10,
        max_hypotheses: int = 6,
        summarizer_threshold: int = 2000,
        require_approval: bool = False,
        repository: InvestigationRepository | None = None,
        domain_registry: DomainRegistry | None = None,
        mcp_bridge: MCPBridge | None = None,
        mcp_configs: list[MCPServerConfig] | None = None,
        tree_manager: TreeManager | None = None,
    ) -> None:
        self._director = director
        self._researcher = researcher
        self._summarizer = summarizer
        self._registry = registry
        self._max_iterations_per_experiment = max_iterations_per_experiment
        self._max_hypotheses = max_hypotheses
        self._summarizer_threshold = summarizer_threshold
        self._require_approval = require_approval
        self._repository = repository
        self._domain_registry = domain_registry
        self._mcp_bridge = mcp_bridge
        self._mcp_configs = mcp_configs or []
        self._tree_manager = tree_manager
        self._active_config: DomainConfig | None = None
        self._researcher_prompt = RESEARCHER_EXPERIMENT_PROMPT
        self._cache = ToolCache()
        self._dispatcher = ToolDispatcher(registry, self._cache, repository, {})
        self._state_lock = asyncio.Lock()
        self._approval_event = asyncio.Event()
        self._investigation: Investigation | None = None
        self._uploaded_files: dict[str, UploadedFile] = {}
        self._uploaded_data_context = ""

    @property
    def is_awaiting_approval(self) -> bool:
        """Return True if the orchestrator is blocked waiting for hypothesis approval."""
        if self._investigation is None:
            return False
        return self._investigation.status == InvestigationStatus.AWAITING_APPROVAL

    def approve_hypotheses(
        self,
        approved_ids: list[str],
        rejected_ids: list[str],
    ) -> None:
        """Called by API to approve/reject hypotheses and unblock the loop."""
        if self._investigation is None:
            return
        from ehrlich.investigation.domain.hypothesis import HypothesisStatus

        for h in self._investigation.hypotheses:
            if h.id in rejected_ids:
                h.status = HypothesisStatus.REJECTED
        self._investigation.transition_to(InvestigationStatus.RUNNING)
        self._approval_event.set()

    def cancel(self) -> None:
        """Cancel the investigation and unblock any pending waits."""
        if self._investigation is None:
            return
        self._investigation.transition_to(InvestigationStatus.CANCELLED)
        self._approval_event.set()

    def _cost_event(self, cost: CostTracker, investigation_id: str) -> CostUpdate:
        return CostUpdate(
            input_tokens=cost.input_tokens,
            output_tokens=cost.output_tokens,
            cache_read_tokens=cost.cache_read_tokens,
            cache_write_tokens=cost.cache_write_tokens,
            total_tokens=cost.total_tokens,
            total_cost_usd=round(cost.total_cost, 6),
            tool_calls=cost.tool_calls,
            investigation_id=investigation_id,
        )

    async def _director_call(
        self,
        cost: CostTracker,
        system: str,
        user_message: str,
        investigation_id: str,
        output_config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Thinking | _DirectorResult, None]:
        text = ""
        thinking_text = ""
        response = None
        async for event in self._director.stream_message(
            system=system,
            messages=[{"role": "user", "content": user_message}],
            tools=[],
            output_config=output_config,
        ):
            if event["type"] == "thinking":
                thinking_text += event["text"]
                yield Thinking(text=event["text"], investigation_id=investigation_id)
            elif event["type"] == "text":
                text += event["text"]
            elif event["type"] == "result":
                response = event["response"]

        if response:
            cost.add_usage(
                response.input_tokens,
                response.output_tokens,
                self._director.model,
                role="director",
                cache_read_tokens=response.cache_read_input_tokens,
                cache_write_tokens=response.cache_write_input_tokens,
            )

        yield _DirectorResult(data=json.loads(text), thinking=thinking_text)

    # ------------------------------------------------------------------
    # Main orchestration loop
    # ------------------------------------------------------------------

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.transition_to(InvestigationStatus.RUNNING)
        cost = CostTracker()

        # Build uploaded data context for prompt injection
        if investigation.uploaded_files:
            self._uploaded_files = {f.file_id: f for f in investigation.uploaded_files}
            self._uploaded_data_context = build_uploaded_data_context(investigation.uploaded_files)
        else:
            self._uploaded_files = {}
            self._uploaded_data_context = ""
        self._dispatcher.update_uploaded_files(self._uploaded_files)

        # Connect MCP servers if configured
        if self._mcp_bridge and self._mcp_configs:
            try:
                await self._mcp_bridge.connect(self._mcp_configs)
                for cfg in self._mcp_configs:
                    if cfg.enabled and cfg.name in self._mcp_bridge.connected_servers:
                        await self._registry.register_mcp_tools(
                            self._mcp_bridge, cfg.name, cfg.tags
                        )
            except Exception:
                logger.exception("MCP bridge connection failed, continuing without MCP")

        try:
            # 1. Classify domain + PICO decomposition
            pico: dict[str, Any] = {}
            prior_context = ""
            async for event in run_classification_phase(
                investigation,
                cost,
                self._summarizer,
                self._uploaded_data_context,
                self._repository,
                self._domain_registry,
                self._director_call,
            ):
                if isinstance(event, dict):
                    result = event["__phase_result__"]
                    pico = result["pico"]
                    prior_context = result["prior_context"]
                    self._active_config = result["active_config"]
                    if result["researcher_prompt"]:
                        self._researcher_prompt = result["researcher_prompt"]
                else:
                    yield event
            yield self._cost_event(cost, investigation.id)

            # 2. Literature survey
            yield PhaseChanged(
                phase=2,
                name="Literature Survey",
                description="Structured literature search with PICO framework and citation chasing",
                investigation_id=investigation.id,
            )
            async for event in run_literature_survey(
                self._researcher,
                self._summarizer,
                self._dispatcher,
                self._registry,
                self._active_config,
                self._summarizer_threshold,
                self._max_iterations_per_experiment,
                investigation,
                cost,
                pico,
            ):
                yield event
            yield self._cost_event(cost, investigation.id)

            # 3. Director formulates hypotheses
            neg_control_suggestions: list[dict[str, Any]] = []
            pos_control_suggestions: list[dict[str, Any]] = []
            async for event in run_formulation_phase(
                investigation,
                cost,
                self._active_config,
                self._uploaded_data_context,
                prior_context,
                pico,
                self._require_approval,
                self._approval_event,
                self._director_call,
                self._cost_event,
            ):
                if isinstance(event, dict):
                    result = event["__phase_result__"]
                    neg_control_suggestions = result["neg_control_suggestions"]
                    pos_control_suggestions = result["pos_control_suggestions"]
                else:
                    yield event

            # 4. Hypothesis testing loop
            async for event in run_hypothesis_testing_phase(
                investigation,
                cost,
                self._active_config,
                self._uploaded_data_context,
                self._researcher_prompt,
                self._researcher,
                self._summarizer,
                self._dispatcher,
                self._registry,
                self._max_hypotheses,
                self._max_iterations_per_experiment,
                self._summarizer_threshold,
                self._state_lock,
                self._director_call,
                self._cost_event,
                tree_manager=self._tree_manager,
            ):
                yield event

            # 5. Controls validation
            validation_metrics: dict[str, Any] = {}
            async for event in run_controls_phase(
                investigation,
                cost,
                self._active_config,
                neg_control_suggestions,
                pos_control_suggestions,
                self._dispatcher,
            ):
                if isinstance(event, dict):
                    validation_metrics = event["__phase_result__"]["validation_metrics"]
                else:
                    yield event

            # 6. Director synthesis
            async for event in run_synthesis_phase(
                investigation,
                cost,
                self._active_config,
                validation_metrics,
                self._mcp_bridge,
                self._director_call,
            ):
                yield event

        except Exception as e:
            logger.exception("Investigation %s failed", investigation.id)
            investigation.transition_to(InvestigationStatus.FAILED)
            investigation.error = str(e)
            investigation.cost_data = cost.to_dict()
            yield InvestigationError(error=str(e), investigation_id=investigation.id)
        finally:
            if self._mcp_bridge:
                try:
                    await self._mcp_bridge.disconnect()
                except Exception:
                    logger.warning("MCP bridge disconnect failed", exc_info=True)
