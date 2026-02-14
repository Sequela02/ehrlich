"""Literature survey runner extracted from MultiModelOrchestrator.

Contains the structured literature survey with PICO framework, citation
chasing, evidence grading, and helper utilities shared with the researcher
executor (compact result schemas, search tool set).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.prompts.builders import (
    build_literature_assessment_prompt,
    build_literature_survey_prompt,
)
from ehrlich.investigation.application.researcher_executor import (
    _compact_result as compact_result,
)
from ehrlich.investigation.application.researcher_executor import (
    maybe_viz_event,
    summarize_output,
)
from ehrlich.investigation.domain.events import (
    DomainEvent,
    FindingRecorded,
    LiteratureSurveyCompleted,
    Thinking,
    ToolCalled,
    ToolResultEvent,
)
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.schemas import LITERATURE_GRADING_SCHEMA

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.cost_tracker import CostTracker
    from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.investigation import Investigation
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SEARCH_TOOLS: frozenset[str] = frozenset(
    {
        "search_literature",
        "search_citations",
        "explore_dataset",
        "search_bioactivity",
        "search_compounds",
        "search_pharmacology",
        "search_training_literature",
        "search_pubmed_training",
        "search_clinical_trials",
        "search_exercise_database",
        "search_supplement_evidence",
        "search_prior_research",
    }
)


def _build_output_config(schema: dict[str, Any]) -> dict[str, Any]:
    return {"format": {"type": "json_schema", "schema": schema}}


# ---------------------------------------------------------------------------
# Literature context builder (static helper)
# ---------------------------------------------------------------------------


def build_literature_context(
    investigation: Investigation,
    pico: dict[str, Any],
) -> str:
    """Build structured XML context from PICO + findings for Director formulation."""
    parts: list[str] = ["<literature_survey>"]
    pop = pico.get("population", "")
    interv = pico.get("intervention", "")
    comp = pico.get("comparison", "")
    outcome = pico.get("outcome", "")
    parts.append(
        f'  <pico population="{pop}" intervention="{interv}" '
        f'comparison="{comp}" outcome="{outcome}"/>'
    )
    if investigation.findings:
        parts.append("  <findings>")
        for f in investigation.findings:
            parts.append(
                f'    <finding level="{f.evidence_level}" '
                f'type="{f.evidence_type}">{f.title}: {f.detail}</finding>'
            )
        parts.append("  </findings>")
    parts.append("</literature_survey>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Literature survey runner
# ---------------------------------------------------------------------------


async def run_literature_survey(
    researcher: AnthropicClientAdapter,
    summarizer: AnthropicClientAdapter,
    dispatcher: ToolDispatcher,
    registry: ToolRegistry,
    active_config: DomainConfig | None,
    summarizer_threshold: int,
    max_iterations: int,
    investigation: Investigation,
    cost: CostTracker,
    pico: dict[str, Any],
) -> AsyncGenerator[DomainEvent, None]:
    """Structured literature survey with PICO, citation chasing, and evidence grading."""
    # A. Domain-filtered tools (no hardcoded set)
    if active_config:
        excluded = {
            "conclude_investigation",
            "propose_hypothesis",
            "design_experiment",
            "evaluate_hypothesis",
        }
        tool_schemas = [
            t
            for t in registry.list_schemas_for_domain(active_config.tool_tags)
            if t["name"] not in excluded
        ]
    else:
        lit_tools = {
            "search_literature",
            "search_citations",
            "get_reference",
            "explore_dataset",
            "record_finding",
        }
        tool_schemas = [t for t in registry.list_schemas() if t["name"] in lit_tools]

    # Build structured survey prompt
    survey_prompt = build_literature_survey_prompt(active_config, pico)

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Research prompt: {investigation.prompt}\n\n"
                f"Conduct a structured literature survey following the protocol above."
            ),
        },
    ]

    search_queries = 0
    total_results = 0

    for _iteration in range(max_iterations):
        investigation.iteration += 1
        tool_choice = {"type": "any"} if _iteration == 0 else None
        response = await researcher.create_message(
            system=survey_prompt,
            messages=messages,
            tools=tool_schemas,
            tool_choice=tool_choice,
        )
        cost.add_usage(
            response.input_tokens,
            response.output_tokens,
            researcher.model,
            cache_read_tokens=response.cache_read_input_tokens,
            cache_write_tokens=response.cache_write_input_tokens,
        )

        assistant_content: list[dict[str, Any]] = []
        tool_use_blocks: list[dict[str, Any]] = []

        for block in response.content:
            assistant_content.append(block)
            if block["type"] == "text":
                yield Thinking(text=block["text"], investigation_id=investigation.id)
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

            # Track search stats
            if tool_name in SEARCH_TOOLS:
                search_queries += 1

            yield ToolCalled(
                tool_name=tool_name,
                tool_input=tool_input,
                investigation_id=investigation.id,
            )

            result_str = await dispatcher.dispatch(tool_name, tool_input, investigation)
            result_str = compact_result(tool_name, result_str)

            # Track result counts
            try:
                result_data = json.loads(result_str)
                if isinstance(result_data, dict):
                    total_results += int(result_data.get("count", 0))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

            summarized_str, summarize_event = await summarize_output(
                summarizer,
                cost,
                tool_name,
                result_str,
                investigation.id,
                summarizer_threshold,
            )
            if summarize_event is not None:
                yield summarize_event

            content_for_model = summarized_str if summarize_event else result_str
            preview = result_str[:1500] if len(result_str) > 1500 else result_str
            yield ToolResultEvent(
                tool_name=tool_name,
                result_preview=preview,
                investigation_id=investigation.id,
            )

            # Emit visualization event if tool returned viz payload
            viz_event = maybe_viz_event(result_str, "", investigation.id)
            if viz_event is not None:
                yield viz_event

            if tool_name == "record_finding":
                finding = Finding(
                    title=tool_input.get("title", ""),
                    detail=tool_input.get("detail", ""),
                    evidence=tool_input.get("evidence", ""),
                    hypothesis_id=tool_input.get("hypothesis_id", ""),
                    evidence_type=tool_input.get("evidence_type", "neutral"),
                    source_type=tool_input.get("source_type", ""),
                    source_id=tool_input.get("source_id", ""),
                    evidence_level=int(tool_input.get("evidence_level", 0)),
                )
                investigation.record_finding(finding)
                yield FindingRecorded(
                    title=finding.title,
                    detail=finding.detail,
                    hypothesis_id=finding.hypothesis_id,
                    evidence_type=finding.evidence_type,
                    evidence=finding.evidence,
                    source_type=finding.source_type,
                    source_id=finding.source_id,
                    evidence_level=finding.evidence_level,
                    investigation_id=investigation.id,
                )

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content_for_model,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # B. Body-of-evidence grading (Haiku, 1 call)
    evidence_grade = ""
    assessment = ""
    if investigation.findings:
        findings_for_grading = "\n".join(
            f"- [level={f.evidence_level}] {f.title}: {f.detail}" for f in investigation.findings
        )
        grade_response = await summarizer.create_message(
            system=build_literature_assessment_prompt(),
            messages=[{"role": "user", "content": findings_for_grading}],
            tools=[],
            output_config=_build_output_config(LITERATURE_GRADING_SCHEMA),
        )
        cost.add_usage(
            grade_response.input_tokens,
            grade_response.output_tokens,
            summarizer.model,
            cache_read_tokens=grade_response.cache_read_input_tokens,
            cache_write_tokens=grade_response.cache_write_input_tokens,
        )
        grade_text = ""
        for block in grade_response.content:
            if block.get("type") == "text":
                grade_text += block["text"]
        grade_data = json.loads(grade_text)
        evidence_grade = grade_data.get("evidence_grade", "")
        assessment = grade_data.get("assessment", "")

    # C. Yield LiteratureSurveyCompleted event
    yield LiteratureSurveyCompleted(
        pico=pico,
        search_queries=search_queries,
        total_results=total_results,
        included_results=len(investigation.findings),
        evidence_grade=evidence_grade,
        assessment=assessment,
        investigation_id=investigation.id,
    )
