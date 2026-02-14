# Contributing to Ehrlich

Ehrlich is an AI-powered scientific discovery engine that uses Claude as a hypothesis-driven reasoning engine. The core engine is domain-agnostic -- any scientific domain can plug in with its own tools, scoring, and visualization.

See [docs/domain-agnostic.md](docs/domain-agnostic.md) for the full story of how and why the engine was generalized.

## Contributor License Agreement

By submitting a pull request to this repository, you agree to the following terms:

1. **You grant Ehrlich's maintainers a perpetual, worldwide, non-exclusive, royalty-free license** to use, reproduce, modify, distribute, sublicense, and relicense your contributions as part of this project.

2. **You retain copyright** to your contributions. This agreement does not transfer ownership.

3. **You have the right to submit** the contribution. If your contribution includes code from your employer or third parties, you have obtained the necessary permissions.

4. **Your contribution is provided "as is"** without warranty of any kind.

### Why This Matters

Ehrlich is currently licensed under AGPL-3.0. This CLA preserves the option to change the license in the future (e.g., to MIT) without requiring permission from every past contributor. This is standard practice for open source projects with dual-licensing strategies.

If you have questions about this CLA, open an issue before contributing.

---

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

**Scopes:** `kernel`, `shared`, `literature`, `chemistry`, `analysis`, `prediction`, `simulation`, `training`, `nutrition`, `investigation`, `api`, `console`, `mol`, `data`

### Code Standards (Non-Negotiable)

Every contribution must respect:

- **DDD + Clean Architecture** -- Respect bounded contexts. `domain/` is pure Python with zero external deps. `application/` depends on domain interfaces, never infrastructure. `infrastructure/` implements domain ABCs. No cross-context domain imports.
- **No redundancy** -- DRY across layers. If a pattern exists, reuse it. If a utility exists, find it before writing a new one. Three similar lines of code is better than a premature abstraction, but true duplication is never acceptable.
- **No dead code** -- No commented-out blocks, no unused imports, no orphaned functions. Delete what you don't need.
- **No boilerplate** -- If it can be derived (schemas from type hints, routes from file conventions), derive it. Don't write what the framework gives you.
- **No backward-compatibility hacks** -- No renamed `_unused` vars, no re-exports for removed code, no `# removed` comments. If something is unused, delete it. Exception: production hotfixes with a follow-up cleanup ticket.
- **Clean Code** -- Readability over cleverness. Explicit imports only (no wildcards). Fail fast at boundaries. Meaningful names. Small focused functions.
- **Documentation as code** -- Every code change updates relevant docs in the same commit. Tool counts, event counts, file tables, component lists. This is the #1 recurring failure -- never skip it.
- **Test before claiming complete** -- All quality gates must pass. Never say "done" without running the full suite.

## Architecture

DDD monorepo with 10 bounded contexts. Each context follows `domain/` -> `application/` -> `infrastructure/` layering.

### Layer Rules (Strict)

1. `domain/` has ZERO external dependencies -- pure Python only
2. `application/` depends on `domain/` interfaces, never on `infrastructure/`
3. `infrastructure/` implements `domain/` repository interfaces
4. `tools.py` calls `application/` services, returns JSON for Claude
5. No cross-context domain imports -- communicate via `kernel/` primitives or `shared/` ports
6. `shared/` contains cross-cutting ports (ABCs) and value objects -- no infrastructure deps
7. RDKit imports ONLY in `chemistry/infrastructure/rdkit_adapter.py`

### Multi-Model Orchestrator

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence (NO tools)
Sonnet 4.5 (Researcher) -- Executes experiments with 70 tools (parallel: 2 per batch)
Haiku 4.5 (Summarizer)  -- Compresses large outputs, classifies domains
```

### Bounded Contexts

| Context | Domain | Purpose |
|---------|--------|---------|
| kernel | All | Shared primitives (SMILES, Molecule, exceptions) |
| shared | All | Cross-cutting ports and value objects (ChemistryPort, Fingerprint, Conformer3D) |
| literature | All | Paper search (Semantic Scholar) |
| chemistry | Molecular | RDKit cheminformatics |
| analysis | Molecular | Dataset exploration (ChEMBL, PubChem, GtoPdb) |
| prediction | Molecular | ML models (XGBoost, Chemprop) |
| simulation | Molecular | Docking, ADMET, targets (RCSB PDB, UniProt, Open Targets, EPA CompTox) |
| training | Training | Exercise physiology (evidence analysis, protocol comparison, injury risk, training metrics, clinical trials) |
| nutrition | Nutrition | Nutrition science (supplement evidence, labels, nutrients, safety, interactions, adequacy, inflammatory index) |
| investigation | All | Multi-model orchestration + domain registry + SQLite persistence |

## Testing

- Server: `uv run pytest` -- unit + integration tests
- Console: `bunx vitest run` -- component + utility tests
- Coverage minimum: 80% (server), enforced by pytest-cov

---

## Adding a New Scientific Domain

The engine is designed so that adding a new domain requires **zero changes to existing code**. You create new files and register them.

### Phase 0: Research Your Domain

Before writing any code, research the domain deeply. This upfront work determines the quality of every downstream decision -- tools, scoring, prompts, and visualization.

**What to research:**

1. **Problem definition** -- What scientific questions should this domain answer? What does "discovery" mean here? (e.g., molecular: find candidate drugs; training: find optimal training protocols)
2. **Data sources** -- Where does real experimental data come from? Identify free APIs, databases, or datasets. For each source: base URL, auth requirements, rate limits, response format, coverage
3. **Candidate criteria** -- What makes a good candidate in this domain? What scores matter? What thresholds separate good from bad? (e.g., molecular: prediction_score > 0.7, docking < -7.0 kcal/mol; training: effect_size > 0.5, evidence_grade A-B)
4. **Hypothesis types** -- What kinds of hypotheses does this domain test? (mechanistic, structural, correlational, physiological, etc.)
5. **Visualization needs** -- How should results be displayed? Charts, 3D models, diagrams, maps, tables?
6. **Domain vocabulary** -- Key terms, units, standard notations that Claude needs in its prompts

**Document your research** in `research/{yourdomain}/`:

```
research/yourdomain/
    data-sources.md       # APIs, databases, auth, rate limits
    domain-model.md       # Entities, scoring criteria, thresholds
    prior-work.md         # Existing tools and approaches in this field
```

See `research/molecular/`, `research/methodology/`, and the `training/` and `nutrition/` bounded contexts for examples of thorough domain research and implementation.

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
    # visualization is reactive: LiveLabViewer auto-appears for molecular tools,
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
- **Visualization**: Visualization is reactive -- LiveLabViewer auto-appears when molecular tool events (docking, descriptors, etc.) are detected in the SSE stream. Chart visualizations render inline from `VisualizationRendered` events. No configuration needed.
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

### Step 6: Add Visualization Components (Optional)

The visualization system supports **any rendering technology**: Recharts charts, Visx plots, custom SVG, 3Dmol.js 3D viewers, maps, network graphs, tables -- anything that renders in React. Each visualization is a lazy-loaded component registered by a `viz_type` string.

**Backend: create a visualization tool**

Add a tool that returns a `VisualizationPayload` JSON. The orchestrator auto-intercepts any tool result containing `viz_type` and emits a `VisualizationRendered` SSE event -- no orchestrator changes needed.

```python
# server/src/ehrlich/yourdomain/tools_viz.py (or in tools.py)

import json
from typing import Any

async def render_your_chart(
    items: list[dict[str, Any]],
    title: str = "Your Chart",
) -> str:
    """Render an interactive chart of your domain data.

    Args:
        items: List of data points with numeric properties
        title: Chart title
    """
    points = [{"label": i.get("name", ""), "value": i.get("score", 0)} for i in items]
    return json.dumps({
        "viz_type": "your_chart",        # Must match VizRegistry key
        "title": title,
        "data": {"points": points},
        "config": {"domain": "your_domain"},
    })
```

Register the tool in `_build_registry()` with a visualization tag:

```python
_yourdomain_viz = frozenset({"yourdomain", "visualization"})
("render_your_chart", render_your_chart, _yourdomain_viz),
```

**Frontend: create and register the component**

1. Create your chart component (any rendering library):

```typescript
// console/src/features/visualization/charts/YourChart.tsx

interface YourChartProps {
  data: { points: Array<{ label: string; value: number }> };
  title: string;
}

export default function YourChart({ data, title }: YourChartProps) {
  return (
    <div>
      <h4 className="mb-2 font-mono text-sm">{title}</h4>
      {/* Your rendering logic: Recharts, Visx, SVG, canvas, etc. */}
    </div>
  );
}
```

2. Register it in `console/src/features/visualization/VizRegistry.tsx`:

```typescript
const LazyYourChart = lazy(() => import('./charts/YourChart'));
registry.set('your_chart', LazyYourChart as unknown as ChartComponent);
```

That's it. The `VisualizationPanel` handles Suspense boundaries, grid layout, and error fallbacks automatically.

**Theming:** Use OKLCH tokens from `console/src/features/visualization/theme.ts` for consistent colors across all charts.

**3D molecular viewers:** If your domain uses 3Dmol.js-style 3D visualization, add your tool names to `MOLECULAR_TOOL_NAMES` in `console/src/features/visualization/VisualizationPanel.tsx` so the `LiveLabViewer` auto-appears.

### Step 7: Write Tests

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

### Step 8: Update Documentation

Update these files (in the same commit as the code):

| File | What to update |
|------|---------------|
| `CLAUDE.md` | Tool count, bounded contexts table, tools section, scopes list |
| `README.md` | Tool count, bounded contexts table, tools table, "What Can Ehrlich Investigate" |
| `docs/architecture.md` | Bounded contexts, tool count, data flow |
| `docs/roadmap.md` | Add completion entry |
| `web/src/lib/constants.ts` | STATS counts, DOMAINS array (toolCount, capabilities, sources, vizTools), DATA_SOURCES array |
| `console/` | Template prompts, domain badges, tool references where applicable |

### Step 9: Verify

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
6. Update tool counts and references in `web/src/lib/constants.ts` (STATS, DOMAINS toolCount) and `console/` where applicable

### Improving Score Definitions

Edit the domain's config file (e.g., `domains/molecular.py`). Add or modify `ScoreDefinition` entries. The frontend automatically picks up new columns.

### Improving Director Prompts

Edit `director_examples` in the domain's config. Better multishot examples = better hypothesis formulation. Follow the pattern: research question + literature findings + structured JSON output with hypothesis, prediction, criteria, and negative controls.

### Adding Template Prompts

Add entries to `template_prompts` in the config and matching cards in `TemplateCards.tsx`.

### Adding External Data Sources

Follow the DDD layering pattern used throughout the codebase:

**1. Domain layer** -- Define entities and repository ABC:

```python
# server/src/ehrlich/yourdomain/domain/entities.py
from dataclasses import dataclass

@dataclass(frozen=True)
class YourEntity:
    id: str
    name: str
    score: float
```

```python
# server/src/ehrlich/yourdomain/domain/repository.py
from abc import ABC, abstractmethod
from ehrlich.yourdomain.domain.entities import YourEntity

class YourRepository(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int) -> list[YourEntity]: ...
```

**2. Infrastructure layer** -- Implement the repository with an HTTP client:

```python
# server/src/ehrlich/yourdomain/infrastructure/your_client.py
import httpx
from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.yourdomain.domain.entities import YourEntity
from ehrlich.yourdomain.domain.repository import YourRepository

_BASE_URL = "https://api.example.com/v1"
_TIMEOUT = 20.0
_MAX_RETRIES = 3

class YourClient(YourRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, query: str, max_results: int = 10) -> list[YourEntity]:
        # Retry with exponential backoff, raise ExternalServiceError on failure
        ...
```

**3. Tool layer** -- Wire the client into your tool function:

```python
# In tools.py
from ehrlich.yourdomain.infrastructure.your_client import YourClient

_client = YourClient()

async def search_your_data(query: str, max_results: int = 10) -> str:
    results = await _client.search(query, max_results)
    return json.dumps([{"id": r.id, "name": r.name, "score": r.score} for r in results])
```

**4. Testing** -- Mock the HTTP client, test adapter and tool separately:

```python
# tests/yourdomain/test_tools.py -- test tool with mocked client
# tests/yourdomain/test_your_client.py -- test HTTP parsing with httpx mock
```

See `server/src/ehrlich/training/` and `server/src/ehrlich/nutrition/` for complete examples with real data sources (ClinicalTrials.gov, NIH DSLD, USDA FoodData, OpenFDA CAERS), each following this exact pattern.
