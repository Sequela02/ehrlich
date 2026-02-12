# Contributing to Ehrlich

Ehrlich is an AI-powered scientific discovery engine that uses Claude as a hypothesis-driven reasoning engine. The core engine is domain-agnostic -- any scientific domain can plug in with its own tools, scoring, and visualization.

See [docs/domain-agnostic.md](docs/domain-agnostic.md) for the full story of how and why the engine was generalized.

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

**Scopes:** `kernel`, `literature`, `chemistry`, `analysis`, `prediction`, `simulation`, `sports`, `investigation`, `api`, `console`, `mol`, `data`

## Architecture

DDD monorepo with 8 bounded contexts. Each context follows `domain/` -> `application/` -> `infrastructure/` layering.

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
Sonnet 4.5 (Researcher) -- Executes experiments with 36 domain-filtered tools (parallel: 2 per batch)
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
| sports | Sports science (evidence analysis, protocol comparison, injury risk, training metrics) |
| investigation | Multi-model orchestration + domain registry + SQLite persistence |

## Testing

- Server: `uv run pytest` -- unit + integration tests
- Console: `bunx vitest run` -- component + utility tests
- Coverage minimum: 80% (server), enforced by pytest-cov

---

## Adding a New Scientific Domain

The engine is designed so that adding a new domain requires **zero changes to existing code**. You create new files and register them.

### Step 1: Create the Bounded Context

Create a new directory under `server/src/ehrlich/`:

```
server/src/ehrlich/yourdomain/
    __init__.py
    tools.py                 # Tool functions (async, return JSON strings)
    domain/
        __init__.py
    application/
        __init__.py
    infrastructure/
        __init__.py
```

### Step 2: Write Tools

Each tool is an async function that returns a JSON string. The function's type hints and docstring are auto-converted to Claude's tool schema.

```python
# server/src/ehrlich/yourdomain/tools.py

import json

async def analyze_something(
    query: str,
    threshold: float = 0.5,
) -> str:
    """Analyze something for your domain.

    Computes X, Y, Z metrics and returns a structured result.

    Args:
        query: What to analyze
        threshold: Minimum score threshold (default: 0.5)
    """
    # Your logic here
    return json.dumps({"query": query, "result": "..."})
```

Rules:
- Always `async def`, always returns `str` (JSON)
- Docstring becomes the tool description Claude sees
- `Args:` section becomes parameter descriptions
- Type hints become JSON Schema types (str, int, float, bool, list)
- Keep tools focused -- one tool, one responsibility

### Step 3: Create the DomainConfig

Create a config file at `server/src/ehrlich/investigation/domain/domains/yourdomain.py`:

```python
from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

YOUR_DOMAIN = DomainConfig(
    name="your_domain",                    # Internal name
    display_name="Your Domain",            # Shown in UI
    identifier_type="compound",            # Type of candidate identifier
    identifier_label="Compound",           # Column header for identifier
    candidate_label="Candidate Compounds", # Section title in reports
    tool_tags=frozenset({
        "yourdomain",                      # Must match tags in Step 4
        "literature",                      # Include "literature" if using paper search
    }),
    score_definitions=(
        ScoreDefinition(
            key="relevance_score",         # Key in candidate's scores dict
            label="Relevance",             # Column header
            format_spec=".2f",             # Python format spec
            higher_is_better=True,         # Controls color coding
            good_threshold=0.7,            # Green above this
            ok_threshold=0.4,              # Yellow above this, red below
        ),
        # Add more ScoreDefinitions as needed
    ),
    attribute_keys=("category", "source"), # Non-numeric candidate attributes
    negative_control_threshold=0.5,        # Score below = correctly classified
    visualization_type="table",            # "molecular" for 3Dmol.js, "table" for generic
    hypothesis_types=(
        "mechanistic",                     # Valid hypothesis_type values for this domain
        "correlational",
        "predictive",
    ),
    valid_domain_categories=(
        "your_domain",                     # Categories the classifier might output
        "related_field",                   # Map these to your domain
    ),
    template_prompts=(
        {
            "title": "Example Investigation",
            "domain": "Your Domain",
            "prompt": "Your example research question here...",
        },
    ),
    director_examples="""<examples>...</examples>""",     # 2 multishot examples for hypothesis formulation
    experiment_examples="""<examples>...</examples>""",    # 1 multishot example for experiment design
    synthesis_scoring_instructions="...",                  # How to score candidates
)
```

Key decisions:
- **`visualization_type`**: Use `"molecular"` only if your candidates are SMILES strings and you want 3Dmol.js. Use `"table"` for everything else.
- **`tool_tags`**: This frozenset determines which tools the Researcher can see. Include `"literature"` if you want paper search.
- **`director_examples`**: These are the most impactful part. Good multishot examples make the Director formulate domain-appropriate hypotheses. Use `{{` and `}}` for literal braces in f-string-like contexts.
- **`score_definitions`**: These become the columns in the CandidateTable. The frontend auto-generates color-coded cells based on thresholds.

### Step 4: Register Tools and Domain

Edit `server/src/ehrlich/api/routes/investigation.py`:

```python
# Add imports
from ehrlich.yourdomain.tools import analyze_something, other_tool
from ehrlich.investigation.domain.domains.yourdomain import YOUR_DOMAIN

# In _build_registry():
_yourdomain = frozenset({"yourdomain"})
# Add to tagged_tools list:
("analyze_something", analyze_something, _yourdomain),
("other_tool", other_tool, _yourdomain),

# In _build_domain_registry():
domain_registry.register(YOUR_DOMAIN)
```

### Step 5: Add Frontend Templates (Optional)

If you added `template_prompts` in your DomainConfig, add matching templates in `console/src/features/investigation/components/TemplateCards.tsx`:

```typescript
{
  title: "Example Investigation",
  description: "Short description",
  prompt: "Your example research question...",
  icon: SomeIcon,           // Lucide React icon
  domainTag: "Your Domain",
},
```

### Step 6: Write Tests

Create `server/tests/yourdomain/test_tools.py`:

```python
import json
import pytest

from ehrlich.yourdomain.tools import analyze_something

class TestAnalyzeSomething:
    @pytest.mark.asyncio()
    async def test_returns_result(self) -> None:
        result = json.loads(await analyze_something("test query"))
        assert "result" in result
```

Mock external API calls. Test edge cases (empty input, invalid data).

### Step 7: Update Documentation

Update these files (in the same commit as the code):

| File | What to update |
|------|---------------|
| `CLAUDE.md` | Tool count, bounded contexts table, tools section, scopes list |
| `README.md` | Tool count, bounded contexts table, tools table, "What Can Ehrlich Investigate" |
| `docs/architecture.md` | Bounded contexts, tool count, data flow |
| `docs/roadmap.md` | Add completion entry |

### Step 8: Verify

```bash
# Server
uv run pytest --tb=short -q           # All tests pass (including new ones)
uv run ruff check src/ tests/         # Zero violations
uv run mypy src/ehrlich/              # Zero errors

# Console
bun run build                          # Builds successfully
bun run typecheck                      # Zero errors
bunx vitest run                        # All tests pass
```

That's it. Your domain is live. The orchestrator will auto-detect it from the user's research question, filter tools, adapt prompts, and render domain-appropriate results.

---

## Improving an Existing Domain

### Adding a New Tool to a Domain

1. Write the tool function in the domain's `tools.py`
2. Register it in `_build_registry()` with the domain's tag
3. Write tests
4. Update the integration test tool count in `tests/integration/test_e2e.py`
5. Update docs (tool counts in CLAUDE.md, README.md, docs/architecture.md)

### Improving Score Definitions

Edit the domain's config file (e.g., `domains/molecular.py`). Add or modify `ScoreDefinition` entries. The frontend automatically picks up new columns.

### Improving Director Prompts

Edit `director_examples` in the domain's config. Better multishot examples = better hypothesis formulation. Follow the pattern: research question + literature findings + structured JSON output with hypothesis, prediction, criteria, and negative controls.

### Adding Template Prompts

Add entries to `template_prompts` in the config and matching cards in `TemplateCards.tsx`.

### Adding External Data Sources

1. Create an infrastructure client in your domain's `infrastructure/` directory
2. Follow the pattern: `httpx.AsyncClient`, retry with exponential backoff, structured error handling
3. Use the client in your tool functions
4. Mock the client in tests
