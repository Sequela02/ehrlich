"""Investigation phase runners extracted from MultiModelOrchestrator.run().

Each function runs one phase of the investigation pipeline, yielding
DomainEvent objects. The orchestrator's run() method delegates to these
in sequence.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.batch_executor import run_experiment_batch
from ehrlich.investigation.application.diagram_builder import generate_diagram
from ehrlich.investigation.application.prompts.builders import (
    build_pico_and_classification_prompt,
    build_researcher_prompt,
)
from ehrlich.investigation.application.prompts.constants import (
    DIRECTOR_EVALUATION_PROMPT,
    DIRECTOR_EXPERIMENT_PROMPT,
    DIRECTOR_FORMULATION_PROMPT,
    DIRECTOR_SYNTHESIS_PROMPT,
)
from ehrlich.investigation.application.prompts.director import (
    build_experiment_prompt,
    build_formulation_prompt,
    build_multi_investigation_context,
    build_synthesis_prompt,
)
from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.domain_config import merge_domain_configs
from ehrlich.investigation.domain.events import (
    CostUpdate,
    DomainDetected,
    DomainEvent,
    ExperimentCompleted,
    ExperimentStarted,
    HypothesisApprovalRequested,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    NegativeControlRecorded,
    PhaseChanged,
    PositiveControlRecorded,
    ValidationMetricsComputed,
)
from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.domain.positive_control import PositiveControl
from ehrlich.investigation.domain.schemas import (
    EVALUATION_SCHEMA,
    EXPERIMENT_DESIGN_SCHEMA,
    FORMULATION_SCHEMA,
    PICO_SCHEMA,
    SYNTHESIS_SCHEMA,
)
from ehrlich.investigation.domain.validation import compute_z_prime

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from ehrlich.investigation.application.cost_tracker import CostTracker
    from ehrlich.investigation.application.tool_dispatcher import ToolDispatcher
    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.domain_registry import DomainRegistry
    from ehrlich.investigation.domain.repository import InvestigationRepository
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _DirectorResult:
    data: dict[str, Any]
    thinking: str


def _build_output_config(schema: dict[str, Any]) -> dict[str, Any]:
    return {"format": {"type": "json_schema", "schema": schema}}


# ---------------------------------------------------------------------------
# Phase 1: Classification & PICO
# ---------------------------------------------------------------------------


async def run_classification_phase(
    investigation: Investigation,
    cost: CostTracker,
    summarizer: AnthropicClientAdapter,
    uploaded_data_context: str,
    repository: InvestigationRepository | None,
    domain_registry: DomainRegistry | None,
    director_call: Callable[..., AsyncGenerator[Any, None]],
) -> AsyncGenerator[DomainEvent | dict[str, Any], None]:
    """Phase 1: Classify domain + PICO decomposition.

    Yields DomainEvent instances and finally a special dict sentinel
    ``{"__phase_result__": ...}`` containing the phase outputs so the
    orchestrator can capture them without shared mutable state.
    """
    yield PhaseChanged(
        phase=1,
        name="Classification & PICO",
        description="Detecting domain and decomposing research question",
        investigation_id=investigation.id,
    )

    pico: dict[str, Any] = {}
    prior_context = ""
    active_config: DomainConfig | None = None
    researcher_prompt = ""

    if repository:
        valid_categories: frozenset[str] = frozenset()
        if domain_registry:
            valid_categories = domain_registry.all_categories()
        pico_prompt = build_pico_and_classification_prompt(valid_categories, uploaded_data_context)
        pico_response = await summarizer.create_message(
            system=pico_prompt,
            messages=[{"role": "user", "content": investigation.prompt}],
            tools=[],
            output_config=_build_output_config(PICO_SCHEMA),
        )
        cost.add_usage(
            pico_response.input_tokens,
            pico_response.output_tokens,
            summarizer.model,
            cache_read_tokens=pico_response.cache_read_input_tokens,
            cache_write_tokens=pico_response.cache_write_input_tokens,
        )
        pico_text = ""
        for block in pico_response.content:
            if block.get("type") == "text":
                pico_text += block["text"]
        pico_data = json.loads(pico_text)
        raw_domain = pico_data.get("domain", "other")
        domain_categories: list[str] = (
            [d.strip().lower() for d in raw_domain]
            if isinstance(raw_domain, list)
            else [raw_domain.strip().lower()]
        )
        investigation.domain = ", ".join(domain_categories)
        pico = {
            "population": pico_data.get("population", ""),
            "intervention": pico_data.get("intervention", ""),
            "comparison": pico_data.get("comparison", ""),
            "outcome": pico_data.get("outcome", ""),
            "search_terms": pico_data.get("search_terms", []),
        }

        # Detect domain configs (multi-domain) and yield event
        if domain_registry:
            detected_configs, is_fallback = domain_registry.detect(domain_categories)
            active_config = merge_domain_configs(detected_configs)
            researcher_prompt = build_researcher_prompt(active_config, uploaded_data_context)
            yield DomainDetected(
                domain=active_config.name,
                display_config=active_config.to_display_dict(),
                is_fallback=is_fallback,
                investigation_id=investigation.id,
            )

        all_investigations = await repository.list_all()
        related = [
            inv
            for inv in all_investigations
            if inv.status == InvestigationStatus.COMPLETED
            and inv.id != investigation.id
            and any(cat in inv.domain for cat in domain_categories)
        ]
        if related:
            prior_context = build_multi_investigation_context(related)

    yield {
        "__phase_result__": {
            "pico": pico,
            "prior_context": prior_context,
            "active_config": active_config,
            "researcher_prompt": researcher_prompt,
        }
    }


# ---------------------------------------------------------------------------
# Phase 3: Hypothesis Formulation
# ---------------------------------------------------------------------------


async def run_formulation_phase(
    investigation: Investigation,
    cost: CostTracker,
    active_config: DomainConfig | None,
    uploaded_data_context: str,
    prior_context: str,
    pico: dict[str, Any],
    require_approval: bool,
    approval_event: asyncio.Event,
    director_call: Callable[..., AsyncGenerator[Any, None]],
    cost_event_fn: Callable[..., CostUpdate],
) -> AsyncGenerator[DomainEvent | dict[str, Any], None]:
    """Phase 3: Director formulates hypotheses, optionally waits for approval."""
    from ehrlich.investigation.application.literature_survey import build_literature_context

    yield PhaseChanged(
        phase=3,
        name="Formulation",
        description="Director formulating testable hypotheses from literature evidence",
        investigation_id=investigation.id,
    )
    prior_section = f"\n\n{prior_context}" if prior_context else ""
    formulation_prompt = (
        build_formulation_prompt(active_config, uploaded_data_context)
        if active_config
        else DIRECTOR_FORMULATION_PROMPT
    )

    # Build structured XML context from PICO + findings
    literature_context = build_literature_context(investigation, pico)
    result = _DirectorResult(data={}, thinking="")
    async for director_event in director_call(
        cost,
        formulation_prompt,
        f"Research prompt: {investigation.prompt}\n\n"
        f"{literature_context}\n\n"
        f"Formulate 2-4 testable hypotheses and identify negative controls." + prior_section,
        investigation.id,
        output_config=_build_output_config(FORMULATION_SCHEMA),
    ):
        if isinstance(director_event, _DirectorResult):
            result = director_event
        else:
            yield director_event
    formulation = result.data

    # Create hypothesis entities
    for h_data in formulation.get("hypotheses", []):
        hypothesis = Hypothesis(
            statement=h_data.get("statement", ""),
            rationale=h_data.get("rationale", ""),
            prediction=h_data.get("prediction", ""),
            null_prediction=h_data.get("null_prediction", ""),
            success_criteria=h_data.get("success_criteria", ""),
            failure_criteria=h_data.get("failure_criteria", ""),
            scope=h_data.get("scope", ""),
            hypothesis_type=h_data.get("hypothesis_type", ""),
            prior_confidence=min(1.0, max(0.0, h_data.get("prior_confidence", 0.0))),
        )
        investigation.add_hypothesis(hypothesis)
        yield HypothesisFormulated(
            hypothesis_id=hypothesis.id,
            statement=hypothesis.statement,
            rationale=hypothesis.rationale,
            prediction=hypothesis.prediction,
            null_prediction=hypothesis.null_prediction,
            success_criteria=hypothesis.success_criteria,
            failure_criteria=hypothesis.failure_criteria,
            scope=hypothesis.scope,
            hypothesis_type=hypothesis.hypothesis_type,
            prior_confidence=hypothesis.prior_confidence,
            parent_id="",
            investigation_id=investigation.id,
        )

    # Store control suggestions for later
    neg_control_suggestions = formulation.get("negative_controls", [])
    pos_control_suggestions = formulation.get("positive_controls", [])
    yield cost_event_fn(cost, investigation.id)

    # Request user approval before testing
    if require_approval:
        yield HypothesisApprovalRequested(
            hypotheses=[
                {
                    "id": h.id,
                    "statement": h.statement,
                    "rationale": h.rationale,
                    "prediction": h.prediction,
                    "scope": h.scope,
                    "hypothesis_type": h.hypothesis_type,
                    "prior_confidence": h.prior_confidence,
                }
                for h in investigation.hypotheses
                if h.status == HypothesisStatus.PROPOSED
            ],
            investigation_id=investigation.id,
        )
        try:
            await asyncio.wait_for(approval_event.wait(), timeout=300)
        except TimeoutError:
            logger.info("Approval timeout, auto-approving all hypotheses")
        approval_event.clear()

    yield {
        "__phase_result__": {
            "neg_control_suggestions": neg_control_suggestions,
            "pos_control_suggestions": pos_control_suggestions,
        }
    }


# ---------------------------------------------------------------------------
# Phase 4: Hypothesis Testing
# ---------------------------------------------------------------------------


async def run_hypothesis_testing_phase(
    investigation: Investigation,
    cost: CostTracker,
    active_config: DomainConfig | None,
    uploaded_data_context: str,
    researcher_prompt: str,
    researcher: AnthropicClientAdapter,
    summarizer: AnthropicClientAdapter,
    dispatcher: ToolDispatcher,
    registry: ToolRegistry,
    max_hypotheses: int,
    max_iterations_per_experiment: int,
    summarizer_threshold: int,
    state_lock: asyncio.Lock,
    director_call: Callable[..., AsyncGenerator[Any, None]],
    cost_event_fn: Callable[..., CostUpdate],
) -> AsyncGenerator[DomainEvent, None]:
    """Phase 4: Batched parallel hypothesis testing + Director evaluation loop."""

    yield PhaseChanged(
        phase=4,
        name="Hypothesis Testing",
        description="Running parallel experiments to test hypotheses",
        investigation_id=investigation.id,
    )
    tested = 0
    while tested < max_hypotheses:
        proposed = [h for h in investigation.hypotheses if h.status == HypothesisStatus.PROPOSED]
        if not proposed:
            break

        # Take up to 2 hypotheses per batch
        batch_hypotheses = proposed[:2]
        batch: list[tuple[Hypothesis, Experiment, dict[str, Any]]] = []
        prior_designs: list[str] = []

        for hypothesis in batch_hypotheses:
            hypothesis.status = HypothesisStatus.TESTING
            investigation.current_hypothesis_id = hypothesis.id
            tested += 1

            # Director designs experiment
            if active_config:
                tools_csv = ", ".join(registry.list_tools_for_domain(active_config.tool_tags))
            else:
                tools_csv = ", ".join(registry.list_tools())
            experiment_prompt = (
                build_experiment_prompt(active_config, uploaded_data_context)
                if active_config
                else DIRECTOR_EXPERIMENT_PROMPT
            )
            sibling_section = ""
            if prior_designs:
                joined = "\n---\n".join(prior_designs)
                sibling_section = (
                    f"\n\n<sibling_experiments>\n{joined}\n"
                    f"</sibling_experiments>\n\n"
                    f"Your experiment runs in PARALLEL with the above. "
                    f"Design a DIFFERENT approach: use different tools, "
                    f"data sources, or validation strategies."
                )

            result = _DirectorResult(data={}, thinking="")
            async for director_event in director_call(
                cost,
                experiment_prompt,
                f"Research prompt: {investigation.prompt}"
                f"\n\nHypothesis to test: "
                f"{hypothesis.statement}\n"
                f"Rationale: {hypothesis.rationale}\n\n"
                f"Available tools: {tools_csv}\n\n"
                f"Design an experiment to test this "
                f"hypothesis." + sibling_section,
                investigation.id,
                output_config=_build_output_config(EXPERIMENT_DESIGN_SCHEMA),
            ):
                if isinstance(director_event, _DirectorResult):
                    result = director_event
                else:
                    yield director_event
            design = result.data

            desc = design.get(
                "description",
                f"Test: {hypothesis.statement}",
            )
            prior_designs.append(
                f"Hypothesis: {hypothesis.statement}\n"
                f"Experiment: {desc}\n"
                f"Tools: {', '.join(design.get('tool_plan', []))}"
            )
            experiment = Experiment(
                hypothesis_id=hypothesis.id,
                description=desc,
                tool_plan=design.get("tool_plan", []),
                independent_variable=design.get("independent_variable", ""),
                dependent_variable=design.get("dependent_variable", ""),
                controls=design.get("controls", []),
                confounders=design.get("confounders", []),
                analysis_plan=design.get("analysis_plan", ""),
                success_criteria=design.get("success_criteria", ""),
                failure_criteria=design.get("failure_criteria", ""),
            )
            experiment.status = ExperimentStatus.RUNNING
            investigation.add_experiment(experiment)
            investigation.current_experiment_id = experiment.id

            yield ExperimentStarted(
                experiment_id=experiment.id,
                hypothesis_id=hypothesis.id,
                description=experiment.description,
                independent_variable=experiment.independent_variable,
                dependent_variable=experiment.dependent_variable,
                controls=experiment.controls,
                analysis_plan=experiment.analysis_plan,
                success_criteria=experiment.success_criteria,
                failure_criteria=experiment.failure_criteria,
                investigation_id=investigation.id,
            )

            batch.append((hypothesis, experiment, design))

        # Run batch (parallel if 2, sequential if 1)
        exp_tool_count = cost.tool_calls
        exp_finding_count = len(investigation.findings)
        async for event in run_experiment_batch(
            researcher,
            summarizer,
            dispatcher,
            registry,
            active_config,
            researcher_prompt,
            summarizer_threshold,
            max_iterations_per_experiment,
            investigation,
            batch,
            cost,
            state_lock,
        ):
            yield event

        # Mark completed + Director evaluates each
        for hypothesis, experiment, _design in batch:
            experiment.status = ExperimentStatus.COMPLETED
            yield ExperimentCompleted(
                experiment_id=experiment.id,
                hypothesis_id=hypothesis.id,
                tool_count=(cost.tool_calls - exp_tool_count),
                finding_count=(len(investigation.findings) - exp_finding_count),
                investigation_id=investigation.id,
            )

            # Director evaluates hypothesis
            findings_for_hyp = [
                f for f in investigation.findings if f.hypothesis_id == hypothesis.id
            ]
            findings_text = "\n".join(
                f"- [{f.evidence_type}] {f.title}: {f.detail}" for f in findings_for_hyp
            )
            controls_text = ", ".join(experiment.controls) or "None specified"
            result = _DirectorResult(data={}, thinking="")
            async for director_event in director_call(
                cost,
                DIRECTOR_EVALUATION_PROMPT,
                f"Hypothesis: {hypothesis.statement}\n"
                f"Mechanism: {hypothesis.rationale}\n"
                f"Prediction: {hypothesis.prediction or 'N/A'}\n"
                f"Hypothesis success criteria: {hypothesis.success_criteria or 'N/A'}\n"
                f"Hypothesis failure criteria: {hypothesis.failure_criteria or 'N/A'}\n"
                f"Prior confidence: {hypothesis.prior_confidence}\n\n"
                f"Experiment: {experiment.description}\n"
                f"Independent variable: {experiment.independent_variable or 'N/A'}\n"
                f"Dependent variable: {experiment.dependent_variable or 'N/A'}\n"
                f"Controls: {controls_text}\n"
                f"Analysis plan: {experiment.analysis_plan or 'N/A'}\n"
                f"Experiment success criteria: {experiment.success_criteria or 'N/A'}\n"
                f"Experiment failure criteria: {experiment.failure_criteria or 'N/A'}\n"
                f"\nFindings:\n{findings_text}\n\n"
                f"Compare the findings against the pre-defined "
                f"success/failure criteria. Evaluate this hypothesis.",
                investigation.id,
                output_config=_build_output_config(EVALUATION_SCHEMA),
            ):
                if isinstance(director_event, _DirectorResult):
                    result = director_event
                else:
                    yield director_event
            evaluation = result.data

            eval_status = evaluation.get("status", "supported")
            eval_confidence = float(evaluation.get("confidence", 0.5))
            eval_certainty = evaluation.get("certainty_of_evidence", "")
            status_map = {
                "supported": HypothesisStatus.SUPPORTED,
                "refuted": HypothesisStatus.REFUTED,
                "revised": HypothesisStatus.REVISED,
            }
            hypothesis.status = status_map.get(eval_status, HypothesisStatus.SUPPORTED)
            hypothesis.confidence = max(0.0, min(1.0, eval_confidence))
            hypothesis.certainty_of_evidence = eval_certainty

            logger.info(
                "Hypothesis %s convergence: %s",
                hypothesis.id,
                evaluation.get("evidence_convergence", ""),
            )

            yield HypothesisEvaluated(
                hypothesis_id=hypothesis.id,
                status=eval_status,
                confidence=eval_confidence,
                reasoning=evaluation.get("reasoning", ""),
                certainty_of_evidence=eval_certainty,
                investigation_id=investigation.id,
            )

            # If revised, add new hypothesis to queue
            if eval_status == "revised" and evaluation.get("revision"):
                revised = Hypothesis(
                    statement=evaluation["revision"],
                    rationale=evaluation.get(
                        "reasoning",
                        "Revised from prior evidence",
                    ),
                    prediction=evaluation.get("prediction", hypothesis.prediction),
                    success_criteria=evaluation.get(
                        "success_criteria", hypothesis.success_criteria
                    ),
                    failure_criteria=evaluation.get(
                        "failure_criteria", hypothesis.failure_criteria
                    ),
                    scope=hypothesis.scope,
                    hypothesis_type=hypothesis.hypothesis_type,
                    parent_id=hypothesis.id,
                )
                investigation.add_hypothesis(revised)
                yield HypothesisFormulated(
                    hypothesis_id=revised.id,
                    statement=revised.statement,
                    rationale=revised.rationale,
                    prediction=revised.prediction,
                    success_criteria=revised.success_criteria,
                    failure_criteria=revised.failure_criteria,
                    scope=revised.scope,
                    hypothesis_type=revised.hypothesis_type,
                    parent_id=hypothesis.id,
                    investigation_id=investigation.id,
                )

        yield cost_event_fn(cost, investigation.id)


# ---------------------------------------------------------------------------
# Phase 5: Controls Validation
# ---------------------------------------------------------------------------


async def run_controls_phase(
    investigation: Investigation,
    cost: CostTracker,
    active_config: DomainConfig | None,
    neg_control_suggestions: list[dict[str, Any]],
    pos_control_suggestions: list[dict[str, Any]],
    dispatcher: ToolDispatcher,
) -> AsyncGenerator[DomainEvent | dict[str, Any], None]:
    """Phase 5: Validate controls and compute Z'-factor."""
    yield PhaseChanged(
        phase=5,
        name="Controls Validation",
        description="Validating model with positive and negative controls",
        investigation_id=investigation.id,
    )

    # Score controls through trained model if available
    score_map: dict[str, float] = {}
    has_model = bool(investigation.trained_model_ids)
    is_molecular = active_config is not None and any(
        t in active_config.tool_tags for t in ("chemistry", "prediction")
    )
    if has_model and is_molecular:
        model_id = investigation.trained_model_ids[-1]
        all_identifiers = [
            nc.get("identifier", nc.get("smiles", ""))
            for nc in neg_control_suggestions
            if nc.get("identifier", nc.get("smiles", ""))
        ] + [pc.get("identifier", "") for pc in pos_control_suggestions if pc.get("identifier", "")]
        if all_identifiers:
            try:
                pred_result = await dispatcher.dispatch(
                    "predict_candidates",
                    {"smiles_list": all_identifiers, "model_id": model_id},
                    investigation,
                )
                pred_data = json.loads(pred_result)
                if isinstance(pred_data, dict):
                    for entry in pred_data.get("predictions", []):
                        smiles = entry.get("smiles", "")
                        prob = float(entry.get("probability", 0.0))
                        if smiles:
                            score_map[smiles] = prob
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning("Failed to score controls via model %s", model_id)

    for nc_data in neg_control_suggestions:
        identifier = nc_data.get("identifier", nc_data.get("smiles", ""))
        name = nc_data.get("name", "")
        source = nc_data.get("source", "")
        if identifier:
            nc_score = score_map.get(identifier, 0.0)
            control = NegativeControl(
                identifier=identifier,
                identifier_type=nc_data.get("identifier_type", ""),
                name=name,
                score=nc_score,
                source=source,
            )
            investigation.add_negative_control(control)
            yield NegativeControlRecorded(
                identifier=identifier,
                identifier_type=control.identifier_type,
                name=name,
                score=nc_score,
                correctly_classified=control.correctly_classified,
                investigation_id=investigation.id,
            )

    for pc_data in pos_control_suggestions:
        pc_identifier = pc_data.get("identifier", "")
        pc_name = pc_data.get("name", "")
        known_activity = pc_data.get("known_activity", "")
        pc_source = pc_data.get("source", "")
        if pc_identifier:
            pc_score = score_map.get(pc_identifier, 0.0)
            pos_control = PositiveControl(
                identifier=pc_identifier,
                identifier_type=pc_data.get("identifier_type", ""),
                name=pc_name,
                known_activity=known_activity,
                source=pc_source,
                score=pc_score,
            )
            investigation.add_positive_control(pos_control)
            yield PositiveControlRecorded(
                identifier=pc_identifier,
                identifier_type=pos_control.identifier_type,
                name=pc_name,
                known_activity=known_activity,
                score=pc_score,
                correctly_classified=pos_control.correctly_classified,
                investigation_id=investigation.id,
            )

    # Compute Z'-factor from control scores
    pos_scores = [pc.score for pc in investigation.positive_controls]
    neg_scores = [nc.score for nc in investigation.negative_controls]
    z_metrics = compute_z_prime(pos_scores, neg_scores)
    validation_metrics = {
        "z_prime": z_metrics.z_prime,
        "z_prime_quality": z_metrics.quality,
        "positive_mean": z_metrics.positive_mean,
        "positive_std": z_metrics.positive_std,
        "negative_mean": z_metrics.negative_mean,
        "negative_std": z_metrics.negative_std,
        "positive_count": z_metrics.positive_count,
        "negative_count": z_metrics.negative_count,
    }
    yield ValidationMetricsComputed(
        z_prime=z_metrics.z_prime,
        z_prime_quality=z_metrics.quality,
        positive_control_count=z_metrics.positive_count,
        negative_control_count=z_metrics.negative_count,
        positive_mean=z_metrics.positive_mean,
        negative_mean=z_metrics.negative_mean,
        investigation_id=investigation.id,
    )

    yield {"__phase_result__": {"validation_metrics": validation_metrics}}


# ---------------------------------------------------------------------------
# Phase 6: Synthesis
# ---------------------------------------------------------------------------


async def run_synthesis_phase(
    investigation: Investigation,
    cost: CostTracker,
    active_config: DomainConfig | None,
    validation_metrics: dict[str, Any],
    mcp_bridge: MCPBridge | None,
    director_call: Callable[..., AsyncGenerator[Any, None]],
) -> AsyncGenerator[DomainEvent, None]:
    """Phase 6: Director synthesis + candidate ranking + diagram generation."""

    yield PhaseChanged(
        phase=6,
        name="Synthesis",
        description="Director synthesizing final report and ranking candidates",
        investigation_id=investigation.id,
    )
    all_findings_text = "\n".join(
        f"- [H:{f.hypothesis_id}|{f.evidence_type}] {f.title}: {f.detail}"
        for f in investigation.findings
    )
    hypothesis_text = "\n".join(
        f"- {h.id}: {h.statement} -> {h.status.value} (confidence: {h.confidence})"
        for h in investigation.hypotheses
    )
    nc_text = "\n".join(
        f"- {nc.name}: score={nc.score}, correct={nc.correctly_classified}"
        for nc in investigation.negative_controls
    )
    pc_text = "\n".join(
        f"- {pc.name}: known_activity={pc.known_activity}, score={pc.score}"
        for pc in investigation.positive_controls
    )

    # Build validation metrics text for synthesis context
    vm_text = ""
    if validation_metrics.get("z_prime") is not None:
        vm_text = (
            f"\nValidation metrics:\n"
            f"- Z'-factor: {validation_metrics['z_prime']:.3f} "
            f"({validation_metrics['z_prime_quality']})\n"
            f"- Positive controls: mean={validation_metrics['positive_mean']:.3f}, "
            f"std={validation_metrics['positive_std']:.3f}, "
            f"n={validation_metrics['positive_count']}\n"
            f"- Negative controls: mean={validation_metrics['negative_mean']:.3f}, "
            f"std={validation_metrics['negative_std']:.3f}, "
            f"n={validation_metrics['negative_count']}\n"
        )
    else:
        vm_text = (
            f"\nValidation metrics: insufficient controls "
            f"(pos={validation_metrics.get('positive_count', 0)}, "
            f"neg={validation_metrics.get('negative_count', 0)})\n"
        )

    synthesis_prompt = (
        build_synthesis_prompt(active_config) if active_config else DIRECTOR_SYNTHESIS_PROMPT
    )
    result = _DirectorResult(data={}, thinking="")
    async for director_event in director_call(
        cost,
        synthesis_prompt,
        f"Original prompt: {investigation.prompt}\n\n"
        f"Hypothesis outcomes:\n{hypothesis_text}\n\n"
        f"All findings:\n{all_findings_text}\n\n"
        f"Negative controls:\n{nc_text or 'None recorded'}\n\n"
        f"Positive controls:\n{pc_text or 'None recorded'}\n\n"
        f"{vm_text}\n"
        f"Synthesize final report.",
        investigation.id,
        output_config=_build_output_config(SYNTHESIS_SCHEMA),
    ):
        if isinstance(director_event, _DirectorResult):
            result = director_event
        else:
            yield director_event
    synthesis = result.data

    # Apply synthesis
    validation_quality = synthesis.get("model_validation_quality", "insufficient")
    logger.info(
        "Investigation %s model_validation_quality: %s",
        investigation.id,
        validation_quality,
    )
    investigation.summary = synthesis.get("summary", "")
    raw_candidates = synthesis.get("candidates") or []
    candidates = [
        Candidate(
            identifier=c.get("identifier", c.get("smiles", "")),
            identifier_type=c.get("identifier_type", ""),
            name=c.get("name", ""),
            notes=c.get("rationale", c.get("notes", "")),
            rank=c.get("rank", i + 1),
            priority=c.get("priority", 0),
            scores={
                k: float(v) for k, v in c.get("scores", {}).items() if isinstance(v, (int, float))
            },
            attributes={k: str(v) for k, v in c.get("attributes", {}).items()},
        )
        for i, c in enumerate(raw_candidates)
    ]
    citations = synthesis.get("citations") or []
    investigation.set_candidates(candidates, citations)

    # Post-synthesis: generate Excalidraw diagram if MCP available
    diagram_url = ""
    if mcp_bridge and mcp_bridge.has_tool("excalidraw:create_view"):
        diagram_url = await generate_diagram(mcp_bridge, investigation)

    investigation.status = InvestigationStatus.COMPLETED
    investigation.cost_data = cost.to_dict()

    candidate_dicts = [
        {
            "identifier": c.identifier,
            "identifier_type": c.identifier_type,
            "name": c.name,
            "rank": c.rank,
            "priority": c.priority,
            "notes": c.notes,
            "scores": c.scores,
            "attributes": c.attributes,
        }
        for c in candidates
    ]
    finding_dicts = [
        {
            "title": f.title,
            "detail": f.detail,
            "hypothesis_id": f.hypothesis_id,
            "evidence_type": f.evidence_type,
            "evidence": f.evidence,
        }
        for f in investigation.findings
    ]
    hypothesis_dicts = [
        {
            "id": h.id,
            "statement": h.statement,
            "rationale": h.rationale,
            "status": h.status.value,
            "parent_id": h.parent_id,
            "confidence": h.confidence,
            "certainty_of_evidence": h.certainty_of_evidence,
            "supporting_evidence": h.supporting_evidence,
            "contradicting_evidence": h.contradicting_evidence,
        }
        for h in investigation.hypotheses
    ]
    nc_dicts = [
        {
            "identifier": nc.identifier,
            "identifier_type": nc.identifier_type,
            "name": nc.name,
            "score": nc.score,
            "threshold": nc.threshold,
            "correctly_classified": nc.correctly_classified,
            "source": nc.source,
        }
        for nc in investigation.negative_controls
    ]
    pc_dicts = [
        {
            "identifier": pc.identifier,
            "identifier_type": pc.identifier_type,
            "name": pc.name,
            "known_activity": pc.known_activity,
            "score": pc.score,
            "correctly_classified": pc.correctly_classified,
            "source": pc.source,
        }
        for pc in investigation.positive_controls
    ]
    yield InvestigationCompleted(
        investigation_id=investigation.id,
        candidate_count=len(candidates),
        summary=investigation.summary,
        cost=cost.to_dict(),
        candidates=candidate_dicts,
        findings=finding_dicts,
        hypotheses=hypothesis_dicts,
        negative_controls=nc_dicts,
        positive_controls=pc_dicts,
        validation_metrics=validation_metrics,
        diagram_url=diagram_url,
    )
