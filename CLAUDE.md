# Ehrlich - AI Scientific Discovery Engine

## Project Overview

Ehrlich is a domain-agnostic scientific discovery platform built for the Claude Code Hackathon (Feb 10-16, 2026). It uses Claude as a hypothesis-driven scientific reasoning engine that works across multiple scientific domains. Named after Paul Ehrlich, the father of the "magic bullet" concept.

The hypothesis-driven engine is domain-agnostic: a pluggable `DomainConfig` + `DomainRegistry` system lets any scientific domain plug in with its own tools, score definitions, and prompt examples. Visualization is reactive -- LiveLabViewer auto-appears when molecular tool events are detected in the stream, chart visualizations render inline from `VisualizationRendered` events. Currently supports two domains:

- **Molecular Science** -- antimicrobial resistance, drug discovery, toxicology, agricultural biocontrol
- **Sports Science** -- training protocol optimization, injury risk assessment, supplement evidence analysis

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 48 tools (parallel: 2 experiments per batch)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars), PICO decomposition, evidence grading
```

Always uses `MultiModelOrchestrator`. Hypotheses tested in parallel batches of 2.

### Bounded Contexts

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| shared | `server/src/ehrlich/shared/` | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D, MolecularDescriptors) |
| literature | `server/src/ehrlich/literature/` | Paper search (Semantic Scholar), references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration (ChEMBL, PubChem), enrichment |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance, target discovery (RCSB PDB), toxicity (EPA CompTox) |
| sports | `server/src/ehrlich/sports/` | Sports science: evidence analysis, protocol comparison, injury risk, training metrics, clinical trials, supplement safety |
| investigation | `server/src/ehrlich/investigation/` | Multi-model agent orchestration + SQLite persistence + domain registry + MCP bridge |

### External Data Sources (12 external + 1 internal)

| Source | API | Purpose | Auth |
|--------|-----|---------|------|
| ChEMBL | `https://www.ebi.ac.uk/chembl/api/data` | Bioactivity data (any assay type: MIC, IC50, Ki, EC50, Kd) | None |
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1` | Scientific paper search | None |
| RCSB PDB | `https://search.rcsb.org` + `https://data.rcsb.org` | Dynamic protein target discovery by organism/function | None |
| PubChem | `https://pubchem.ncbi.nlm.nih.gov/rest/pug` | Compound search by target/activity/similarity | None |
| EPA CompTox | `https://api-ccte.epa.gov` | Environmental toxicity, bioaccumulation, fate (1M+ chemicals) | Free API key |
| UniProt | `https://rest.uniprot.org` | Protein function, disease associations, GO terms, PDB cross-refs | None |
| Open Targets | `https://api.platform.opentargets.org` | Disease-target associations (GraphQL, scored evidence) | None |
| GtoPdb | `https://www.guidetopharmacology.org/services` | Expert-curated pharmacology (pKi, pIC50, receptor classification) | None |
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2` | Registered clinical trials for exercise/training RCTs | None |
| NIH DSLD | `https://api.ods.od.nih.gov/dsld/v9` | Dietary supplement label database (ingredients, amounts) | None |
| USDA FoodData | `https://api.nal.usda.gov/fdc/v1` | Nutrient profiles for foods and supplements | API key |
| OpenFDA CAERS | `https://api.fda.gov/food/event.json` | Supplement adverse event reports (safety monitoring) | None |
| Ehrlich FTS5 | internal | Full-text search of past investigation findings | None |

### Dependency Rules (STRICT)

1. `domain/` has ZERO external deps -- pure Python only (dataclasses, ABC, typing)
2. `application/` depends on `domain/` interfaces, never on `infrastructure/`
3. `infrastructure/` implements `domain/` repository interfaces
4. `tools.py` calls `application/` services, returns JSON for Claude
5. No cross-context domain imports -- communicate via `kernel/` primitives or `shared/` ports
6. `shared/` contains cross-cutting ports (ABCs) and value objects -- no infrastructure deps
7. RDKit imports ONLY in `chemistry/infrastructure/rdkit_adapter.py`
8. External API clients live in `infrastructure/` of their bounded context

## Commands

### Server

```bash
cd server
uv sync --extra dev                                      # Core + dev deps
# uv sync --extra all --extra dev                        # All deps (docking + deep learning)
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
uv run pytest --cov=ehrlich --cov-report=term-missing    # Tests
uv run ruff check src/ tests/                            # Lint
uv run ruff format src/ tests/                           # Format
uv run mypy src/ehrlich/                                 # Type check
```

Optional extras: `docking` (vina, meeko), `deeplearning` (chemprop), `all` (everything).

### Console

```bash
cd console
bun install
bun dev              # Dev server :5173
bun test             # Vitest
bun run build        # vite build (generates route tree + bundles)
bun run typecheck    # tsc --noEmit (run after build for route types)
```

## Quality Gates

- Linting: `ruff` -- zero violations
- Formatting: `ruff format --check` -- zero violations
- Type checking: `mypy` strict -- zero errors
- Test coverage: `pytest-cov` -- 80% minimum
- TypeScript: `tsc --noEmit` -- zero errors

## Commit Format

```
type(scope): description
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

Scopes: kernel, shared, literature, chemistry, analysis, prediction, simulation, sports, investigation, api, console, mol, data, ci, docs, infra

## Tools (48 Total)

### Chemistry (6) -- RDKit cheminformatics, domain-agnostic
- `validate_smiles` -- Validate SMILES string
- `compute_descriptors` -- MW, LogP, TPSA, HBD, HBA, QED, rings
- `compute_fingerprint` -- Morgan (2048-bit) or MACCS (166-bit)
- `tanimoto_similarity` -- Similarity between two molecules
- `generate_3d` -- 3D conformer with MMFF94 optimization
- `substructure_match` -- SMARTS/SMILES substructure search

### Literature (3) -- Semantic Scholar
- `search_literature` -- Paper search (title, authors, year, DOI, abstract, citations)
- `search_citations` -- Citation chasing (snowballing) via references/citing papers
- `get_reference` -- Curated reference lookup by key or DOI

### Analysis (6) -- ChEMBL + PubChem + GtoPdb
- `explore_dataset` -- Load ChEMBL bioactivity data for any organism/target
- `search_bioactivity` -- Flexible ChEMBL query (any assay type: MIC, Ki, EC50, IC50, Kd)
- `search_compounds` -- PubChem compound search by target/activity/similarity
- `search_pharmacology` -- GtoPdb curated receptor/ligand interactions with affinities
- `analyze_substructures` -- Chi-squared enrichment of SMARTS patterns
- `compute_properties` -- Property distributions (active vs inactive)

### Prediction (3) -- XGBoost, Chemprop
- `train_model` -- Train ML model on any SMILES+activity dataset (scaffold-split + random-split metrics, permutation p-value)
- `predict_candidates` -- Score compounds with trained model
- `cluster_compounds` -- Butina structural clustering

### Simulation (7) -- Docking, ADMET, targets, toxicity, annotations
- `search_protein_targets` -- RCSB PDB search by organism/function/keyword
- `get_protein_annotation` -- UniProt protein function, disease links, GO terms
- `search_disease_targets` -- Open Targets disease-target associations (scored)
- `dock_against_target` -- AutoDock Vina docking (or RDKit fallback)
- `predict_admet` -- Drug-likeness profiling (absorption, metabolism, toxicity)
- `fetch_toxicity_profile` -- EPA CompTox environmental toxicity data
- `assess_resistance` -- Knowledge-based resistance mutation scoring

### Sports Science (10) -- Evidence-based sports research
- `search_sports_literature` -- Semantic Scholar with sports science context
- `analyze_training_evidence` -- Pooled effect sizes, heterogeneity, evidence grading (A-D)
- `compare_protocols` -- Evidence-weighted protocol comparison with composite scoring
- `assess_injury_risk` -- Knowledge-based injury risk scoring (sport, load, history, age)
- `compute_training_metrics` -- ACWR, monotony, strain, session RPE load
- `search_supplement_evidence` -- Supplement efficacy literature search
- `search_clinical_trials` -- ClinicalTrials.gov exercise/training RCT search
- `search_supplement_labels` -- NIH DSLD supplement product ingredient lookup
- `search_nutrient_data` -- USDA FoodData Central nutrient profiles
- `search_supplement_safety` -- OpenFDA CAERS adverse event reports for supplements

### Visualization (6) -- Domain-specific interactive charts
- `render_binding_scatter` -- Scatter plot of compound binding affinities (Recharts)
- `render_admet_radar` -- Radar chart of ADMET/drug-likeness properties (Recharts)
- `render_training_timeline` -- Training load timeline with ACWR danger zones (Recharts)
- `render_muscle_heatmap` -- Anatomical body diagram with muscle activation/risk (Custom SVG)
- `render_forest_plot` -- Forest plot for meta-analysis results (Visx)
- `render_evidence_matrix` -- Hypothesis-by-evidence heatmap (Visx)

### Investigation (7) -- Hypothesis lifecycle + self-referential
- `propose_hypothesis` -- Register testable hypothesis
- `design_experiment` -- Plan experiment with tool sequence
- `evaluate_hypothesis` -- Assess outcome (supported/refuted/revised)
- `record_finding` -- Record finding linked to hypothesis + evidence_type
- `record_negative_control` -- Validate model with known-inactive compounds
- `search_prior_research` -- Search Ehrlich's own past findings via FTS5
- `conclude_investigation` -- Final summary with ranked candidates

## Key Patterns

- Each bounded context has: `domain/`, `application/`, `infrastructure/`, `tools.py`
- Domain entities use `@dataclass` with `__post_init__` validation
- Repository interfaces are ABCs in `domain/repository.py`
- Infrastructure adapters implement repository ABCs
- Tool functions in `tools.py` are the boundary between Claude and application services
- **Hypothesis-driven investigation loop**: formulate hypotheses (with predictions, criteria, scope, prior confidence), design structured experiment protocols (variables, controls, confounders, analysis plan, criteria), execute tools with methodology guidance (sensitivity, AD, UQ, verification, negative results), evaluate with scientific methodology (evidence hierarchy, effect size thresholds, Bayesian updating, contradiction resolution, convergence check, certainty_of_evidence grading), revise/reject, synthesize with GRADE certainty grading (5 downgrading + 3 upgrading domains), priority tiers (1-4), structured limitations taxonomy, knowledge gap analysis, and follow-up experiment recommendations
- **Domain-agnostic prompts**: Director infers domain from user's research question, adapts scientific context
- **Evidence-linked findings**: every finding references a `hypothesis_id` + `evidence_type` (supporting/contradicting/neutral)
- **Negative controls**: validate model predictions with known-inactive compounds (`NegativeControl` entity)
- **Positive controls**: validate pipeline can detect true actives with known-active compounds (`PositiveControl` entity); validation quality assessment (sufficient/marginal/insufficient) in synthesis
- **Validation metrics**: Z'-factor assay quality (Zhang et al., 1999), permutation significance (Y-scrambling, p-value), scaffold-split vs random-split comparison; controls scored through trained models in Phase 5; `ValidationMetricsComputed` event
- **Dynamic target discovery**: RCSB PDB Search API finds protein targets for any organism/disease
- **Flexible data loading**: ChEMBL queries accept any assay type (MIC, Ki, EC50, etc.), not hardcoded
- **Protein targets**: YAML-configured (`data/targets/*.yaml`) + dynamic RCSB PDB discovery
- **Resistance data**: YAML-configured (`data/resistance/*.yaml`), extensible per domain
- 7 control tools: `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_finding`, `record_negative_control`, `search_prior_research`, `conclude_investigation`
- **Domain configuration**: `DomainConfig` defines per-domain tool tags, score definitions, prompt examples; `DomainRegistry` auto-detects domain from classification; `DomainDetected` SSE event sends display config to frontend
- **Multi-domain investigations**: `DomainRegistry.detect()` returns `list[DomainConfig]` for cross-domain research; `merge_domain_configs()` creates synthetic merged config with union of tool_tags, concatenated score_definitions, joined prompt examples; `DomainDisplayConfig.domains` carries sub-domain list to frontend
- **Self-referential research**: `search_prior_research` tool queries FTS5 full-text index of past investigation findings; indexed on completion via `_rebuild_fts()`; intercepted in orchestrator `_dispatch_tool()` and routed to `SqliteInvestigationRepository.search_findings()`; "ehrlich" source type on findings links to past investigations
- **MCP bridge**: Optional `MCPBridge` connects to external MCP servers (e.g. Excalidraw for visual summaries); tools registered dynamically via `ToolRegistry.register_mcp_tools()`; lifecycle managed by orchestrator (connect on start, disconnect on completion); enabled via `EHRLICH_MCP_EXCALIDRAW=true` env var
- **Tool tagging**: Tools tagged with frozenset domain tags (chemistry, analysis, prediction, simulation, sports, nutrition, clinical, safety, literature, visualization); investigation control tools are universal (no tags); researcher sees only domain-relevant tools
- **Visualization tools**: 6 tools return structured `VisualizationPayload` JSON; orchestrator intercepts via `_maybe_viz_event()` and emits `VisualizationRendered` SSE event; frontend `VizRegistry` maps `viz_type` to lazy-loaded React component; `VisualizationPanel` renders charts in investigation page + report
- SSE streaming for real-time investigation updates (20 event types)
- **Phase progress indicator**: `PhaseChanged` event tracks 6 orchestrator phases (Classification & PICO → Literature Survey → Formulation → Hypothesis Testing → Negative Controls → Synthesis); frontend renders 6-segment progress bar
- **Literature survey methodology**: PICO decomposition + domain classification merged into single Haiku call; structured search protocol with citation chasing (snowballing); 6-level evidence hierarchy on findings; GRADE-adapted body-of-evidence grading (high/moderate/low/very_low) via Haiku; AMSTAR-2-adapted self-assessment; `LiteratureSurveyCompleted` event carries PICO, search stats, grade for PRISMA-lite transparency
- **Streaming cost indicator**: `CostUpdate` event yields cost snapshots after each phase/batch; `CostBadge` updates progressively (not just at completion)
- **Investigation templates**: 6 cross-domain prompts (4 molecular + 2 sports science) on home page via `TemplateCards` with domain badges
- **Citation provenance**: `source_type` + `source_id` on findings, rendered as clickable badges linking to ChEMBL, PDB, DOI, PubChem, UniProt, Open Targets
- **Markdown report export**: client-side markdown generation from InvestigationReport data, 8 sections, browser download
- **Candidate comparison**: side-by-side scoring view for 2-4 selected candidates with best-in-group highlighting
- **User-guided hypothesis steering**: `HypothesisApprovalRequested` event pauses orchestrator after formulation; user approves/rejects via `POST /investigate/{id}/approve`; `REJECTED` hypothesis status; 5-min auto-approve timeout
- **Scientific hypothesis model**: Based on Popper (falsifiability), Platt (strong inference), Feynman (compute consequences), Bayesian updating. Each hypothesis carries: prediction, null_prediction, success_criteria, failure_criteria, scope, hypothesis_type, prior_confidence, certainty_of_evidence. Evaluation uses evidence hierarchy (8 tiers), effect size thresholds, Bayesian prior→posterior updating, contradiction resolution, and convergence checks. See `docs/scientific-methodology.md` for full research and roadmap for all 6 phases.
- **Structured experiment protocols**: Based on Fisher (1935), Platt (1964), Cohen (1988), Saltelli (2008), OECD (2007), Tropsha (2010). Each experiment carries: independent_variable, dependent_variable, controls, confounders, analysis_plan, success_criteria, failure_criteria. Director designs with 5-principle methodology (VARIABLES, CONTROLS, CONFOUNDERS, ANALYSIS PLAN, SENSITIVITY). Researcher executes with 5-principle methodology (SENSITIVITY, APPLICABILITY DOMAIN, UNCERTAINTY, VERIFICATION, NEGATIVE RESULTS). Evaluator checks controls, criteria, analysis plan adherence, confounders.
- **Event persistence**: all SSE events stored in SQLite `events` table; completed investigations replay full timeline on page reload
- TanStack Router file-based routing in console
- `MultiModelOrchestrator`: hypothesis-driven loop with parallel experiment batches (2 hypotheses tested concurrently)
- **Parallel researchers**: `_run_experiment_batch()` uses `asyncio.Queue` to merge events from 2 concurrent researcher experiments
- **Prompt engineering**: XML-tagged instructions, multishot examples (2 per Director prompt), tool usage examples for Researcher
- **Context compaction**: `_build_prior_context()` compresses completed hypotheses into XML summary for Director
- `ToolCache` provides in-memory TTL-based caching for deterministic and API tools
- `SqliteInvestigationRepository` persists investigations + events to SQLite (WAL mode)
- `CostTracker` tracks per-model token usage with tiered pricing
- SSE reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- Semantic Scholar client: exponential backoff retry (3 attempts, 1s/2s/4s) on 429 and timeout
- All external API clients follow same pattern: httpx.AsyncClient, retry with backoff, structured error handling
- Molecule visualization: server-side 2D SVG depiction (RDKit `rdMolDraw2D`), 3Dmol.js for 3D/docking views
- `CandidateTable` shows 2D structure thumbnails with expandable detail panel (3D viewer + properties + Lipinski badge)
- Molecule API: `/molecule/depict` (SVG, cached 24h), `/molecule/conformer`, `/molecule/descriptors`, `/targets`
- Toast notifications via `sonner` (completion + error events, dark-themed OKLCH colors)
- Custom scrollbar CSS: 8px webkit + Firefox `scrollbar-width: thin` with OKLCH theme colors
- `InvestigationCompleted` event carries `findings[]`, `hypotheses[]`, `negative_controls[]`, `prompt` for replay hydration
- `CompletionSummaryCard` replaces `ActiveExperimentCard` post-completion (candidate + finding + hypothesis counts)
- `HypothesisBoard`: kanban-style card grid showing hypothesis status (proposed/testing/supported/refuted/revised)
- `NegativeControlPanel`: table of known-inactive compounds with pass/fail classification indicators
- **Unified Visualization**: `VisualizationPanel` is the single rendering surface for all visualizations. LiveLabViewer (3Dmol.js) auto-appears when molecular tool events are detected in the SSE stream. Chart visualizations from `VisualizationRendered` events render alongside.
- `LiveLabViewer` subscribes to SSE stream, renders molecular scene: protein cartoon + ligand sticks + score labels. Self-contained with internal experiment filter state.
- SSE event → 3D action mapping: `dock_against_target` → ligand appears in binding pocket, `predict_candidates` → molecules color by probability, `completed` → top candidates glow
- Interactive: rotate, zoom, click molecules for details; split-pane with Timeline
- **React Flow investigation diagrams**: `@xyflow/react` node graph with custom `InvestigationNode` and `AnnotationNode` types
- `InvestigationDiagram` lazy-loads React Flow via `React.lazy()` + `Suspense` (code-split ~188KB chunk)
- `DiagramRenderer`: React Flow with `fitView`, `colorMode="dark"`, `Background`, `Controls`, `MiniMap`
- `diagram-builder.ts` outputs React Flow `Node[]` + `Edge[]` with `smoothstep` edge routing
- Dark-friendly palette: dark fills (`#1f2937`, `#14532d`, `#450a0a`), light text, visible strokes
- Dashed edges for hypothesis revisions, solid `smoothstep` edges for experiment/finding links
- Section labels as `annotation` node type, investigation data as `investigation` node type
- Status-colored nodes: proposed (gray), testing (blue), supported (green), refuted (red), revised (orange)
- Read-only: `nodesDraggable={false}`, `nodesConnectable={false}`; built-in zoom/pan/minimap
- `ErrorBoundary` wraps both LiveLabViewer and InvestigationDiagram to prevent page crashes
- **Structured investigation report**: `InvestigationReport` component with 8 sections (Research Question, Executive Summary, Hypotheses & Outcomes, Methodology, Key Findings, Candidate Molecules, Model Validation, Cost & Performance)
- Report replaces plain-text ReportViewer; shown only after completion with full audit trail

## Key Files (Investigation Context)

| File | Purpose |
|------|---------|
| `investigation/application/multi_orchestrator.py` | Hypothesis-driven Director-Worker-Summarizer orchestrator |
| `investigation/application/cost_tracker.py` | Per-model cost tracking with tiered pricing |
| `investigation/application/tool_cache.py` | In-memory TTL cache for tool results (deterministic + API) |
| `investigation/application/prompts.py` | Domain-adaptive prompts: PICO+classification, literature survey, assessment, director (4 phases with experiment methodology + evidence evaluation with hierarchy/effect sizes/Bayesian updating/contradiction resolution/convergence + synthesis with GRADE certainty/priority tiers/knowledge gaps/follow-up), researcher (with sensitivity/AD/UQ methodology), summarizer |
| `investigation/domain/hypothesis.py` | Hypothesis entity (statement, rationale, prediction, null_prediction, success/failure_criteria, scope, hypothesis_type, prior_confidence, confidence, certainty_of_evidence) + HypothesisStatus + HypothesisType enums |
| `investigation/domain/experiment.py` | Experiment entity (description, tool_plan, independent_variable, dependent_variable, controls, confounders, analysis_plan, success_criteria, failure_criteria) + ExperimentStatus enum |
| `investigation/domain/negative_control.py` | NegativeControl frozen dataclass |
| `investigation/domain/positive_control.py` | PositiveControl frozen dataclass (known active, correctly_classified >= 0.5) |
| `investigation/domain/validation.py` | Z'-factor assay quality metric (compute_z_prime, AssayQualityMetrics) |
| `investigation/domain/candidate.py` | Candidate dataclass (identifier, identifier_type, name, rank, priority, notes, scores dict, attributes dict) |
| `investigation/domain/events.py` | 20 domain events (Hypothesis*, HypothesisApproval*, Experiment*, NegativeControl*, PositiveControl*, ValidationMetricsComputed, VisualizationRendered, DomainDetected, Finding, LiteratureSurveyCompleted, Tool*, Thinking, PhaseChanged, CostUpdate, Completed, Error) |
| `investigation/domain/visualization.py` | VisualizationPayload frozen dataclass (viz_type, title, data, config, domain) |
| `investigation/tools_viz.py` | 6 visualization tools: binding scatter, ADMET radar, training timeline, muscle heatmap, forest plot, evidence matrix |
| `investigation/domain/repository.py` | InvestigationRepository ABC (save_event, get_events for audit trail) |
| `investigation/infrastructure/sqlite_repository.py` | SQLite implementation with hypothesis/experiment/negative_control/event serialization + FTS5 findings search |
| `investigation/infrastructure/anthropic_client.py` | Anthropic API adapter with retry |
| `investigation/infrastructure/mcp_bridge.py` | MCP client bridge: connects to external MCP servers (stdio/SSE/streamable_http), routes tool calls |
| `investigation/domain/mcp_config.py` | `MCPServerConfig` frozen dataclass for MCP server connection config |
| `api/routes/investigation.py` | REST + SSE endpoints, 48-tool registry with domain tagging, domain registry, MCP bridge |
| `api/routes/methodology.py` | GET /methodology endpoint: phases, domains, tools, data sources, models |
| `api/routes/molecule.py` | Molecule depiction, conformer, descriptors, targets endpoints |
| `api/sse.py` | Domain event to SSE conversion (20 types) |

## Key Files (Data Source Clients)

| File | Purpose |
|------|---------|
| `analysis/infrastructure/chembl_loader.py` | ChEMBL bioactivity loader (flexible assay types) |
| `analysis/infrastructure/pubchem_client.py` | PubChem PUG REST compound search |
| `simulation/infrastructure/rcsb_client.py` | RCSB PDB Search + Data API for target discovery |
| `simulation/infrastructure/comptox_client.py` | EPA CompTox CTX API for environmental toxicity |
| `simulation/infrastructure/protein_store.py` | YAML-based protein target store + RCSB PDB fallback |
| `simulation/infrastructure/uniprot_client.py` | UniProt REST client for protein annotations |
| `simulation/infrastructure/opentargets_client.py` | Open Targets GraphQL client for disease-target associations |
| `analysis/infrastructure/gtopdb_client.py` | GtoPdb REST client for curated pharmacology |
| `literature/infrastructure/semantic_scholar_client.py` | Semantic Scholar paper search with retry |
| `sports/infrastructure/clinicaltrials_client.py` | ClinicalTrials.gov v2 API for exercise/training RCTs |
| `sports/infrastructure/dsld_client.py` | NIH DSLD supplement label database |
| `sports/infrastructure/fooddata_client.py` | USDA FoodData Central nutrient profiles |
| `sports/infrastructure/openfda_client.py` | OpenFDA CAERS adverse event reporting |

## Key Files (Molecule Visualization)

| File | Purpose |
|------|---------|
| `chemistry/infrastructure/rdkit_adapter.py` | RDKit adapter including `depict_2d` (SVG via `rdMolDraw2D`) |
| `chemistry/application/chemistry_service.py` | Thin wrapper over adapter |
| `api/routes/molecule.py` | 4 endpoints: depict (SVG), conformer (JSON), descriptors (JSON), targets (JSON) |
| `console/.../molecule/components/MolViewer2D.tsx` | Server-side SVG via `<img>` tag, lazy loading, error fallback |
| `console/.../molecule/components/MolViewer3D.tsx` | 3Dmol.js WebGL viewer for conformers |
| `console/.../molecule/components/DockingViewer.tsx` | 3Dmol.js protein+ligand overlay viewer |
| `console/.../investigation/components/CandidateDetail.tsx` | Expandable panel: 2D + 3D views + property card + Lipinski badge |
| `console/.../investigation/components/CandidateTable.tsx` | Thumbnail grid with expand/collapse rows |
| `console/.../investigation/components/HypothesisBoard.tsx` | Kanban-style hypothesis status grid |
| `console/.../investigation/components/HypothesisCard.tsx` | Expandable hypothesis card with confidence bar |
| `console/.../investigation/components/ActiveExperimentCard.tsx` | Live experiment activity card (tool name, counters) |
| `console/.../investigation/components/NegativeControlPanel.tsx` | Negative control validation table |
| `console/.../investigation/components/CompletionSummaryCard.tsx` | Post-completion card (candidate + finding + hypothesis counts) |
| `console/.../shared/components/ui/Toaster.tsx` | Sonner toast wrapper with dark OKLCH theme |

## Key Files (Live Lab + Diagrams + Report)

| File | Purpose |
|------|---------|
| `console/.../investigation/components/LiveLabViewer.tsx` | 3Dmol.js scene driven by SSE events: proteins, ligands, scores in real-time |
| `console/.../investigation/lib/scene-builder.ts` | Maps SSE events to 3Dmol.js operations (addModel, setStyle, addLabel, zoom) |
| `console/.../investigation/components/InvestigationDiagram.tsx` | Lazy-loaded React Flow wrapper with Suspense fallback |
| `console/.../investigation/components/DiagramRenderer.tsx` | React Flow renderer with custom InvestigationNode/AnnotationNode types, minimap, controls |
| `console/.../investigation/lib/diagram-builder.ts` | Transforms hypotheses/experiments/findings into React Flow Node[] + Edge[] |
| `console/.../investigation/components/InvestigationReport.tsx` | Structured 8-section report (research question, summary, hypotheses, methodology, findings, candidates, validation, cost) |
| `console/.../shared/components/ErrorBoundary.tsx` | Class-based error boundary wrapping LiveLabViewer and InvestigationDiagram |

## Key Files (Phase 1 Additions)

| File | Purpose |
|------|---------|
| `console/.../investigation/components/TemplateCards.tsx` | 6 cross-domain research prompt templates (4 molecular + 2 sports) with domain badges |
| `console/.../investigation/components/PromptInput.tsx` | Controlled component (value/onChange props), parent owns state |
| `console/.../investigation/components/CandidateComparison.tsx` | Side-by-side candidate scoring comparison (2-4 candidates) |
| `console/.../investigation/components/HypothesisApprovalCard.tsx` | Approve/reject hypotheses before testing with POST to /approve |
| `console/.../investigation/lib/export-markdown.ts` | Client-side markdown generation for 8-section report export |

## Key Files (Shared Context)

| File | Purpose |
|------|---------|
| `shared/chemistry_port.py` | `ChemistryPort` ABC -- cross-cutting interface for chemistry operations |
| `shared/fingerprint.py` | `Fingerprint` value object used across contexts |
| `shared/descriptors.py` | `MolecularDescriptors` value object |
| `shared/conformer.py` | `Conformer3D` value object |

## Key Files (Methodology Page)

| File | Purpose |
|------|---------|
| `api/routes/methodology.py` | GET /methodology endpoint: phases, domains, tools, data sources, models |
| `api/routes/stats.py` | GET /stats endpoint: aggregate counts (tools, domains, phases, data sources, events) |
| `console/src/routes/methodology.tsx` | Methodology page: phases, models, domains, tools, data sources |
| `console/src/features/investigation/hooks/use-methodology.ts` | React hook for fetching methodology data |

## Key Files (Visualization System)

| File | Purpose |
|------|---------|
| `investigation/domain/visualization.py` | `VisualizationPayload` frozen dataclass |
| `investigation/tools_viz.py` | 6 viz tools: binding scatter, ADMET radar, training timeline, muscle heatmap, forest plot, evidence matrix |
| `investigation/domain/events.py` | `VisualizationRendered` event (viz_type, title, data, config, domain) |
| `console/.../visualization/VizRegistry.tsx` | Lazy-loaded component registry mapping viz_type to React component |
| `console/.../visualization/VisualizationPanel.tsx` | Grid layout rendering multiple visualizations |
| `console/.../visualization/theme.ts` | OKLCH color tokens for charts |
| `console/.../visualization/charts/BindingScatter.tsx` | Recharts ScatterChart for compound affinities |
| `console/.../visualization/charts/ADMETRadar.tsx` | Recharts RadarChart for ADMET profiles |
| `console/.../visualization/charts/TrainingTimeline.tsx` | Recharts ComposedChart with ACWR danger zones + Brush |
| `console/.../visualization/charts/ForestPlot.tsx` | Visx custom forest plot for meta-analysis |
| `console/.../visualization/charts/EvidenceMatrix.tsx` | Visx HeatmapRect with diverging OKLCH color scale |
| `console/.../visualization/anatomy/BodyDiagram.tsx` | Custom SVG anatomical body diagram with muscle heatmap |
| `console/.../visualization/anatomy/body-paths.ts` | SVG path data for front/back anatomical views |
| `console/.../visualization/anatomy/color-scale.ts` | OKLCH intensity color interpolation (activation + risk modes) |

## Key Files (Domain Configuration)

| File | Purpose |
|------|---------|
| `investigation/domain/domain_config.py` | `DomainConfig` + `ScoreDefinition` frozen dataclasses + `merge_domain_configs()` for cross-domain |
| `investigation/domain/domain_registry.py` | `DomainRegistry`: register, multi-detect (returns `list[DomainConfig]`), lookup domains |
| `investigation/domain/domains/molecular.py` | `MOLECULAR_SCIENCE` config (tool tags, scores, prompt examples) |
| `investigation/domain/domains/sports.py` | `SPORTS_SCIENCE` config (protocol-based, table visualization) |
| `investigation/application/tool_registry.py` | `ToolRegistry` with domain tag filtering |
| `sports/tools.py` | 10 sports science tools (literature, evidence, protocols, injury, metrics, supplements, clinical trials, supplement labels, nutrient data, supplement safety) |
