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
Dataset exploration and statistical analysis. Loads bioactivity data from ChEMBL, performs substructure enrichment analysis, computes property distributions.

### Prediction
Machine learning for antimicrobial activity prediction. Supports Chemprop (D-MPNN) and XGBoost models with Morgan fingerprints. Ensemble predictions combine multiple models.

### Simulation
Molecular simulation: docking (AutoDock Vina), ADMET prediction (pkCSM), and resistance mutation assessment.

### Investigation
Agent orchestration. Manages the Claude-driven research loop: receives a research question, systematically calls tools across all contexts, records findings, and produces a ranked list of candidates. Supports two modes: single-model (Orchestrator) and multi-model (MultiModelOrchestrator).

## Multi-Model Architecture

Ehrlich uses a three-tier Claude model architecture for cost-efficient investigations:

```
Opus 4.6 (Director)     -- Plans phases, reviews results, synthesizes report (3-5 calls)
    │                       NO tool access, structured JSON responses only
    │
    ├── Sonnet 4.5 (Researcher) -- Executes each phase with 19 tools (10-20 calls)
    │                               Tool-calling loop with max_iterations_per_phase guard
    │
    └── Haiku 4.5 (Summarizer)  -- Compresses large tool outputs >2000 chars (5-10 calls)
                                    Reduces context bloat, preserves key scientific data
```

**Cost**: ~$3-4 per investigation (vs ~$11 with all-Opus).

### Flow

1. **Director plans** -- Opus receives the research prompt and outputs a JSON plan with phases, goals, and key questions
2. **Researcher executes** -- For each phase, Sonnet runs a tool-calling loop (max 10 iterations per phase). Large outputs are compressed by Haiku before appending to conversation
3. **Director reviews** -- After each phase, Opus reviews findings and decides whether to proceed or stop early
4. **Director synthesizes** -- After all phases, Opus produces the final report with summary, ranked candidates, and citations

### Fallback

When `EHRLICH_ANTHROPIC_MODEL` is set (or researcher == director model), the system falls back to the single-model `Orchestrator` which uses one model for everything.

## Persistence

Investigations are persisted to SQLite (WAL mode) via `aiosqlite`. The `SqliteInvestigationRepository` implements the `InvestigationRepository` ABC defined in the domain layer. Findings, candidates, citations, and cost data are JSON-serialized into a single `investigations` table.

The API keeps an in-memory `_active_investigations` dict for in-flight SSE streaming, and persists to SQLite on completion (or error).

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

1. User submits research prompt via Console
2. API creates Investigation, persists to SQLite, starts MultiModelOrchestrator
3. **Director** (Opus) plans phases and goals as structured JSON
4. For each phase:
   a. **Researcher** (Sonnet) executes tool-calling loop with 19 tools
   b. **Summarizer** (Haiku) compresses outputs exceeding threshold
   c. **Director** (Opus) reviews phase results, decides whether to proceed
5. **Director** (Opus) synthesizes final report with candidates and citations
6. All events stream via SSE (10 event types) to Console in real-time
7. Investigation persisted to SQLite with findings, candidates, and cost breakdown
8. Console displays report, candidates, phase progress, and cost

### Single-Model (Fallback)

1. User submits research prompt via Console
2. API creates Investigation, persists to SQLite, starts Orchestrator
3. Single Claude model reasons and calls tools across all phases
4. Results stream back via SSE to Console
5. Final report with ranked candidates displayed
