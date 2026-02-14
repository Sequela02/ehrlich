from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.researcher_executor import run_researcher_experiment

if TYPE_CHECKING:
    import asyncio
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.cost_tracker import CostTracker
    from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.events import DomainEvent
    from ehrlich.investigation.domain.experiment import Experiment
    from ehrlich.investigation.domain.hypothesis import Hypothesis
    from ehrlich.investigation.domain.investigation import Investigation
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter

logger = logging.getLogger(__name__)


async def run_experiment_batch(
    researcher: AnthropicClientAdapter,
    summarizer: AnthropicClientAdapter,
    dispatcher: ToolDispatcher,
    registry: ToolRegistry,
    active_config: DomainConfig | None,
    researcher_prompt: str,
    summarizer_threshold: int,
    max_iterations: int,
    investigation: Investigation,
    batch: list[tuple[Hypothesis, Experiment, dict[str, Any]]],
    cost: CostTracker,
    state_lock: asyncio.Lock,
) -> AsyncGenerator[DomainEvent, None]:
    """Run up to 2 experiments concurrently with sibling awareness."""
    if len(batch) == 1:
        h, exp, design = batch[0]
        async for event in run_researcher_experiment(
            researcher,
            summarizer,
            dispatcher,
            registry,
            active_config,
            researcher_prompt,
            summarizer_threshold,
            max_iterations,
            investigation,
            h,
            exp,
            cost,
            design,
            state_lock,
        ):
            yield event
        return

    # Build sibling context strings so each researcher knows what the other is doing
    sibling_contexts: list[str] = []
    for i, (_hyp, _exp, _design) in enumerate(batch):
        other_idx = 1 - i
        other_hyp, other_exp, other_design = batch[other_idx]
        sibling_contexts.append(
            f"Hypothesis: {other_hyp.statement}\n"
            f"Experiment: {other_exp.description}\n"
            f"Tools: {', '.join(other_design.get('tool_plan', []))}"
        )

    import asyncio

    queue: asyncio.Queue[DomainEvent | None] = asyncio.Queue()

    async def _run_one(
        hyp: Hypothesis,
        exp: Experiment,
        design: dict[str, Any],
        sib_ctx: str,
    ) -> None:
        try:
            async for ev in run_researcher_experiment(
                researcher,
                summarizer,
                dispatcher,
                registry,
                active_config,
                researcher_prompt,
                summarizer_threshold,
                max_iterations,
                investigation,
                hyp,
                exp,
                cost,
                design,
                state_lock,
                sibling_context=sib_ctx,
            ):
                await queue.put(ev)
        except Exception as e:
            logger.warning("Experiment %s failed: %s", exp.id, e)
        finally:
            await queue.put(None)

    tasks = [
        asyncio.create_task(_run_one(h, e, d, sc))
        for (h, e, d), sc in zip(batch, sibling_contexts, strict=True)
    ]

    done_count = 0
    while done_count < len(tasks):
        item: DomainEvent | None = await queue.get()
        if item is None:
            done_count += 1
            continue
        yield item

    await asyncio.gather(*tasks, return_exceptions=True)
