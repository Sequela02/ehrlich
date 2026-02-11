# Ehrlich - AI Antimicrobial Discovery Agent

## Project Overview

Ehrlich is an AI-powered antimicrobial discovery agent built for the Claude Code Hackathon (Feb 10-16, 2026). It uses Claude as a scientific reasoning engine with cheminformatics, ML, and molecular simulation tools.

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Formulates hypotheses, designs experiments, evaluates evidence, synthesizes (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 23 tools
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs (>2000 chars)
```

Falls back to single-model `Orchestrator` when `director_model == researcher_model`.

### Bounded Contexts

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| literature | `server/src/ehrlich/literature/` | Paper search, references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration, enrichment |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance |
| investigation | `server/src/ehrlich/investigation/` | Multi-model agent orchestration + SQLite persistence |

### Dependency Rules (STRICT)

1. `domain/` has ZERO external deps -- pure Python only (dataclasses, ABC, typing)
2. `application/` depends on `domain/` interfaces, never on `infrastructure/`
3. `infrastructure/` implements `domain/` repository interfaces
4. `tools.py` calls `application/` services, returns JSON for Claude
5. No cross-context domain imports -- communicate via `kernel/` primitives
6. RDKit imports ONLY in `chemistry/infrastructure/rdkit_adapter.py`

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

## Key Patterns

- Each bounded context has: `domain/`, `application/`, `infrastructure/`, `tools.py`
- Domain entities use `@dataclass` with `__post_init__` validation
- Repository interfaces are ABCs in `domain/repository.py`
- Infrastructure adapters implement repository ABCs
- Tool functions in `tools.py` are the boundary between Claude and application services
- **Hypothesis-driven investigation loop**: formulate hypotheses, design experiments, execute tools, evaluate evidence, revise/reject, synthesize
- **Evidence-linked findings**: every finding references a `hypothesis_id` + `evidence_type` (supporting/contradicting/neutral)
- **Negative controls**: validate model predictions with known-inactive compounds (`NegativeControl` entity)
- 6 control tools: `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_finding`, `record_negative_control`, `conclude_investigation`
- SSE streaming for real-time investigation updates (12 event types)
- TanStack Router file-based routing in console
- `MultiModelOrchestrator`: hypothesis-driven loop (formulate -> design -> execute -> evaluate per hypothesis)
- `Orchestrator` is the single-model fallback (used when all models are the same)
- `SqliteInvestigationRepository` persists investigations to SQLite (WAL mode)
- `CostTracker` tracks per-model token usage with tiered pricing
- SSE reconnection with exponential backoff (1s, 2s, 4s, max 3 retries)
- Semantic Scholar client: exponential backoff retry (3 attempts, 1s/2s/4s) on 429 and timeout
- Molecule visualization: server-side 2D SVG depiction (RDKit `rdMolDraw2D`), 3Dmol.js for 3D/docking views
- `CandidateTable` shows 2D structure thumbnails with expandable detail panel (3D viewer + properties + Lipinski badge)
- Molecule API: `/molecule/depict` (SVG, cached 24h), `/molecule/conformer`, `/molecule/descriptors`, `/targets`
- Toast notifications via `sonner` (completion + error events, dark-themed OKLCH colors)
- Custom scrollbar CSS: 8px webkit + Firefox `scrollbar-width: thin` with OKLCH theme colors
- Findings replay: `InvestigationCompleted` event carries `findings[]` so page reloads hydrate findings from SSE
- `CompletionSummaryCard` replaces `ActiveExperimentCard` post-completion (candidate + finding + hypothesis counts)
- `HypothesisBoard`: kanban-style card grid showing hypothesis status (proposed/testing/supported/refuted/revised)
- `NegativeControlPanel`: table of known-inactive compounds with pass/fail classification indicators

## Key Files (Investigation Context)

| File | Purpose |
|------|---------|
| `investigation/application/orchestrator.py` | Single-model agentic loop with hypothesis control tool dispatch |
| `investigation/application/multi_orchestrator.py` | Hypothesis-driven Director-Worker-Summarizer orchestrator |
| `investigation/application/cost_tracker.py` | Per-model cost tracking with tiered pricing |
| `investigation/application/prompts.py` | 7 prompts: scientist, director (formulation/experiment/evaluation/synthesis), researcher, summarizer |
| `investigation/domain/hypothesis.py` | Hypothesis entity + HypothesisStatus enum |
| `investigation/domain/experiment.py` | Experiment entity + ExperimentStatus enum |
| `investigation/domain/negative_control.py` | NegativeControl frozen dataclass |
| `investigation/domain/events.py` | 12 domain events (Hypothesis*, Experiment*, NegativeControl*, Finding, Tool*, Thinking, Completed, Error) |
| `investigation/domain/repository.py` | InvestigationRepository ABC |
| `investigation/infrastructure/sqlite_repository.py` | SQLite implementation with hypothesis/experiment/negative_control serialization |
| `investigation/infrastructure/anthropic_client.py` | Anthropic API adapter with retry |
| `api/routes/investigation.py` | REST + SSE endpoints, 23-tool registry, auto-selects orchestrator |
| `api/routes/molecule.py` | Molecule depiction, conformer, descriptors, targets endpoints |
| `api/sse.py` | Domain event to SSE conversion (12 types) |

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
