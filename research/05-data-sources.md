# Data Sources — ChEMBL, Tox21, ZINC

## ChEMBL

### Access Methods
1. **Python client** (recommended): `pip install chembl-webresource-client`
2. **REST API:** `https://www.ebi.ac.uk/chembl/api/data/`
3. **Bulk download (fastest for large queries):** SQLite/PostgreSQL dumps from FTP

### Key Fields
- `molecule_chembl_id` — unique compound ID
- `canonical_smiles` — SMILES string
- `standard_type` — MIC, IC50, EC50, Ki
- `standard_value` — numeric activity value
- `standard_units` — nM or ug/mL
- `pchembl_value` — standardized -log(molar), comparable across types
- `target_organism` — species name

### Filtering for Antimicrobial Data

```python
from chembl_webresource_client.new_client import new_client

activity = new_client.activity
sa_mic = activity.filter(
    target_organism="Staphylococcus aureus",
    standard_type="MIC",
    standard_relation="=",
).only([
    "molecule_chembl_id", "canonical_smiles",
    "standard_value", "standard_units", "pchembl_value"
])
```

For MRSA: filter `assay_description` containing "MRSA" or "methicillin-resistant" (ChEMBL stores species as "Staphylococcus aureus" regardless of strain).

### Target Organisms
- *Staphylococcus aureus* (MRSA)
- *Escherichia coli*
- *Pseudomonas aeruginosa*
- *Klebsiella pneumoniae*
- *Acinetobacter baumannii*
- *Mycobacterium tuberculosis*

### Dataset Sizes (after filtering and dedup)
- S. aureus: ~15,000-20,000 usable pairs
- E. coli: ~10,000-15,000 usable pairs
- Combined multi-organism: ~40,000-50,000 usable pairs
- Total ChEMBL: 5.4M bioactivities, 1M+ compounds

## Tox21

### Access
- **DeepChem (easiest):** `dc.molnet.load_tox21(featurizer='ECFP')`
- **Direct CSV:** `https://github.com/deepchem/deepchem/blob/master/datasets/tox21.csv.gz`
- **Zenodo backup:** `https://zenodo.org/records/3540423`

### Specs
- ~8,000 compounds with SMILES
- 12 binary toxicity endpoints (0=inactive, 1=toxic, NaN=untested)

### The 12 Endpoints

**Nuclear Receptor Panel (7):**
NR-AR, NR-AR-LBD, NR-AhR, NR-Aromatase, NR-ER, NR-ER-LBD, NR-PPAR-gamma

**Stress Response Panel (5):**
SR-ARE, SR-ATAD5 (genotoxicity), SR-HSE, SR-MMP (mitochondrial), SR-p53

### Data Format
```csv
smiles, NR-AR, NR-AR-LBD, NR-AhR, ..., SR-p53, mol_id
CCOc1ccc2nc(S)n(...)c2c1, 0, 0, 1, ..., 0, TOX123
```

## Cross-Referencing ChEMBL + Tox21

Join on **InChIKey** (neither shares a common ID directly):

```python
from rdkit import Chem

def smiles_to_inchikey(smi):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None
    inchi = Chem.MolToInchi(mol)
    return Chem.InchiToInchiKey(inchi)

# Generate InChIKeys for both datasets, then pd.merge(on="inchikey")
```

Expected overlap: **500-2,000 compounds** with both antimicrobial + toxicity data.

## ZINC Database

Free database of commercially available compounds (UCSF).

| Version | Scale |
|---------|-------|
| ZINC15 | 230M compounds |
| ZINC20 | 1.4B compounds |
| ZINC22 | 37B+ make-on-demand |

**Use for:**
1. Validation: check if predicted compounds are purchasable
2. Virtual screening: score ZINC compounds with trained model
3. Negative/diverse set for training

## Pre-Processed Datasets

**Best option:** Ersilia `antimicrobial-ml-tasks` repo
- https://github.com/ersilia-os/antimicrobial-ml-tasks
- Pre-extracted ChEMBL antimicrobial datasets by pathogen

Also: DeepChem MoleculeNet (Tox21, HIV, BACE, BBBP, ClinTox)

## Data Pipeline Summary

```
ChEMBL (API/SQL)                    Tox21 (DeepChem/CSV)
       |                                    |
  Filter by organism,                  Load SMILES +
  standard_type, relation             12 toxicity labels
       |                                    |
  Standardize, dedup,               Generate InChIKeys
  compute pActivity                      |
       |                                    |
  Generate InChIKeys  ------JOIN-------->  |
       |
  SMILES -> RDKit -> Morgan/ECFP (2048-bit)
       |
  Scaffold split -> Train / Val / Test
       |
  XGBoost / RF / Chemprop
       |
  Score ZINC -> rank candidates -> check purchasability
```

## Key Libraries
```
pip install chembl-webresource-client  # ChEMBL API
pip install rdkit                       # Chemistry toolkit
pip install deepchem                    # MoleculeNet datasets
pip install scikit-learn                # Classical ML
pip install xgboost                     # Gradient boosting
```

## Sources

- ChEMBL API: https://www.ebi.ac.uk/chembl/api/data/docs
- ChEMBL Python Client: https://github.com/chembl/chembl_webresource_client
- Tox21: https://tox21.gov/data-and-tools/
- ZINC: https://zinc.docking.org/
- Ersilia: https://github.com/ersilia-os/antimicrobial-ml-tasks
