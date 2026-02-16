Back to [Roadmap Index](README.md)

# Phase 10B: Domain-Agnostic Generalization (Feb 11-12) -- DONE

Generalized the entire engine from molecular-science-specific to domain-agnostic. Proved the architecture works by adding Training Science and Nutrition Science as additional domains.

## Backend Entity Generalization
- [x] `Candidate` entity: generic `identifier`/`identifier_type`/`scores`/`attributes` (replaces `smiles`/`prediction_score`/`docking_score`/`admet_score`/`resistance_risk`)
- [x] `NegativeControl` entity: generic `identifier`/`identifier_type`/`score`/`threshold` (replaces `smiles`/`prediction_score`)
- [x] `NegativeControlRecorded` event: generic fields
- [x] SQLite serialization updated for new field names
- [x] All 274 existing tests pass after entity changes (274 at time of this phase)

## Domain Configuration + Tool Tagging
- [x] `DomainConfig` + `ScoreDefinition` frozen dataclasses
- [x] `DomainRegistry`: register, detect by classified category, list template prompts
- [x] `MOLECULAR_SCIENCE` config (6 tool tags, 3 scores, 4 templates, multishot examples)
- [x] `TRAINING_SCIENCE` config (3 tool tags, 3 scores, 2 templates, multishot examples)
- [x] `NUTRITION_SCIENCE` config (3 tool tags, 3 scores, 1 template, multishot examples)
- [x] `ToolRegistry` with domain tag filtering (`list_schemas_for_domain`, `list_tools_for_domain`)
- [x] Tools tagged: chemistry, analysis, prediction, simulation, training, clinical, nutrition, safety, literature; investigation control universal
- [x] `DomainDetected` SSE event (16th event type) sends display config to frontend

## Prompt Template Generalization
- [x] Builder functions: `build_scientist_prompt()`, `build_formulation_prompt()`, `build_experiment_prompt()`, `build_synthesis_prompt()`
- [x] Dynamic domain classification from all registered domain categories
- [x] HypothesisType enum expanded: PHYSIOLOGICAL, PERFORMANCE, EPIDEMIOLOGICAL

## Frontend Generalization
- [x] Dynamic score columns from `DomainDisplayConfig` (replaces hardcoded Pred/Dock/ADMET/Resist)
- [x] Conditional MolViewer2D: only when `identifier_type === "smiles"`
- [x] Unified reactive VisualizationPanel: LiveLabViewer auto-appears for molecular tool events, charts render inline
- [x] 7 template cards (4 molecular + 2 training + 1 nutrition) with domain badges
- [x] Generic candidate comparison, negative control panel, markdown export

## Training Science Bounded Context (6 tools)
- [x] `search_training_literature` -- Semantic Scholar with training science context
- [x] `analyze_training_evidence` -- effect sizes, heterogeneity, evidence grading (A-D)
- [x] `compare_protocols` -- evidence-weighted composite scoring
- [x] `assess_injury_risk` -- knowledge-based multi-factor risk scoring
- [x] `compute_training_metrics` -- ACWR, monotony, strain, RPE load
- [x] `search_clinical_trials` -- ClinicalTrials.gov exercise/training RCT search

## Nutrition Science Bounded Context (10 tools)
- [x] `search_supplement_evidence` -- supplement meta-analysis search
- [x] `search_supplement_labels` -- NIH DSLD supplement product ingredient lookup
- [x] `search_nutrient_data` -- USDA FoodData Central nutrient profiles
- [x] `search_supplement_safety` -- OpenFDA CAERS adverse event reports for supplements
- [x] `compare_nutrients` -- side-by-side nutrient comparison (added in Nutrition Enhancement)
- [x] `assess_nutrient_adequacy` -- DRI-based adequacy assessment (added in Nutrition Enhancement)
- [x] `check_intake_safety` -- UL safety screening (added in Nutrition Enhancement)
- [x] `check_interactions` -- RxNav drug interactions (added in Nutrition Enhancement)
- [x] `analyze_nutrient_ratios` -- nutrient ratio analysis (added in Nutrition Enhancement)
- [x] `compute_inflammatory_index` -- DII scoring (added in Nutrition Enhancement)
- [x] Tests: training (8 tests) + nutrition (10 tests initially, expanded in Enhancement), all passing

**Verification:** 288 server tests, 107 console tests. All quality gates green: ruff 0, mypy 0 (117 files), tsc 0, vitest 107/107.

---

# Multi-Domain Investigations (Feb 12) -- DONE

Cross-domain research questions that span multiple scientific domains (e.g., molecular + nutrition, training + nutrition).

## Changes

- [x] `DomainRegistry.detect()` returns `list[DomainConfig]` (multi-domain detection, deduplicates)
- [x] Haiku classifier outputs JSON array of domain categories
- [x] `merge_domain_configs()` creates synthetic merged config (union tool_tags, concatenated scores, joined examples)
- [x] Tool filtering uses merged config's union of domain tags
- [x] Prompt examples merged from all relevant domains
- [x] `DomainDetected` SSE event carries merged display config with `domains` sub-list
- [x] Frontend `DomainDisplayConfig.domains` for sub-domain rendering
- [x] Tests: 16 tests (multi-detect, deduplication, fallback, merge, display dict)

---

# Self-Referential Research (Feb 12) -- DONE

Ehrlich builds institutional knowledge by querying its own past investigations during new research.

## Changes

- [x] SQLite FTS5 virtual table (`findings_fts`) on finding title, detail, evidence_type, hypothesis statement/status, source provenance
- [x] `search_prior_research` tool -- intercepted in orchestrator, routed to FTS5 via repository
- [x] BM25-ranked full-text search with investigation prompt context
- [x] FTS5 query sanitization (quoted tokens for literal hyphens/operators)
- [x] FTS5 index rebuilt on investigation completion via `_rebuild_fts()`
- [x] Provenance: `source_type: "ehrlich"`, `source_id: "{investigation_id}"`
- [x] Available during Phase 2 (Literature Survey) alongside external search tools
- [x] Frontend: Ehrlich-branded source badges with internal navigation
- [x] Tests: 6 FTS5 tests (empty, match, prompt context, limit, completion-gating, cross-investigation)

---

# Shared Context + MCP Bridge + Training/Nutrition APIs (Feb 12) -- DONE

DDD cleanup, shared bounded context, MCP bridge for external tools, 4 new data source clients (training + nutrition), and methodology page.

## Shared Bounded Context
- [x] `shared/` context: cross-cutting ports and value objects (`ChemistryPort` ABC, `Fingerprint`, `MolecularDescriptors`, `Conformer3D`)
- [x] `ChemistryPort` ABC decouples chemistry operations from RDKit infrastructure
- [x] Moved value objects from `chemistry/domain/` to `shared/` for cross-context use

## MCP Bridge
- [x] `MCPBridge` connects to external MCP servers (stdio/SSE/streamable_http transports)
- [x] Tools registered dynamically via `ToolRegistry.register_mcp_tools()` with domain tags
- [x] Lifecycle managed by orchestrator (connect on start, disconnect on completion)
- [x] Enabled via `EHRLICH_MCP_EXCALIDRAW=true` env var

## Data Source API Tools (4 tools across training + nutrition)
- [x] `search_clinical_trials` (training) -- ClinicalTrials.gov v2 API for exercise/training RCTs
- [x] `search_supplement_labels` (nutrition) -- NIH DSLD supplement label database
- [x] `search_nutrient_data` (nutrition) -- USDA FoodData Central nutrient profiles
- [x] `search_supplement_safety` (nutrition) -- OpenFDA CAERS adverse event reports
- [x] Full DDD: domain entities + repository ABCs + infrastructure clients in respective bounded contexts

## Methodology Page
- [x] `GET /methodology` endpoint: phases, domains, tools, data sources, models
- [x] `GET /stats` endpoint: aggregate counts
- [x] Console methodology page with phases, models, domains, tools, data sources

**Verification:** 527 server tests, 107 console tests. All quality gates green.

---

# Domain-Specific Visualization System (Feb 12) -- DONE

6 visualization tools with structured payloads, orchestrator interception, and lazy-loaded React components.

## Backend
- [x] `VisualizationPayload` frozen dataclass (viz_type, title, data, config, domain)
- [x] 6 viz tools: `render_binding_scatter`, `render_admet_radar`, `render_training_timeline`, `render_muscle_heatmap`, `render_forest_plot`, `render_evidence_matrix`
- [x] Orchestrator intercepts viz tool results via `_maybe_viz_event()`, emits `VisualizationRendered` SSE event (20th event type)

## Frontend
- [x] `VizRegistry` maps viz_type to lazy-loaded React component
- [x] `VisualizationPanel` renders multiple charts in grid layout
- [x] Recharts: scatter (compound affinities), radar (ADMET), timeline (training load + ACWR)
- [x] Visx: forest plot (meta-analysis), evidence matrix (heatmap)
- [x] Custom SVG: anatomical body diagram with muscle activation/risk heatmap
- [x] OKLCH color tokens for consistent chart theming

**Verification:** 527 server tests, 107 console tests. All quality gates green.
