Back to [Roadmap Index](README.md)

# Phase 14: Scientific Engine Hardening (Feb 14-15) -- IN PROGRESS

Architecture cleanup, scientific depth improvements, agentic tree search, and paper generation. Runs in parallel with Phase 13A-2 (upload). Addresses audit findings from codebase review.

## Prior Art

Ehrlich sits alongside three contemporary AI scientific discovery systems:

- **Sakana AI Scientist v2** (Apr 2025): End-to-end paper generation via agentic tree search. First AI-generated peer-reviewed workshop paper. ML-only. [arXiv:2504.08066](https://arxiv.org/abs/2504.08066)
- **FutureHouse Robin** (May 2025): Multi-agent system that discovered ripasudil as therapeutic candidate for AMD in 2.5 months. Biology-only, lab-in-the-loop. [arXiv:2505.13400](https://arxiv.org/abs/2505.13400)
- **Ai2 AutoDiscovery** (Feb 2026): Bayesian surprise-guided hypothesis exploration over large search spaces. [allenai.org/blog/autodiscovery](https://allenai.org/blog/autodiscovery)

Ehrlich differentiates by: domain-agnostic architecture (4 domains vs single-domain competitors), multi-model orchestration (Director/Researcher/Summarizer), real-time streaming UI, 18 external data sources, and computational laboratory (ML pipelines + causal inference as experimentation).

## 14A: Orchestrator Decomposition -- DONE

Split `MultiModelOrchestrator` (1,788 lines, 11 concerns) into focused modules following Clean Architecture. No behavior changes -- pure structural refactoring.

- [x] Extract `diagram_builder.py` -- Excalidraw element building + MCP bridge export (127 lines)
- [x] Extract `tool_dispatcher.py` -- tool execution + caching + `search_prior_research` / `query_uploaded_data` interception (34 lines)
- [x] Extract `researcher_executor.py` -- single experiment runner with tool loop (216 lines)
- [x] Extract `batch_executor.py` -- parallel experiment execution via asyncio.Queue (56 lines)
- [x] Merged uploaded_data_query into tool_dispatcher.py
- [x] Kept run() in multi_orchestrator.py as main coordination point
- [x] Extract `phase_runner.py` -- 5 investigation phases as standalone async generators
- [x] Extract `literature_survey.py` -- literature survey runner + PICO context builder + SEARCH_TOOLS
- [x] Orchestrator reduced to ~240 lines: init, run (delegates to phase runners), approve, director_call

Result: `multi_orchestrator.py` from 1,788 to ~240 lines (6 modules extracted). 87/87 tests passing.

## 14B: Route File Cleanup -- DONE

Moved infrastructure concerns out of `api/routes/investigation.py` (829 lines) into the application layer.

- [x] Extract `application/registry_factory.py` -- `build_tool_registry()` + `build_domain_registry()` + `build_mcp_configs()` with `lru_cache` singletons
- [x] Extract `application/orchestrator_factory.py` -- `create_orchestrator()` with Anthropic adapter wiring
- [x] Move Pydantic DTOs + serialization helpers to `api/schemas/investigation.py` (6 models, 5 serializers)
- [x] Eliminated ~70 lines of duplicated entity-to-dict serialization between `_to_detail()` and `_replay_final()`

Result: `api/routes/investigation.py` from 829 to 366 lines (56% reduction). Three new modules: `registry_factory.py` (237 lines), `orchestrator_factory.py` (71 lines), `api/schemas/investigation.py` (140 lines).

## 14C: Prompt Module Split -- DONE

Split `prompts.py` (1,505 lines) into `prompts/` package with 3 focused modules. Removed dead code (`SCIENTIST_SYSTEM_PROMPT`, `_build_prior_context` -- zero external imports).

- [x] `prompts/__init__.py` -- package docstring only (no re-exports; consumers import from submodules directly)
- [x] `prompts/constants.py` -- 6 static prompt strings (`DIRECTOR_FORMULATION_PROMPT`, `DIRECTOR_EXPERIMENT_PROMPT`, `DIRECTOR_EVALUATION_PROMPT`, `DIRECTOR_SYNTHESIS_PROMPT`, `RESEARCHER_EXPERIMENT_PROMPT`, `SUMMARIZER_PROMPT`)
- [x] `prompts/director.py` -- 4 Director-phase builder functions (`build_formulation_prompt`, `build_experiment_prompt`, `build_synthesis_prompt`, `build_multi_investigation_context`)
- [x] `prompts/builders.py` -- 6 non-Director builders (`build_pico_and_classification_prompt`, `build_literature_survey_prompt`, `build_literature_assessment_prompt`, `build_researcher_prompt`, `build_uploaded_data_context`, `_DEFAULT_CATEGORIES`)

## 14D: Domain Tool Enrichment -- TODO

Upgrade 4 composite tools from thin pass-throughs to real domain-specific logic.

- [ ] `search_training_literature` -- MeSH term expansion, study type ranking (SR > RCT > cohort), date recency weighting, non-human study filtering
- [ ] `search_supplement_evidence` -- GRADE-style quality filtering, RCT/meta-analysis prioritization, retracted paper exclusion
- [ ] `compare_nutrients` -- per-nutrient delta computation, winner highlighting per category, overall MAR score comparison
- [ ] Fix `TrainingService` I-squared reimplementation -- delegate to `StatisticsService` (training_service.py:79-85)

## 14E: Agentic Hypothesis Tree Search -- TODO

Replace linear hypothesis testing with tree-based exploration inspired by AI Scientist v2's agentic tree search. The current parallel batch system (2 experiments per hypothesis) becomes a tree where hypotheses can branch, deepen, or be pruned based on evidence.

- [ ] `HypothesisNode` dataclass -- extends Hypothesis with `depth`, `branch_score`, `children: list[str]`
- [ ] `TreeManager` in `application/tree_manager.py` -- decides which branches to explore based on confidence scores, prunes low-confidence branches (<0.4 threshold), tracks exploration budget
- [ ] Director formulation prompt update -- "given current evidence tree, propose sub-hypotheses for the most promising branch OR prune low-confidence branches"
- [ ] Director evaluation prompt update -- after evaluating, decide: (a) deepen (spawn sub-hypotheses), (b) prune (mark branch as dead), (c) branch (revise into alternative direction)
- [ ] `max_depth` parameter (default: 3) to prevent infinite recursion
- [ ] Budget-aware exploration -- track API cost per branch, prefer deepening high-confidence/low-cost branches
- [ ] `HypothesisTreeEvent` SSE event for frontend tree rendering
- [ ] Console: `InvestigationDiagram.tsx` already renders React Flow graph -- tree structure renders naturally as growing/pruning graph

## 14F: Scientific Paper Generator -- TODO

Generate structured scientific papers from completed investigations. Not AI-generated prose -- structured assembly of existing investigation data into publication format.

- [ ] `application/paper_generator.py` -- takes `Investigation` entity, produces structured sections:
  - Title (from research question)
  - Abstract (Director synthesis summary)
  - Introduction (PICO decomposition + literature survey context)
  - Methods (experiment designs, tool descriptions, statistical approach)
  - Results (findings with statistical tests, visualizations as base64 SVG)
  - Discussion (hypothesis assessments, GRADE certainty, limitations, knowledge gaps)
  - References (collected DOIs + citations)
  - Supplementary (cost breakdown, model info, negative controls, tool call trace)
- [ ] `GET /investigate/{id}/paper` endpoint -- returns structured paper as JSON or Markdown
- [ ] `GET /investigate/{id}/paper?format=pdf` -- server-side PDF generation (optional, `weasyprint` or `reportlab`)
- [ ] Console: "Export Paper" button on completed investigation page
- [ ] Console: paper preview with section navigation

## 14G: Validation Runs -- TODO

Run real investigations to validate the engine produces meaningful scientific results. Compare Ehrlich vs raw Claude Opus 4.6 on identical prompts.

- [ ] Molecular science validation: known drug discovery question with verifiable answer
- [ ] Training science validation: exercise physiology question with literature-backed answer
- [ ] Impact evaluation validation: real program evaluation data (CODESON) compared against professional auditors and raw Claude
- [ ] Document comparison results: where Ehrlich agrees/disagrees with baseline, where tree search found non-obvious paths
- [ ] Capture investigation traces for demo video

## Dependency Graph

```
Phase 14A (Orchestrator Decomposition)
    |
Phase 14B (Route File Cleanup)        -- parallel with 14A
    |
Phase 14C (Prompt Module Split)        -- parallel with 14A/B
    |
Phase 14D (Domain Tool Enrichment)     -- after 14A (touches tool layer)
    |
Phase 14E (Agentic Tree Search)        -- after 14A (modifies orchestrator)
    |
Phase 14F (Paper Generator)            -- after 14A (reads investigation data)
    |
Phase 14G (Validation Runs)            -- after 14E + 14F (needs tree search + paper gen)
```

14A, 14B, 14C can run in parallel (independent refactorings).
14D, 14E, 14F depend on 14A (clean orchestrator).
14G depends on everything else being done.

**Verification:** All existing tests pass after each sub-phase. New tests for tree search, paper generator, and enriched tools. Quality gates: ruff 0, mypy 0, pytest pass, tsc 0, vitest pass.
