# Antimicrobial ML — Prior Work and Approaches

## Paul Ehrlich's "Magic Bullet" (1907)

Paul Ehrlich (1854-1915), German Nobel laureate. Coined "magic bullet" (Zauberkugel): a compound that selectively kills a pathogen without harming the host. Created Salvarsan (Compound 606) in 1909 — first rationally designed antimicrobial drug. Tested 606 arsenic compounds manually. Our project is the computational evolution: screen 107M+ molecules computationally. Same goal.

## Halicin (2020) — MIT

**Paper:** Stokes et al., "A Deep Learning Approach to Antibiotic Discovery," Cell, Feb 2020.

- **Model:** D-MPNN (Directed Message Passing Neural Network) via Chemprop library
- **Training:** 2,335 molecules screened for E. coli growth inhibition
- **Screening:** Drug Repurposing Hub (~6K compounds) + ZINC15 (107M molecules)
- **Result:** Discovered halicin (originally SU3327, diabetes drug candidate)
  - Broad-spectrum: M. tuberculosis, carbapenem-resistant Enterobacteriaceae, C. difficile, pan-resistant A. baumannii
  - Mechanism: disrupts electrochemical gradient across bacterial membranes
  - Structurally divergent from ALL known antibiotic classes
- **Hit rate:** 51.5% true positive for top 99 ranked molecules
- **From ZINC15:** 8 additional novel antibacterials from 23 tested predictions

## Abaucin (2023) — MIT

**Paper:** Liu et al., Nature Chemical Biology, May 2023.

- **Model:** GNN ensemble (D-MPNN lineage)
- **Training:** ~7,500 molecules screened for A. baumannii growth inhibition
- **Result:** Discovered abaucin — narrow-spectrum, targets only A. baumannii
  - Mechanism: perturbs lipoprotein trafficking via LolE
  - Validated in mouse wound infection model
  - Narrow spectrum is a feature: reduces microbiome damage, slows resistance

## Other Notable Discoveries

| Discovery | Year | Method |
|-----------|------|--------|
| Encrypted peptides from paleoproteome mining | 2024 | ML + ancient human proteins, 59% hit rate |
| Aldoxorubicin & Quarfloxin (anti-TB) | 2025 | ML + DL virtual screening of 11,576 DrugBank compounds |
| LLM-based antimicrobial peptides | 2024-2025 | LLMs as generative models |
| PolyCLOVER | 2025-2026 | Multi-stage self-supervised + active learning |

## Molecular Representations

| Representation | Description | Use Case |
|----------------|-------------|----------|
| **Morgan/ECFP** (radius=2, 2048-bit) | Circular fingerprints, local chemical environments | Most widely used baseline for virtual screening |
| **MACCS Keys** (166-bit) | Predefined structural fragment queries | Simple, interpretable, good baseline |
| **RDKit Descriptors** (~200) | Physicochemical (MW, LogP, TPSA, HBD/HBA) | Drug-likeness, QSAR models |
| **D-MPNN (Chemprop)** | Learned graph neural network representations | State-of-the-art (Halicin, Abaucin) |
| **Combined** | MACCS + ECFP + molecular graphs | Outperform single-representation |

**Practical:** Morgan/ECFP is the standard baseline. D-MPNN is state-of-the-art but harder to set up.

## ML Models

| Model | Notes |
|-------|-------|
| **Random Forest** | Strong baseline, handles high-dim fingerprints, accuracy 0.89-1.00 |
| **XGBoost / LightGBM** | Top traditional ML, best on tabular fingerprint data |
| **D-MPNN / GNN** | State-of-the-art, learns from molecular graphs (Halicin, Abaucin) |
| **SVM** | Good with fingerprints, interpretable |

Ensemble methods (RF, XGBoost) provide >80% accuracy baselines. D-MPNNs are current gold standard.

## What Makes a Good Antimicrobial Candidate

**Activity:**
- MIC <= 25 uM for pure compounds (standard selection criterion)
- pChEMBL >= 5 (equivalent to <= 10 uM, common binary threshold)

**Structural features favoring activity:**
- Long carbon chains (membrane interaction)
- Charged ammonium groups (electrostatic with bacterial membranes)
- Low dipole moment
- Appropriate LogP (balanced hydrophilicity/lipophilicity)
- Structural novelty (reduces cross-resistance)

**Drug-likeness:**
- Lipinski's Rule of 5: MW < 500, LogP < 5, HBD <= 5, HBA <= 10
- QED score > 0.67 = drug-like
- Acceptable ADMET profile
- Selectivity index (therapeutic window between antimicrobial and mammalian toxicity)

## Key Takeaways for Our Project

1. D-MPNN (Chemprop) discovered both Halicin and Abaucin — proven architecture
2. Training data matters more than model choice — 2,335 molecules sufficed for Halicin
3. Morgan fingerprints + RF/XGBoost are strong baselines before deep learning
4. ChEMBL is primary data source; ZINC is screening library
5. MIC <= 25 uM is standard hit threshold
6. Narrow-spectrum activity increasingly valued over broad-spectrum

## Sources

- Stokes et al., Cell 2020: https://www.cell.com/cell/fulltext/S0092-8674(20)30102-1
- Liu et al., Nature Chem Bio 2023: https://www.nature.com/articles/s41589-023-01349-8
- Chemprop: https://github.com/chemprop/chemprop
