# Cheminformatics, RDKit, and Visualization

## SMILES Notation

SMILES (Simplified Molecular Input Line Entry System) — ASCII strings encoding molecular structure. The universal format.

| Symbol | Meaning |
|--------|---------|
| `C`, `N`, `O`, `S` | Aliphatic atoms |
| `c`, `n`, `o` | Aromatic atoms |
| `=`, `#` | Double, triple bonds |
| `()` | Branches |
| Digits | Ring closures |

Examples:
- Ethanol: `CCO`
- Benzene: `c1ccccc1`
- Aspirin: `CC(=O)Oc1ccccc1C(=O)O`
- Caffeine: `CN1C=NC2=C1C(=O)N(C(=O)N2C)C`

Canonical SMILES = unique deterministic string per molecule (good as DB key).

## RDKit Python

### Installation
```bash
pip install rdkit
# If DLL issues on Windows: conda install -c conda-forge rdkit
# Verify: python -c "from rdkit import Chem; print(Chem.MolFromSmiles('CCO').GetNumAtoms())"
```

### Core: SMILES to Mol
```python
from rdkit import Chem
mol = Chem.MolFromSmiles('CC(=O)Oc1ccccc1C(=O)O')
# ALWAYS null-check: returns None on invalid SMILES
```

### Morgan Fingerprints (ECFP)
```python
from rdkit.Chem import rdFingerprintGenerator
import numpy as np

# radius=2 = ECFP4 (industry standard), fpSize=2048
gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fp = gen.GetFingerprint(mol)
fp_array = np.array(fp)  # for ML

# With atom mapping (for highlighting)
ao = rdFingerprintGenerator.AdditionalOutput()
ao.AllocateBitInfoMap()
fp = gen.GetFingerprint(mol, additionalOutput=ao)
bit_info = ao.GetBitInfoMap()
# bit_info[872] -> ((6, 2),) = atom index 6, radius 2
```

### MACCS Keys
```python
from rdkit.Chem import MACCSkeys
fp = MACCSkeys.GenMACCSKeys(mol)  # 167-bit vector
```

### Molecular Descriptors
```python
from rdkit.Chem import Descriptors

mw   = Descriptors.MolWt(mol)
logp = Descriptors.MolLogP(mol)
hbd  = Descriptors.NumHDonors(mol)
hba  = Descriptors.NumHAcceptors(mol)
tpsa = Descriptors.TPSA(mol)

# All at once
all_desc = Descriptors.CalcMolDescriptors(mol)
```

### Lipinski Rule of Five
```python
def lipinski_pass(mol):
    return (
        Descriptors.MolWt(mol) <= 500 and
        Descriptors.MolLogP(mol) <= 5 and
        Descriptors.NumHDonors(mol) <= 5 and
        Descriptors.NumHAcceptors(mol) <= 10
    )
```

### QED (Drug-likeness score)
```python
from rdkit.Chem import QED
score = QED.qed(mol)  # 0-1, >0.67 = drug-like
```

### Tanimoto Similarity
```python
from rdkit import DataStructs
similarity = DataStructs.TanimotoSimilarity(fp1, fp2)  # 0.0 to 1.0
```

### 3D Coordinate Generation (for 3Dmol.js)
```python
from rdkit.Chem import AllChem

mol = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
AllChem.MMFFOptimizeMolecule(mol)
molblock = Chem.MolToMolBlock(mol)  # send this to frontend
```

## RDKit.js (WASM — Browser)

Install: `npm install @rdkit/rdkit` (~8MB WASM)

### Initialization
```javascript
let RDKitModule;
window.initRDKitModule().then(module => {
    RDKitModule = module;
});
```

### Capabilities
- Parse SMILES: `RDKitModule.get_mol(smiles)`
- SVG rendering: `mol.get_svg()`
- Canvas rendering: `mol.draw_to_canvas(canvas, w, h)`
- Substructure match: `mol.get_substruct_match(qmol)`
- Highlight: `mol.get_svg_with_highlights(match)`
- Morgan FP as JSON: `mol.get_morgan_fp()`

### Cannot Do
No 3D conformer generation, no advanced descriptors, no reaction handling. Backend handles these.

### Memory Management (Critical)
```javascript
const mol = RDKitModule.get_mol("CCO");
// ... use ...
mol.delete();  // MUST call or WASM memory leaks
```

## 3Dmol.js (WebGL — 3D Viewer)

Install: `npm install 3dmol`

### Cannot parse SMILES directly
Must receive MOL block from backend.

### Basic Usage
```javascript
let viewer = $3Dmol.createViewer("viewport", { backgroundColor: "white" });
viewer.addModel(molblock, "sdf");
viewer.setStyle({}, { stick: { colorscheme: "Jmol" } });
viewer.zoomTo();
viewer.render();
```

### Substructure Highlighting in 3D
Compute match in backend/RDKit.js, get atom indices, then:
```javascript
viewer.setStyle({}, { stick: { color: "0xCCCCCC" } });
viewer.setStyle(
    { index: atomIndices },
    { stick: { color: "0xFF4444", radius: 0.15 },
      sphere: { color: "0xFF4444", scale: 0.3 } }
);
viewer.render();
```

## Full Pipeline (Hackathon Architecture)

```
User enters SMILES
    |
[Backend: Python/RDKit]
    |-- Generate Morgan FP, descriptors, QED
    |-- Lipinski pass/fail
    |-- Generate 3D conformer -> MolToMolBlock
    |-- Substructure match -> atom indices
    |
[Frontend]
    |-- RDKit.js: 2D structure with highlighted substructure (SVG)
    |-- 3Dmol.js: 3D interactive view with highlighted atoms
    |-- Dashboard: descriptors, QED score, Lipinski table
```

## Gotchas

1. RDKit.js WASM is ~8MB — load async, takes 1-2 seconds
2. `MolFromSmiles` returns None silently — always null-check
3. Morgan radius=2 = ECFP4 (most papers use this)
4. 3Dmol.js needs 3D coordinates from backend (EmbedMolecule + MMFFOptimize)
5. Windows: if pip fails with DLL errors, use conda-forge

## Sources

- RDKit Getting Started: https://www.rdkit.org/docs/GettingStartedInPython.html
- RDKit.js: https://github.com/rdkit/rdkit-js
- 3Dmol.js: https://3dmol.csb.pitt.edu/doc/index.html
