# Ehrlich - AI Antimicrobial Discovery Agent

## Project Overview

Ehrlich is an AI-powered antimicrobial discovery agent built for the Claude Code Hackathon (Feb 10-16, 2026). It uses Claude as a scientific reasoning engine with cheminformatics, ML, and molecular simulation tools.

## Architecture

DDD monorepo: `server/` (Python 3.12) + `console/` (React 19 / TypeScript / Bun).

### Bounded Contexts

| Context | Location | Purpose |
|---------|----------|---------|
| kernel | `server/src/ehrlich/kernel/` | Shared primitives (SMILES, Molecule, exceptions) |
| literature | `server/src/ehrlich/literature/` | Paper search, references |
| chemistry | `server/src/ehrlich/chemistry/` | RDKit cheminformatics |
| analysis | `server/src/ehrlich/analysis/` | Dataset exploration, enrichment |
| prediction | `server/src/ehrlich/prediction/` | ML models (Chemprop, XGBoost) |
| simulation | `server/src/ehrlich/simulation/` | Docking, ADMET, resistance |
| investigation | `server/src/ehrlich/investigation/` | Agent orchestration loop |

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
- SSE streaming for real-time investigation updates
- TanStack Router file-based routing in console
