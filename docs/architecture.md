# Ehrlich Architecture

## Overview

Ehrlich follows Domain-Driven Design (DDD) with Clean Architecture principles adapted for Python.

## Bounded Contexts

### Kernel (Shared)
Shared domain primitives used across all contexts: SMILES/InChIKey/MolBlock type aliases, Molecule value object, domain exception hierarchy.

### Literature
Searches and manages scientific references. Integrates with Semantic Scholar and PubMed APIs.

### Chemistry
Cheminformatics operations: molecular descriptors, fingerprints, 3D conformer generation, substructure matching, and 2D SVG depiction. All RDKit usage is isolated in the infrastructure adapter (`rdkit_adapter.py`).

### Analysis
Dataset exploration and statistical analysis. Loads bioactivity data from ChEMBL, compound search via PubChem, curated pharmacology via GtoPdb, substructure enrichment analysis, property distributions.

### Prediction
Machine learning for antimicrobial activity prediction. Supports Chemprop (D-MPNN) and XGBoost models with Morgan fingerprints. Ensemble predictions combine multiple models.

### Simulation
Molecular simulation and target discovery: docking (AutoDock Vina/RDKit fallback), ADMET prediction, resistance assessment, protein targets (RCSB PDB), protein annotations (UniProt), disease-target associations (Open Targets), environmental toxicity (EPA CompTox).

### Sports
Sports science research: evidence-based training analysis, protocol comparison, injury risk assessment, training load monitoring, and supplement evidence search. Uses Semantic Scholar for literature search.

### Investigation
Hypothesis-driven agent orchestration. Manages the Claude-driven research loop: literature survey, hypothesis formulation (with predictions, criteria, scope), parallel experiment execution, criteria-based evaluation, negative controls, and synthesis. Uses multi-model architecture (Director/Researcher/Summarizer) with user-guided steering, domain classification, and multi-investigation memory. Includes domain configuration system (`DomainConfig` + `DomainRegistry`) for pluggable scientific domains with tool tagging, score definitions, prompt adaptation, and visualization control.

## Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Formulates hypotheses, evaluates evidence, synthesizes (3-5 calls)
    │                       NO tool access, structured JSON responses only
    │
    ├── Sonnet 4.5 (Researcher) -- Executes experiments with 37 domain-filtered tools (10-20 calls, parallel x2)
    │                               Tool-calling loop with max_iterations_per_experiment guard
    │
    └── Haiku 4.5 (Summarizer)  -- Compresses large tool outputs >2000 chars, PICO+classification, evidence grading
                                    Reduces context bloat, preserves key scientific data
```

**Cost**: ~$3-4 per investigation (vs ~$11 with all-Opus).

### Flow (Hypothesis-Driven)

1. **Classification & PICO** -- Haiku decomposes prompt into PICO framework (Population, Intervention, Comparison, Outcome) and classifies domain in a single call
2. **Literature Survey** -- Sonnet researcher conducts structured search with domain-filtered tools, citation chasing (snowballing), evidence-level grading; Haiku grades body-of-evidence (GRADE-adapted) and self-assesses quality (AMSTAR-2-adapted)
3. **Hypothesis Formulation** -- Opus Director formulates 2-4 hypotheses with predictions, criteria, scope, Bayesian priors (grounded in Popper, Platt, Feynman, Bayesian frameworks -- see `docs/scientific-methodology.md`); receives structured XML literature context (PICO + graded findings)
4. **User Approval Gate** -- User approves/rejects hypotheses before testing begins (5-min auto-approve timeout)
5. **Experiment Design + Execution** -- Director designs structured experiment protocols (variables, controls, confounders, analysis plan, criteria), 2 Sonnet researchers execute in parallel per batch (max 10 tool calls each) with methodology guidance (sensitivity, applicability domain, uncertainty, verification, negative results)
6. **Hypothesis Evaluation** -- Director compares findings against both hypothesis-level and experiment-level criteria with methodology checks (control validation, confounders, analysis plan adherence)
7. **Negative Controls** -- Validate model with known-inactive compounds
8. **Synthesis** -- Director synthesizes final report with ranked candidates, citations, cost breakdown

## Persistence

Investigations are persisted to SQLite (WAL mode) via `aiosqlite`. The `SqliteInvestigationRepository` implements the `InvestigationRepository` ABC defined in the domain layer. Hypotheses, experiments, findings, candidates, negative controls, citations, domain, and cost data are JSON-serialized into a single `investigations` table. All SSE events are persisted to a separate `events` table for full timeline replay on page reload.

The API keeps `_active_investigations` and `_active_orchestrators` dicts for in-flight SSE streaming and user-guided steering (hypothesis approval). Persists to SQLite on completion (or error).

## Molecule Visualization

Ehrlich uses a hybrid approach for molecule rendering:

- **2D Depiction**: Server-side SVG via RDKit `rdMolDraw2D`. The `/api/v1/molecule/depict` endpoint returns `image/svg+xml` with 24h browser caching. The console uses `<img>` tags -- zero frontend complexity, browser handles caching.
- **3D Viewing**: Client-side 3Dmol.js (~2MB, MIT license) loaded via dynamic import for code splitting. Used for both `MolViewer3D` (conformer stick models) and `DockingViewer` (protein cartoon + ligand stick overlay).
- **Candidate Detail**: Expandable panel in `CandidateTable` fetches conformer + descriptors in parallel, displays 2D/3D views alongside a property card with Lipinski badge.

### Molecule API

| Endpoint | Returns | Cache |
|----------|---------|-------|
| `GET /molecule/depict?smiles=&w=&h=` | SVG (`image/svg+xml`) | 24h `Cache-Control` |
| `GET /molecule/conformer?smiles=` | JSON `{mol_block, energy, num_atoms}` | None |
| `GET /molecule/descriptors?smiles=` | JSON descriptors + `passes_lipinski` | None |
| `GET /targets` | JSON list of `{pdb_id, name, organism}` | None |

Invalid SMILES on `/depict` returns a dark error SVG (200 status). Invalid SMILES on `/conformer` or `/descriptors` returns 400.

## Visual Identity — "Lab Protocol"

Dark-only theme mixing Industrial Scientific + Editorial Academic + Cyberpunk Lab aesthetics.

### Design Tokens (OKLCH)

| Token | Value | Purpose |
|-------|-------|---------|
| background | `oklch(0.10 0.005 155)` | Deep black with green micro-tint |
| surface | `oklch(0.14 0.008 155)` | Raised cards, panels |
| foreground | `oklch(0.93 0.005 155)` | Primary text |
| primary | `oklch(0.72 0.19 155)` | Molecular Green — CTAs, active states |
| secondary | `oklch(0.55 0.10 200)` | Teal — completed states |
| accent | `oklch(0.75 0.15 80)` | Amber — director events |
| muted | `oklch(0.18 0.005 155)` | Muted backgrounds |
| border | `oklch(0.22 0.01 155)` | Subtle borders |
| destructive | `oklch(0.60 0.22 25)` | Error red |

### Typography

- **Display/Body**: Space Grotesk (400, 500, 600, 700) — geometric, scientific
- **Data/Code/Labels**: JetBrains Mono (400, 500) — SMILES, costs, tool names, IDs
- Labels use monospace uppercase with wide tracking (0.08em)

### Signature Elements

1. **Molecular bond phase progress** — Nodes connected by lines (not bars). Active node pulses green.
2. **Terminal-style timeline** — Monospace tool names, green-tinted findings, amber director events.
3. **Section headers** — Monospace uppercase with left green border accent (`border-l-2 border-primary`).
4. **Green glow pulse** — Running states emit soft green `box-shadow` animation.

### Anti-Patterns (Deliberately Avoided)

- No purple/indigo — molecular green is the identity color
- No Inter/Roboto — Space Grotesk for display, JetBrains Mono for data
- No light mode — dark-only, scientific instrument aesthetic
- No centered hero — left-aligned, utilitarian layout
- No blur shadows — hard borders or glow effects only
- No gradient blobs or decorative elements

## Dependency Rules

```
domain/ -> ZERO external deps (pure Python)
application/ -> domain/ interfaces only
infrastructure/ -> implements domain/ ABCs
tools.py -> calls application/ services
api/ -> investigation/application/ only
```

## Data Flow

### Multi-Model (Default)

1. User submits research prompt via Console (or selects a template)
2. API creates Investigation, persists to SQLite, starts MultiModelOrchestrator
3. **Haiku** decomposes prompt via PICO framework (Population, Intervention, Comparison, Outcome) and classifies domain in a single call; queries past completed investigations in same domain
4. **Domain detection** -- `DomainRegistry.detect()` selects `DomainConfig` (molecular/sports), emits `DomainDetected` SSE event with display config; researcher tool list filtered to domain-relevant tools
5. **Researcher** (Sonnet) conducts structured literature survey with domain-filtered tools, citation chasing, evidence-level grading; **Haiku** grades body-of-evidence (GRADE-adapted) and self-assesses quality (AMSTAR-2); emits `LiteratureSurveyCompleted` event
6. **Director** (Opus) formulates 2-4 hypotheses with predictions, criteria, scope, Bayesian priors; receives structured XML literature context (PICO + graded findings)
7. **User Approval Gate** -- user approves/rejects hypotheses (5-min timeout auto-approves)
8. For each batch of 2 hypotheses:
   a. **Director** designs experiment protocol (description, tool plan, variables, controls, confounders, analysis plan, criteria)
   b. **2 Researchers** (Sonnet) execute in parallel via asyncio.Queue
   c. **Summarizer** (Haiku) compresses outputs exceeding threshold
   d. **Director** evaluates hypothesis against pre-defined success/failure criteria
   e. If revised: new hypothesis spawned with parent link
9. **Negative controls** recorded from formulation suggestions
10. **Director** synthesizes final report with candidates, citations, cost
11. All events stream via SSE (17 event types) to Console in real-time
    - `DomainDetected` sends display config (score columns, visualization type) to frontend
    - `FindingRecorded` includes evidence + source provenance (source_type, source_id) + evidence_level (1-6)
    - `LiteratureSurveyCompleted` carries PICO, search stats, evidence grade, self-assessment
    - `PhaseChanged` tracks 6-step progress
    - `CostUpdate` streams progressive cost snapshots
    - `HypothesisApprovalRequested` pauses for user steering
    - `InvestigationCompleted` includes candidates, hypotheses, findings, negative controls
12. Investigation persisted to SQLite with full state + events for timeline replay
13. Console displays: phase indicator, hypothesis board, lab view (3Dmol.js, molecular only), investigation diagram (React Flow), findings with source badges, dynamic candidate table with domain-specific score columns, structured 8-section report with markdown export
