from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.prompts import SUMMARIZER_PROMPT
from ehrlich.investigation.domain.events import (
    DomainEvent,
    FindingRecorded,
    NegativeControlRecorded,
    OutputSummarized,
    Thinking,
    ToolCalled,
    ToolResultEvent,
    VisualizationRendered,
)
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.negative_control import NegativeControl

if TYPE_CHECKING:
    import asyncio
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.cost_tracker import CostTracker
    from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.experiment import Experiment
    from ehrlich.investigation.domain.hypothesis import Hypothesis
    from ehrlich.investigation.domain.investigation import Investigation
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)

_COMPACT_SCHEMAS: dict[str, list[str]] = {
    "compute_descriptors": ["molecular_weight", "logp", "tpsa", "hbd", "hba", "qed", "num_rings"],
    "compute_fingerprint": ["fingerprint_type", "num_bits"],
    "validate_smiles": ["valid", "canonical_smiles"],
    "explore_dataset": ["name", "target", "size", "active_count"],
    "search_bioactivity": ["target", "size", "active_count"],
    "search_protein_targets": ["query", "count", "targets"],
    "tanimoto_similarity": ["similarity"],
}


def _compact_result(tool_name: str, result: str) -> str:
    schema = _COMPACT_SCHEMAS.get(tool_name)
    if not schema:
        return result
    try:
        data = json.loads(result)
        compacted = {k: data[k] for k in schema if k in data}
        return json.dumps(compacted)
    except (json.JSONDecodeError, TypeError):
        return result


async def summarize_output(
    summarizer: AnthropicClientAdapter,
    cost: CostTracker,
    tool_name: str,
    output: str,
    investigation_id: str,
    threshold: int,
) -> tuple[str, OutputSummarized | None]:
    if len(output) <= threshold:
        return output, None

    response = await summarizer.create_message(
        system=SUMMARIZER_PROMPT,
        messages=[
            {"role": "user", "content": f"Tool: {tool_name}\nOutput:\n{output}"},
        ],
        tools=[],
    )
    cost.add_usage(
        response.input_tokens,
        response.output_tokens,
        summarizer.model,
        cache_read_tokens=response.cache_read_input_tokens,
        cache_write_tokens=response.cache_write_input_tokens,
    )
    summarized = ""
    for block in response.content:
        if block["type"] == "text":
            summarized += block["text"]

    event = OutputSummarized(
        tool_name=tool_name,
        original_length=len(output),
        summarized_length=len(summarized),
        investigation_id=investigation_id,
    )
    return summarized, event


def maybe_viz_event(
    result_str: str,
    experiment_id: str,
    investigation_id: str,
) -> VisualizationRendered | None:
    """If a tool result contains viz_type, build a VisualizationRendered event."""
    try:
        data = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict) or "viz_type" not in data:
        return None
    return VisualizationRendered(
        investigation_id=investigation_id,
        experiment_id=experiment_id,
        viz_type=data["viz_type"],
        title=data.get("title", ""),
        data=data.get("data", {}),
        config=data.get("config", {}),
        domain=data.get("config", {}).get("domain", ""),
    )


async def run_researcher_experiment(
    researcher: AnthropicClientAdapter,
    summarizer: AnthropicClientAdapter,
    dispatcher: ToolDispatcher,
    registry: ToolRegistry,
    active_config: DomainConfig | None,
    researcher_prompt: str,
    summarizer_threshold: int,
    max_iterations: int,
    investigation: Investigation,
    hypothesis: Hypothesis,
    experiment: Experiment,
    cost: CostTracker,
    design: dict[str, Any],
    state_lock: asyncio.Lock,
    sibling_context: str = "",
) -> AsyncGenerator[DomainEvent, None]:
    planned = set(experiment.tool_plan) if experiment.tool_plan else set()
    control_tools = {"record_finding", "record_negative_control"}
    if planned:
        allowed = planned | control_tools
        tool_schemas = [t for t in registry.list_schemas() if t["name"] in allowed]
    elif active_config:
        excluded = {
            "conclude_investigation",
            "propose_hypothesis",
            "design_experiment",
            "evaluate_hypothesis",
        }
        domain_schemas = registry.list_schemas_for_domain(active_config.tool_tags)
        tool_schemas = [t for t in domain_schemas if t["name"] not in excluded]
    else:
        excluded = {
            "conclude_investigation",
            "propose_hypothesis",
            "design_experiment",
            "evaluate_hypothesis",
        }
        tool_schemas = [t for t in registry.list_schemas() if t["name"] not in excluded]

    exp_controls = ", ".join(experiment.controls) or "None specified"
    sibling_section = ""
    if sibling_context:
        sibling_section = (
            f"\n\n<parallel_experiment>\n"
            f"A parallel researcher is simultaneously testing a different hypothesis:\n"
            f"{sibling_context}\n\n"
            f"Avoid duplicating their queries. Use different search terms, "
            f"data sources, or analytical approaches where your experiment "
            f"design allows flexibility.\n"
            f"</parallel_experiment>"
        )
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"Research prompt: {investigation.prompt}\n\n"
                f"Hypothesis: {hypothesis.statement}\n"
                f"Mechanism: {hypothesis.rationale}\n"
                f"Prediction: {hypothesis.prediction or 'N/A'}\n"
                f"Hypothesis success criteria: {hypothesis.success_criteria or 'N/A'}\n"
                f"Hypothesis failure criteria: {hypothesis.failure_criteria or 'N/A'}\n"
                f"Scope: {hypothesis.scope or 'N/A'}\n\n"
                f"Experiment: {experiment.description}\n"
                f"Planned tools: {', '.join(experiment.tool_plan)}\n"
                f"Controls: {exp_controls}\n"
                f"Analysis plan: {experiment.analysis_plan or 'N/A'}\n"
                f"Experiment success criteria: {experiment.success_criteria or 'N/A'}\n"
                f"Experiment failure criteria: {experiment.failure_criteria or 'N/A'}\n\n"
                f"Execute this experiment. Compare results against the "
                f"pre-defined success/failure criteria. Link all findings to "
                f"hypothesis_id='{hypothesis.id}'." + sibling_section
            ),
        },
    ]

    for _iteration in range(max_iterations):
        investigation.iteration += 1
        tool_choice = {"type": "any"} if _iteration == 0 else None
        response = await researcher.create_message(
            system=researcher_prompt,
            messages=messages,
            tools=tool_schemas,
            tool_choice=tool_choice,
        )
        async with state_lock:
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
            async with state_lock:
                cost.add_tool_call()

            yield ToolCalled(
                tool_name=tool_name,
                tool_input=tool_input,
                experiment_id=experiment.id,
                investigation_id=investigation.id,
            )

            result_str = await dispatcher.dispatch(tool_name, tool_input, investigation)
            result_str = _compact_result(tool_name, result_str)

            summarized_str, summarize_event = await summarize_output(
                summarizer, cost, tool_name, result_str, investigation.id, summarizer_threshold
            )
            if summarize_event is not None:
                yield summarize_event

            content_for_model = summarized_str if summarize_event else result_str
            preview = result_str[:1500] if len(result_str) > 1500 else result_str
            yield ToolResultEvent(
                tool_name=tool_name,
                result_preview=preview,
                experiment_id=experiment.id,
                investigation_id=investigation.id,
            )

            # Emit visualization event if tool returned viz payload
            viz_event = maybe_viz_event(result_str, experiment.id, investigation.id)
            if viz_event is not None:
                yield viz_event

            if tool_name == "record_finding":
                h_id = tool_input.get("hypothesis_id", hypothesis.id)
                e_type = tool_input.get("evidence_type", "neutral")
                finding = Finding(
                    title=tool_input.get("title", ""),
                    detail=tool_input.get("detail", ""),
                    evidence=tool_input.get("evidence", ""),
                    hypothesis_id=h_id,
                    evidence_type=e_type,
                    source_type=tool_input.get("source_type", ""),
                    source_id=tool_input.get("source_id", ""),
                    evidence_level=int(tool_input.get("evidence_level", 0)),
                )
                async with state_lock:
                    investigation.record_finding(finding)
                    h = investigation.get_hypothesis(h_id)
                    if h:
                        if e_type == "supporting":
                            h.supporting_evidence.append(finding.title)
                        elif e_type == "contradicting":
                            h.contradicting_evidence.append(finding.title)
                yield FindingRecorded(
                    title=finding.title,
                    detail=finding.detail,
                    hypothesis_id=h_id,
                    evidence_type=e_type,
                    evidence=finding.evidence,
                    source_type=finding.source_type,
                    source_id=finding.source_id,
                    evidence_level=finding.evidence_level,
                    investigation_id=investigation.id,
                )

            if tool_name == "train_model":
                try:
                    train_result = json.loads(result_str)
                    if isinstance(train_result, dict) and "model_id" in train_result:
                        async with state_lock:
                            investigation.trained_model_ids.append(train_result["model_id"])
                except (json.JSONDecodeError, TypeError):
                    pass

            if tool_name == "record_negative_control":
                control = NegativeControl(
                    identifier=tool_input.get("identifier", tool_input.get("smiles", "")),
                    identifier_type=tool_input.get("identifier_type", ""),
                    name=tool_input.get("name", ""),
                    score=float(
                        tool_input.get("score", tool_input.get("prediction_score", 0.0))
                    ),
                    threshold=float(tool_input.get("threshold", 0.5)),
                    source=tool_input.get("source", ""),
                )
                async with state_lock:
                    investigation.add_negative_control(control)
                yield NegativeControlRecorded(
                    identifier=control.identifier,
                    identifier_type=control.identifier_type,
                    name=control.name,
                    score=control.score,
                    threshold=control.threshold,
                    correctly_classified=(control.correctly_classified),
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
