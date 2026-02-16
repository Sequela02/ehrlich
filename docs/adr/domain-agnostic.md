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

### 5. ML capabilities should be domain-agnostic too

The prediction pipeline was originally hardwired to molecular science (SMILES fingerprints, scaffold splits, Butina clustering). But model training, prediction, and clustering are generic operations on feature matrices. The refactor introduced domain ports (`FeatureExtractor`, `DataSplitter`, `Clusterer` ABCs) with molecular adapters preserving exact behavior and generic adapters (random split, Ward hierarchical clustering) enabling any domain. Three new generic tools (`train_classifier`, `predict_scores`, `cluster_data`) accept flat feature matrices -- training and nutrition science can now train XGBoost models on their own data without molecular dependencies.

### 6. Frontend abstractions pay for themselves immediately

Converting the CandidateTable from 4 hardcoded columns to dynamic `score_columns` took effort. But the training science domain rendered correctly on the first try -- zero frontend work needed for new domains.

### 7. Tests as refactoring insurance

274 server tests caught every breaking change during the entity generalization. The refactor touched 30+ files across backend and frontend. Not a single silent regression.

## The Horizon

### Next Domain: Impact Evaluation (In Planning)

The fourth domain proves the architecture handles non-scientific domains too. **Impact Evaluation** applies the same hypothesis-driven loop to social program analysis:

- "Does the Sonora sports scholarship improve athlete competition performance?" → DiD + PSM
- "Is the conditional cash transfer reducing school dropout rates?" → RDD
- "Compare cost-effectiveness of state sports programs" → Synthetic Control + benchmarking

**Why it matters:** Of 2,800 evaluations commissioned by CONEVAL in Mexico, only 11 are impact evaluations (0.4%). No existing platform combines autonomous hypothesis formulation, automated causal inference, public API integration, and evidence-graded reporting. Ehrlich fills this gap.

**What's new:** Document/CSV upload (user-provided program data), causal inference tools (DiD, PSM, RDD, synthetic control), Mexico + US public data API clients (INEGI, Census, World Bank, FRED), evaluation report templates (CONEVAL ECR, WWC-compliant). See `impact-evaluation-domain.md` for full design.

**What stays the same:** The DomainConfig, tool tagging, multi-model orchestration, hypothesis framework, evidence grading, and visualization pipeline are all reused. Zero changes to existing code paths.

### Other Planned Domains

- **Competitive Sports** -- game statistics, player performance, team analysis
- **Genomics** -- gene expression, pathway enrichment, variant interpretation
- **Materials Science** -- property prediction, crystal structure search
- **Environmental Science** -- ecosystem assessment, biodiversity metrics

### Medium-Term Evolution (Months)

- **Cross-domain investigations** -- "Find compounds that improve both athletic recovery AND reduce inflammation" would use tools from molecular + training + nutrition domains simultaneously. Already works via `merge_domain_configs()`.
- **Impact + Training + Nutrition** -- "Evaluate the Sonora sports program: athlete performance, nutrition support, and cost-effectiveness" triggers all three domains.
- **Custom domain builder** -- A UI where researchers define their own DomainConfig: name their scores, pick their tools, write their prompt examples. No code required.
- **MCP bridge self-service** -- Users register their own data sources (e.g., CODESON internal database, Colombian education ministry) as MCP servers.

### Long-Term Vision

The engine becomes a general-purpose scientific reasoning framework. The domains are plugins. Ehrlich is a scientific discovery engine that currently ships with three domains (Molecular Science, Training Science, Nutrition Science) with a fourth (Impact Evaluation) in planning. The architecture supports any number.

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
