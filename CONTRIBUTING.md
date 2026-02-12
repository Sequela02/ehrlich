# Contributing to Ehrlich

Ehrlich is an AI-powered molecular discovery engine that uses Claude as a hypothesis-driven scientific reasoning engine. It combines cheminformatics, ML, molecular simulation, and multi-source data tools to investigate any molecular science question.

## Prerequisites

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) package manager
- **Bun** (or Node 20+) for the console
- **ANTHROPIC_API_KEY** environment variable set

## Setup

### Server

```bash
cd server
uv sync --extra dev
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
```

### Console

```bash
cd console
bun install
bun dev    # Dev server at :5173
```

## Development Workflow

### Quality Gates (all must pass before commit)

**Server:**
```bash
uv run ruff check src/ tests/              # Lint (zero violations)
uv run ruff format src/ tests/ --check     # Format check
uv run mypy src/ehrlich/                    # Type check (strict)
uv run pytest --cov=ehrlich                 # Tests (80%+ coverage)
```

**Console:**
```bash
bun run build       # Vite build (generates route tree)
bun run typecheck   # tsc --noEmit (run after build)
bunx vitest run     # Tests
```

### Commit Format

```
type(scope): description
```

**Types:** `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

**Scopes:** `kernel`, `literature`, `chemistry`, `analysis`, `prediction`, `simulation`, `investigation`, `api`, `console`, `mol`, `data`

## Architecture

DDD monorepo with 7 bounded contexts. Each context follows `domain/` -> `application/` -> `infrastructure/` layering.

### Layer Rules (Strict)

1. `domain/` has ZERO external dependencies -- pure Python only
2. `application/` depends on `domain/` interfaces, never on `infrastructure/`
3. `infrastructure/` implements `domain/` repository interfaces
4. `tools.py` calls `application/` services, returns JSON for Claude
5. No cross-context domain imports -- communicate via `kernel/` primitives
6. RDKit imports ONLY in `chemistry/infrastructure/rdkit_adapter.py`

### Multi-Model Orchestrator

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 30 tools (parallel: 2 per batch)
Haiku 4.5 (Summarizer)  -- Compresses large outputs, classifies domains
```

### Bounded Contexts

| Context | Purpose |
|---------|---------|
| kernel | Shared primitives (SMILES, Molecule, exceptions) |
| literature | Paper search (Semantic Scholar) |
| chemistry | RDKit cheminformatics |
| analysis | Dataset exploration (ChEMBL, PubChem, GtoPdb) |
| prediction | ML models (XGBoost, Chemprop) |
| simulation | Docking, ADMET, targets (RCSB PDB, UniProt, Open Targets, EPA CompTox) |
| investigation | Multi-model orchestration + SQLite persistence |

## Testing

- Server: `uv run pytest` -- unit + integration tests
- Console: `bunx vitest run` -- component + utility tests
- Coverage minimum: 80% (server), enforced by pytest-cov
