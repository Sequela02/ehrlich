# Changelog

All notable changes to Ehrlich will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Token optimization: prompt caching via `cache_control: ephemeral` on system messages (90% cheaper cached tokens across 20-40 calls)
- Token optimization: phase-based tool filtering -- researcher gets only planned tools per experiment (5-10 instead of 23)
- Token optimization: structured extraction (`_compact_result`) strips verbose fields before summarizer check, eliminating 50-80% of Haiku calls
- Token optimization: in-memory TTL tool cache (`ToolCache`) -- deterministic tools cached forever, API results cached 24h-7d
- Per-experiment Lab View: `experiment_id` field on `ToolCalled` and `ToolResultEvent` domain events
- Per-experiment Lab View: experiment selector dropdown in `LiveLabViewer` for filtering 3D scene by experiment
- Per-experiment Lab View: `eventsByExperiment` state in `use-sse.ts` for grouping SSE events
- Data source: UniProt REST client (`uniprot_client.py`) -- protein function, disease associations, GO terms, PDB cross-refs
- Data source: Open Targets GraphQL client (`opentargets_client.py`) -- disease-target associations with scored evidence
- Data source: GtoPdb REST client (`gtopdb_client.py`) -- expert-curated receptor/ligand interactions with affinities
- Tools: `get_protein_annotation` -- UniProt protein annotations (tool #28)
- Tools: `search_disease_targets` -- Open Targets disease-target associations (tool #29)
- Tools: `search_pharmacology` -- GtoPdb curated pharmacology data (tool #30)
- Domain entities: `ProteinAnnotation`, `TargetAssociation`, `PharmacologyEntry`
- Repository ABCs: `ProteinAnnotationRepository`, `TargetAssociationRepository`, `PharmacologyRepository`
- Tests: UniProt, Open Targets, GtoPdb client tests with respx mocking

### Changed

- Always uses `MultiModelOrchestrator` (single-model `Orchestrator` removed)
- Tool count: 27 -> 30 (3 new data source tools)
- Prompts: `SCIENTIST_SYSTEM_PROMPT` and `RESEARCHER_EXPERIMENT_PROMPT` mention 3 new data source tools
- E2E tests: rewritten to use `MultiModelOrchestrator`
- Server tests: 267 -> 270 passing (80.2% coverage)

### Removed

- `Orchestrator` class (`orchestrator.py`) -- single-model fallback path eliminated
- `test_orchestrator.py` -- tests for removed class

---

### Added

- Auditability: SSE event persistence in SQLite `events` table -- all events stored during investigation, replayed on page reload
- Auditability: `save_event()` / `get_events()` methods on `InvestigationRepository` interface and SQLite implementation
- Auditability: `prompt` field included in `completed` SSE event during replay (research question visible in report)
- Console: `InvestigationReport` -- structured 8-section report replacing plain-text ReportViewer (Research Question, Executive Summary, Hypotheses & Outcomes, Methodology, Key Findings, Candidate Molecules, Model Validation, Cost & Performance)
- Console: `DiagramRenderer` -- React Flow (`@xyflow/react`) investigation diagram with custom node types, minimap, controls
- Console: Dark-friendly diagram palette with dark fills and light text
- Console: Diagram zoom, pan, and minimap via React Flow built-ins
- Dependencies: `@xyflow/react` for node-graph diagrams

### Changed

- Console: `InvestigationDiagram` uses React Flow instead of Excalidraw (lazy-loaded, code-split ~188KB chunk)
- Console: `diagram-builder.ts` outputs React Flow `Node[]` + `Edge[]` with `smoothstep` routing instead of Excalidraw skeletons
- Console: Investigation diagram is always read-only (`nodesDraggable={false}`)
- Console: Investigation page shows `FindingsPanel` during live investigation, full `InvestigationReport` after completion
- Console: Completed investigation replay includes full timeline (all SSE events) instead of just final status
- Server: `_replay_final()` yields stored events before completed event for full timeline reconstruction

### Removed

- Console: `ExcalidrawWrapper` component (replaced by `DiagramRenderer`)
- Console: `ReportViewer` component (replaced by `InvestigationReport`)
- Console: `@excalidraw/excalidraw` dependency removed from `package.json`

---

### Added

- Domain-agnostic engine: RCSB PDB client for dynamic protein target discovery by organism/function/keyword
- Domain-agnostic engine: PubChem PUG REST client for compound search by name/SMILES/similarity
- Domain-agnostic engine: EPA CompTox CTX API client for environmental toxicity profiles (LD50, LC50, BCF, mutagenicity)
- Domain-agnostic engine: Flexible ChEMBL bioactivity search supporting any assay type (Ki, EC50, Kd, MIC, IC50)
- Tools: `search_protein_targets` -- RCSB PDB search by organism/function (tool #24)
- Tools: `search_compounds` -- PubChem compound search by name/SMILES/similarity (tool #25)
- Tools: `search_bioactivity` -- flexible ChEMBL query with configurable assay types (tool #26)
- Tools: `fetch_toxicity_profile` -- EPA CompTox environmental toxicity data (tool #27)
- Domain entities: `ToxicityProfile`, `CompoundSearchResult`
- Repository ABCs: `ProteinTargetRepository`, `ToxicityRepository`, `CompoundSearchRepository`
- Data: `data/targets/default.yaml` -- YAML-configured protein targets (replaces hardcoded dict)
- Data: `data/resistance/default.yaml` -- YAML-configured resistance mutations and SMARTS patterns
- Config: `EHRLICH_COMPTOX_API_KEY` setting for EPA CompTox API access
- Console: `LiveLabViewer` -- 3Dmol.js WebGL scene driven by SSE events (proteins load, ligands dock, candidates color by score)
- Console: `InvestigationDiagram` -- Excalidraw hypothesis map with status-colored nodes and evidence-chain arrows
- Console: `ExcalidrawWrapper` -- lazy-loaded Excalidraw component with dark theme
- Console: `scene-builder.ts` -- maps SSE events to 3Dmol.js operations (addProtein, addLigand, colorByScore, highlight)
- Console: `diagram-builder.ts` -- converts investigation data to Excalidraw elements (nodes, arrows, labels)
- Console: Tab system on investigation page (Timeline | Lab View | Diagram)
- Tests: 45+ new tests for RCSB, PubChem, CompTox clients, resistance YAML loader, new tool functions
- Dependencies: `pyyaml`, `respx` (dev), `@excalidraw/excalidraw`

### Changed

- Engine generalized from antimicrobial-only to domain-agnostic molecular discovery (23 -> 27 tools)
- Prompts: all "antimicrobial scientist" language replaced with "molecular discovery scientist"
- Prompts: added domain-adaptive instruction ("The user's research question defines the domain")
- Prompts: tool references updated to include 4 new data source tools
- Prediction docstrings: "antimicrobial activity" -> "bioactivity"
- `ProteinStore`: hardcoded 5-target dict replaced with YAML loader + RCSB PDB fallback search
- `SimulationService`: hardcoded resistance mutations/patterns replaced with YAML-loaded data
- `ChEMBLLoader`: parameterized `assay_types` (was hardcoded `MIC,IC50`), type-aware cache keys
- `AnalysisService`: added `compound_repo` for PubChem integration
- Tool registry: 23 -> 27 tools registered in investigation routes
- Server tests: 212 -> 257 passing (80.6% coverage)

---

### Added

- Investigation: hypothesis-driven scientific method replacing linear pipeline
- Investigation: `propose_hypothesis` tool -- register testable hypotheses with rationale
- Investigation: `design_experiment` tool -- plan experiments with tool sequences
- Investigation: `evaluate_hypothesis` tool -- assess outcomes (supported/refuted/revised) with confidence
- Investigation: `record_finding` tool -- findings linked to hypothesis + evidence type
- Investigation: `record_negative_control` tool -- validate models with known-inactive compounds
- Investigation: `conclude_investigation` tool -- final summary with ranked candidates
- Domain: `Hypothesis` entity with status enum (proposed/testing/supported/refuted/revised)
- Domain: `Experiment` entity with status enum (planned/running/completed/failed)
- Domain: `NegativeControl` frozen dataclass
- Domain: 5 new events (HypothesisFormulated, HypothesisEvaluated, ExperimentStarted, ExperimentCompleted, NegativeControlRecorded)
- SSE: 5 new event types (hypothesis_formulated, hypothesis_evaluated, experiment_started, experiment_completed, negative_control)
- Console: `HypothesisBoard` -- kanban-style hypothesis status grid
- Console: `HypothesisCard` -- expandable card with confidence bar
- Console: `ActiveExperimentCard` -- live experiment activity card
- Console: `NegativeControlPanel` -- validation results table
- Console: `CompletionSummaryCard` -- post-completion counts (candidates, findings, hypotheses)
- Console: Findings replay from `InvestigationCompleted` event on page reload
- Console: Toast notifications via `sonner` for completion + error events
- Console: Custom scrollbar CSS (8px webkit + Firefox thin) with OKLCH theme

### Changed

- `MultiModelOrchestrator`: hypothesis-driven loop (formulate -> design -> execute -> evaluate per hypothesis)
- Director prompts: 4 phases (formulation, experiment, evaluation, synthesis) with domain-adaptive language
- Tool count: 19 -> 23 (6 investigation control tools added)
- SQLite repository: serializes hypothesis/experiment/negative_control data

---

### Added

- Branding: "Lab Protocol" dark-only visual identity (Industrial Scientific + Editorial + Cyberpunk Lab)
- Branding: OKLCH color system with Molecular Green primary (`oklch(0.72 0.19 155)`)
- Branding: Space Grotesk display/body font + JetBrains Mono data/label font via Google Fonts
- Branding: `pulse-glow` keyframe animation for active/running states
- Branding: Dark prose overrides for react-markdown content
- Console: Molecular bond phase progress (node-and-bond visualization replacing flat bars)
- Console: Section headers with monospace uppercase + left green border accent
- Data pipeline: `evidence` field threaded from Finding entity through FindingRecorded event to SSE to frontend
- Data pipeline: Candidate scoring fields (`prediction_score`, `docking_score`, `admet_score`, `resistance_risk`) populated from orchestrator prompts and serialized through SSE
- Console: Expandable Timeline events -- tool results, thinking, director decisions expand on click
- Console: Rich Director decision cards -- planning shows phase goals, review shows quality/gaps/guidance, synthesis shows confidence/limitations
- Console: FindingsPanel grid layout (2-3 columns) with evidence section
- Console: CandidateTable scoring columns (Prediction, Docking, ADMET, Resistance) with color-coded values
- Console: CostBadge per-model breakdown popover (Director, Researcher, Summarizer costs)
- Molecule visualization: server-side 2D SVG depiction via RDKit `rdMolDraw2D` (`depict_2d` on RDKitAdapter and ChemistryService)
- Molecule API: `GET /molecule/depict` returns `image/svg+xml` with 24h cache, error SVG for invalid SMILES
- Molecule API: `GET /molecule/conformer` returns 3D conformer JSON (mol_block, energy, num_atoms)
- Molecule API: `GET /molecule/descriptors` returns molecular descriptors + Lipinski pass/fail
- Molecule API: `GET /targets` returns list of protein targets (pdb_id, name, organism)
- Console: `MolViewer2D` component -- server-side SVG via `<img>` tag with lazy loading and error fallback
- Console: `MolViewer3D` component -- 3Dmol.js WebGL viewer with stick style and Jmol coloring
- Console: `DockingViewer` component -- 3Dmol.js protein (cartoon/spectrum) + ligand (stick/green) overlay
- Console: `CandidateDetail` expandable panel with 2D/3D views, property card, and Lipinski badge
- Console: `CandidateTable` rewrite with 2D structure thumbnails, expand/collapse rows, chevron indicators
- Console: 3Dmol.js dependency for 3D molecular visualization
- Tests: 10 molecule API tests, 3 RDKit depict tests, 4 MolViewer2D component tests

### Removed

- Console: `useRDKit` hook (dead code, replaced by server-side SVG rendering)

### Changed

- Console: Complete dark theme overhaul — all 15 components restyled for dark background
- Console: AppLayout header redesigned with green bar accent, monospace alpha badge, right-aligned label
- Console: Home page left-aligned (anti-AI pattern), mono stat line "19 tools · 7 phases · multi-model"
- Console: Investigation page redesigned as full-width vertical stack (was 2/3+1/3 grid)
- Console: Timeline events restyled — green findings, amber director events, mono tool names
- Console: CostBadge uses monospace with green-highlighted cost amount, clickable for model breakdown
- Console: PromptInput dark textarea with green focus ring and glow hover on button
- Console: InvestigationList dark cards with green border hover effect
- Console: FindingsPanel dark surface cards with green file icon
- Console: ReportViewer uses `prose-invert` with custom dark prose colors
- Console: Lipinski badges use `bg-primary/20` (pass) and `bg-destructive/20` (fail)
- Molecule: 3Dmol.js viewers use dark background (`#1a1e1a`) instead of white
- Molecule: Error SVG uses dark background matching surface color
- Molecule: MolViewer2D error fallback uses `bg-surface` instead of `bg-white`
- `CandidateTable` replaces raw SMILES text column with inline 2D structure thumbnails (100x75)
- `CandidateTable` rows are now clickable to expand `CandidateDetail` panel
- `FindingsPanel` shows full detail text (removed 200-char truncation)
- Tool result preview increased from 500 to 1500 chars in both orchestrators
- Prompts: `DIRECTOR_SYNTHESIS_PROMPT` and `SCIENTIST_SYSTEM_PROMPT` request candidate scoring fields

---

### Added

- Multi-model: Director-Worker-Summarizer architecture (Opus 4.6 plans, Sonnet 4.5 executes tools, Haiku 4.5 compresses large outputs)
- Multi-model: `MultiModelOrchestrator` with phase-based execution, director review, and final synthesis
- Multi-model: Per-model cost tracking with tiered pricing (Opus $15/$75, Sonnet $3/$15, Haiku $0.80/$4 per M tokens)
- Multi-model: 5 new prompts -- director planning, review, synthesis, researcher phase, summarizer
- Multi-model: 3 new domain events -- `DirectorPlanning`, `DirectorDecision`, `OutputSummarized`
- Multi-model: 3 new SSE event types -- `director_planning`, `director_decision`, `output_summarized`
- Persistence: SQLite repository with WAL mode via `aiosqlite` for investigation storage
- Persistence: `InvestigationRepository` ABC in domain layer
- API: `GET /investigate` -- list all investigations (most recent first)
- API: `GET /investigate/{id}` -- full investigation detail with findings, candidates, cost
- API: Orchestrator creation from model settings (always multi-model)
- Console: SSE reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- Console: Investigation history list on home page with status badges and candidate counts
- Console: Phase progress bar (7-segment) with active/completed/inactive states
- Console: Director event rendering in Timeline (planning, decision, output summarized)
- Console: `useInvestigations` hook with TanStack Query (10s refetch interval)
- Investigation: `created_at` and `cost_data` fields on Investigation entity
- Config: Per-model settings (`EHRLICH_DIRECTOR_MODEL`, `EHRLICH_RESEARCHER_MODEL`, `EHRLICH_SUMMARIZER_MODEL`)
- Config: `EHRLICH_SUMMARIZER_THRESHOLD`, `EHRLICH_MAX_ITERATIONS_PER_PHASE`, `EHRLICH_DB_PATH`
- Tests: 25+ new tests for multi-model orchestrator, SQLite repository, updated API and cost tracker

### Fixed

- Added `pyarrow` to core dependencies -- required for ChEMBL parquet caching (`explore_dataset` crashed without it)

### Changed

- Cost tracker refactored to track per-model usage with model-specific pricing breakdown
- `AnthropicClientAdapter` exposes `model` property for cost attribution
- Orchestrator passes model to `cost.add_usage()` for accurate per-model tracking
- API routes use SQLite repository instead of in-memory dict
- `InvestigationCompleted` event includes `candidates` list
- SSE `completed` event includes candidates and cost data from investigation
- Integration: API key wired from `Settings` to `AnthropicClientAdapter` constructor
- Integration: Exponential backoff retry (3 attempts) for rate-limit and timeout errors
- Integration: Startup lifespan event with API key validation, tool count logging, optional dependency checks
- Integration: Data preparation script (`data/scripts/prepare_data.py`) using `ChEMBLLoader` for pre-downloading ChEMBL bioactivity data and PDB protein structures
- Integration: E2E smoke test exercising full pipeline (tool registry, orchestrator dispatch, SSE events)
- Integration: Environment variable documentation in README
- Integration: Demo instructions in README

### Changed

- Removed `modify_molecule` stub from tool registry (19 tools, down from 20)
- Improved error handling in `explore_dataset` (ChEMBL timeout, empty datasets)
- Improved error handling in `train_model` (dataset too small)
- Improved error handling in `predict_candidates` (model not found)
- Improved error handling in `dock_against_target` (invalid target, lists available targets)
- Improved error handling in `assess_resistance` (invalid target, invalid SMILES)
- Added `has_api_key` property to `Settings` for startup validation

### Fixed

- `AnthropicClientAdapter` no longer ignores `Settings.anthropic_api_key` (was reading only from env)

---

- Initial project scaffolding with DDD architecture (6 bounded contexts)
- Server: Python 3.12 + FastAPI + uv with full domain/application/infrastructure layers
- Console: React 19 + TypeScript 5.7 + Bun + Vite 6 + TanStack Router
- Shared kernel: SMILES/InChIKey/MolBlock types, Molecule value object, exception hierarchy
- API layer: FastAPI factory with CORS, health endpoint, investigation route stub
- SSE event types for real-time investigation streaming
- Investigation feature: Timeline, PromptInput, CandidateTable, ReportViewer, CostBadge
- Molecule feature: MolViewer2D, MolViewer3D, DockingViewer, PropertyCard stubs
- CI/CD: GitHub Actions (server: ruff + mypy + pytest, console: build + typecheck + test)
- Docker: multi-stage builds for server (uv + python:3.12-slim) and console (bun + nginx)
- Data: core references JSON, data preparation script, protein directory
- Optional dependency groups: `docking` (vina, meeko), `deeplearning` (chemprop)
- Pre-commit hooks: ruff lint + format
- Chemistry context: full RDKit adapter (descriptors, fingerprints, conformers, scaffolds, Butina clustering, substructure matching), ChemistryService, 7 tools (44 tests)
- Literature context: Semantic Scholar client, PubMed stub, core reference set with 6 key papers, LiteratureService, 2 tools (11 tests)
- Analysis context: ChEMBL loader with parquet caching, Tox21 loader, substructure enrichment (chi-squared), property distributions, AnalysisService, 3 tools (12 tests)
- Prediction context: XGBoost adapter (train/predict with scale_pos_weight, AUROC/AUPRC/F1 metrics, feature importance), model store (joblib save/load/list), Chemprop adapter (guarded), scaffold split, Butina clustering, ensemble, PredictionService, 3 tools (20 tests)
- Simulation context: protein store (5 MRSA targets -- PBP2a, DHPS, DNA Gyrase, MurA, NDM-1), Vina adapter (guarded), RDKit-based ADMET prediction (Lipinski, mutagenic SMARTS alerts, hERG, BBB, hepatotoxicity), knowledge-based resistance assessment (7 mutations across 5 targets, compound class pattern matching), SimulationService, 3 tools (20 tests)
