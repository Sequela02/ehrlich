# Adding a New Scientific Domain

Ehrlich's domain-agnostic engine supports pluggable scientific domains via the `DomainConfig` + `DomainRegistry` system. This guide walks through adding a new domain step-by-step.

## Prerequisites

- Familiarity with the bounded context structure (`domain/`, `application/`, `infrastructure/`, `tools.py`)
- Understanding of the tool tagging system (see `CLAUDE.md` Key Patterns)

## Step-by-Step Guide

### 1. Create the Bounded Context

Create a new directory under `server/src/ehrlich/`:

```
server/src/ehrlich/genomics/
    __init__.py
    domain/
        __init__.py
        entities.py        # Domain entities (dataclasses)
        repository.py      # Repository ABCs (if needed)
    application/
        __init__.py
        genomics_service.py  # Business logic
    infrastructure/
        __init__.py
        *_client.py        # External API clients
    tools.py               # Tool functions for Claude
```

### 2. Define Domain Entities

Create domain entities as frozen dataclasses in `domain/entities.py`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class GeneVariant:
    gene_symbol: str
    variant_id: str
    chromosome: str
    position: int
    consequence: str
    significance: str
```

### 3. Build Infrastructure Clients

Create external API clients in `infrastructure/`. Follow the established pattern:
- Use `httpx.AsyncClient` with retry and backoff
- Return domain entities, not raw JSON
- Handle errors with structured error responses

### 4. Implement Tool Functions

Create tool functions in `tools.py`. Each tool:
- Is an `async` function returning a JSON string
- Has a clear docstring with `Args:` section (used for schema generation)
- Calls application services, not infrastructure directly

```python
async def search_gene_variants(
    gene_symbol: str,
    significance: str = "pathogenic",
    limit: int = 10,
) -> str:
    """Search for gene variants by symbol and clinical significance.

    Args:
        gene_symbol: Gene symbol (e.g. 'BRCA1', 'TP53')
        significance: Clinical significance filter (default: pathogenic)
        limit: Maximum results to return (default: 10)
    """
    variants = await _service.search_variants(gene_symbol, significance, limit)
    return json.dumps({"gene": gene_symbol, "count": len(variants), "variants": [...]})
```

### 5. Create the DomainConfig

Create `investigation/domain/domains/genomics.py`:

```python
from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

GENOMICS = DomainConfig(
    name="genomics",
    display_name="Genomics",
    identifier_type="gene",
    identifier_label="Gene",
    candidate_label="Gene Variants",
    tool_tags=frozenset({"genomics", "literature"}),
    score_definitions=(
        ScoreDefinition(
            key="pathogenicity_score",
            label="Pathogenicity",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.8,
            ok_threshold=0.5,
        ),
    ),
    attribute_keys=("gene_symbol", "chromosome", "consequence"),
    negative_control_threshold=0.5,
    # visualization is reactive: LiveLabViewer auto-appears for molecular tools,
    hypothesis_types=("mechanistic", "epidemiological", "pharmacogenomic"),
    valid_domain_categories=("genomics", "genetics", "pharmacogenomics"),
    template_prompts=(...),
    director_examples="...",
    experiment_examples="...",
    synthesis_scoring_instructions="...",
)
```

### 6. Register Tools in investigation.py

In `api/routes/investigation.py`, import and register your tools:

```python
from ehrlich.genomics.tools import search_gene_variants, ...

# In _build_registry():
_genomics = frozenset({"genomics"})
tagged_tools.extend([
    ("search_gene_variants", search_gene_variants, _genomics),
    ...
])
```

### 7. Register the Domain

In `_build_domain_registry()`:

```python
from ehrlich.investigation.domain.domains.genomics import GENOMICS

def _build_domain_registry() -> DomainRegistry:
    domain_registry = DomainRegistry()
    domain_registry.register(MOLECULAR_SCIENCE)
    domain_registry.register(SPORTS_SCIENCE)
    domain_registry.register(GENOMICS)
    return domain_registry
```

### 8. Add Tests

Create tests for:
- Tool functions (`tests/genomics/test_tools.py`)
- Domain entities (`tests/genomics/test_entities.py`)
- Infrastructure clients (`tests/genomics/test_*_client.py`)
- Integration: verify tools appear in registry with correct tags

## DomainConfig Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Internal identifier (snake_case) |
| `display_name` | `str` | Human-readable name |
| `identifier_type` | `str` | Type of candidate identifier (e.g. "smiles", "protocol", "gene") |
| `identifier_label` | `str` | Column header for identifier |
| `candidate_label` | `str` | Plural label for candidates |
| `tool_tags` | `frozenset[str]` | Tags that select which tools this domain uses |
| `score_definitions` | `tuple[ScoreDefinition, ...]` | Score columns for candidate table |
| `attribute_keys` | `tuple[str, ...]` | Extra attribute columns |
| `negative_control_threshold` | `float` | Score threshold for negative controls |
| `hypothesis_types` | `tuple[str, ...]` | Valid hypothesis types for this domain |
| `valid_domain_categories` | `tuple[str, ...]` | Categories the Haiku classifier can output |
| `template_prompts` | `tuple[dict, ...]` | Template research questions for home page |
| `director_examples` | `str` | XML multishot examples for Director prompts |
| `experiment_examples` | `str` | XML multishot examples for experiment design |
| `synthesis_scoring_instructions` | `str` | Instructions for candidate scoring in synthesis |

## Tool Tagging

Tools are tagged with `frozenset[str]` domain tags. When a domain is detected:

1. `DomainRegistry.detect()` returns matching `DomainConfig`(s)
2. `DomainConfig.tool_tags` is the union of all relevant tags
3. `ToolRegistry.list_schemas_for_domain(tags)` filters tools to those with matching tags
4. Investigation control tools (no tags) are always included

Multi-tag tools (e.g. `frozenset({"sports", "nutrition"})`) match any domain whose `tool_tags` includes either tag.

## Checklist

- [ ] Domain entities in `domain/entities.py`
- [ ] Infrastructure clients with retry/backoff
- [ ] Tool functions with proper docstrings
- [ ] `DomainConfig` with all required fields
- [ ] Tools registered in `_build_registry()` with tags
- [ ] Domain registered in `_build_domain_registry()`
- [ ] Tests for tools, entities, and clients
- [ ] Update `CLAUDE.md` tool count and tables
- [ ] Update `README.md` tool count and data sources
- [ ] Update `docs/architecture.md` bounded contexts
