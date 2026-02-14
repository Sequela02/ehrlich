# Ehrlich Architecture

## Overview

Ehrlich follows Domain-Driven Design (DDD) with Clean Architecture principles adapted for Python.

## Bounded Contexts

### Kernel
Shared domain primitives used across all contexts: SMILES/InChIKey/MolBlock type aliases, Molecule value object, domain exception hierarchy.

### Shared
Cross-cutting ports (abstract interfaces) and value objects used by multiple bounded contexts. Contains `ChemistryPort` ABC, `Fingerprint`, `MolecularDescriptors`, and `Conformer3D` value objects. No infrastructure dependencies -- pure Python only.

### Literature
Searches and manages scientific references. Integrates with Semantic Scholar API.

### Chemistry
Cheminformatics operations: molecular descriptors, fingerprints, 3D conformer generation, substructure matching, and 2D SVG depiction. All RDKit usage is isolated in the infrastructure adapter (`rdkit_adapter.py`).

### Analysis
Dataset exploration, statistical analysis, and domain-agnostic causal inference. Loads bioactivity data from ChEMBL, compound search via PubChem, curated pharmacology via GtoPdb, substructure enrichment analysis, property distributions. Causal inference methods (DiD, PSM, RDD, Synthetic Control) with threat assessment and cost-effectiveness analysis -- usable by any domain, not just impact evaluation.

### Prediction
Machine learning for activity/outcome prediction. Supports XGBoost models with Morgan fingerprints (all domains) and Chemprop D-MPNN (molecular only). Ensemble predictions combine multiple models.

### Simulation
Simulation and target discovery (Molecular Science domain): descriptor-based binding energy estimation, ADMET prediction, resistance assessment, protein targets (RCSB PDB), protein annotations (UniProt), disease-target associations (Open Targets), environmental toxicity (EPA CompTox).

### Training
Exercise physiology and sports medicine research: evidence-based training analysis, protocol comparison, injury risk assessment, training load monitoring, and clinical trial search (ClinicalTrials.gov). Uses Semantic Scholar for literature search.

### Nutrition
Nutrition science research: supplement evidence analysis, supplement label lookup (NIH DSLD), nutrient data (USDA FoodData), supplement safety monitoring (OpenFDA CAERS), drug interaction screening (RxNav), DRI-based nutrient adequacy assessment, nutrient ratio analysis, and inflammatory index scoring. Uses Semantic Scholar for literature search.

### Impact
Social program evaluation. Provides economic indicator search (World Bank, WHO GHO, FRED), international benchmarking, and cross-program comparison using existing statistical tests. Hypothesis-driven analysis of any program type (education, health, sports, employment, housing) in any country. Full DDD structure with domain entities, repository ABCs, and infrastructure clients for three external APIs. Causal inference methods (DiD, PSM, RDD, Synthetic Control) live in `analysis/` as domain-agnostic tools. Future phases will add Mexico/US-specific data sources. See `docs/impact-evaluation-domain.md` for full design.

### Investigation
Hypothesis-driven agent orchestration. Manages the Claude-driven research loop: literature survey, hypothesis formulation (with predictions, criteria, scope), parallel experiment execution, criteria-based evaluation, negative controls, and synthesis. Uses multi-model architecture (Director/Researcher/Summarizer) with user-guided steering, domain classification, and multi-investigation memory. Supports document upload (CSV/XLSX/PDF) with prompt injection and queryable data via `query_uploaded_data` tool. Includes domain configuration system (`DomainConfig` + `DomainRegistry`) for pluggable scientific domains with tool tagging, score definitions, prompt adaptation, and visualization control. Each domain config includes `tool_examples` in `experiment_examples` with realistic tool chaining patterns for complete tool coverage. Optional MCP bridge (`MCPBridge`) connects to external MCP servers for extensibility (e.g. Excalidraw for visual summaries).

## Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence, synthesizes (3-5 calls)
    │                       NO tool access, structured JSON responses only
    │
    ├── Sonnet 4.5 (Researcher) -- Executes experiments with 85 domain-filtered tools (10-20 calls, parallel x2)
    │                               Tool-calling loop with max_iterations_per_experiment guard
    │
    └── Haiku 4.5 (Summarizer)  -- Compresses large tool outputs >2000 chars, PICO+classification, evidence grading
                                    Reduces context bloat, preserves key scientific data
```

**Cost**: ~$3-4 per investigation (vs ~$11 with all-Opus).

### Flow (Hypothesis-Driven)

1. **Classification & PICO** -- Haiku decomposes prompt into PICO framework (Population, Intervention, Comparison, Outcome) and classifies domain in a single call
2. **Literature Survey** -- Sonnet researcher conducts structured search with domain-filtered tools, citation chasing (snowballing), evidence-level grading; Haiku grades body-of-evidence (GRADE-adapted) and self-assesses quality (AMSTAR-2-adapted)
3. **Hypothesis Formulation** -- Opus Director formulates 2-4 hypotheses with predictions, criteria, scope, Bayesian priors (grounded in Popper, Platt, Feynman, Bayesian frameworks -- see `docs/scientific-methodology.md`); receives structured XML literature context (PICO + graded findings)
4. **User Approval Gate** -- User approves/rejects hypotheses before testing begins (5-min auto-approve timeout)
5. **Experiment Design + Execution** -- Director designs structured experiment protocols (variables, controls, confounders, analysis plan, criteria), 2 Sonnet researchers execute in parallel per batch (max 10 tool calls each) with methodology guidance (sensitivity, applicability domain, uncertainty, verification, negative results)
6. **Hypothesis Evaluation** -- Director compares findings against both hypothesis-level and experiment-level criteria with methodology checks (control validation, confounders, analysis plan adherence)
7. **Controls Validation** -- Score positive/negative controls through trained models; compute Z'-factor assay quality, permutation significance, scaffold-split vs random-split comparison
8. **Synthesis** -- Director synthesizes final report with ranked candidates, citations, validation metrics, cost breakdown

## Persistence

Investigations are persisted to PostgreSQL via `asyncpg` connection pooling. The `InvestigationRepository` implements the `InvestigationRepository` ABC defined in the domain layer. Hypotheses, experiments, findings, candidates, negative controls, citations, domain, and cost data are stored in `JSONB` columns in the `investigations` table. All SSE events are persisted to a separate `events` table for full timeline replay on page reload.

Additional tables: `users` (WorkOS identity, credit balance, encrypted API key), `credit_transactions` (audit trail for credit purchases/spending/refunds). Full-text search uses PostgreSQL `tsvector` + GIN index.

The API keeps `_active_investigations` and `_active_orchestrators` dicts for in-flight SSE streaming and user-guided steering (hypothesis approval). Persists to PostgreSQL on completion (or error).

## Authentication & Credits

### WorkOS JWT Authentication

User identity is managed via WorkOS AuthKit (1M MAU free tier). The backend verifies JWTs against WorkOS JWKS endpoints (`api/auth.py`). Three dependency functions support different auth patterns:

- `get_current_user` -- extracts JWT from `Authorization: Bearer <token>` header (standard REST endpoints)
- `get_current_user_sse` -- supports both header auth and `?token=<jwt>` query parameter (EventSource API does not support custom headers)
- `get_optional_user` -- returns user dict or `None` for public endpoints

The frontend wraps the app in `<AuthKitProvider>` from `@workos-inc/authkit-react`. Authenticated fetch is handled via `shared/lib/api.ts`.

### Credit System

Investigations consume credits based on the director model tier:

| Tier | Director Model | Credits |
|------|---------------|---------|
| haiku | Haiku 4.5 | 1 |
| sonnet | Sonnet 4.5 | 3 |
| opus | Opus 4.6 | 5 |

Researcher is always Sonnet 4.5 and Summarizer is always Haiku 4.5, regardless of tier. Credits are deducted on investigation start (not completion) to prevent abuse. Credits are refunded on investigation failure. The `credit_transactions` table provides a full audit trail.

### BYOK (Bring Your Own Key)

Users can provide their own Anthropic API key via the `X-Anthropic-Key` HTTP header. BYOK users bypass the credit system entirely -- they pay Anthropic directly. The API key is forwarded to `AnthropicClientAdapter` for that investigation's API calls.

## Multi-Domain Investigations

Cross-domain research questions (e.g., "How does creatine supplementation affect muscle protein synthesis at the molecular level?") trigger multi-domain detection. `DomainRegistry.detect()` returns `list[DomainConfig]` -- one per matched domain. `merge_domain_configs()` creates a synthetic merged config with the union of tool_tags, concatenated score_definitions, joined prompt examples, and deduplicated attribute_keys/hypothesis_types. The merged config carries `source_configs` for frontend sub-domain display.

The Haiku classifier outputs a JSON array of domain categories. Tool filtering uses the merged config's union of tags. The Director receives merged prompt examples from all relevant domains.

**What stays the same:** The 6-phase pipeline, hypothesis loop, evaluation framework, and event system are domain-agnostic. Only the detection layer and tool/prompt filtering changed.

## Self-Referential Research

Ehrlich queries its own past investigation findings during new research. The `search_prior_research` tool (available during Phase 2 Literature Survey) queries a PostgreSQL `tsvector` column with GIN index on the `investigations` table, indexing finding titles, details, evidence types, hypothesis statements/statuses, and source provenance.

The tool is intercepted by `ToolDispatcher.dispatch()` in `tool_dispatcher.py` and routed to `InvestigationRepository.search_findings()`, which performs ranked full-text search with prompt context.

Findings from past investigations carry provenance `source_type: "ehrlich"`, `source_id: "{investigation_id}"`. Frontend renders Ehrlich-branded source badges linking to past investigations (internal navigation, no external tab).

## Molecule Visualization

Ehrlich uses a hybrid approach for molecule rendering:

- **2D Depiction**: Server-side SVG via RDKit `rdMolDraw2D`. The `/api/v1/molecule/depict` endpoint returns `image/svg+xml` with 24h browser caching. The console uses `<img>` tags -- zero frontend complexity, browser handles caching.
- **3D Viewing**: Client-side 3Dmol.js (~2MB, MIT license) loaded via dynamic import for code splitting. Used for both `MolViewer3D` (conformer stick models) and `DockingViewer` (protein cartoon + ligand stick overlay).
- **Candidate Detail**: Expandable panel in `CandidateTable` fetches conformer + descriptors in parallel, displays 2D/3D views alongside a property card with Lipinski badge.

### Molecule API

| Endpoint | Returns | Cache |
|----------|---------|-------|
| `GET /molecule/depict?smiles=&w=&h=` | SVG (`image/svg+xml`) | 24h `Cache-Control` |
| `GET /molecule/conformer?smiles=` | JSON `{mol_block, energy, num_atoms}` | None |
| `GET /molecule/descriptors?smiles=` | JSON descriptors + `passes_lipinski` | None |
| `GET /targets` | JSON list of `{pdb_id, name, organism}` | None |

Invalid SMILES on `/depict` returns a dark error SVG (200 status). Invalid SMILES on `/conformer` or `/descriptors` returns 400.

## Domain-Specific Visualization

17 visualization tools produce structured `VisualizationPayload` JSON (viz_type, title, data, config, domain). Viz tool results are intercepted by `maybe_viz_event()` in `researcher_executor.py`, which emits a `VisualizationRendered` SSE event. On the frontend, `VizRegistry` maps each `viz_type` to a lazy-loaded React component rendered in the `VisualizationPanel` grid.

| Tool | Chart Library | Purpose |
|------|--------------|---------|
| `render_binding_scatter` | Recharts ScatterChart | Compound binding affinities |
| `render_admet_radar` | Recharts RadarChart | ADMET/drug-likeness profiles |
| `render_training_timeline` | Recharts ComposedChart | Training load with ACWR danger zones |
| `render_muscle_heatmap` | Custom SVG | Anatomical body diagram with activation/risk |
| `render_forest_plot` | Visx | Meta-analysis forest plot |
| `render_evidence_matrix` | Visx HeatmapRect | Hypothesis-by-evidence heatmap |
| `render_performance_chart` | Recharts ComposedChart | Banister fitness-fatigue model curves |
| `render_funnel_plot` | Visx | Publication bias funnel plot |
| `render_dose_response` | Visx | Dose-response curve with confidence band |
| `render_nutrient_comparison` | Recharts BarChart | Grouped nutrient profile comparison |
| `render_nutrient_adequacy` | Recharts BarChart | DRI adequacy assessment with MAR score |
| `render_therapeutic_window` | Visx | Therapeutic window with EAR/RDA/AI/UL zones |
| `render_program_dashboard` | Recharts BarChart | Multi-indicator KPI dashboard with target tracking |
| `render_geographic_comparison` | Recharts BarChart | Region comparison with benchmark reference line |
| `render_parallel_trends` | Recharts ComposedChart | DiD parallel trends (treatment vs control) |
| `render_rdd_plot` | Visx | Regression discontinuity scatter with cutoff |
| `render_causal_diagram` | Visx | DAG showing treatment, outcome, confounders |

Chart theming uses OKLCH color tokens consistent with the application's visual identity.

## Visual Identity — "Lab Protocol"

Dark-only theme mixing Industrial Scientific + Editorial Academic + Cyberpunk Lab aesthetics.

### Design Tokens (OKLCH)

| Token | Value | Purpose |
|-------|-------|---------|
| background | `oklch(0.10 0.005 155)` | Deep black with green micro-tint |
| surface | `oklch(0.14 0.008 155)` | Raised cards, panels |
| foreground | `oklch(0.93 0.005 155)` | Primary text |
| primary | `oklch(0.72 0.19 155)` | Molecular Green — CTAs, active states |
| secondary | `oklch(0.60 0.10 200)` | Teal — completed states |
| accent | `oklch(0.75 0.15 80)` | Amber — director events |
| muted | `oklch(0.18 0.005 155)` | Muted backgrounds |
| muted-foreground | `oklch(0.60 0.01 155)` | Secondary text (WCAG AA compliant) |
| border | `oklch(0.22 0.01 155)` | Subtle borders |
| destructive | `oklch(0.60 0.22 25)` | Error red |

### Typography

- **Display/Body**: Space Grotesk (400, 500, 600, 700) — geometric, scientific
- **Data/Code/Labels**: JetBrains Mono (400, 500) — SMILES, costs, tool names, IDs
- Labels use monospace uppercase with wide tracking (0.08em)

### Signature Elements

1. **Molecular bond phase progress** — Nodes connected by lines (not bars). Active node pulses green.
2. **Terminal-style timeline** — Monospace tool names, green-tinted findings, amber director events.
3. **Section headers** — Monospace uppercase with left green border accent (`border-l-2 border-primary`).
4. **Green glow pulse** — Running states emit soft green `box-shadow` animation.

### Anti-Patterns (Deliberately Avoided)

- No purple/indigo — molecular green is the identity color
- No Inter/Roboto — Space Grotesk for display, JetBrains Mono for data
- No light mode — dark-only, scientific instrument aesthetic
- No centered hero — left-aligned, utilitarian layout
- No blur shadows — hard borders or glow effects only
- No animated particle backgrounds — static CSS patterns only (dot grid, radial accents)

## Landing Site (`web/`)

Separate TanStack Start project for the public-facing landing page. SSR/SSG for SEO via Nitro server, same React + TypeScript + Bun toolchain as console. Shares design tokens (OKLCH Lab Protocol identity, self-hosted Space Grotesk + JetBrains Mono fonts) but no code dependencies on console -- each project builds independently.

**Performance optimizations (Lighthouse 95+):** Self-hosted WOFF2 fonts (6 files, 76KB total) eliminate render-blocking external requests. Below-fold components lazy loaded via React.lazy() + Suspense boundaries (11 components split into 2-11KB chunks). Zero unused dependencies. Chunk size warnings at 300KB prevent regressions.

- **Console** (`console/`): authenticated SPA for running investigations (TanStack Router, client-side only)
- **Web** (`web/`): public landing page with SSR/SSG for SEO (TanStack Start + Nitro, server-rendered)

16 component files: Nav (scroll progress, eager), Hero (MolecularNetwork 3D canvas, eager), HowItWorks (6-phase timeline, lazy), ConsolePreview (browser-frame mockups, lazy), Architecture (model cards + dot grid bg + amber glow, lazy), Domains (4 domain cards, lazy), Visualizations (4 category cards, lazy), DataSources (19 source cards + teal glow, lazy), WhoItsFor (3 persona cards, lazy), Differentiators (3 cards, lazy), OpenSource (code snippet + licensing, lazy), Roadmap (planned domains/features, lazy), CTA (pricing tiers + terminal quickstart + primary glow, lazy), SectionHeader, Footer (lazy), MolecularNetwork. All use OKLCH tokens, Motion scroll animations, and staggered children reveals. Section zoning via alternating `bg-surface/30` backgrounds and strategic radial accent glows (amber on Architecture, teal on DataSources, primary on CTA).

Both deploy independently: console to app server, web to CDN/static hosting.

## Dependency Rules

```
domain/ -> ZERO external deps (pure Python)
shared/ -> cross-cutting ports and value objects (pure Python)
application/ -> domain/ and shared/ interfaces only
infrastructure/ -> implements domain/ ABCs
tools.py -> calls application/ services
api/ -> investigation/application/ only
```

## Data Flow

### Multi-Model (Default)

1. User submits research prompt via Console (or selects a template), optionally with uploaded files (CSV/XLSX/PDF via `POST /upload`)
2. API creates Investigation, links any uploaded files, persists to PostgreSQL, starts MultiModelOrchestrator (with uploaded data context injected into prompts)
3. **Haiku** decomposes prompt via PICO framework (Population, Intervention, Comparison, Outcome) and classifies domain in a single call; queries past completed investigations in same domain
4. **Domain detection** -- `DomainRegistry.detect()` returns `list[DomainConfig]` (one or more); `merge_domain_configs()` creates merged config for cross-domain; emits `DomainDetected` SSE event with display config (includes `domains` sub-list for multi-domain); researcher tool list filtered to merged domain-relevant tools
5. **Researcher** (Sonnet) conducts structured literature survey with domain-filtered tools, citation chasing, evidence-level grading; **Haiku** grades body-of-evidence (GRADE-adapted) and self-assesses quality (AMSTAR-2); emits `LiteratureSurveyCompleted` event
6. **Director** (Opus) formulates 2-4 hypotheses with predictions, criteria, scope, Bayesian priors; receives structured XML literature context (PICO + graded findings)
7. **User Approval Gate** -- user approves/rejects hypotheses (5-min timeout auto-approves)
8. For each batch of 2 hypotheses:
   a. **Director** designs experiment protocol (description, tool plan, variables, controls, confounders, analysis plan, criteria, optional statistical test plan)
   b. **2 Researchers** (Sonnet) execute in parallel via asyncio.Queue
   c. **Summarizer** (Haiku) compresses outputs exceeding threshold
   d. **Director** evaluates hypothesis against pre-defined success/failure criteria
   e. If revised: new hypothesis spawned with parent link
9. **Negative controls** recorded from formulation suggestions
10. **Director** synthesizes final report with candidates, citations, cost
11. All events stream via SSE (20 event types) to Console in real-time
    - `DomainDetected` sends display config (score columns, visualization type) to frontend
    - `FindingRecorded` includes evidence + source provenance (source_type, source_id) + evidence_level (1-6)
    - `LiteratureSurveyCompleted` carries PICO, search stats, evidence grade, self-assessment
    - `PhaseChanged` tracks 6-step progress
    - `CostUpdate` streams progressive cost snapshots
    - `HypothesisApprovalRequested` pauses for user steering
    - `ValidationMetricsComputed` carries Z'-factor, quality, control separation stats
    - `InvestigationCompleted` includes candidates, hypotheses, findings, negative controls, validation metrics
12. Investigation persisted to PostgreSQL with full state + events for timeline replay
13. Console displays: phase indicator, hypothesis board, lab view (3Dmol.js, molecular domain only), investigation diagram (React Flow), domain-specific visualizations (charts, diagrams), findings with source badges, dynamic candidate table with domain-specific score columns, structured 8-section report with markdown export
