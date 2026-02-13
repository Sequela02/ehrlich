# Ehrlich - AI Scientific Discovery Engine

AGPL-3.0 | Claude Code Hackathon (Feb 10-16, 2026)

## Project Overview

Ehrlich is a domain-agnostic scientific discovery platform that uses Claude as a hypothesis-driven scientific reasoning engine. Named after Paul Ehrlich, the father of the "magic bullet" concept.

The engine is domain-agnostic: a pluggable `DomainConfig` + `DomainRegistry` system lets any scientific domain plug in with its own tools, score definitions, and prompt examples. Currently supports three domains:

- **Molecular Science** -- antimicrobial resistance, drug discovery, toxicology, agricultural biocontrol
- **Training Science** -- exercise physiology, protocol optimization, injury risk assessment, clinical trials
- **Nutrition Science** -- supplement evidence analysis, dietary supplement safety, nutrient profiling, DRI adequacy assessment, drug-nutrient interactions, inflammatory index scoring

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun) + `web/` (TanStack Start landing page).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 67 tools (parallel: 2 experiments per batch)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars), PICO decomposition, evidence grading
```

Always uses `MultiModelOrchestrator`. Hypotheses tested in parallel batches of 2.

### Bounded Contexts (10)

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| shared | `server/src/ehrlich/shared/` | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D, MolecularDescriptors) |
| literature | `server/src/ehrlich/literature/` | Paper search (Semantic Scholar), references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration (ChEMBL, PubChem, GtoPdb), enrichment |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance, target discovery (RCSB PDB, UniProt, Open Targets), toxicity (EPA CompTox) |
| training | `server/src/ehrlich/training/` | Evidence analysis, protocol comparison, injury risk, training metrics, clinical trials (ClinicalTrials.gov), PubMed literature (E-utilities), exercise database (wger) |
| nutrition | `server/src/ehrlich/nutrition/` | Supplement evidence, supplement labels (NIH DSLD), nutrient data (USDA FoodData), supplement safety (OpenFDA CAERS), drug-nutrient interactions (RxNav), DRI adequacy, nutrient ratios, inflammatory index |
| investigation | `server/src/ehrlich/investigation/` | Multi-model orchestration + SQLite persistence + domain registry + MCP bridge |

### External Data Sources (15 external + 1 internal)

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
| PubMed | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils` | Biomedical literature search with MeSH terms (E-utilities) | None |
| wger | `https://wger.de/api/v2` | Exercise database (muscles, equipment, categories) | None |
| NIH DSLD | `https://api.ods.od.nih.gov/dsld/v9` | Dietary supplement label database (ingredients, amounts) | None |
| USDA FoodData | `https://api.nal.usda.gov/fdc/v1` | Nutrient profiles for foods and supplements | API key |
| OpenFDA CAERS | `https://api.fda.gov/food/event.json` | Supplement adverse event reports (safety monitoring) | None |
| RxNav | `https://rxnav.nlm.nih.gov/REST` | Drug-supplement and drug-nutrient interactions (RxNorm) | None |
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
# uv sync --extra all --extra dev                        # All deps (deep learning)
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
uv run pytest --cov=ehrlich --cov-report=term-missing    # Tests
uv run ruff check src/ tests/                            # Lint
uv run ruff format src/ tests/                           # Format
uv run mypy src/ehrlich/                                 # Type check
```

Optional extras: `deeplearning` (chemprop), `all` (everything).

### Console

```bash
cd console
bun install
bun dev              # Dev server :5173
bun test             # Vitest
bun run build        # vite build (generates route tree + bundles)
bun run typecheck    # tsc --noEmit (run after build for route types)
```

### Web (Landing Page)

```bash
cd web
bun install
bun run dev          # Dev server :3000 (vite dev)
bun run build        # vite build (generates .output/)
bun run typecheck    # tsc --noEmit
bun run start        # node .output/server/index.mjs
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

Scopes: kernel, shared, literature, chemistry, analysis, prediction, simulation, training, nutrition, investigation, api, console, mol, data, ci, docs, infra

## Tools (67 Total)

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
- `dock_against_target` -- Descriptor-based binding energy estimation
- `predict_admet` -- Drug-likeness profiling (absorption, metabolism, toxicity)
- `fetch_toxicity_profile` -- EPA CompTox environmental toxicity data
- `assess_resistance` -- Knowledge-based resistance mutation scoring

### Training Science (11) -- Exercise physiology and sports medicine
- `search_training_literature` -- Semantic Scholar with training science context
- `analyze_training_evidence` -- Pooled effect sizes, heterogeneity, evidence grading (A-D)
- `compare_protocols` -- Evidence-weighted protocol comparison with composite scoring
- `assess_injury_risk` -- Knowledge-based injury risk scoring (sport, load, history, age)
- `compute_training_metrics` -- ACWR, monotony, strain, session RPE load
- `search_clinical_trials` -- ClinicalTrials.gov exercise/training RCT search
- `search_pubmed_training` -- PubMed E-utilities with MeSH term support
- `search_exercise_database` -- wger exercise database by muscle/equipment/category
- `compute_performance_model` -- Banister fitness-fatigue model (CTL/ATL/TSB)
- `compute_dose_response` -- Dose-response curve from dose-effect data points
- `plan_periodization` -- Evidence-based periodization planning (linear/undulating/block)

### Nutrition Science (10) -- Supplement evidence, safety, adequacy, interactions
- `search_supplement_evidence` -- Supplement efficacy literature search
- `search_supplement_labels` -- NIH DSLD supplement product ingredient lookup
- `search_nutrient_data` -- USDA FoodData Central nutrient profiles
- `search_supplement_safety` -- OpenFDA CAERS adverse event reports for supplements
- `compare_nutrients` -- Side-by-side nutrient comparison across multiple foods
- `assess_nutrient_adequacy` -- DRI-based nutrient adequacy assessment (EAR/RDA/AI/UL)
- `check_intake_safety` -- Tolerable Upper Intake Level (UL) safety screening
- `check_interactions` -- Drug-supplement and drug-nutrient interaction screening (RxNav)
- `analyze_nutrient_ratios` -- Clinically relevant nutrient ratios (omega-6:3, Ca:Mg, Na:K, Zn:Cu, Ca:P, Fe:Cu)
- `compute_inflammatory_index` -- Simplified Dietary Inflammatory Index (DII) scoring

### Visualization (12) -- Domain-specific interactive charts
- `render_binding_scatter` -- Scatter plot of compound binding affinities (Recharts)
- `render_admet_radar` -- Radar chart of ADMET/drug-likeness properties (Recharts)
- `render_training_timeline` -- Training load timeline with ACWR danger zones (Recharts)
- `render_muscle_heatmap` -- Anatomical body diagram with muscle activation/risk (Custom SVG)
- `render_forest_plot` -- Forest plot for meta-analysis results (Visx)
- `render_evidence_matrix` -- Hypothesis-by-evidence heatmap (Visx)
- `render_performance_chart` -- Banister fitness-fatigue performance chart (Recharts)
- `render_funnel_plot` -- Funnel plot for publication bias assessment (Visx)
- `render_dose_response` -- Dose-response curve with confidence intervals (Visx)
- `render_nutrient_comparison` -- Grouped bar chart comparing nutrient profiles across foods (Recharts)
- `render_nutrient_adequacy` -- Horizontal bar chart showing % RDA with MAR score (Recharts)
- `render_therapeutic_window` -- Range chart showing EAR/RDA/UL safety zones per nutrient (Visx)

### Statistics (2) -- Domain-agnostic hypothesis testing (scipy.stats)
- `run_statistical_test` -- Compare two numeric groups (auto-selects t-test/Welch/Mann-Whitney, returns p-value, Cohen's d, 95% CI)
- `run_categorical_test` -- Test contingency tables (auto-selects Fisher's exact/chi-squared, returns p-value, odds ratio/Cramer's V)

### Investigation (7) -- Hypothesis lifecycle + self-referential
- `propose_hypothesis` -- Register testable hypothesis
- `design_experiment` -- Plan experiment with tool sequence
- `evaluate_hypothesis` -- Assess outcome (supported/refuted/revised)
- `record_finding` -- Record finding linked to hypothesis + evidence_type
- `record_negative_control` -- Validate model with known-inactive compounds
- `search_prior_research` -- Search Ehrlich's own past findings via FTS5
- `conclude_investigation` -- Final summary with ranked candidates

## Key Patterns

### Scientific Methodology

- **Hypothesis-driven investigation loop**: formulate hypotheses (with predictions, criteria, scope, prior confidence) -> design structured experiment protocols -> execute tools with methodology guidance -> evaluate with scientific methodology -> revise/reject -> synthesize. See `docs/scientific-methodology.md` for full details
- **Hypothesis model**: Based on Popper (falsifiability), Platt (strong inference), Feynman (compute consequences), Bayesian updating. Each hypothesis carries: prediction, null_prediction, success_criteria, failure_criteria, scope, hypothesis_type, prior_confidence, certainty_of_evidence. Evaluation uses 8-tier evidence hierarchy, effect size thresholds, Bayesian prior-to-posterior updating, contradiction resolution, and convergence checks
- **Experiment protocols**: Based on Fisher (1935), Platt (1964), Cohen (1988), Saltelli (2008), OECD (2007), Tropsha (2010). Each experiment carries: independent_variable, dependent_variable, controls, confounders, analysis_plan, success_criteria, failure_criteria. Director designs with 5-principle methodology (VARIABLES, CONTROLS, CONFOUNDERS, ANALYSIS PLAN, SENSITIVITY). Researcher executes with 5-principle methodology (SENSITIVITY, APPLICABILITY DOMAIN, UNCERTAINTY, VERIFICATION, NEGATIVE RESULTS)
- **Statistical testing in experiments** -- Director plans statistical tests (test type, alpha, effect size) in experiment design via optional `statistical_test_plan`; Researcher executes `run_statistical_test` (continuous) or `run_categorical_test` (categorical) after gathering comparison data; results recorded as findings with evidence_type based on significance
- **Evidence-linked findings**: every finding references a `hypothesis_id` + `evidence_type` (supporting/contradicting/neutral)
- **Controls**: negative controls validate model predictions with known-inactive compounds (`NegativeControl` entity); positive controls validate pipeline with known-active compounds (`PositiveControl` entity, correctly_classified >= 0.5, quality: sufficient/marginal/insufficient)
- **Validation metrics**: Z'-factor assay quality (Zhang et al., 1999), permutation significance (Y-scrambling, p-value), scaffold-split vs random-split comparison; controls scored through trained models; `ValidationMetricsComputed` event
- **Literature survey**: PICO decomposition + domain classification merged into single Haiku call; structured search with citation chasing (snowballing); GRADE-adapted body-of-evidence grading via Haiku; AMSTAR-2-adapted self-assessment; `LiteratureSurveyCompleted` event carries PICO, search stats, grade
- **User-guided steering**: `HypothesisApprovalRequested` event pauses orchestrator after formulation; user approves/rejects via `POST /investigate/{id}/approve`; `REJECTED` status; 5-min auto-approve timeout
- **Synthesis**: GRADE certainty grading (5 downgrading + 3 upgrading domains), priority tiers (1-4), structured limitations taxonomy, knowledge gap analysis, follow-up experiment recommendations

### System Patterns

- Each bounded context has: `domain/`, `application/`, `infrastructure/`, `tools.py`
- Domain entities use `@dataclass` with `__post_init__` validation; repository interfaces are ABCs in `domain/repository.py`; infrastructure adapters implement those ABCs
- Tool functions in `tools.py` are the boundary between Claude and application services
- **Parallel researchers**: `_run_experiment_batch()` uses `asyncio.Queue` to merge events from 2 concurrent experiments
- **Context compaction**: `_build_prior_context()` compresses completed hypotheses into XML summary for Director
- **Prompt engineering**: XML-tagged instructions (`<instructions>`, `<examples>`, `<output_format>`, `<tool_reference>`), multishot examples (2 per Director prompt), tool usage examples for Researcher
- **ToolCache**: in-memory TTL-based caching for deterministic and API tool results
- **Event persistence**: all SSE events stored in SQLite `events` table (WAL mode); completed investigations replay full timeline on page reload
- **CostTracker**: per-model token usage with tiered pricing; `CostUpdate` event yields cost snapshots after each phase/batch
- **Structured outputs**: Director calls use `output_config` with JSON schemas (6 schemas in `domain/schemas.py`) to guarantee valid JSON; eliminates parsing fallbacks
- **Director streaming**: `_director_call()` is an async generator using `stream_message()`; yields `Thinking` events in real time as tokens arrive; Researcher and Summarizer remain non-streaming
- All external API clients follow same pattern: `httpx.AsyncClient`, retry with exponential backoff, structured error handling

### Integration Patterns

- **Domain configuration**: `DomainConfig` defines per-domain tool tags, score definitions, prompt examples; `DomainRegistry` auto-detects domain; `DomainDetected` SSE event sends display config to frontend
- **Domain tool examples**: each `DomainConfig` includes `tool_examples` in `experiment_examples` showing realistic tool chaining patterns; ensures Researcher (Sonnet 4.5) has usage guidance for all domain-specific tools
- **Multi-domain investigations**: `DomainRegistry.detect()` returns `list[DomainConfig]`; `merge_domain_configs()` creates synthetic merged config with union of tool_tags, concatenated score_definitions, joined prompt examples
- **Tool tagging**: Tools tagged with frozenset domain tags (chemistry, analysis, prediction, simulation, training, clinical, nutrition, safety, literature, visualization); investigation control tools are universal (no tags); researcher sees only domain-relevant tools
- **Self-referential research**: `search_prior_research` queries FTS5 full-text index of past findings; indexed on completion via `_rebuild_fts()`; intercepted in orchestrator `_dispatch_tool()` and routed to repository; "ehrlich" source type links to past investigations
- **MCP bridge**: Optional `MCPBridge` connects to external MCP servers (e.g. Excalidraw); tools registered dynamically via `ToolRegistry.register_mcp_tools()`; lifecycle managed by orchestrator; enabled via `EHRLICH_MCP_EXCALIDRAW=true`
- **SSE streaming**: 20 event types for real-time updates; reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- **Phase progress**: `PhaseChanged` event tracks 6 orchestrator phases (Classification & PICO -> Literature Survey -> Formulation -> Hypothesis Testing -> Negative Controls -> Synthesis); frontend renders 6-segment progress bar
- **Citation provenance**: `source_type` + `source_id` on findings, rendered as clickable badges linking to ChEMBL, PDB, DOI, PubChem, UniProt, Open Targets
- **Data configuration**: protein targets via YAML (`data/targets/*.yaml`) + dynamic RCSB PDB discovery; resistance data via YAML (`data/resistance/*.yaml`)
- **Flexible data loading**: ChEMBL queries accept any assay type (MIC, Ki, EC50, etc.), not hardcoded

### UI Patterns

- **Visualization pipeline**: 12 viz tools return `VisualizationPayload` JSON; orchestrator intercepts via `_maybe_viz_event()` and emits `VisualizationRendered` SSE event; `VizRegistry` maps `viz_type` to lazy-loaded React component; `VisualizationPanel` renders all charts
- **LiveLabViewer**: 3Dmol.js scene driven by SSE events -- protein targets load, ligands dock, candidates color by score. SSE event mapping: `dock_against_target` -> ligand in binding pocket, `predict_candidates` -> color by probability, `completed` -> top candidates glow. Interactive rotate/zoom/click, split-pane with Timeline
- **React Flow diagrams**: `@xyflow/react` node graph with custom `InvestigationNode` and `AnnotationNode` types; status-colored nodes (proposed=gray, testing=blue, supported=green, refuted=red, revised=orange); dashed edges for revisions, solid smoothstep for links; read-only with zoom/pan/minimap; lazy-loaded (~188KB chunk)
- **Investigation report**: 8 sections (Research Question, Executive Summary, Hypotheses & Outcomes, Methodology, Key Findings, Candidate Molecules, Model Validation, Cost & Performance); shown post-completion with full audit trail; markdown export via client-side generation
- **Molecule visualization**: server-side 2D SVG (RDKit `rdMolDraw2D`), 3Dmol.js for 3D/docking; `CandidateTable` shows thumbnails with expandable detail (3D viewer + properties + Lipinski badge)
- **Molecule API**: `/molecule/depict` (SVG, cached 24h), `/molecule/conformer`, `/molecule/descriptors`, `/molecule/targets`
- **Investigation templates**: 7 cross-domain prompts (4 molecular + 2 training + 1 nutrition) on home page via `TemplateCards` with domain badges
- **Candidate comparison**: side-by-side scoring view for 2-4 candidates with best-in-group highlighting
- **HypothesisBoard**: kanban-style card grid showing hypothesis status with expandable confidence bars
- TanStack Router file-based routing; `ErrorBoundary` wraps LiveLabViewer and InvestigationDiagram
- Toast notifications via `sonner` (dark-themed OKLCH colors); custom scrollbar CSS (8px webkit + Firefox thin)
- `InvestigationCompleted` event carries `findings[]`, `hypotheses[]`, `negative_controls[]`, `prompt` for replay hydration

## Key Files (Server)

All paths relative to `server/src/ehrlich/`.

### shared/

| File | Purpose |
|------|---------|
| `chemistry_port.py` | `ChemistryPort` ABC -- cross-cutting interface for chemistry operations |
| `fingerprint.py` | `Fingerprint` value object |
| `descriptors.py` | `MolecularDescriptors` value object |
| `conformer.py` | `Conformer3D` value object |

### literature/

| File | Purpose |
|------|---------|
| `infrastructure/semantic_scholar.py` | Semantic Scholar paper search with retry |

### chemistry/

| File | Purpose |
|------|---------|
| `infrastructure/rdkit_adapter.py` | RDKit adapter including `depict_2d` (SVG) |
| `application/chemistry_service.py` | Thin wrapper over adapter |

### analysis/

| File | Purpose |
|------|---------|
| `domain/statistics.py` | `StatisticalResult` frozen dataclass |
| `application/statistics_service.py` | `StatisticsService` -- scipy.stats hypothesis testing (t-test, Welch, Mann-Whitney, chi-squared, Fisher) |
| `infrastructure/chembl_loader.py` | ChEMBL bioactivity loader (flexible assay types) |
| `infrastructure/pubchem_client.py` | PubChem PUG REST compound search |
| `infrastructure/gtopdb_client.py` | GtoPdb REST client for curated pharmacology |

### simulation/

| File | Purpose |
|------|---------|
| `infrastructure/rcsb_client.py` | RCSB PDB Search + Data API for target discovery |
| `infrastructure/comptox_client.py` | EPA CompTox CTX API for environmental toxicity |
| `infrastructure/protein_store.py` | YAML-based protein target store + RCSB PDB fallback |
| `infrastructure/uniprot_client.py` | UniProt REST client for protein annotations |
| `infrastructure/opentargets_client.py` | Open Targets GraphQL client for disease-target associations |

### training/

| File | Purpose |
|------|---------|
| `tools.py` | 10 training science tools |
| `domain/entities.py` | EvidenceGrade, StudyResult, EvidenceAnalysis, TrainingProtocol, ProtocolComparison, InjuryRiskAssessment, WorkloadMetrics, ClinicalTrial, PubMedArticle, Exercise, PerformanceModelPoint, DoseResponsePoint |
| `domain/repository.py` | ClinicalTrialRepository, PubMedRepository, ExerciseRepository ABCs |
| `application/training_service.py` | TrainingService (evidence analysis, protocol comparison, injury risk, metrics, clinical trials, PubMed, exercises, performance model, dose-response) |
| `infrastructure/clinicaltrials_client.py` | ClinicalTrials.gov v2 API |
| `infrastructure/pubmed_client.py` | PubMed E-utilities API (ESearch + EFetch) |
| `infrastructure/wger_client.py` | wger exercise database REST API |

### nutrition/

| File | Purpose |
|------|---------|
| `tools.py` | 10 nutrition science tools |
| `domain/entities.py` | IngredientEntry, SupplementLabel, NutrientEntry, NutrientProfile, AdverseEvent, DrugInteraction, NutrientRatio, AdequacyResult |
| `domain/repository.py` | SupplementRepository, NutrientRepository, AdverseEventRepository, InteractionRepository ABCs |
| `domain/dri.py` | Dietary Reference Intake (DRI) tables -- EAR, RDA, AI, UL for ~30 nutrients by age/sex |
| `application/nutrition_service.py` | NutritionService (supplement evidence, labels, nutrients, safety, comparison, adequacy, interactions, ratios, inflammatory index) |
| `infrastructure/dsld_client.py` | NIH DSLD supplement label database |
| `infrastructure/fooddata_client.py` | USDA FoodData Central nutrient profiles |
| `infrastructure/openfda_client.py` | OpenFDA CAERS adverse event reporting |
| `infrastructure/rxnav_client.py` | RxNav drug-nutrient interaction API |

### investigation/

| File | Purpose |
|------|---------|
| `application/multi_orchestrator.py` | Director-Worker-Summarizer orchestrator |
| `application/cost_tracker.py` | Per-model cost tracking with tiered pricing |
| `application/tool_cache.py` | In-memory TTL cache for tool results |
| `application/tool_registry.py` | `ToolRegistry` with domain tag filtering |
| `application/prompts.py` | Domain-adaptive prompts (PICO, literature survey, director, researcher, summarizer) |
| `domain/schemas.py` | JSON schemas for structured output responses (6 schemas: PICO, Formulation, Experiment Design, Evaluation, Synthesis, Literature Grading) |
| `domain/hypothesis.py` | Hypothesis entity + HypothesisStatus + HypothesisType enums |
| `domain/experiment.py` | Experiment entity + ExperimentStatus enum |
| `domain/candidate.py` | Candidate dataclass (identifier, scores, attributes) |
| `domain/negative_control.py` | NegativeControl frozen dataclass |
| `domain/positive_control.py` | PositiveControl frozen dataclass |
| `domain/validation.py` | Z'-factor assay quality metric |
| `domain/events.py` | 20 domain events |
| `domain/visualization.py` | `VisualizationPayload` frozen dataclass |
| `domain/repository.py` | InvestigationRepository ABC |
| `domain/domain_config.py` | `DomainConfig` + `ScoreDefinition` + `merge_domain_configs()` |
| `domain/domain_registry.py` | `DomainRegistry` (register, multi-detect, lookup) |
| `domain/domains/molecular.py` | `MOLECULAR_SCIENCE` config |
| `domain/domains/training.py` | `TRAINING_SCIENCE` config |
| `domain/domains/nutrition.py` | `NUTRITION_SCIENCE` config |
| `domain/mcp_config.py` | `MCPServerConfig` frozen dataclass |
| `tools_viz.py` | 12 visualization tools |
| `infrastructure/sqlite_repository.py` | SQLite persistence + FTS5 findings search |
| `infrastructure/anthropic_client.py` | Anthropic API adapter with retry, streaming, and structured outputs |
| `infrastructure/mcp_bridge.py` | MCP client bridge (stdio/SSE/streamable_http) |

## Key Files (API)

All paths relative to `server/src/ehrlich/api/`.

| File | Purpose |
|------|---------|
| `routes/investigation.py` | REST + SSE endpoints, 67-tool registry, domain registry, MCP bridge |
| `routes/methodology.py` | GET /methodology: phases, domains, tools, data sources, models |
| `routes/molecule.py` | Molecule depiction, conformer, descriptors, targets endpoints |
| `routes/stats.py` | GET /stats: aggregate counts |
| `sse.py` | Domain event to SSE conversion (20 types) |

## Key Files (Console)

All paths relative to `console/src/`.

### Investigation components

| File | Purpose |
|------|---------|
| `features/investigation/components/LiveLabViewer.tsx` | 3Dmol.js SSE-driven molecular scene |
| `features/investigation/components/InvestigationDiagram.tsx` | Lazy-loaded React Flow wrapper |
| `features/investigation/components/DiagramRenderer.tsx` | React Flow renderer with custom node types, minimap, controls |
| `features/investigation/components/InvestigationReport.tsx` | 8-section structured report |
| `features/investigation/components/CandidateTable.tsx` | Thumbnail grid with expandable rows |
| `features/investigation/components/CandidateDetail.tsx` | 2D + 3D views + property card + Lipinski badge |
| `features/investigation/components/CandidateComparison.tsx` | Side-by-side scoring comparison |
| `features/investigation/components/HypothesisBoard.tsx` | Kanban-style hypothesis status grid |
| `features/investigation/components/HypothesisCard.tsx` | Expandable hypothesis card with confidence bar |
| `features/investigation/components/HypothesisApprovalCard.tsx` | Approve/reject before testing |
| `features/investigation/components/ActiveExperimentCard.tsx` | Live experiment activity card |
| `features/investigation/components/CompletionSummaryCard.tsx` | Post-completion summary card |
| `features/investigation/components/NegativeControlPanel.tsx` | Negative control validation table |
| `features/investigation/components/TemplateCards.tsx` | 7 cross-domain research prompt templates |
| `features/investigation/components/PromptInput.tsx` | Controlled prompt input |

### Investigation lib + hooks

| File | Purpose |
|------|---------|
| `features/investigation/lib/scene-builder.ts` | SSE events to 3Dmol.js operations |
| `features/investigation/lib/diagram-builder.ts` | Hypotheses/experiments/findings to React Flow nodes + edges |
| `features/investigation/lib/export-markdown.ts` | Client-side markdown report generation |
| `features/investigation/hooks/use-methodology.ts` | React hook for methodology data |

### Molecule components

| File | Purpose |
|------|---------|
| `features/molecule/components/MolViewer2D.tsx` | Server-side SVG viewer |
| `features/molecule/components/MolViewer3D.tsx` | 3Dmol.js WebGL conformer viewer |
| `features/molecule/components/DockingViewer.tsx` | 3Dmol.js protein+ligand overlay |

### Visualization system

| File | Purpose |
|------|---------|
| `features/visualization/VizRegistry.tsx` | Lazy-loaded component registry (viz_type to React component) |
| `features/visualization/VisualizationPanel.tsx` | Grid layout for multiple visualizations |
| `features/visualization/theme.ts` | OKLCH color tokens for charts |
| `features/visualization/charts/BindingScatter.tsx` | Recharts ScatterChart |
| `features/visualization/charts/ADMETRadar.tsx` | Recharts RadarChart |
| `features/visualization/charts/TrainingTimeline.tsx` | Recharts ComposedChart with ACWR + Brush |
| `features/visualization/charts/ForestPlot.tsx` | Visx custom forest plot |
| `features/visualization/charts/EvidenceMatrix.tsx` | Visx HeatmapRect with OKLCH scale |
| `features/visualization/charts/PerformanceChart.tsx` | Recharts ComposedChart for Banister fitness-fatigue model |
| `features/visualization/charts/FunnelPlot.tsx` | Visx funnel plot for publication bias assessment |
| `features/visualization/charts/DoseResponseCurve.tsx` | Visx dose-response curve with confidence band |
| `features/visualization/charts/NutrientComparison.tsx` | Recharts grouped BarChart for food nutrient comparison |
| `features/visualization/charts/NutrientAdequacy.tsx` | Recharts horizontal BarChart showing % RDA with MAR score |
| `features/visualization/charts/TherapeuticWindow.tsx` | Visx custom range chart with EAR/RDA/UL safety zones |
| `features/visualization/anatomy/BodyDiagram.tsx` | Custom SVG anatomical body diagram |
| `features/visualization/anatomy/body-paths.ts` | SVG path data for front/back views |
| `features/visualization/anatomy/color-scale.ts` | OKLCH intensity color interpolation |

### Shared + routes

| File | Purpose |
|------|---------|
| `shared/components/ErrorBoundary.tsx` | Error boundary for LiveLabViewer and InvestigationDiagram |
| `shared/components/ui/Toaster.tsx` | Sonner toast wrapper with dark OKLCH theme |
| `routes/methodology.tsx` | Methodology page |

## Key Files (Web Landing Page)

All paths relative to `web/src/`.

| File | Purpose |
|------|---------|
| `routes/__root.tsx` | Root layout with shellComponent, HeadContent, SEO meta, font loading |
| `routes/index.tsx` | Landing page wiring all 10 components |
| `components/Nav.tsx` | Fixed navbar with scroll progress bar + mobile menu |
| `components/Footer.tsx` | Minimal footer with links and license |
| `components/SectionHeader.tsx` | Mono label with left border accent |
| `components/Hero.tsx` | Bottom-third hero with ASCII bg, stats bar, CTAs |
| `components/Architecture.tsx` | Director-Worker-Summarizer diagram with fork/merge connectors |
| `components/Methodology.tsx` | 6-phase pipeline with glow-pulse active node |
| `components/Domains.tsx` | 3 asymmetric domain cards with tool counts |
| `components/DataSources.tsx` | 15 sources with large number visual anchor |
| `components/OpenSource.tsx` | Typography-driven sparse section |
| `components/CTA.tsx` | Minimal CTA with arrow links |
| `styles/app.css` | Tailwind 4 + OKLCH tokens + scroll/stagger animations |
| `lib/constants.ts` | Stats, nav/footer links, domains, data sources, methodology phases |
| `lib/ascii-patterns.ts` | ASCII art backgrounds (hero, architecture, methodology, data sources) |
| `lib/use-reveal.ts` | IntersectionObserver scroll reveal hook |
| `lib/use-scroll-progress.ts` | Scroll progress fraction (0-1) hook |
