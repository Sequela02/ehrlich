# Ehrlich Research

Pre-development research that informed the architecture and scientific methodology of the Ehrlich discovery engine. Organized by category.

## Platform

Architecture and infrastructure decisions made before and during initial development.

| File | Topic |
|------|-------|
| [mcp-server.md](platform/mcp-server.md) | MCP protocol research (explored, not pursued -- Ehrlich is an MCP consumer, not provider) |
| [agent-patterns.md](platform/agent-patterns.md) | Claude agent loop, scientist persona, streaming |
| [literature-api.md](platform/literature-api.md) | Semantic Scholar / PubMed APIs, citation model, reliability |

## Methodology

Scientific methodology research (phases 2-6). Each file contains verified sources, implementation notes, and design rationale. See [scientific-methodology.md](../scientific-methodology.md) for the implemented specification.

| File | Phase | Sources |
|------|-------|---------|
| [literature-survey.md](methodology/literature-survey.md) | Phase 2: Literature Survey | PRISMA, Cochrane, PICO, snowballing |
| [experiment-design.md](methodology/experiment-design.md) | Phase 3: Experiment Design | Fisher, Platt, Cohen, OECD QSAR |
| [evidence-evaluation.md](methodology/evidence-evaluation.md) | Phase 4: Evidence Evaluation | GRADE, Bayesian updating, effect sizes |
| [negative-controls.md](methodology/negative-controls.md) | Phase 5: Negative Controls | Z'-factor, DUD-E, BEDROC, Y-scrambling |
| [synthesis.md](methodology/synthesis.md) | Phase 6: Synthesis | GRADE certainty, PRISMA, desirability functions |

## Molecular

Domain-specific research for the Molecular Science domain (antimicrobial resistance, drug discovery).

| File | Topic |
|------|-------|
| [antimicrobial-ml.md](molecular/antimicrobial-ml.md) | Prior work (Halicin, Abaucin), ML models, representations |
| [cheminformatics-rdkit.md](molecular/cheminformatics-rdkit.md) | SMILES, RDKit, 3Dmol.js, molecular visualization |
| [data-sources.md](molecular/data-sources.md) | ChEMBL, Tox21, ZINC, data pipeline |
| [amr-crisis.md](molecular/amr-crisis.md) | AMR crisis, market failure, global potential |
| [simulation-docking-admet.md](molecular/simulation-docking-admet.md) | Molecular docking (Vina), ADMET prediction, mutant docking |
