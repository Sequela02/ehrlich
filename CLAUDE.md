# Ehrlich - AI Scientific Discovery Engine

AGPL-3.0 | Claude Code Hackathon (Feb 10-16, 2026)

## Project Overview

Ehrlich is a domain-agnostic scientific discovery platform that uses Claude as a hypothesis-driven scientific reasoning engine. Named after Paul Ehrlich, the father of the "magic bullet" concept.

The engine is domain-agnostic: a pluggable `DomainConfig` + `DomainRegistry` system lets any scientific domain plug in with its own tools, score definitions, and prompt examples. Currently supports four domains:

- **Molecular Science** -- antimicrobial resistance, drug discovery, toxicology, agricultural biocontrol
- **Training Science** -- exercise physiology, protocol optimization, injury risk assessment, clinical trials
- **Nutrition Science** -- supplement evidence analysis, dietary supplement safety, nutrient profiling, DRI adequacy assessment, drug-nutrient interactions, inflammatory index scoring
- **Impact Evaluation** -- causal analysis of social programs (education, health, sports, employment, housing). Economic indicators (World Bank, WHO GHO, FRED), cross-program comparison, benchmark fetching. See `docs/impact-evaluation-domain.md`

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun) + `web/` (TanStack Start landing page).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 79 tools (parallel: 2 experiments per batch)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars), PICO decomposition, evidence grading
```

Always uses `MultiModelOrchestrator`. Hypotheses tested in parallel batches of 2.

### Bounded Contexts (11)

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| shared | `server/src/ehrlich/shared/` | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D, MolecularDescriptors) |
| literature | `server/src/ehrlich/literature/` | Paper search (Semantic Scholar), references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration (ChEMBL, PubChem, GtoPdb), enrichment, domain-agnostic causal inference (DiD, PSM, RDD, Synthetic Control) |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance, target discovery (RCSB PDB, UniProt, Open Targets), toxicity (EPA CompTox) |
| training | `server/src/ehrlich/training/` | Evidence analysis, protocol comparison, injury risk, training metrics, clinical trials (ClinicalTrials.gov), PubMed literature (E-utilities), exercise database (wger) |
| nutrition | `server/src/ehrlich/nutrition/` | Supplement evidence, supplement labels (NIH DSLD), nutrient data (USDA FoodData), supplement safety (OpenFDA CAERS), drug-nutrient interactions (RxNav), DRI adequacy, nutrient ratios, inflammatory index |
| impact | `server/src/ehrlich/impact/` | Social program evaluation: economic indicators (World Bank, WHO GHO, FRED), cross-program comparison, benchmarking |
| investigation | `server/src/ehrlich/investigation/` | Multi-model orchestration + PostgreSQL persistence + domain registry + MCP bridge |

### External Data Sources (18 external + 1 internal)

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
| World Bank | `https://api.worldbank.org/v2/` | Development indicators by country (GDP, poverty, education, health) | None |
| WHO GHO | `https://ghoapi.azureedge.net/api/` | Global health statistics by country (life expectancy, mortality, disease burden) | None |
| FRED | `https://api.stlouisfed.org/fred/` | 800K+ US economic time series (GDP, unemployment, CPI, interest rates) | API key |
| Ehrlich tsvector | internal | Full-text search of past investigation findings (PostgreSQL GIN index) | None |

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

Required env vars: `ANTHROPIC_API_KEY`, `EHRLICH_DATABASE_URL` (PostgreSQL), `EHRLICH_WORKOS_CLIENT_ID`, `EHRLICH_WORKOS_API_KEY`.

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

Required env vars in `console/.env.local`: `VITE_API_URL` (e.g. `http://localhost:8000/api/v1`), `VITE_WORKOS_CLIENT_ID`, `VITE_WORKOS_REDIRECT_URI` (e.g. `http://localhost:5173/callback`).

WorkOS dashboard must whitelist the console origin (e.g. `http://localhost:5173`) in **Authentication > Sessions > CORS**.

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

Scopes: kernel, shared, literature, chemistry, analysis, prediction, simulation, training, nutrition, impact, investigation, api, console, mol, data, ci, docs, infra

## Tools (84 Total)

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

### Analysis (12) -- ChEMBL + PubChem + GtoPdb + Domain-Agnostic Causal Inference
- `explore_dataset` -- Load ChEMBL bioactivity data for any organism/target
- `search_bioactivity` -- Flexible ChEMBL query (any assay type: MIC, Ki, EC50, IC50, Kd)
- `search_compounds` -- PubChem compound search by target/activity/similarity
- `search_pharmacology` -- GtoPdb curated receptor/ligand interactions with affinities
- `analyze_substructures` -- Chi-squared enrichment of SMARTS patterns
- `compute_properties` -- Property distributions (active vs inactive)
- `estimate_did` -- Difference-in-differences causal estimation with parallel trends test and threat assessment
- `estimate_psm` -- Propensity score matching with balance diagnostics
- `estimate_rdd` -- Regression discontinuity design (sharp/fuzzy)
- `estimate_synthetic_control` -- Synthetic control method for single treated unit
- `assess_threats` -- Knowledge-based validity threat assessment for causal methods (DiD, PSM, RDD, RCT, IV)
- `compute_cost_effectiveness` -- Cost per unit outcome, ICER calculation

### Prediction (6) -- XGBoost, domain-agnostic ML
- `train_model` -- Train ML model on SMILES+activity dataset (scaffold-split + random-split metrics, permutation p-value)
- `predict_candidates` -- Score compounds with trained model
- `cluster_compounds` -- Butina structural clustering
- `train_classifier` -- Train binary classifier on tabular feature data (any domain)
- `predict_scores` -- Score samples with trained classifier (any domain)
- `cluster_data` -- Hierarchical clustering on tabular feature data (any domain)

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

### Impact Evaluation (3) -- Social program analysis, economic indicators
- `search_economic_indicators` -- Query economic time series from FRED, World Bank, or WHO GHO
- `fetch_benchmark` -- Get comparison values from international sources (World Bank, WHO GHO)
- `compare_programs` -- Cross-program comparison using existing statistical tests

### Visualization (17) -- Domain-specific interactive charts
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
- `render_program_dashboard` -- Multi-indicator KPI dashboard with target tracking (Recharts)
- `render_geographic_comparison` -- Region bar chart with benchmark reference line (Recharts)
- `render_parallel_trends` -- DiD parallel trends chart, treatment vs control over time (Recharts)
- `render_rdd_plot` -- Regression discontinuity scatter with cutoff line and fitted curves (Visx)
- `render_causal_diagram` -- DAG showing treatment, outcome, confounders, and mediators (Visx)

### Statistics (2) -- Domain-agnostic hypothesis testing (scipy.stats)
- `run_statistical_test` -- Compare two numeric groups (auto-selects t-test/Welch/Mann-Whitney, returns p-value, Cohen's d, 95% CI)
- `run_categorical_test` -- Test contingency tables (auto-selects Fisher's exact/chi-squared, returns p-value, odds ratio/Cramer's V)

### Investigation (7) -- Hypothesis lifecycle + self-referential
- `propose_hypothesis` -- Register testable hypothesis
- `design_experiment` -- Plan experiment with tool sequence
- `evaluate_hypothesis` -- Assess outcome (supported/refuted/revised)
- `record_finding` -- Record finding linked to hypothesis + evidence_type
- `record_negative_control` -- Validate model with known-inactive compounds
- `search_prior_research` -- Search Ehrlich's own past findings via full-text search
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
- **Parallel researchers**: `_run_experiment_batch()` uses `asyncio.Queue` to merge events from 2 concurrent experiments; three-layer differentiation prevents duplicate work: (1) orthogonal hypothesis formulation via Director prompt, (2) sibling-aware experiment design with `<sibling_experiments>` context, (3) researcher sibling context via `<parallel_experiment>` tag
- **Context compaction**: `_build_prior_context()` compresses completed hypotheses into XML summary for Director
- **Prompt engineering**: XML-tagged instructions (`<instructions>`, `<examples>`, `<output_format>`, `<tool_reference>`), multishot examples (2 per Director prompt), tool usage examples for Researcher
- **ToolCache**: in-memory TTL-based caching for deterministic and API tool results
- **Event persistence**: all SSE events stored in PostgreSQL `events` table; completed investigations replay full timeline on page reload
- **CostTracker**: per-model token usage with tiered pricing; `CostUpdate` event yields cost snapshots after each phase/batch
- **Structured outputs**: Director calls use `output_config` with JSON schemas (6 schemas in `domain/schemas.py`) to guarantee valid JSON; eliminates parsing fallbacks
- **Director streaming**: `_director_call()` is an async generator using `stream_message()`; yields `Thinking` events in real time as tokens arrive; Researcher and Summarizer remain non-streaming
- All external API clients follow same pattern: `httpx.AsyncClient`, retry with exponential backoff, structured error handling
- **Authentication**: WorkOS JWT middleware (`api/auth.py`); JWKS verification via `PyJWKClient`; `get_current_user` (header) and `get_current_user_sse` (header or `?token=` query param for EventSource); `get_optional_user` for public routes
- **Credit system**: director tier selection (haiku=1cr, sonnet=3cr, opus=5cr); credits deducted on investigation start; refunded on failure; `credit_transactions` table for audit trail; `GET /credits/balance` endpoint
- **BYOK (Bring Your Own Key)**: `X-Anthropic-Key` header pass-through; bypasses credit system; API key forwarded to `AnthropicClientAdapter`; checked on both `POST /investigate` and `GET /investigate/{id}/stream`

### Integration Patterns

- **Domain configuration**: `DomainConfig` defines per-domain tool tags, score definitions, prompt examples; `DomainRegistry` auto-detects domain; `DomainDetected` SSE event sends display config to frontend
- **Domain tool examples**: each `DomainConfig` includes `tool_examples` in `experiment_examples` showing realistic tool chaining patterns; ensures Researcher (Sonnet 4.5) has usage guidance for all domain-specific tools
- **Multi-domain investigations**: `DomainRegistry.detect()` returns `list[DomainConfig]`; `merge_domain_configs()` creates synthetic merged config with union of tool_tags, concatenated score_definitions, joined prompt examples
- **Tool tagging**: Tools tagged with frozenset domain tags (chemistry, analysis, prediction, simulation, training, clinical, nutrition, safety, impact, causal, literature, visualization); investigation control tools are universal (no tags); researcher sees only domain-relevant tools
- **Self-referential research**: `search_prior_research` queries PostgreSQL `tsvector` + GIN index of past findings; indexed on completion; intercepted in orchestrator `_dispatch_tool()` and routed to repository; "ehrlich" source type links to past investigations
- **MCP bridge**: Optional `MCPBridge` connects to external MCP servers (e.g. Excalidraw); tools registered dynamically via `ToolRegistry.register_mcp_tools()`; lifecycle managed by orchestrator; enabled via `EHRLICH_MCP_EXCALIDRAW=true`
- **SSE streaming**: 20 event types for real-time updates; reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- **Phase progress**: `PhaseChanged` event tracks 6 orchestrator phases (Classification & PICO -> Literature Survey -> Formulation -> Hypothesis Testing -> Negative Controls -> Synthesis); frontend renders 6-segment progress bar
- **Citation provenance**: `source_type` + `source_id` on findings, rendered as clickable badges linking to ChEMBL, PDB, DOI, PubChem, UniProt, Open Targets
- **Data configuration**: protein targets via YAML (`data/targets/*.yaml`) + dynamic RCSB PDB discovery; resistance data via YAML (`data/resistance/*.yaml`)
- **Flexible data loading**: ChEMBL queries accept any assay type (MIC, Ki, EC50, etc.), not hardcoded

### UI Patterns

- **Visualization pipeline**: 17 viz tools return `VisualizationPayload` JSON; orchestrator intercepts via `_maybe_viz_event()` and emits `VisualizationRendered` SSE event; `VizRegistry` maps `viz_type` to lazy-loaded React component; `VisualizationPanel` renders all charts
- **LiveLabViewer**: 3Dmol.js scene driven by SSE events -- protein targets load, ligands dock, candidates color by score. SSE event mapping: `dock_against_target` -> ligand in binding pocket, `predict_candidates` -> color by probability, `completed` -> top candidates glow. Interactive rotate/zoom/click, split-pane with Timeline
- **React Flow diagrams**: `@xyflow/react` node graph with custom `InvestigationNode` and `AnnotationNode` types; status-colored nodes (proposed=gray, testing=blue, supported=green, refuted=red, revised=orange); dashed edges for revisions, solid smoothstep for links; read-only with zoom/pan/minimap; lazy-loaded (~188KB chunk)
- **Investigation report**: 8 sections (Research Question, Executive Summary, Hypotheses & Outcomes, Methodology, Key Findings, Candidate Molecules, Model Validation, Cost & Performance); shown post-completion with full audit trail; markdown export via client-side generation
- **Molecule visualization**: server-side 2D SVG (RDKit `rdMolDraw2D`), 3Dmol.js for 3D/docking; `CandidateTable` shows thumbnails with expandable detail (3D viewer + properties + Lipinski badge)
- **Molecule API**: `/molecule/depict` (SVG, cached 24h), `/molecule/conformer`, `/molecule/descriptors`, `/molecule/targets`
- **Investigation templates**: 9 cross-domain prompts (4 molecular + 2 training + 1 nutrition + 2 impact) on home page via `TemplateCards` with domain badges
- **Candidate comparison**: side-by-side scoring view for 2-4 candidates with best-in-group highlighting
- **HypothesisBoard**: kanban-style card grid showing hypothesis status with expandable confidence bars
- **Hypothesis approval**: `HypothesisApprovalCard` renders in main content area (not status bar) for maximum prominence during approval gate
- **Home page**: hero section with stats, collapsible BYOK toggle, SectionHeader-driven sections, empty state for new users
- **Design system**: OKLCH hue 155 (green) brand primary; `rounded-sm` buttons, `rounded-md` cards; `hover:opacity-90` (no glow); Space Grotesk + JetBrains Mono fonts; shared `SectionHeader` component for consistent section headings; VIZ_COLORS aligned to hue 155
- **Layout**: conditional `hideHeader` on AppLayout for investigation/compare pages (own header); consistent `max-w-[1200px]` across all pages
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
| `domain/causal.py` | `ThreatToValidity`, `CausalEstimate`, `CostEffectivenessResult` frozen dataclasses |
| `domain/causal_ports.py` | `DiDEstimatorPort`, `PSMEstimatorPort`, `RDDEstimatorPort`, `SyntheticControlPort` ABCs |
| `domain/evidence_standards.py` | WWC evidence tiers, CONEVAL MIR levels, CREMAA criteria, `classify_evidence_tier()` |
| `application/statistics_service.py` | `StatisticsService` -- scipy.stats hypothesis testing (t-test, Welch, Mann-Whitney, chi-squared, Fisher) |
| `application/causal_service.py` | `CausalService` -- DiD, PSM, RDD, Synthetic Control estimation, threat assessment, cost-effectiveness |
| `infrastructure/chembl_loader.py` | ChEMBL bioactivity loader (flexible assay types) |
| `infrastructure/pubchem_client.py` | PubChem PUG REST compound search |
| `infrastructure/gtopdb_client.py` | GtoPdb REST client for curated pharmacology |
| `infrastructure/did_estimator.py` | DiD estimator: effect size, SE, p-value, parallel trends, automated threat assessment |
| `infrastructure/psm_estimator.py` | Propensity score matching with balance diagnostics |
| `infrastructure/rdd_estimator.py` | Regression discontinuity design (sharp/fuzzy) estimator |
| `infrastructure/synthetic_control_estimator.py` | Synthetic control method for single treated unit |

### prediction/

| File | Purpose |
|------|---------|
| `domain/ports.py` | `FeatureExtractor`, `DataSplitter`, `Clusterer` ABCs (domain-agnostic ML ports) |
| `domain/prediction_result.py` | `PredictionResult` frozen dataclass (generic `identifier: str`) |
| `application/prediction_service.py` | Generic ML service: train, predict, cluster via injected ports |
| `infrastructure/molecular_adapters.py` | `MolecularFeatureExtractor`, `ScaffoldSplitter`, `MolecularClusterer` (RDKit) |
| `infrastructure/generic_adapters.py` | `RandomSplitter`, `DistanceClusterer` (scipy hierarchical) |
| `infrastructure/xgboost_adapter.py` | XGBoost training, prediction, permutation test |
| `tools.py` | 6 prediction tools (3 molecular + 3 generic) |

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

### impact/

| File | Purpose |
|------|---------|
| `tools.py` | 3 impact evaluation tools (economic indicators, benchmarks, program comparison) |
| `domain/entities.py` | DataPoint, Program, Indicator, Benchmark, EconomicSeries, HealthIndicator |
| `domain/repository.py` | EconomicDataRepository, HealthDataRepository, DevelopmentDataRepository ABCs |
| `application/impact_service.py` | ImpactService (economic indicators, benchmarks, program comparison) |
| `infrastructure/worldbank_client.py` | World Bank API v2 client for development indicators |
| `infrastructure/who_client.py` | WHO GHO API client for health statistics |
| `infrastructure/fred_client.py` | FRED API client for US economic time series |

### investigation/

| File | Purpose |
|------|---------|
| `application/multi_orchestrator.py` | Director-Worker-Summarizer orchestrator (main 6-phase loop) |
| `application/diagram_builder.py` | Excalidraw evidence synthesis diagram generation |
| `application/tool_dispatcher.py` | Tool execution dispatcher with caching and special handlers |
| `application/researcher_executor.py` | Single researcher experiment executor with tool loop |
| `application/batch_executor.py` | Parallel batch experiment executor (2 concurrent researchers) |
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
| `domain/domains/impact.py` | `IMPACT_EVALUATION` config |
| `domain/mcp_config.py` | `MCPServerConfig` frozen dataclass |
| `tools_viz.py` | 17 visualization tools |
| `infrastructure/repository.py` | PostgreSQL persistence (asyncpg) + tsvector findings search + user/credit management |
| `infrastructure/anthropic_client.py` | Anthropic API adapter with retry, streaming, and structured outputs |
| `infrastructure/mcp_bridge.py` | MCP client bridge (stdio/SSE/streamable_http) |

## Key Files (API)

All paths relative to `server/src/ehrlich/api/`.

| File | Purpose |
|------|---------|
| `auth.py` | WorkOS JWT middleware (JWKS verification, header + query param auth for SSE) |
| `routes/investigation.py` | REST + SSE endpoints, 84-tool registry, domain registry, MCP bridge, credit system, BYOK |
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
| `features/investigation/components/CompletionSummaryCard.tsx` | Post-completion summary card with expandable cost breakdown |
| `features/investigation/components/NegativeControlPanel.tsx` | Negative control validation table |
| `features/investigation/components/TemplateCards.tsx` | 9 cross-domain research prompt templates |
| `features/investigation/components/ThreatAssessment.tsx` | Validity threat assessment panel with severity badges |
| `features/investigation/components/PromptInput.tsx` | Controlled prompt input with director tier selector pills |
| `features/investigation/components/BYOKSettings.tsx` | API key management for BYOK users |

### Investigation lib + hooks

| File | Purpose |
|------|---------|
| `features/investigation/lib/scene-builder.ts` | SSE events to 3Dmol.js operations |
| `features/investigation/lib/diagram-builder.ts` | Hypotheses/experiments/findings to React Flow nodes + edges |
| `features/investigation/lib/export-markdown.ts` | Client-side markdown report generation |
| `features/investigation/hooks/use-methodology.ts` | React hook for methodology data |
| `features/investigation/hooks/use-credits.ts` | Credit balance hook (TanStack Query) |

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
| `features/visualization/charts/ProgramDashboard.tsx` | Recharts horizontal BarChart with target tracking |
| `features/visualization/charts/GeographicComparison.tsx` | Recharts BarChart with benchmark ReferenceLine |
| `features/visualization/charts/ParallelTrends.tsx` | Recharts ComposedChart for DiD treatment vs control |
| `features/visualization/charts/RDDPlot.tsx` | Visx regression discontinuity scatter with cutoff and fitted curves |
| `features/visualization/charts/CausalDiagram.tsx` | Visx DAG showing treatment, outcome, confounders, mediators |
| `features/visualization/anatomy/BodyDiagram.tsx` | Custom SVG anatomical body diagram |
| `features/visualization/anatomy/body-paths.ts` | SVG path data for front/back views |
| `features/visualization/anatomy/color-scale.ts` | OKLCH intensity color interpolation |

### Shared + routes

| File | Purpose |
|------|---------|
| `shared/hooks/use-auth.ts` | WorkOS auth hook wrapper (AuthKitProvider integration) |
| `shared/lib/api.ts` | Authenticated fetch with BYOK `X-Anthropic-Key` header support |
| `shared/components/ErrorBoundary.tsx` | Error boundary for LiveLabViewer and InvestigationDiagram |
| `shared/components/ui/SectionHeader.tsx` | Shared section header with icon, title, description (border-l-2 accent) |
| `shared/components/ui/Toaster.tsx` | Sonner toast wrapper with dark OKLCH theme |
| `routes/methodology.tsx` | Methodology page |
| `routes/callback.tsx` | WorkOS OAuth callback (waits for auth, then redirects home) |

## Key Files (Web Landing Page)

All paths relative to `web/src/`.

| File | Purpose |
|------|---------|
| `routes/__root.tsx` | Root layout with shellComponent, HeadContent, SEO meta, self-hosted font preloads |
| `routes/index.tsx` | Landing page with lazy-loaded components (React.lazy + Suspense) |
| `components/Nav.tsx` | Fixed navbar with scroll progress bar + mobile menu |
| `components/Footer.tsx` | Minimal footer with links and license |
| `components/SectionHeader.tsx` | Mono label with left border accent |
| `components/Hero.tsx` | Bottom-third hero with MolecularNetwork, stats badges, CTAs |
| `components/MolecularNetwork.tsx` | 3D rotating node graph (Canvas 2D, mouse repulsion, CSS mask edge fade) |
| `components/HowItWorks.tsx` | 6-phase methodology timeline with vertical connecting line |
| `components/ConsolePreview.tsx` | Browser-frame mockups (timeline, hypothesis board, candidates, radar) |
| `components/Architecture.tsx` | Director-Worker-Summarizer model cards, dot grid bg, amber glow |
| `components/Domains.tsx` | 4 domain cards with tool counts, multi-domain callout |
| `components/Visualizations.tsx` | 4 visualization category cards with tech labels |
| `components/DataSources.tsx` | 19 source cards, surface bg with teal glow |
| `components/WhoItsFor.tsx` | 3 persona cards (Student, Academic, Industry) |
| `components/Differentiators.tsx` | 3 differentiator cards with capabilities lists |
| `components/OpenSource.tsx` | Typography-driven section with code snippet + licensing |
| `components/Roadmap.tsx` | Planned domains + platform features (dashed border cards) |
| `components/CTA.tsx` | Pricing tiers, terminal quickstart, primary glow accent |
| `styles/app.css` | Tailwind 4 + OKLCH tokens + @font-face declarations + scroll/stagger/terminal animations |
| `public/fonts/*.woff2` | Self-hosted fonts (6 files: Space Grotesk 400-700, JetBrains Mono 400-500) |
| `lib/constants.ts` | Stats, nav/footer links, domains, data sources, methodology phases |
| `lib/use-reveal.ts` | IntersectionObserver scroll reveal hook |
| `lib/use-scroll-progress.ts` | Scroll progress fraction (0-1) hook |
