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

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EHRLICH_ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `ANTHROPIC_API_KEY` | Alt | Falls back to this if EHRLICH_ not set |
| `EHRLICH_ANTHROPIC_MODEL` | No | Model name (default: `claude-sonnet-4-5-20250929`) |
| `EHRLICH_MAX_ITERATIONS` | No | Max agent loop iterations (default: 50) |
| `EHRLICH_LOG_LEVEL` | No | Logging level (default: INFO) |

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

### Data Preparation (Optional)

Pre-download ChEMBL bioactivity data to avoid first-run delays:

```bash
# Download bioactivity data for all target organisms
uv run python data/scripts/prepare_data.py --chembl

# Download protein structures from RCSB PDB
uv run python data/scripts/prepare_data.py --proteins

# Download everything
uv run python data/scripts/prepare_data.py --all
```

Cached datasets are stored in `data/datasets/` as parquet files.

### Docker

```bash
docker compose up
```

Server at :8000, Console at :3000.

## Demo

1. Start the server: `cd server && uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`
2. Start the console: `cd console && bun dev`
3. Open http://localhost:5173
4. Type a research prompt, e.g.: *"Find novel antimicrobial candidates against MRSA"*
5. Watch the investigation unfold in real-time via SSE streaming

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
