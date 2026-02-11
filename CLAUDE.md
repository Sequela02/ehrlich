# Ehrlich - AI Molecular Discovery Engine

## Project Overview

Ehrlich is a domain-agnostic molecular discovery platform built for the Claude Code Hackathon (Feb 10-16, 2026). It uses Claude as a hypothesis-driven scientific reasoning engine with cheminformatics, ML, molecular simulation, and multi-source data tools. Named after Paul Ehrlich, the father of the "magic bullet" concept -- finding the right molecule for any target.

Ehrlich handles any molecular science question: antimicrobial resistance, Alzheimer's drug candidates, environmental toxicity, agricultural biocontrol, and beyond. The hypothesis-driven engine is domain-agnostic; the data sources make it universal.

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 27 tools
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars)
```

Falls back to single-model `Orchestrator` when `director_model == researcher_model`.

### Bounded Contexts

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| literature | `server/src/ehrlich/literature/` | Paper search (Semantic Scholar), references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration (ChEMBL, PubChem), enrichment |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance, target discovery (RCSB PDB), toxicity (EPA CompTox) |
| investigation | `server/src/ehrlich/investigation/` | Multi-model agent orchestration + SQLite persistence |

### External Data Sources

| Source | API | Purpose | Auth |
|--------|-----|---------|------|
| ChEMBL | `https://www.ebi.ac.uk/chembl/api/data` | Bioactivity data (any assay type: MIC, IC50, Ki, EC50, Kd) | None |
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1` | Scientific paper search | None |
| RCSB PDB | `https://search.rcsb.org` + `https://data.rcsb.org` | Dynamic protein target discovery by organism/function | None |
| PubChem | `https://pubchem.ncbi.nlm.nih.gov/rest/pug` | Compound search by target/activity/similarity | None |
| EPA CompTox | `https://api-ccte.epa.gov` | Environmental toxicity, bioaccumulation, fate (1M+ chemicals) | Free API key |

### Dependency Rules (STRICT)

1. `domain/` has ZERO external deps -- pure Python only (dataclasses, ABC, typing)
2. `application/` depends on `domain/` interfaces, never on `infrastructure/`
3. `infrastructure/` implements `domain/` repository interfaces
4. `tools.py` calls `application/` services, returns JSON for Claude
5. No cross-context domain imports -- communicate via `kernel/` primitives
6. RDKit imports ONLY in `chemistry/infrastructure/rdkit_adapter.py`
7. External API clients live in `infrastructure/` of their bounded context

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

Scopes: kernel, literature, chemistry, analysis, prediction, simulation, investigation, api, console, mol, data, ci, docs, infra

## Tools (27 Total)

### Chemistry (6) -- RDKit cheminformatics, domain-agnostic
- `validate_smiles` -- Validate SMILES string
- `compute_descriptors` -- MW, LogP, TPSA, HBD, HBA, QED, rings
- `compute_fingerprint` -- Morgan (2048-bit) or MACCS (166-bit)
- `tanimoto_similarity` -- Similarity between two molecules
- `generate_3d` -- 3D conformer with MMFF94 optimization
- `substructure_match` -- SMARTS/SMILES substructure search

### Literature (2) -- Semantic Scholar
- `search_literature` -- Paper search (title, authors, year, DOI, abstract, citations)
- `get_reference` -- Curated reference lookup by key or DOI

### Analysis (5) -- ChEMBL + PubChem
- `explore_dataset` -- Load ChEMBL bioactivity data for any organism/target
- `search_bioactivity` -- Flexible ChEMBL query (any assay type: MIC, Ki, EC50, IC50, Kd)
- `search_compounds` -- PubChem compound search by target/activity/similarity
- `analyze_substructures` -- Chi-squared enrichment of SMARTS patterns
- `compute_properties` -- Property distributions (active vs inactive)

### Prediction (3) -- XGBoost, Chemprop
- `train_model` -- Train ML model on any SMILES+activity dataset
- `predict_candidates` -- Score compounds with trained model
- `cluster_compounds` -- Butina structural clustering

### Simulation (5) -- Docking, ADMET, targets, toxicity
- `search_protein_targets` -- RCSB PDB search by organism/function/keyword
- `dock_against_target` -- AutoDock Vina docking (or RDKit fallback)
- `predict_admet` -- Drug-likeness profiling (absorption, metabolism, toxicity)
- `fetch_toxicity_profile` -- EPA CompTox environmental toxicity data
- `assess_resistance` -- Knowledge-based resistance mutation scoring

### Investigation (6) -- Hypothesis lifecycle
- `propose_hypothesis` -- Register testable hypothesis
- `design_experiment` -- Plan experiment with tool sequence
- `evaluate_hypothesis` -- Assess outcome (supported/refuted/revised)
- `record_finding` -- Record finding linked to hypothesis + evidence_type
- `record_negative_control` -- Validate model with known-inactive compounds
- `conclude_investigation` -- Final summary with ranked candidates

## Key Patterns

- Each bounded context has: `domain/`, `application/`, `infrastructure/`, `tools.py`
- Domain entities use `@dataclass` with `__post_init__` validation
- Repository interfaces are ABCs in `domain/repository.py`
- Infrastructure adapters implement repository ABCs
- Tool functions in `tools.py` are the boundary between Claude and application services
- **Hypothesis-driven investigation loop**: formulate hypotheses, design experiments, execute tools, evaluate evidence, revise/reject, synthesize
- **Domain-agnostic prompts**: Director infers domain from user's research question, adapts scientific context
- **Evidence-linked findings**: every finding references a `hypothesis_id` + `evidence_type` (supporting/contradicting/neutral)
- **Negative controls**: validate model predictions with known-inactive compounds (`NegativeControl` entity)
- **Dynamic target discovery**: RCSB PDB Search API finds protein targets for any organism/disease
- **Flexible data loading**: ChEMBL queries accept any assay type (MIC, Ki, EC50, etc.), not hardcoded
- **Protein targets**: YAML-configured (`data/targets/*.yaml`) + dynamic RCSB PDB discovery
- **Resistance data**: YAML-configured (`data/resistance/*.yaml`), extensible per domain
- 6 control tools: `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_finding`, `record_negative_control`, `conclude_investigation`
- SSE streaming for real-time investigation updates (12 event types)
- **Event persistence**: all SSE events stored in SQLite `events` table; completed investigations replay full timeline on page reload
- TanStack Router file-based routing in console
- `MultiModelOrchestrator`: hypothesis-driven loop (formulate -> design -> execute -> evaluate per hypothesis)
- `Orchestrator` is the single-model fallback (used when all models are the same)
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
- **Live Lab Viewer**: 3Dmol.js scene that updates in real-time from SSE events -- protein targets load, ligands dock, candidates color by score
- `LiveLabViewer` subscribes to SSE stream, renders molecular scene: protein cartoon + ligand sticks + score labels
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
| `investigation/application/orchestrator.py` | Single-model agentic loop with hypothesis control tool dispatch |
| `investigation/application/multi_orchestrator.py` | Hypothesis-driven Director-Worker-Summarizer orchestrator |
| `investigation/application/cost_tracker.py` | Per-model cost tracking with tiered pricing |
| `investigation/application/prompts.py` | Domain-adaptive prompts: scientist, director (4 phases), researcher, summarizer |
| `investigation/domain/hypothesis.py` | Hypothesis entity + HypothesisStatus enum |
| `investigation/domain/experiment.py` | Experiment entity + ExperimentStatus enum |
| `investigation/domain/negative_control.py` | NegativeControl frozen dataclass |
| `investigation/domain/events.py` | 12 domain events (Hypothesis*, Experiment*, NegativeControl*, Finding, Tool*, Thinking, Completed, Error) |
| `investigation/domain/repository.py` | InvestigationRepository ABC (save_event, get_events for audit trail) |
| `investigation/infrastructure/sqlite_repository.py` | SQLite implementation with hypothesis/experiment/negative_control/event serialization |
| `investigation/infrastructure/anthropic_client.py` | Anthropic API adapter with retry |
| `api/routes/investigation.py` | REST + SSE endpoints, 27-tool registry, auto-selects orchestrator |
| `api/routes/molecule.py` | Molecule depiction, conformer, descriptors, targets endpoints |
| `api/sse.py` | Domain event to SSE conversion (12 types) |

## Key Files (Data Source Clients)

| File | Purpose |
|------|---------|
| `analysis/infrastructure/chembl_loader.py` | ChEMBL bioactivity loader (flexible assay types) |
| `analysis/infrastructure/pubchem_client.py` | PubChem PUG REST compound search |
| `simulation/infrastructure/rcsb_client.py` | RCSB PDB Search + Data API for target discovery |
| `simulation/infrastructure/comptox_client.py` | EPA CompTox CTX API for environmental toxicity |
| `simulation/infrastructure/protein_store.py` | YAML-based protein target store + RCSB PDB fallback |
| `literature/infrastructure/semantic_scholar_client.py` | Semantic Scholar paper search with retry |

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
