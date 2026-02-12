# Ehrlich Data

## Directory Structure

```
data/
├── proteins/          # PDBQT files for docking targets
├── references/        # Curated reference papers
├── datasets/          # Downloaded datasets (gitignored)
└── scripts/           # Data preparation scripts
```

## Data Preparation

### Prerequisites

- Python 3.12 with uv
- Internet connection for downloads

### Download ChEMBL Data

```bash
cd server
uv run python ../data/scripts/prepare_data.py --chembl
```

### Download Protein Structures

```bash
uv run python ../data/scripts/prepare_data.py --proteins
```

### Datasets

Datasets are downloaded on-demand and cached in `data/datasets/` (gitignored).

**ChEMBL**: Bioactivity data for any target organism/assay type (MIC, IC50, Ki, EC50, Kd)

## Core References

`references/core_references.json` contains curated papers on antimicrobial discovery,
resistance mechanisms, and computational drug design.
