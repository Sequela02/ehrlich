from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.application.cost_tracker import CostTracker
from ehrlich.investigation.application.prompts import (
    DIRECTOR_EVALUATION_PROMPT,
    DIRECTOR_EXPERIMENT_PROMPT,
    DIRECTOR_FORMULATION_PROMPT,
    DIRECTOR_SYNTHESIS_PROMPT,
    RESEARCHER_EXPERIMENT_PROMPT,
    SUMMARIZER_PROMPT,
    build_experiment_prompt,
    build_formulation_prompt,
    build_literature_assessment_prompt,
    build_literature_survey_prompt,
    build_multi_investigation_context,
    build_pico_and_classification_prompt,
    build_researcher_prompt,
    build_synthesis_prompt,
)
from ehrlich.investigation.application.tool_cache import ToolCache
from ehrlich.investigation.domain.candidate import Candidate
from ehrlich.investigation.domain.domain_config import merge_domain_configs
from ehrlich.investigation.domain.events import (
    CostUpdate,
    DomainDetected,
    DomainEvent,
    ExperimentCompleted,
    ExperimentStarted,
    FindingRecorded,
    HypothesisApprovalRequested,
    HypothesisEvaluated,
    HypothesisFormulated,
    InvestigationCompleted,
    InvestigationError,
    LiteratureSurveyCompleted,
    NegativeControlRecorded,
    OutputSummarized,
    PhaseChanged,
    PositiveControlRecorded,
    Thinking,
    ToolCalled,
    ToolResultEvent,
    ValidationMetricsComputed,
    VisualizationRendered,
)
from ehrlich.investigation.domain.experiment import Experiment, ExperimentStatus
from ehrlich.investigation.domain.finding import Finding
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.domain.positive_control import PositiveControl
from ehrlich.investigation.domain.schemas import (
    EVALUATION_SCHEMA,
    EXPERIMENT_DESIGN_SCHEMA,
    FORMULATION_SCHEMA,
    LITERATURE_GRADING_SCHEMA,
    PICO_SCHEMA,
    SYNTHESIS_SCHEMA,
)
from ehrlich.investigation.domain.validation import compute_z_prime

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ehrlich.investigation.application.tool_registry import ToolRegistry
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.domain_registry import DomainRegistry
    from ehrlich.investigation.domain.mcp_config import MCPServerConfig
    from ehrlich.investigation.domain.repository import InvestigationRepository
    from ehrlich.investigation.infrastructure.anthropic_client import AnthropicClientAdapter
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge


@dataclass(frozen=True)
class _DirectorResult:
    data: dict[str, Any]
    thinking: str


def _build_output_config(schema: dict[str, Any]) -> dict[str, Any]:
    return {"format": {"type": "json_schema", "schema": schema}}

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
        self._active_config: DomainConfig | None = None
        self._researcher_prompt = RESEARCHER_EXPERIMENT_PROMPT
        self._cache = ToolCache()
        self._state_lock = asyncio.Lock()
        self._approval_event = asyncio.Event()
        self._investigation: Investigation | None = None

    def approve_hypotheses(
        self,
        approved_ids: list[str],
        rejected_ids: list[str],
    ) -> None:
        """Called by API to approve/reject hypotheses and unblock the loop."""
        if self._investigation:
            for h in self._investigation.hypotheses:
                if h.id in rejected_ids:
                    h.status = HypothesisStatus.REJECTED
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

    async def run(self, investigation: Investigation) -> AsyncGenerator[DomainEvent, None]:
        investigation.status = InvestigationStatus.RUNNING
        cost = CostTracker()
        pico: dict[str, Any] = {}

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
            # 1. Classify domain + PICO decomposition (single Haiku call)
            yield PhaseChanged(
                phase=1,
                name="Classification & PICO",
                description="Detecting domain and decomposing research question",
                investigation_id=investigation.id,
            )

            prior_context = ""
            if self._repository:
                valid_categories: frozenset[str] = frozenset()
                if self._domain_registry:
                    valid_categories = self._domain_registry.all_categories()
                pico_prompt = build_pico_and_classification_prompt(valid_categories)
                pico_response = await self._summarizer.create_message(
                    system=pico_prompt,
                    messages=[{"role": "user", "content": investigation.prompt}],
                    tools=[],
                    output_config=_build_output_config(PICO_SCHEMA),
                )
                cost.add_usage(
                    pico_response.input_tokens,
                    pico_response.output_tokens,
                    self._summarizer.model,
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
                if self._domain_registry:
                    detected_configs = self._domain_registry.detect(domain_categories)
                    self._active_config = merge_domain_configs(detected_configs)
                    self._researcher_prompt = build_researcher_prompt(self._active_config)
                    yield DomainDetected(
                        domain=self._active_config.name,
                        display_config=self._active_config.to_display_dict(),
                        investigation_id=investigation.id,
                    )

                all_investigations = await self._repository.list_all()
                related = [
                    inv
                    for inv in all_investigations
                    if inv.status == InvestigationStatus.COMPLETED
                    and inv.id != investigation.id
                    and any(cat in inv.domain for cat in domain_categories)
                ]
                if related:
                    prior_context = build_multi_investigation_context(related)

            yield self._cost_event(cost, investigation.id)

            # 2. Literature survey by researcher (structured, domain-aware)
            yield PhaseChanged(
                phase=2,
                name="Literature Survey",
                description="Structured literature search with PICO framework and citation chasing",
                investigation_id=investigation.id,
            )
            async for event in self._run_literature_survey(investigation, cost, pico):
                yield event

            yield self._cost_event(cost, investigation.id)

            # 3. Director formulates hypotheses
            yield PhaseChanged(
                phase=3,
                name="Formulation",
                description="Director formulating testable hypotheses from literature evidence",
                investigation_id=investigation.id,
            )
            prior_section = f"\n\n{prior_context}" if prior_context else ""
            formulation_prompt = (
                build_formulation_prompt(self._active_config)
                if self._active_config
                else DIRECTOR_FORMULATION_PROMPT
            )

            # Build structured XML context from PICO + findings
            literature_context = self._build_literature_context(investigation, pico)
            result = _DirectorResult(data={}, thinking="")
            async for director_event in self._director_call(
                cost,
                formulation_prompt,
                f"Research prompt: {investigation.prompt}\n\n"
                f"{literature_context}\n\n"
                f"Formulate 2-4 testable hypotheses and identify negative controls."
                + prior_section,
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
            yield self._cost_event(cost, investigation.id)

            # Request user approval before testing
            if self._require_approval:
                self._investigation = investigation
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
                    await asyncio.wait_for(self._approval_event.wait(), timeout=300)
                except TimeoutError:
                    logger.info("Approval timeout, auto-approving all hypotheses")
                self._approval_event.clear()

            # 4. Hypothesis loop -- batched parallel execution
            yield PhaseChanged(
                phase=4,
                name="Hypothesis Testing",
                description="Running parallel experiments to test hypotheses",
                investigation_id=investigation.id,
            )
            tested = 0
            while tested < self._max_hypotheses:
                proposed = [
                    h for h in investigation.hypotheses if h.status == HypothesisStatus.PROPOSED
                ]
                if not proposed:
                    break

                # Take up to 2 hypotheses per batch
                batch_hypotheses = proposed[:2]
                batch: list[tuple[Hypothesis, Experiment, dict[str, Any]]] = []

                for hypothesis in batch_hypotheses:
                    hypothesis.status = HypothesisStatus.TESTING
                    investigation.current_hypothesis_id = hypothesis.id
                    tested += 1

                    # Director designs experiment
                    if self._active_config:
                        tools_csv = ", ".join(
                            self._registry.list_tools_for_domain(self._active_config.tool_tags)
                        )
                    else:
                        tools_csv = ", ".join(self._registry.list_tools())
                    experiment_prompt = (
                        build_experiment_prompt(self._active_config)
                        if self._active_config
                        else DIRECTOR_EXPERIMENT_PROMPT
                    )
                    result = _DirectorResult(data={}, thinking="")
                    async for director_event in self._director_call(
                        cost,
                        experiment_prompt,
                        f"Research prompt: {investigation.prompt}"
                        f"\n\nHypothesis to test: "
                        f"{hypothesis.statement}\n"
                        f"Rationale: {hypothesis.rationale}\n\n"
                        f"Available tools: {tools_csv}\n\n"
                        f"Design an experiment to test this "
                        f"hypothesis.",
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
                async for event in self._run_experiment_batch(investigation, batch, cost):
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
                    async for director_event in self._director_call(
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

                yield self._cost_event(cost, investigation.id)

            # 5. Controls validation (from director suggestions)
            yield PhaseChanged(
                phase=5,
                name="Controls Validation",
                description="Validating model with positive and negative controls",
                investigation_id=investigation.id,
            )
            validation_metrics: dict[str, Any] = {}

            # Score controls through trained model if available
            score_map: dict[str, float] = {}
            has_model = bool(investigation.trained_model_ids)
            is_molecular = self._active_config is not None and any(
                t in self._active_config.tool_tags for t in ("chemistry", "prediction")
            )
            if has_model and is_molecular:
                model_id = investigation.trained_model_ids[-1]
                all_identifiers = [
                    nc.get("identifier", nc.get("smiles", ""))
                    for nc in neg_control_suggestions
                    if nc.get("identifier", nc.get("smiles", ""))
                ] + [
                    pc.get("identifier", "")
                    for pc in pos_control_suggestions
                    if pc.get("identifier", "")
                ]
                if all_identifiers:
                    try:
                        pred_result = await self._dispatch_tool(
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

            # 6. Director synthesizes
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
                build_synthesis_prompt(self._active_config)
                if self._active_config
                else DIRECTOR_SYNTHESIS_PROMPT
            )
            result = _DirectorResult(data={}, thinking="")
            async for director_event in self._director_call(
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
                        k: float(v)
                        for k, v in c.get("scores", {}).items()
                        if isinstance(v, (int, float))
                    },
                    attributes={k: str(v) for k, v in c.get("attributes", {}).items()},
                )
                for i, c in enumerate(raw_candidates)
            ]
            citations = synthesis.get("citations") or []
            investigation.set_candidates(candidates, citations)

            # Post-synthesis: generate Excalidraw diagram if MCP available
            diagram_url = ""
            if self._mcp_bridge and self._mcp_bridge.has_tool("excalidraw:create_view"):
                diagram_url = await self._generate_diagram(investigation)

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

        except Exception as e:
            logger.exception("Investigation %s failed", investigation.id)
            investigation.status = InvestigationStatus.FAILED
            investigation.error = str(e)
            investigation.cost_data = cost.to_dict()
            yield InvestigationError(error=str(e), investigation_id=investigation.id)
        finally:
            if self._mcp_bridge:
                try:
                    await self._mcp_bridge.disconnect()
                except Exception:
                    logger.warning("MCP bridge disconnect failed", exc_info=True)

    async def _generate_diagram(self, investigation: Investigation) -> str:
        """Generate an Excalidraw evidence synthesis diagram and return its URL."""
        if not self._mcp_bridge:
            return ""

        elements = _build_excalidraw_elements(investigation)
        elements_json = json.dumps(elements)
        try:
            await self._mcp_bridge.call_tool("excalidraw:read_me", {})
            await self._mcp_bridge.call_tool("excalidraw:create_view", {"elements": elements_json})
            export_result = await self._mcp_bridge.call_tool(
                "excalidraw:export_to_excalidraw",
                {"json": json.dumps({"elements": elements, "appState": {}})},
            )
            data = json.loads(export_result)
            url: str = data.get("url", "")
            if url:
                logger.info("Diagram exported: %s", url)
            return url
        except Exception:
            logger.warning("Diagram generation failed", exc_info=True)
            return ""

    @staticmethod
    def _build_literature_context(
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
                cache_read_tokens=response.cache_read_input_tokens,
                cache_write_tokens=response.cache_write_input_tokens,
            )

        yield _DirectorResult(data=json.loads(text), thinking=thinking_text)

    async def _summarize_output(
        self,
        cost: CostTracker,
        tool_name: str,
        output: str,
        investigation_id: str,
    ) -> tuple[str, OutputSummarized | None]:
        if len(output) <= self._summarizer_threshold:
            return output, None

        response = await self._summarizer.create_message(
            system=SUMMARIZER_PROMPT,
            messages=[
                {"role": "user", "content": f"Tool: {tool_name}\nOutput:\n{output}"},
            ],
            tools=[],
        )
        cost.add_usage(
            response.input_tokens,
            response.output_tokens,
            self._summarizer.model,
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

    async def _run_literature_survey(
        self,
        investigation: Investigation,
        cost: CostTracker,
        pico: dict[str, Any],
    ) -> AsyncGenerator[DomainEvent, None]:
        """Structured literature survey with PICO, citation chasing, and evidence grading."""
        # A. Domain-filtered tools (no hardcoded set)
        if self._active_config:
            excluded = {
                "conclude_investigation",
                "propose_hypothesis",
                "design_experiment",
                "evaluate_hypothesis",
            }
            tool_schemas = [
                t
                for t in self._registry.list_schemas_for_domain(self._active_config.tool_tags)
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
            tool_schemas = [t for t in self._registry.list_schemas() if t["name"] in lit_tools]

        # Build structured survey prompt
        survey_prompt = build_literature_survey_prompt(self._active_config, pico)

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

        for _iteration in range(self._max_iterations_per_experiment):
            investigation.iteration += 1
            tool_choice = {"type": "any"} if _iteration == 0 else None
            response = await self._researcher.create_message(
                system=survey_prompt,
                messages=messages,
                tools=tool_schemas,
                tool_choice=tool_choice,
            )
            cost.add_usage(
                response.input_tokens,
                response.output_tokens,
                self._researcher.model,
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
                if tool_name in (
                    "search_literature",
                    "search_citations",
                    "explore_dataset",
                    "search_bioactivity",
                    "search_compounds",
                    "search_pharmacology",
                    "search_training_literature",
                    "search_supplement_evidence",
                    "search_prior_research",
                ):
                    search_queries += 1

                yield ToolCalled(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    investigation_id=investigation.id,
                )

                result_str = await self._dispatch_tool(tool_name, tool_input, investigation)
                result_str = _compact_result(tool_name, result_str)

                # Track result counts
                try:
                    result_data = json.loads(result_str)
                    if isinstance(result_data, dict):
                        total_results += int(result_data.get("count", 0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

                summarized_str, summarize_event = await self._summarize_output(
                    cost, tool_name, result_str, investigation.id
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
                viz_event = self._maybe_viz_event(result_str, "", investigation.id)
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
                f"- [level={f.evidence_level}] {f.title}: {f.detail}"
                for f in investigation.findings
            )
            grade_response = await self._summarizer.create_message(
                system=build_literature_assessment_prompt(),
                messages=[{"role": "user", "content": findings_for_grading}],
                tools=[],
                output_config=_build_output_config(LITERATURE_GRADING_SCHEMA),
            )
            cost.add_usage(
                grade_response.input_tokens,
                grade_response.output_tokens,
                self._summarizer.model,
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

    async def _run_researcher_experiment(
        self,
        investigation: Investigation,
        hypothesis: Hypothesis,
        experiment: Experiment,
        cost: CostTracker,
        design: dict[str, Any],
    ) -> AsyncGenerator[DomainEvent, None]:
        planned = set(experiment.tool_plan) if experiment.tool_plan else set()
        control_tools = {"record_finding", "record_negative_control"}
        if planned:
            allowed = planned | control_tools
            tool_schemas = [t for t in self._registry.list_schemas() if t["name"] in allowed]
        elif self._active_config:
            excluded = {
                "conclude_investigation",
                "propose_hypothesis",
                "design_experiment",
                "evaluate_hypothesis",
            }
            domain_schemas = self._registry.list_schemas_for_domain(self._active_config.tool_tags)
            tool_schemas = [t for t in domain_schemas if t["name"] not in excluded]
        else:
            excluded = {
                "conclude_investigation",
                "propose_hypothesis",
                "design_experiment",
                "evaluate_hypothesis",
            }
            tool_schemas = [t for t in self._registry.list_schemas() if t["name"] not in excluded]

        exp_controls = ", ".join(experiment.controls) or "None specified"
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
                    f"hypothesis_id='{hypothesis.id}'."
                ),
            },
        ]

        for _iteration in range(self._max_iterations_per_experiment):
            investigation.iteration += 1
            tool_choice = {"type": "any"} if _iteration == 0 else None
            response = await self._researcher.create_message(
                system=self._researcher_prompt,
                messages=messages,
                tools=tool_schemas,
                tool_choice=tool_choice,
            )
            async with self._state_lock:
                cost.add_usage(
                    response.input_tokens,
                    response.output_tokens,
                    self._researcher.model,
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
                async with self._state_lock:
                    cost.add_tool_call()

                yield ToolCalled(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    experiment_id=experiment.id,
                    investigation_id=investigation.id,
                )

                result_str = await self._dispatch_tool(tool_name, tool_input, investigation)
                result_str = _compact_result(tool_name, result_str)

                summarized_str, summarize_event = await self._summarize_output(
                    cost, tool_name, result_str, investigation.id
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
                viz_event = self._maybe_viz_event(result_str, experiment.id, investigation.id)
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
                    async with self._state_lock:
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
                            async with self._state_lock:
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
                    async with self._state_lock:
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

    async def _run_experiment_batch(
        self,
        investigation: Investigation,
        batch: list[tuple[Hypothesis, Experiment, dict[str, Any]]],
        cost: CostTracker,
    ) -> AsyncGenerator[DomainEvent, None]:
        """Run up to 2 experiments concurrently."""
        if len(batch) == 1:
            h, exp, design = batch[0]
            async for event in self._run_researcher_experiment(investigation, h, exp, cost, design):
                yield event
            return

        queue: asyncio.Queue[DomainEvent | None] = asyncio.Queue()

        async def _run_one(
            hyp: Hypothesis,
            exp: Experiment,
            design: dict[str, Any],
        ) -> None:
            try:
                async for ev in self._run_researcher_experiment(
                    investigation, hyp, exp, cost, design
                ):
                    await queue.put(ev)
            except Exception as e:
                logger.warning("Experiment %s failed: %s", exp.id, e)
            finally:
                await queue.put(None)

        tasks = [asyncio.create_task(_run_one(h, e, d)) for h, e, d in batch]

        done_count = 0
        while done_count < len(tasks):
            item: DomainEvent | None = await queue.get()
            if item is None:
                done_count += 1
                continue
            yield item

        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def _maybe_viz_event(
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

    async def _dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        investigation: Investigation,
    ) -> str:
        # Intercept search_prior_research -- query FTS5 via repository
        if tool_name == "search_prior_research" and self._repository:
            query = tool_input.get("query", "")
            limit = int(tool_input.get("limit", 10))
            results = await self._repository.search_findings(query, limit)
            return json.dumps({"results": results, "count": len(results), "query": query})

        args_hash = ToolCache.hash_args(tool_input)
        cached = self._cache.get(tool_name, args_hash)
        if cached is not None:
            return cached

        func = self._registry.get(tool_name)
        if func is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            result = await func(**tool_input)
            result_str = str(result)
            self._cache.put(tool_name, args_hash, result_str)
            return result_str
        except Exception as e:
            logger.warning("Tool %s failed: %s", tool_name, e)
            return json.dumps({"error": f"Tool {tool_name} failed: {e}"})


def _build_excalidraw_elements(investigation: Investigation) -> list[dict[str, Any]]:
    """Build Excalidraw elements representing the investigation evidence map."""
    elements: list[dict[str, Any]] = []
    y_offset = 0

    # Title
    elements.append(
        {
            "type": "text",
            "x": 300,
            "y": y_offset,
            "width": 600,
            "height": 40,
            "text": f"Evidence Synthesis: {investigation.prompt[:80]}",
            "fontSize": 24,
            "fontFamily": 1,
            "textAlign": "center",
            "strokeColor": "#e2e8f0",
            "id": "title",
        }
    )
    y_offset += 80

    # Hypotheses
    status_colors = {
        "supported": "#166534",
        "refuted": "#991b1b",
        "revised": "#9a3412",
        "proposed": "#374151",
        "testing": "#1e40af",
        "rejected": "#7f1d1d",
    }
    hyp_positions: dict[str, tuple[int, int]] = {}
    for i, h in enumerate(investigation.hypotheses):
        x = 50 + (i % 3) * 350
        y = y_offset + (i // 3) * 160
        color = status_colors.get(h.status.value, "#374151")
        elements.append(
            {
                "type": "rectangle",
                "x": x,
                "y": y,
                "width": 300,
                "height": 120,
                "backgroundColor": color,
                "strokeColor": "#94a3b8",
                "roundness": {"type": 3},
                "id": f"hyp-{h.id}",
            }
        )
        label = f"{h.status.value.upper()}\n{h.statement[:60]}"
        if h.confidence > 0:
            label += f"\nConf: {h.confidence:.0%}"
        elements.append(
            {
                "type": "text",
                "x": x + 10,
                "y": y + 10,
                "width": 280,
                "height": 100,
                "text": label,
                "fontSize": 14,
                "fontFamily": 1,
                "strokeColor": "#e2e8f0",
                "id": f"hyp-label-{h.id}",
            }
        )
        hyp_positions[h.id] = (x + 150, y + 120)

    y_offset += ((len(investigation.hypotheses) + 2) // 3) * 160 + 40

    # Findings summary
    if investigation.findings:
        elements.append(
            {
                "type": "text",
                "x": 50,
                "y": y_offset,
                "width": 400,
                "height": 30,
                "text": f"Findings: {len(investigation.findings)} recorded",
                "fontSize": 18,
                "fontFamily": 1,
                "strokeColor": "#94a3b8",
                "id": "findings-header",
            }
        )
        y_offset += 50
        for j, f in enumerate(investigation.findings[:12]):
            elements.append(
                {
                    "type": "text",
                    "x": 60,
                    "y": y_offset + j * 25,
                    "width": 900,
                    "height": 20,
                    "text": f"[{f.evidence_type}] {f.title[:90]}",
                    "fontSize": 12,
                    "fontFamily": 3,
                    "strokeColor": "#94a3b8",
                    "id": f"finding-{j}",
                }
            )

    return elements
