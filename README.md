# Ehrlich

AI-powered antimicrobial discovery agent. Ehrlich uses Claude as a scientific reasoning engine combined with cheminformatics, machine learning, and molecular simulation tools to accelerate the identification of novel antimicrobial compounds.

Built for the [Claude Code Hackathon](https://docs.anthropic.com/en/docs/claude-code-hackathon) (Feb 10-16, 2026).

## Architecture

Ehrlich follows Domain-Driven Design with seven bounded contexts:

| Context | Purpose |
|---------|---------|
| **kernel** | Shared primitives: SMILES, Molecule, exceptions |
| **literature** | Scientific paper search and reference management |
| **chemistry** | Cheminformatics: molecular descriptors, fingerprints, 3D conformers |
| **analysis** | Dataset exploration, substructure enrichment, property analysis |
| **prediction** | ML modeling: train, predict, ensemble, cluster |
| **simulation** | Molecular docking, ADMET prediction, resistance assessment |
| **investigation** | Multi-model agent orchestration with Director-Worker-Summarizer pattern |

### Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Plans phases, reviews results, synthesizes report (3-5 calls)
Sonnet 4.5 (Researcher) -- Executes each phase with 19 tools (10-20 calls)
Haiku 4.5 (Summarizer)  -- Compresses large tool outputs >2000 chars (5-10 calls)
```

Cost: ~$3-4 per investigation (vs ~$11 with all-Opus).

## Tech Stack

- **Server:** Python 3.12, FastAPI, uv, SQLite (aiosqlite)
- **Console:** React 19, TypeScript 5.6+, Bun, Vite 7+, TanStack, 3Dmol.js
- **AI:** Claude Opus 4.6 + Sonnet 4.5 + Haiku 4.5 (Anthropic API) with tool use
- **Science:** RDKit, Chemprop, XGBoost, AutoDock Vina, Meeko, PyArrow (parquet caching)

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
| `EHRLICH_ANTHROPIC_MODEL` | No | Single-model fallback (default: `claude-opus-4-6`) |
| `EHRLICH_DIRECTOR_MODEL` | No | Director model (default: `claude-opus-4-6`) |
| `EHRLICH_RESEARCHER_MODEL` | No | Researcher model (default: `claude-sonnet-4-5-20250929`) |
| `EHRLICH_SUMMARIZER_MODEL` | No | Summarizer model (default: `claude-haiku-4-5-20251001`) |
| `EHRLICH_SUMMARIZER_THRESHOLD` | No | Chars before Haiku summarizes output (default: 2000) |
| `EHRLICH_MAX_ITERATIONS` | No | Max agent loop iterations (default: 50) |
| `EHRLICH_MAX_ITERATIONS_PER_PHASE` | No | Max iterations per phase in multi-model mode (default: 10) |
| `EHRLICH_DB_PATH` | No | SQLite database path (default: `data/ehrlich.db`) |
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

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/investigate` | List all investigations (most recent first) |
| GET | `/api/v1/investigate/{id}` | Full investigation detail |
| POST | `/api/v1/investigate` | Create new investigation |
| GET | `/api/v1/investigate/{id}/stream` | SSE stream of investigation events |
| GET | `/api/v1/molecule/depict?smiles=&w=&h=` | 2D SVG depiction (`image/svg+xml`, cached 24h) |
| GET | `/api/v1/molecule/conformer?smiles=` | 3D conformer (JSON: mol_block, energy, num_atoms) |
| GET | `/api/v1/molecule/descriptors?smiles=` | Molecular descriptors + Lipinski pass/fail |
| GET | `/api/v1/targets` | List protein targets (pdb_id, name, organism) |

### SSE Event Types

| Event | Description |
|-------|-------------|
| `phase_started` | Research phase began |
| `tool_called` | Tool invocation with inputs |
| `tool_result` | Tool output preview |
| `finding_recorded` | Scientific finding captured |
| `thinking` | Model reasoning text |
| `director_planning` | Director planning/reviewing/synthesizing |
| `director_decision` | Director structured decision (plan, review, synthesis) |
| `output_summarized` | Haiku compressed a large tool output |
| `completed` | Investigation finished with candidates and cost |
| `error` | Error occurred |

## Demo

1. Start the server: `cd server && uv run uvicorn ehrlich.api.app:create_app --factory --port 8000`
2. Start the console: `cd console && bun dev`
3. Open http://localhost:5173
4. Type a research prompt, e.g.: *"Find novel antimicrobial candidates against MRSA"*
5. Watch the investigation unfold in real-time via SSE streaming
6. View ranked candidates with 2D structure thumbnails in the results table
7. Click any candidate row to expand the detail panel with 3D conformer viewer, molecular properties, and Lipinski assessment
8. View past investigations in the history section on the home page
9. Browse molecule depictions directly: `/api/v1/molecule/depict?smiles=CCO`

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
