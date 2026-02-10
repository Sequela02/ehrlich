# Ehrlich Research Index

Pre-hackathon research for the AI Antimicrobial Discovery Agent.

## Research Files

| # | File | Topic | Status |
|---|------|-------|--------|
| 01 | [mcp-server.md](01-mcp-server.md) | MCP protocol, Python server, tool design | Done |
| 02 | [agent-patterns.md](02-agent-patterns.md) | Claude agent loop, scientist persona, streaming | Done |
| 03 | [antimicrobial-ml.md](03-antimicrobial-ml.md) | Prior work (Halicin, Abaucin), models, representations | Done |
| 04 | [cheminformatics-rdkit.md](04-cheminformatics-rdkit.md) | SMILES, RDKit Python, RDKit.js, 3Dmol.js, visualization | Done |
| 05 | [data-sources.md](05-data-sources.md) | ChEMBL, Tox21, ZINC, data pipeline | Done |
| 06 | [amr-crisis-and-potential.md](06-amr-crisis-and-potential.md) | AMR crisis, market failure, global potential | Done |
| 07 | [literature-search.md](07-literature-search.md) | Semantic Scholar/PubMed APIs, citation model, reliability | Done |
| 08 | [simulation-docking-admet.md](08-simulation-docking-admet.md) | Molecular docking (Vina), ADMET prediction, mutant docking | Done |

## Key Decisions from Research

### Architecture
- **MCP Server:** FastMCP (Python SDK) with `@mcp.tool()` decorators
- **Agent Loop:** Raw Claude API (`anthropic` Python SDK) — manual agentic loop (while/stop_reason pattern). Chosen over Agent SDK for: pure Python runtime (no Node.js dependency), direct SSE control for React frontend, transparent debugging, and full control over tool dispatch. Agent SDK (v0.1.33) was evaluated but rejected due to Node.js subprocess architecture, opaque loop control, and pre-1.0 instability.
- **Literature Search:** Semantic Scholar API (free, no auth needed for basic) / PubMed E-utilities (free)
- **Frontend-Backend:** SSE streaming from Python orchestrator to React console
- **Molecular Docking:** AutoDock Vina (free, seconds per molecule) + Meeko for ligand prep
- **ADMET Prediction:** pkCSM / SwissADME / ADMETlab 2.0 (all free APIs)
- **Protein Structures:** PDB / AlphaFold DB (free download)
- **No Java** — entire project is Python (server) + TypeScript (console)
- **Team:** Solo (Ricardo Armenta / Sequel)

### Hybrid Analysis Approach
Claude uses the right tool for each question:
- **Statistical analysis (Python):** substructure enrichment, property distributions, chi-squared tests. Finds verifiable patterns in existing data.
- **ML modeling (ensemble):** Two models ensembled for robustness:
  1. **Chemprop v2.2.2 (D-MPNN):** State-of-the-art graph neural network — same architecture that discovered Halicin and Abaucin. ~30-60 min training on CPU for 15-20K molecules. Python-first API via PyTorch Lightning.
  2. **XGBoost on Morgan fingerprints** (radius=2, 2048-bit): Strong classical baseline, trains in ~30 seconds. Captures different molecular features than D-MPNN.
  3. **Ensemble:** Simple probability average (`0.5 * chemprop + 0.5 * xgboost`). Safety net if one model produces garbage; captures complementary molecular representations.
- **Validation:** ML predictions verified by non-ML checks (known antibiotic controls, chemistry sanity checks).
- **Activity threshold:** pChEMBL >= 5 (equivalent to MIC <= 10 uM) for binary classification
- **Toxicity filter:** Tox21 12-endpoint panel, cross-referenced via InChIKey

### Data
- **ChEMBL:** ~15-20K usable S. aureus pairs, ~10-15K E. coli pairs after filtering
- **Tox21:** ~8K compounds with 12 toxicity endpoints
- **Overlap:** ~500-2,000 compounds with both antimicrobial + toxicity data
- **Pre-processed option:** Ersilia `antimicrobial-ml-tasks` repo

### Simulation
- **Molecular Docking:** AutoDock Vina docks candidate against bacterial protein target, returns binding energy (kcal/mol) + 3D pose
- **ADMET Prediction:** pkCSM/SwissADME APIs predict pharmacokinetics (absorption, BBB, CYP450, hepatotoxicity, hERG). Fallback to RDKit descriptors.
- **Mutant Docking:** Dock against mutated proteins to assess resistance vulnerability (energy change > 2.0 kcal/mol = HIGH risk)
- **Key MRSA Targets:** PBP2a (1VQQ), DHPS (1AD4), DNA Gyrase (2XCT), MurA (1UAE), NDM-1 (3SPU)
- **Setup:** ~1 day total. Per-molecule: ~30-60 seconds for full pipeline (dock + ADMET + mutant dock)

### Visualization
- **2D:** RDKit.js (WASM, 8MB) — SVG rendering, substructure highlighting
- **3D:** 3Dmol.js (WebGL) — requires MOL block from backend (can't parse SMILES)
- **Pipeline:** Backend generates 3D coords via `AllChem.EmbedMolecule` -> sends MOL block -> 3Dmol.js renders

### Cost
- ~$0.13 per 5-iteration agent run on Sonnet 4.5
- ~$0.11 with prompt caching

## Resolved Decisions (Feb 10, 2026 — Kickoff Day)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Agent SDK vs Raw API | **Raw Claude API** (`anthropic` Python SDK) | Pure Python, direct SSE control, transparent debugging, no Node.js subprocess. ~55 lines for full agent loop. |
| Chemprop vs XGBoost | **Both (ensemble)** | Chemprop D-MPNN is state-of-the-art (Halicin/Abaucin architecture). XGBoost is fast and captures different features. Ensemble averages both for robustness. |
| Solo vs teammate | **Solo** | Ricardo Armenta / Sequel. |

## Reliability Model
Three layers ensure scientific grounding:
1. **Live literature search** — Semantic Scholar/PubMed APIs return real papers with DOIs. Claude reads actual abstracts, not training memory. Every claim gets a citation.
2. **Pre-loaded references** — Curated key papers (Halicin, Abaucin, WHO BPPL 2024). Verified, structured, always available.
3. **Data grounding** — Statistical analysis and ML are trained on real ChEMBL experimental data (actual MIC values from actual labs). Claude's reasoning interprets data, not memory.
