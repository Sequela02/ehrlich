# Ehrlich - AI Antimicrobial Discovery Agent

## Project Overview

Ehrlich is an AI-powered antimicrobial discovery agent built for the Claude Code Hackathon (Feb 10-16, 2026). It uses Claude as a scientific reasoning engine with cheminformatics, ML, and molecular simulation tools.

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun).

### Multi-Model Architecture (Director-Worker-Summarizer)

```
Opus 4.6 (Director)     -- Plans phases, reviews results, synthesizes report (NO tools)
Sonnet 4.5 (Researcher) -- Executes each phase with 19 tools
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
- SSE streaming for real-time investigation updates (11 event types)
- TanStack Router file-based routing in console
- `MultiModelOrchestrator` uses Director-Worker-Summarizer pattern (3 Claude tiers)
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
- `CompletionSummaryCard` replaces `ActivePhaseCard` post-completion (candidate + finding counts)

## Key Files (Investigation Context)

| File | Purpose |
|------|---------|
| `investigation/application/orchestrator.py` | Single-model agentic loop (fallback) |
| `investigation/application/multi_orchestrator.py` | Director-Worker-Summarizer orchestrator |
| `investigation/application/cost_tracker.py` | Per-model cost tracking with tiered pricing |
| `investigation/application/prompts.py` | System prompts for Director, Researcher, Summarizer |
| `investigation/domain/events.py` | 11 domain events (including Director*, OutputSummarized, PhaseCompleted) |
| `investigation/domain/repository.py` | InvestigationRepository ABC |
| `investigation/infrastructure/sqlite_repository.py` | SQLite implementation |
| `investigation/infrastructure/anthropic_client.py` | Anthropic API adapter with retry |
| `api/routes/investigation.py` | REST + SSE endpoints, auto-selects orchestrator |
| `api/routes/molecule.py` | Molecule depiction, conformer, descriptors, targets endpoints |
| `api/sse.py` | Domain event to SSE conversion (11 types) |

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
| `console/.../investigation/components/ActivePhaseCard.tsx` | Live phase activity card (tool name, counters, director state) |
| `console/.../investigation/components/CompletionSummaryCard.tsx` | Post-completion card (candidate + finding counts) |
| `console/.../shared/components/ui/Toaster.tsx` | Sonner toast wrapper with dark OKLCH theme |
