from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.prompts import SCIENTIST_SYSTEM_PROMPT
from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.events import (
    DomainEvent,
    FindingRecorded,
    InvestigationCompleted,
    InvestigationError,
    PhaseStarted,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)

_PHASE_KEYWORDS: dict[str, str] = {
    "literature": "Literature Review",
    "search_literature": "Literature Review",
    "get_reference": "Literature Review",
    "explore_dataset": "Data Exploration",
    "analyze_substructures": "Data Exploration",
    "compute_properties": "Data Exploration",
    "train_model": "Model Training",
    "predict_candidates": "Virtual Screening",
    "cluster_compounds": "Virtual Screening",
    "compute_descriptors": "Structural Analysis",
    "generate_3d": "Structural Analysis",
    "dock_against_target": "Structural Analysis",
    "predict_admet": "Structural Analysis",
    "assess_resistance": "Resistance Assessment",
    "conclude_investigation": "Conclusions",
}

_CONTROL_TOOLS = {"record_finding", "conclude_investigation"}


class Orchestrator:
    def __init__(
        self,
        client: AnthropicClientAdapter,
        registry: ToolRegistry,
        max_iterations: int = 50,
    ) -> None:
        self._client = client
        self._registry = registry
        self._max_iterations = max_iterations

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.status = InvestigationStatus.RUNNING
        cost = CostTracker()
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": investigation.prompt},
        ]
        tool_schemas = self._registry.list_schemas()
        concluded = False

        try:
            for iteration in range(self._max_iterations):
                investigation.iteration = iteration + 1

                response = await self._client.create_message(
                    system=SCIENTIST_SYSTEM_PROMPT,
                    messages=messages,
                    tools=tool_schemas,
                )
                cost.add_usage(response.input_tokens, response.output_tokens, self._client.model)

                assistant_content: list[dict[str, Any]] = []
                tool_use_blocks: list[dict[str, Any]] = []

                for block in response.content:
                    assistant_content.append(block)
                    if block["type"] == "text":
                        yield Thinking(
                            text=block["text"],
                            investigation_id=investigation.id,
                        )
                    elif block["type"] == "tool_use":
                        tool_use_blocks.append(block)

                messages.append({"role": "assistant", "content": assistant_content})

                if response.stop_reason == "end_turn" or not tool_use_blocks:
                    break

                tool_results: list[dict[str, Any]] = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block["name"]
                    tool_input = tool_block["input"]
                    tool_use_id = tool_block["id"]
                    cost.add_tool_call()

                    phase = _PHASE_KEYWORDS.get(tool_name)
                    if phase and phase != investigation.current_phase:
                        investigation.start_phase(phase)
                        yield PhaseStarted(
                            phase=phase,
                            investigation_id=investigation.id,
                        )

                    yield ToolCalled(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        investigation_id=investigation.id,
                    )

                    result_str = await self._dispatch_tool(tool_name, tool_input, investigation)

                    preview = result_str[:500] if len(result_str) > 500 else result_str
                    yield ToolResultEvent(
                        tool_name=tool_name,
                        result_preview=preview,
                        investigation_id=investigation.id,
                    )

                    if tool_name == "record_finding":
                        yield FindingRecorded(
                            title=tool_input.get("title", ""),
                            detail=tool_input.get("detail", ""),
                            phase=tool_input.get("phase", investigation.current_phase),
                            investigation_id=investigation.id,
                        )

                    if tool_name == "conclude_investigation":
                        concluded = True

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result_str,
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

                if concluded:
                    break

            investigation.status = InvestigationStatus.COMPLETED
            yield InvestigationCompleted(
                investigation_id=investigation.id,
                candidate_count=len(investigation.candidates),
                summary=investigation.summary,
                cost=cost.to_dict(),
            )

        except Exception as e:
            logger.exception("Investigation %s failed", investigation.id)
            investigation.status = InvestigationStatus.FAILED
            investigation.error = str(e)
            yield InvestigationError(
                error=str(e),
                investigation_id=investigation.id,
            )

    async def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        investigation: Investigation,
    ) -> str:
        if tool_name == "record_finding":
            return self._handle_record_finding(tool_input, investigation)

        if tool_name == "conclude_investigation":
            return self._handle_conclude(tool_input, investigation)

        func = self._registry.get(tool_name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await func(**tool_input)
            return str(result)
        except Exception as e:
            logger.warning("Tool %s failed: %s", tool_name, e)
            return json.dumps({"error": f"Tool {tool_name} failed: {e}"})

    def _handle_record_finding(
        self, tool_input: dict[str, Any], investigation: Investigation
    ) -> str:
        finding = Finding(
            title=tool_input.get("title", ""),
            detail=tool_input.get("detail", ""),
            evidence=tool_input.get("evidence", ""),
            phase=tool_input.get("phase", investigation.current_phase),
        )
        investigation.record_finding(finding)
        return json.dumps(
            {
                "status": "recorded",
                "title": finding.title,
                "phase": finding.phase,
                "total_findings": len(investigation.findings),
            }
        )

    def _handle_conclude(self, tool_input: dict[str, Any], investigation: Investigation) -> str:
        investigation.summary = tool_input.get("summary", "")
        raw_candidates = tool_input.get("candidates") or []
        candidates = [
            Candidate(
                smiles=c.get("smiles", ""),
                name=c.get("name", ""),
                notes=c.get("rationale", c.get("notes", "")),
                rank=i + 1,
            )
            for i, c in enumerate(raw_candidates)
        ]
        citations = tool_input.get("citations") or []
        investigation.set_candidates(candidates, citations)
        return json.dumps(
            {
                "status": "concluded",
                "summary": investigation.summary[:200],
                "candidate_count": len(candidates),
                "citation_count": len(citations),
            }
        )
