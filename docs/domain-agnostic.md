# From Molecules to Any Science: The Domain-Agnostic Evolution

## The Starting Point

Ehrlich started as a molecular discovery engine. Every entity, every prompt, every frontend component assumed molecules: `smiles` fields on candidates, hardcoded "Prediction/Docking/ADMET/Resistance" score columns, 3Dmol.js viewers on every investigation page, MRSA/Alzheimer's examples baked into Director prompts.

It worked. 30 tools, 8 data sources, hypothesis-driven reasoning with Popper/Platt/Feynman/Bayesian foundations. But the architecture had a hidden assumption: **science = chemistry**.

## The Insight

The hypothesis-driven engine -- formulate, predict, test, evaluate, revise -- is not chemistry. It is the scientific method. The Director does not care whether it is reasoning about binding affinities or training load ratios. The Researcher does not care whether it calls `dock_against_target` or `compute_training_metrics`. The loop is the same:

1. Classify the domain
2. Formulate testable hypotheses with predictions and criteria
3. Design experiments that use domain-appropriate tools
4. Execute, evaluate against pre-defined criteria
5. Synthesize ranked candidates

The only things that change between domains are: **which tools are available**, **what scores mean**, **how candidates are displayed**, and **what good prompt examples look like**.

## What Changed

### Entities: From Molecular Fields to Generic Structures

**Before:**
```python
@dataclass
class Candidate:
    smiles: str
    name: str
    prediction_score: float = 0.0
    docking_score: float = 0.0
    admet_score: float = 0.0
    resistance_risk: str = ""
```

**After:**
```python
@dataclass
class Candidate:
    identifier: str              # SMILES, protocol name, gene ID -- anything
    identifier_type: str = ""    # "smiles", "protocol", "gene"
    name: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)
```

Same change for `NegativeControl`: `smiles` + `prediction_score` became `identifier` + `score` + configurable `threshold`.

The key decision: no backward-compatibility shims. Old fields deleted completely. The generic structure is simpler and more powerful than the specific one it replaced.

### DomainConfig: One Dataclass Rules Everything

`DomainConfig` is a frozen dataclass that defines everything a domain needs:

```python
@dataclass(frozen=True)
class DomainConfig:
    name: str                    # "molecular_science"
    display_name: str            # "Molecular Science"
    identifier_type: str         # "smiles" or "protocol"
    candidate_label: str         # "Candidate Molecules" or "Training Protocols"
    tool_tags: frozenset[str]    # which tool categories this domain uses
    score_definitions: tuple[ScoreDefinition, ...]  # dynamic table columns
    # visualization is reactive -- determined by tool events in the stream
    hypothesis_types: tuple[str, ...]     # valid hypothesis categories
    director_examples: str       # multishot examples for Opus
    experiment_examples: str     # tool usage examples for Sonnet
    synthesis_scoring_instructions: str   # how to score candidates
```

One config drives: tool filtering, prompt adaptation, frontend rendering, and score column definitions. Visualization is reactive -- LiveLabViewer auto-appears when molecular tool events are detected in the stream, and chart visualizations render inline from `VisualizationRendered` events. No if/else chains. No feature flags. Configuration over code.

### Tool Tagging: Domain-Filtered Availability

Every tool gets a frozenset tag at registration:

```python
registry.register("dock_against_target", dock_against_target, frozenset({"simulation"}))
registry.register("compute_training_metrics", compute_training_metrics, frozenset({"training"}))
registry.register("record_finding", record_finding, None)  # universal -- always available
```

When the Researcher executes an experiment, it only sees tools that match the detected domain's `tool_tags`. A training science investigation never sees docking tools. A molecular investigation never sees training metrics. Investigation control tools (propose_hypothesis, record_finding, etc.) have no tags and are always available.

### Frontend: Dynamic Everything

The frontend went from hardcoded columns to data-driven rendering:

- **CandidateTable**: Score columns come from `DomainDisplayConfig.score_columns`, not constants. Each column knows its label, format, threshold, and whether higher is better.
- **CandidateDetail**: Routes to `MolecularDetail` (2D/3D/descriptors) when `identifier_type === "smiles"`, or `GenericDetail` (score/attribute cards) otherwise.
- **Visualization**: Unified `VisualizationPanel` renders all visualizations inline. LiveLabViewer auto-appears when molecular tool events are detected in the SSE stream. Chart visualizations render from `VisualizationRendered` events. No static configuration needed.
- **Template cards**: Each template carries a domain badge. Users see molecular, training, and nutrition templates on the home page.

The `DomainDetected` SSE event sends the full display config to the frontend early in the investigation, before any results arrive.

### Prompts: Builder Functions Replace Static Constants

Static prompt strings became builder functions that accept a `DomainConfig`:

```python
# Before
DIRECTOR_FORMULATION_PROMPT = "You are investigating molecules..."

# After
def build_formulation_prompt(config: DomainConfig) -> str:
    # Uses config.director_examples, config.hypothesis_types, etc.
```

The Director gets domain-appropriate multishot examples. The Researcher gets domain-appropriate tool guidance. The synthesis prompt knows what scores to ask for. All driven by the same `DomainConfig`.

## What We Learned

### 1. Generic entities are simpler than specific ones

`scores: dict[str, float]` is both more flexible and easier to serialize than four named float fields. The "Candidate" concept -- something ranked by multiple criteria -- is universal. The specific criteria are configuration.

### 2. Configuration beats conditionals

Adding a domain should not require touching existing code paths. `DomainConfig` is a single file that defines everything. No if/else branches in the orchestrator, no switch statements in the frontend. The system reads the config and adapts.

### 3. Tool tagging is the right abstraction

We considered: separate registries per domain, tool namespacing, dynamic tool loading. All too complex. A frozenset tag on each tool, combined with set intersection at query time, is simple, testable, and fast.

### 4. The scientific method is the product

Chemistry tools are impressive. Training and nutrition science tools prove a point. But the real value is the hypothesis-driven loop: formulate with predictions and criteria, test against pre-defined thresholds, evaluate objectively, revise or reject. That loop works for any domain where evidence can be gathered and weighed.

### 5. Frontend abstractions pay for themselves immediately

Converting the CandidateTable from 4 hardcoded columns to dynamic `score_columns` took effort. But the training science domain rendered correctly on the first try -- zero frontend work needed for new domains.

### 6. Tests as refactoring insurance

274 server tests caught every breaking change during the entity generalization. The refactor touched 30+ files across backend and frontend. Not a single silent regression.

## The Horizon

### Near-Term Domains (Weeks)

Domains that could be added with just tools + config, no engine changes:

- **Genomics** -- Gene expression analysis, pathway enrichment, variant interpretation. Tools: search gene databases (NCBI Gene, Ensembl), compute expression metrics, compare pathways.
- **Materials Science** -- Property prediction, crystal structure search, phase diagram analysis. Tools: search materials databases (Materials Project), compute material properties, compare compositions.
- **Environmental Science** -- Ecosystem assessment, biodiversity metrics, climate impact analysis. Tools: search ecological databases, compute impact scores, compare interventions.

### Medium-Term Evolution (Months)

- **Cross-domain investigations** -- "Find compounds that improve both athletic recovery AND reduce inflammation" would use tools from molecular + training + nutrition domains simultaneously.
- **Domain-specific validation** -- Each domain could define its own validation methodology in the DomainConfig (the scientific methodology research is already done for molecular; same treatment for other domains).
- **Custom domain builder** -- A UI where researchers define their own DomainConfig: name their scores, pick their tools, write their prompt examples. No code required.

### Long-Term Vision

The engine becomes a general-purpose scientific reasoning framework. The domains are plugins. Ehrlich is a scientific discovery engine that currently ships with three domains (Molecular Science, Training Science, Nutrition Science). The architecture supports any number.

## Architecture Summary

```
DomainConfig (frozen dataclass)
    ├── tool_tags → ToolRegistry.list_schemas_for_domain()
    ├── score_definitions → CandidateTable dynamic columns
    ├── director_examples → build_formulation_prompt()
    ├── experiment_examples → build_experiment_prompt()
    ├── synthesis_scoring_instructions → build_synthesis_prompt()
    ├── hypothesis_types → HypothesisType validation
    └── valid_domain_categories → DomainRegistry.detect()

DomainRegistry
    ├── register(config) → stores config + builds category map
    ├── detect(classified_category) → returns matching DomainConfig
    └── all_template_prompts() → aggregates across all domains

SSE Pipeline
    classify prompt → detect domain → emit DomainDetected event
    → frontend receives display config → renders domain-appropriate UI
```
