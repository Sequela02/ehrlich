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

## 14D: Domain Tool Enrichment -- DONE

Upgraded 4 composite tools from thin pass-throughs to real domain-specific logic with post-fetch filtering, ranking, and enrichment.

- [x] `search_training_literature` -- MeSH term expansion (6 common abbreviations), study type ranking (meta-analysis > SR > RCT > cohort), date recency weighting, non-human study filtering (mice, rats, in vitro, etc.)
- [x] `search_supplement_evidence` -- GRADE-style quality filtering (meta-analysis > SR > RCT > observational), retracted paper exclusion ([retracted], retracted:, retraction), date recency weighting
- [x] `compare_nutrients` -- per-nutrient delta computation with winner highlighting, MAR (Mean Adequacy Ratio) score via `assess_nutrient_adequacy()`, comparison + mar_scores sections added to JSON output
- [x] Fixed `TrainingService` I-squared reimplementation -- extracted `_compute_i_squared()` module-level function with proper inverse-variance weighting (w_i = sample_size_i), replaced inline calculation in `analyze_training_evidence`

Result: 15 new tests added (6 for search_training_literature, 3 for search_supplement_evidence, 3 for compare_nutrients, 6 for _compute_i_squared). All 61 tests passing (40 training + 21 nutrition). Zero ruff violations, zero mypy errors.

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

## 14F: Scientific Paper Generator -- DONE

Generate structured scientific papers from completed investigations. Structured assembly of investigation data + persisted events into publication-format Markdown.

- [x] `application/paper_generator.py` -- pure function, takes investigation data + events, produces 8-section structured paper:
  - Title (from research question, domain, date, ID)
  - Abstract (Director synthesis summary)
  - Introduction (PICO decomposition + literature survey from events)
  - Methods (experiment designs with variables/controls/analysis plans, tool usage counts from events)
  - Results (hypothesis outcomes table, findings grouped by evidence type with provenance, candidate ranking table)
  - Discussion (hypothesis assessments with evaluation reasoning from events, supporting/contradicting evidence)
  - References (citations + unique data source provenance from findings)
  - Supplementary (negative/positive controls, Z'-factor validation metrics from events, cost breakdown by model)
- [x] `GET /investigate/{id}/paper` endpoint -- returns JSON with section keys + `full_markdown` combined document. Auth + ownership verification, only for COMPLETED investigations
- [x] Console: "Export Paper" button replaces "Export Report" on completed investigations, fetches server-side paper with loading state, downloads as Markdown
- [x] 37 unit tests covering all 8 sections, event extraction, empty data, malformed events

Result: `paper_generator.py` (285 lines), API endpoint (65 lines), console updates (InvestigationReport.tsx). 908 server tests passing, 138 console tests passing.

## 14F-2: Paper View + PDF Export -- DONE

Dedicated paper view route with print-optimized CSS for browser-native PDF export. Zero new dependencies -- Recharts/Visx charts render as SVG, captured at full vector quality by browser print.

- [x] `extract_visualizations(events)` in `paper_generator.py` -- extracts visualization payloads from persisted events
- [x] `GET /investigate/{id}/paper` response updated -- includes `visualizations` key with `[{viz_type, title, data, config}]`
- [x] `routes/paper.$id.tsx` -- new paper view route at `/paper/:id`, renders 8 Markdown sections + numbered figures via VizRegistry
- [x] `styles/print.css` -- `@media print` stylesheet: white bg, serif body, SVG color preservation, page break hints, hidden toolbar
- [x] InvestigationReport: "View Paper" link + "Export Markdown" (renamed from "Export Paper")
- [x] `/paper/` added to `HEADERLESS_ROUTES` in `__root__.tsx`
- [x] 5 unit tests for `extract_visualizations()` (extraction, preservation, empty, no-viz, malformed)

Result: 42 paper generator tests passing, 138 console tests passing. Zero ruff/mypy/tsc violations.

## 14G: Validation Runs -- TODO

Run real investigations to validate the engine produces meaningful scientific results. Compare Ehrlich vs raw Claude Opus 4.6 on identical prompts.

- [ ] Molecular science validation: known drug discovery question with verifiable answer
- [ ] Training science validation: exercise physiology question with literature-backed answer
- [ ] Impact evaluation validation: real program evaluation data (CODESON) compared against professional auditors and raw Claude
- [ ] Document comparison results: where Ehrlich agrees/disagrees with baseline, where tree search found non-obvious paths
- [ ] Capture investigation traces for demo video

## 14H: Upload Validation Hardening -- DONE

Added consistent validation on both backend and frontend for file count and size limits, with clear UI feedback. Removed redundancy.

- [x] Defined `upload_limits.py` domain constants (MAX_FILE_SIZE=50MB, MAX_FILES=10, ALLOWED_EXTENSIONS)
- [x] Enforced max-files limit in Pydantic schema (`InvestigateRequest.file_ids`)
- [x] Removed redundant size check in `upload.py` (delegated to `FileProcessor`)
- [x] Added client-side size validation in `FileUpload.tsx` with per-file error feedback
- [x] Added file count indicator "N / 10 files" in console UI

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
Phase 14F-2 (Paper View + PDF Export)  -- after 14F (needs paper endpoint + viz events)
    |
Phase 14G (Validation Runs)            -- after 14E + 14F (needs tree search + paper gen)
```

14A, 14B, 14C can run in parallel (independent refactorings).
14D, 14E, 14F depend on 14A (clean orchestrator).
14G depends on everything else being done.

**Verification:** All existing tests pass after each sub-phase. New tests for tree search, paper generator, and enriched tools. Quality gates: ruff 0, mypy 0, pytest pass, tsc 0, vitest pass.
