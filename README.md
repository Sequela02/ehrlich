# Ehrlich

AI-powered antimicrobial discovery agent. Ehrlich uses Claude as a scientific reasoning engine combined with cheminformatics, machine learning, and molecular simulation tools to accelerate the identification of novel antimicrobial compounds.

Built for the [Claude Code Hackathon](https://docs.anthropic.com/en/docs/claude-code-hackathon) (Feb 10-16, 2026).

## Architecture

Ehrlich follows Domain-Driven Design with six bounded contexts:

| Context | Purpose |
|---------|---------|
| **literature** | Scientific paper search and reference management |
| **chemistry** | Cheminformatics: molecular descriptors, fingerprints, 3D conformers |
| **analysis** | Dataset exploration, substructure enrichment, property analysis |
| **prediction** | ML modeling: train, predict, ensemble, cluster |
| **simulation** | Molecular docking, ADMET prediction, resistance assessment |
| **investigation** | Agent orchestration: Claude-driven research loop |

## Tech Stack

- **Server:** Python 3.12, FastAPI, uv
- **Console:** React 19, TypeScript 5.6+, Bun, Vite 7+, TanStack
- **AI:** Claude (Anthropic API) with tool use
- **Science:** RDKit, Chemprop, XGBoost, AutoDock Vina, Meeko

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Bun](https://bun.sh/) (JavaScript runtime)
- Python 3.12
- An Anthropic API key

### Server

```bash
cd server
uv sync --extra dev                    # Core + dev dependencies
# uv sync --extra all --extra dev      # All deps including docking + deep learning
export EHRLICH_ANTHROPIC_API_KEY=sk-ant-...
uv run uvicorn ehrlich.api.app:create_app --factory --reload --port 8000
```

Optional dependency groups:
- `docking` -- AutoDock Vina + Meeko (requires Boost C++ libraries)
- `deeplearning` -- Chemprop D-MPNN (pulls PyTorch)
- `all` -- everything

### Console

```bash
cd console
bun install
bun dev
```

Open http://localhost:5173 in your browser.

### Docker

```bash
docker compose up
```

Server at :8000, Console at :3000.

## Development

### Server Commands

```bash
uv run pytest --cov=ehrlich --cov-report=term-missing   # Tests + coverage
uv run ruff check src/ tests/                            # Lint
uv run ruff format src/ tests/                           # Format
uv run mypy src/ehrlich/                                 # Type check
```

### Console Commands

```bash
bun test          # Vitest
bun run build     # vite build (generates routes + bundles)
bun run typecheck # tsc --noEmit (run after build to ensure route types exist)
```

### Quality Gates

| Gate | Tool | Threshold |
|------|------|-----------|
| Linting | ruff | Zero violations |
| Formatting | ruff format | Zero violations |
| Type checking | mypy (strict) | Zero errors |
| Test coverage | pytest-cov | 80% minimum |
| TypeScript | tsc --noEmit | Zero errors |

## License

MIT - see [LICENSE](LICENSE).

## Author

Ricardo Armenta / [Sequel](https://github.com/Sequela02)
