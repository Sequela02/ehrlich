# Ehrlich Architecture

## Overview

Ehrlich follows Domain-Driven Design (DDD) with Clean Architecture principles adapted for Python.

## Bounded Contexts

### Kernel (Shared)
Shared domain primitives used across all contexts: SMILES/InChIKey/MolBlock type aliases, Molecule value object, domain exception hierarchy.

### Literature
Searches and manages scientific references. Integrates with Semantic Scholar and PubMed APIs.

### Chemistry
Cheminformatics operations: molecular descriptors, fingerprints, 3D conformer generation, substructure matching. All RDKit usage is isolated in the infrastructure adapter.

### Analysis
Dataset exploration and statistical analysis. Loads bioactivity data from ChEMBL, performs substructure enrichment analysis, computes property distributions.

### Prediction
Machine learning for antimicrobial activity prediction. Supports Chemprop (D-MPNN) and XGBoost models with Morgan fingerprints. Ensemble predictions combine multiple models.

### Simulation
Molecular simulation: docking (AutoDock Vina), ADMET prediction (pkCSM), and resistance mutation assessment.

### Investigation
Agent orchestration. Manages the Claude-driven research loop: receives a research question, systematically calls tools across all contexts, records findings, and produces a ranked list of candidates.

## Dependency Rules

```
domain/ -> ZERO external deps (pure Python)
application/ -> domain/ interfaces only
infrastructure/ -> implements domain/ ABCs
tools.py -> calls application/ services
api/ -> investigation/application/ only
```

## Data Flow

1. User submits research prompt via Console
2. API creates Investigation, starts Orchestrator
3. Orchestrator calls Claude with scientist persona + tool definitions
4. Claude reasons and calls tools (literature, chemistry, analysis, prediction, simulation)
5. Tools call application services, which use infrastructure adapters
6. Results stream back via SSE to Console
7. Final report with ranked candidates displayed
