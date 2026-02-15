# Ehrlich - AI Scientific Discovery Engine

AGPL-3.0 | Claude Code Hackathon (Feb 10-16, 2026)

Domain-agnostic scientific discovery platform using Claude as a hypothesis-driven reasoning engine. Pluggable `DomainConfig` + `DomainRegistry` system. Four domains: Molecular Science, Training Science, Nutrition Science, Impact Evaluation.

See `README.md` for setup, tools catalog (90 tools), data sources (24 APIs), API endpoints, and demo instructions.

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun) + `web/` (TanStack Start landing page).

### Multi-Model (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 90 tools (parallel: 2 experiments per batch)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars), PICO decomposition, evidence grading
```

Always uses `MultiModelOrchestrator`. Hypotheses tested in parallel batches of 2.

### Bounded Contexts (11)

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| shared | `server/src/ehrlich/shared/` | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D) |
| literature | `server/src/ehrlich/literature/` | Paper search (Semantic Scholar), references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration (ChEMBL, PubChem, GtoPdb), causal inference (DiD, PSM, RDD, SC) |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance, targets (RCSB PDB, UniProt, Open Targets), toxicity (EPA CompTox) |
| training | `server/src/ehrlich/training/` | Evidence analysis, protocol comparison, injury risk, clinical trials, PubMed, exercises |
| nutrition | `server/src/ehrlich/nutrition/` | Supplement evidence, labels, nutrients, safety, interactions, adequacy, inflammatory index |
| impact | `server/src/ehrlich/impact/` | Economic indicators (World Bank, WHO GHO, FRED, Census, BLS), health (CDC WONDER), spending (USAspending), education (College Scorecard), housing (HUD), open data (data.gov) |
| investigation | `server/src/ehrlich/investigation/` | Multi-model orchestration + PostgreSQL persistence + domain registry + MCP bridge |

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
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
uv run pytest --cov=ehrlich --cov-report=term-missing    # Tests
uv run ruff check src/ tests/                            # Lint
uv run ruff format src/ tests/                           # Format
uv run mypy src/ehrlich/                                 # Type check
```

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
bun run dev          # Dev server :3000
bun run build        # vite build (generates .output/)
bun run typecheck    # tsc --noEmit
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

## Key Patterns

### Scientific Methodology

- **Hypothesis-driven investigation loop**: formulate -> design experiment -> execute tools -> evaluate -> tree action (deepen/branch/prune) -> synthesize. See `docs/scientific-methodology.md`
- **Tree search**: `TreeManager` scores hypotheses (`prior_confidence * depth_discount * evidence_bonus`), selects top 2 for testing, processes Director's tree action (deepen=child at depth+1, branch=sibling at same depth, prune=REJECTED). `max_depth=3` prevents infinite recursion
- **Hypothesis model**: Popper + Platt + Feynman + Bayesian updating. Fields: prediction, null_prediction, success/failure_criteria, scope, hypothesis_type, prior_confidence, certainty_of_evidence. Evaluation: 8-tier evidence hierarchy, effect sizes, Bayesian updating, convergence checks
- **Experiment protocols**: Fisher/Platt/Cohen/Saltelli/OECD/Tropsha. Fields: independent/dependent_variable, controls, confounders, analysis_plan, success/failure_criteria. Director designs with 5 principles (VARIABLES, CONTROLS, CONFOUNDERS, ANALYSIS PLAN, SENSITIVITY)
- **Statistical testing**: Director plans tests in `statistical_test_plan`; Researcher executes `run_statistical_test`/`run_categorical_test`; findings recorded with evidence_type based on significance
- **Controls**: negative controls (known-inactive compounds), positive controls (correctly_classified >= 0.5)
- **Validation**: Z'-factor assay quality, permutation significance (Y-scrambling), scaffold-split vs random-split
- **Literature survey**: PICO decomposition + domain classification (Haiku); citation chasing; GRADE-adapted grading; AMSTAR-2 self-assessment
- **User-guided steering**: `HypothesisApprovalRequested` pauses orchestrator; user approves/rejects via `POST /investigate/{id}/approve`; 5-min auto-approve timeout
- **Synthesis**: GRADE certainty grading, priority tiers (1-4), structured limitations, knowledge gap analysis

### System Patterns

- Each bounded context: `domain/`, `application/`, `infrastructure/`, `tools.py`
- Domain entities: `@dataclass` with `__post_init__` validation; repositories: ABCs in `domain/repository.py`
- `tools.py` is the boundary between Claude and application services
- **Parallel researchers**: `run_experiment_batch()` uses `asyncio.Queue` for 2 concurrent experiments; three-layer differentiation prevents duplicates
- **Tree manager**: `TreeManager` in `application/tree_manager.py`; `select_next()` picks batch, `apply_evaluation()` processes Director action, `compute_branch_score()` scores hypotheses
- **Context compaction**: `_build_prior_context()` compresses completed hypotheses for Director
- **Prompt engineering**: XML-tagged instructions, multishot examples (2 per Director prompt), tool usage examples for Researcher
- **ToolCache**: in-memory TTL cache (deterministic: forever, API: 24h-7d)
- **Event persistence**: PostgreSQL `events` table; completed investigations replay full timeline
- **Structured outputs**: Director uses `output_config` with 6 JSON schemas (`domain/schemas.py`)
- **Director streaming**: `_director_call()` async generator with `stream_message()`; Researcher/Summarizer non-streaming
- External API clients: `httpx.AsyncClient`, retry with exponential backoff
- **Auth**: WorkOS JWT middleware; JWKS verification; header + query param auth for SSE
- **Credits**: director tier (haiku=1, sonnet=3, opus=5); deducted on start, refunded on failure
- **BYOK**: `X-Anthropic-Key` header pass-through; bypasses credits
- **Document upload**: CSV/XLSX/PDF via `POST /upload`; `FileProcessor` -> `UploadedFile`; injected as `<uploaded_data>` XML

### Integration Patterns

- **Domain config**: `DomainConfig` with tool_tags, score_definitions, prompt examples; `DomainRegistry` auto-detects; `DomainDetected` SSE event
- **Multi-domain**: `merge_domain_configs()` creates synthetic config from multiple domains
- **Tool tagging**: frozenset domain tags; investigation tools are universal; researcher sees only domain-relevant tools
- **Self-referential**: `search_prior_research` queries PostgreSQL tsvector + GIN index
- **MCP bridge**: Optional external MCP servers; dynamic tool registration; `EHRLICH_MCP_EXCALIDRAW=true`
- **SSE**: 21 event types; reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- **Phase progress**: 6 phases (Classification & PICO -> Literature Survey -> Formulation -> Hypothesis Testing -> Negative Controls -> Synthesis)
- **Citation provenance**: `source_type` + `source_id` on findings (ChEMBL, PDB, DOI, PubChem, UniProt, Open Targets)

### UI Patterns

- **Viz pipeline**: 17 viz tools -> `VisualizationPayload` -> `VisualizationRendered` SSE -> `VizRegistry` lazy-loads React component
- **LiveLabViewer**: 3Dmol.js SSE-driven scene (protein load, ligand dock, candidate score coloring)
- **React Flow**: `@xyflow/react` with custom node types; status-colored (proposed=gray, testing=blue, supported=green, refuted=red, revised=amber, rejected=dimmed gray); tree depth + parent-child revision edges
- **Design system**: OKLCH hue 155 (green); `rounded-sm` buttons, `rounded-md` cards; Space Grotesk + JetBrains Mono
- **Layout**: conditional `hideHeader` for investigation/compare pages; `max-w-[1200px]`
- TanStack Router file-based routing; `ErrorBoundary` wraps LiveLabViewer and InvestigationDiagram

## Key Files (Server)

All paths relative to `server/src/ehrlich/`.

| File | Purpose |
|------|---------|
| `shared/chemistry_port.py` | `ChemistryPort` ABC |
| `chemistry/infrastructure/rdkit_adapter.py` | RDKit adapter (only RDKit import point) |
| `analysis/application/causal_service.py` | DiD, PSM, RDD, Synthetic Control, threat assessment, cost-effectiveness |
| `analysis/domain/causal_ports.py` | Causal estimator port ABCs |
| `analysis/domain/evidence_standards.py` | WWC tiers, CONEVAL MIR, CREMAA criteria |
| `prediction/application/prediction_service.py` | Generic ML: train, predict, cluster via injected ports |
| `prediction/domain/ports.py` | `FeatureExtractor`, `DataSplitter`, `Clusterer` ABCs |
| `training/application/training_service.py` | Evidence, protocols, injury risk, metrics, clinical trials, PubMed, exercises |
| `nutrition/application/nutrition_service.py` | Supplements, labels, nutrients, safety, adequacy, interactions, ratios |
| `nutrition/domain/dri.py` | DRI tables (EAR, RDA, AI, UL by age/sex) |
| `impact/application/impact_service.py` | Economic indicators, benchmarks, program comparison, spending, education, housing, open data |
| `investigation/application/multi_orchestrator.py` | Director-Worker-Summarizer orchestrator (main 6-phase loop) |
| `investigation/application/tool_dispatcher.py` | Tool execution with caching, `search_prior_research` and `query_uploaded_data` interception |
| `investigation/application/tree_manager.py` | Hypothesis tree exploration: scoring, selection, deepen/branch/prune actions |
| `investigation/application/researcher_executor.py` | Single researcher experiment executor |
| `investigation/application/batch_executor.py` | Parallel batch executor (2 concurrent) |
| `investigation/application/paper_generator.py` | Scientific paper generation from investigation data + events |
| `investigation/application/prompts.py` | All domain-adaptive prompts |
| `investigation/domain/schemas.py` | 6 JSON schemas for structured outputs |
| `investigation/domain/domain_config.py` | `DomainConfig` + `ScoreDefinition` + `merge_domain_configs()` |
| `investigation/domain/domain_registry.py` | `DomainRegistry` (register, multi-detect, lookup) |
| `investigation/domain/domains/*.py` | Per-domain configs (molecular, training, nutrition, impact) |
| `investigation/infrastructure/repository.py` | PostgreSQL persistence + tsvector search + credits + uploads |
| `investigation/infrastructure/anthropic_client.py` | Anthropic API adapter (retry, streaming, structured outputs) |

## Key Files (API)

All paths relative to `server/src/ehrlich/api/`.

| File | Purpose |
|------|---------|
| `auth.py` | WorkOS JWT middleware (JWKS, header + query param) |
| `routes/investigation.py` | REST + SSE + paper export, 90-tool registry, domain registry, credits, BYOK |
| `routes/upload.py` | File upload (CSV/XLSX/PDF) |
| `routes/molecule.py` | Molecule depiction, conformer, descriptors, targets |
| `sse.py` | Domain event to SSE conversion (21 types) |

## Key Files (Console)

All paths relative to `console/src/`.

| File | Purpose |
|------|---------|
| `features/investigation/components/LiveLabViewer.tsx` | 3Dmol.js SSE-driven molecular scene |
| `features/investigation/components/InvestigationDiagram.tsx` | Lazy-loaded React Flow wrapper |
| `features/investigation/components/InvestigationReport.tsx` | 8-section structured report |
| `features/investigation/components/CandidateTable.tsx` | Thumbnail grid with expandable rows |
| `features/investigation/components/HypothesisBoard.tsx` | Kanban hypothesis status grid |
| `features/investigation/components/HypothesisApprovalCard.tsx` | Approve/reject before testing |
| `features/investigation/components/PromptInput.tsx` | Prompt input with director tier selector + file upload |
| `features/investigation/components/ThreatAssessment.tsx` | Validity threat panel with severity badges |
| `features/investigation/components/FileUpload.tsx` | Drag-and-drop upload (CSV/XLSX/PDF) |
| `features/investigation/lib/scene-builder.ts` | SSE events to 3Dmol.js operations |
| `features/investigation/lib/diagram-builder.ts` | Hypotheses/experiments/findings to React Flow nodes |
| `features/visualization/VizRegistry.tsx` | Lazy-loaded chart component registry |
| `features/visualization/VisualizationPanel.tsx` | Grid layout for multiple charts |
| `features/visualization/theme.ts` | OKLCH color tokens |
| `routes/paper.$id.tsx` | Print-optimized paper view with PDF export |
| `styles/print.css` | `@media print` stylesheet for PDF export |
| `shared/hooks/use-auth.ts` | WorkOS auth wrapper |
| `shared/lib/api.ts` | Authenticated fetch with BYOK support |

## Key Files (Web Landing Page)

All paths relative to `web/src/`.

| File | Purpose |
|------|---------|
| `routes/__root.tsx` | Root layout, SEO meta, self-hosted font preloads |
| `routes/index.tsx` | Landing page with lazy-loaded sections |
| `components/Hero.tsx` | Hero with MolecularNetwork, stats, CTAs |
| `components/MolecularNetwork.tsx` | 3D rotating node graph (Canvas 2D) |
| `styles/app.css` | Tailwind 4 + OKLCH tokens + animations |
| `lib/constants.ts` | Stats, links, domains, data sources |
