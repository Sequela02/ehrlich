# Simulation: Molecular Docking + ADMET Prediction

## Overview

Three simulation layers that turn Ehrlich from "ML predictions" into "computational lab":

1. **Molecular Docking** — Simulates drug-target binding, predicts binding energy and pose
2. **ADMET Prediction** — Simulates pharmacokinetics (absorption, distribution, metabolism, excretion, toxicity)
3. **Mutant Docking** — Simulates resistance by docking against mutated protein targets

All free. All run in seconds. No GPU required.

---

## 1. Molecular Docking (AutoDock Vina)

### What It Does

Takes a candidate molecule + bacterial protein structure → simulates how the molecule fits in the protein's active site → predicts binding energy (kcal/mol) and binding pose (3D coordinates).

### Why It Matters

- Proves the candidate can physically interact with the bacterial target
- Binding energy provides a quantitative score (-8 to -10 kcal/mol = strong)
- Binding pose shows WHERE in the protein it binds (validates mechanism)
- Visually stunning in 3Dmol.js (protein surface + molecule in pocket)

### Tools

| Tool | Install | Purpose |
|------|---------|---------|
| AutoDock Vina | `pip install vina` | Docking engine |
| Meeko | `pip install meeko` | Prepare molecules for Vina |
| RDKit | `pip install rdkit` | Generate 3D conformers |
| PDB/AlphaFold | Free download/API | Protein structures |

### Key MRSA Target Proteins

| Protein | PDB ID | Role | Why Target It |
|---------|--------|------|---------------|
| PBP2a | 1VQQ | Transpeptidase (cell wall) | The protein that makes MRSA resistant to beta-lactams |
| DHPS | 1AD4 | Dihydropteroate synthase (folate) | Sulfonamide target |
| DNA Gyrase | 2XCT | DNA replication | Quinolone target |
| MurA | 1UAE | Cell wall synthesis | Fosfomycin target |
| NDM-1 (MBL) | 3SPU | Metallo-beta-lactamase | Major resistance enzyme, almost nothing in pipeline |

### Pipeline

```python
from vina import Vina
from meeko import MoleculePreparation, PDBQTMolecule
from rdkit import Chem
from rdkit.Chem import AllChem

def dock_candidate(smiles: str, receptor_pdbqt: str,
                   center: list, box_size: list = [20, 20, 20]) -> dict:
    """Dock a candidate molecule against a protein target."""

    # 1. Generate 3D conformer
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    AllChem.MMFFOptimizeMolecule(mol)

    # 2. Prepare for Vina
    preparator = MoleculePreparation()
    mol_setup = preparator.prepare(mol)
    ligand_pdbqt = mol_setup[0].write_pdbqt_string()

    # 3. Run docking
    v = Vina(sf_name='vina')
    v.set_receptor(receptor_pdbqt)
    v.set_ligand_from_string(ligand_pdbqt)
    v.compute_vina_maps(center=center, box_size=box_size)
    v.dock(n_poses=5)

    # 4. Get results
    energies = v.energies()
    best_energy = energies[0][0]  # kcal/mol
    best_pose = v.poses(n_poses=1)  # PDBQT string of best pose

    return {
        "binding_energy": best_energy,
        "pose_pdbqt": best_pose,
        "interpretation": interpret_energy(best_energy)
    }

def interpret_energy(energy: float) -> str:
    if energy <= -10: return "Excellent binding (drug-like)"
    if energy <= -8: return "Strong binding"
    if energy <= -6: return "Moderate binding"
    if energy <= -4: return "Weak binding"
    return "No significant binding"
```

### Binding Energy Reference

| Energy (kcal/mol) | Interpretation | Reference |
|-------------------|---------------|-----------|
| <= -10 | Excellent (typical for approved drugs) | Vancomycin-like |
| -8 to -10 | Strong | Most drug candidates |
| -6 to -8 | Moderate | Worth investigating |
| -4 to -6 | Weak | Unlikely to be effective |
| > -4 | No binding | Discard |

### Visualization in 3Dmol.js

```javascript
// Load protein
viewer.addModel(proteinPDB, "pdb");
viewer.setStyle({}, { cartoon: { color: "white", opacity: 0.7 } });

// Add surface around binding site
viewer.addSurface($3Dmol.SurfaceType.VDW, {
    opacity: 0.5,
    color: "white"
}, { within: { distance: 8, sel: { index: bindingSiteAtoms } } });

// Load docked ligand
viewer.addModel(ligandPDB, "pdb");
viewer.setStyle(
    { model: 1 },
    { stick: { colorscheme: "greenCarbon", radius: 0.15 },
      sphere: { scale: 0.25 } }
);

// Show hydrogen bonds
for (const hbond of hydrogenBonds) {
    viewer.addCylinder({
        start: hbond.donor, end: hbond.acceptor,
        radius: 0.05, color: "yellow", dashed: true
    });
}

viewer.zoomTo({ model: 1 });
viewer.render();
```

---

## 2. ADMET Prediction

### What It Does

Predicts pharmacokinetic properties from SMILES — what happens to the drug inside a human body.

### Endpoints Available

| Property | Category | Why It Matters |
|----------|----------|---------------|
| Oral bioavailability | Absorption | Can you take it as a pill? |
| Intestinal absorption | Absorption | Will it be absorbed in the gut? |
| BBB penetration | Distribution | Does it cross into the brain? (usually don't want this for antibiotics) |
| Plasma protein binding | Distribution | How much stays active vs bound to proteins? |
| CYP450 inhibition | Metabolism | Will it interfere with other drugs? |
| Total clearance | Excretion | How fast is it eliminated? |
| Half-life | Excretion | How long does it last? |
| hERG inhibition | Toxicity | Will it cause heart problems? |
| Hepatotoxicity | Toxicity | Will it damage the liver? |
| Skin sensitization | Toxicity | Will it cause allergic reactions? |

### APIs (All Free)

**pkCSM (University of Queensland):**
- Web: https://biosig.lab.uq.edu.au/pkcsm/
- API available, SMILES input, JSON output
- 31 ADMET predictions

**SwissADME (SIB):**
- Web: http://www.swissadme.ch/
- REST API, SMILES input
- Lipinski, ADME, pharmacokinetics, drug-likeness

**ADMETlab 2.0 (Zhejiang University):**
- Web: https://admetmesh.scbdd.com/
- API available
- 31 endpoints including oral bioavailability, BBB, CYP

### Implementation

```python
import requests

@mcp.tool()
def predict_admet(smiles: str) -> str:
    """Predict ADMET pharmacokinetic properties for a candidate molecule.
    Returns absorption, distribution, metabolism, excretion, and toxicity predictions."""

    # Option 1: pkCSM API
    response = requests.post(
        "https://biosig.lab.uq.edu.au/pkcsm/prediction",
        data={"smiles": smiles, "format": "json"}
    )

    # Option 2: Fallback to RDKit-based estimates
    # (if API is down or rate-limited)
    mol = Chem.MolFromSmiles(smiles)
    fallback = {
        "MW": Descriptors.MolWt(mol),
        "LogP": Descriptors.MolLogP(mol),
        "HBD": Descriptors.NumHDonors(mol),
        "HBA": Descriptors.NumHAcceptors(mol),
        "TPSA": Descriptors.TPSA(mol),
        "RotBonds": Descriptors.NumRotatableBonds(mol),
        "QED": QED.qed(mol),
        "lipinski_violations": sum([
            Descriptors.MolWt(mol) > 500,
            Descriptors.MolLogP(mol) > 5,
            Descriptors.NumHDonors(mol) > 5,
            Descriptors.NumHAcceptors(mol) > 10
        ])
    }

    return json.dumps(result)
```

---

## 3. Mutant Docking (Resistance Simulation)

### What It Does

Docks the same candidate against MUTATED versions of the target protein. If binding energy drops significantly, the bacteria could develop resistance through that mutation.

### Pipeline

```python
def assess_resistance(smiles: str, target: str, mutations: list) -> dict:
    """Dock candidate against wild-type and mutant proteins.
    Compare binding energies to assess resistance vulnerability."""

    # Dock against wild-type
    wt_result = dock_candidate(smiles, f"{target}_wildtype.pdbqt", center)

    # Dock against each mutant
    mutant_results = {}
    for mutation in mutations:
        mut_result = dock_candidate(smiles, f"{target}_{mutation}.pdbqt", center)
        energy_diff = mut_result["binding_energy"] - wt_result["binding_energy"]
        mutant_results[mutation] = {
            "energy": mut_result["binding_energy"],
            "energy_change": energy_diff,
            "resistance_risk": "HIGH" if energy_diff > 2.0 else
                              "MODERATE" if energy_diff > 1.0 else "LOW"
        }

    return {
        "wildtype_energy": wt_result["binding_energy"],
        "mutations": mutant_results
    }
```

### Known MRSA Resistance Mutations

| Target | Mutation | Effect |
|--------|----------|--------|
| PBP2a | S403A | Reduces beta-lactam binding |
| PBP2a | N146K | Alters active site shape |
| DHPS | F17L | Sulfonamide resistance |
| DNA Gyrase | S84L | Quinolone resistance |

### Pre-preparing Mutant Structures

For the hackathon, pre-compute a set of mutant PDB structures:
1. Download wild-type from PDB
2. Introduce mutation with PyMOL or RDKit
3. Energy-minimize the mutant structure
4. Convert to PDBQT for Vina
5. Store as pre-loaded files

This way docking against mutants is as fast as wild-type (seconds).

---

## Combined MCP Tools

```python
@mcp.tool()
def dock_against_target(smiles: str, target: str = "pbp2a") -> str:
    """Dock a candidate molecule against a bacterial protein target.
    Returns binding energy, binding pose, and key interactions.
    Available targets: pbp2a, dhps, dna_gyrase, mura, ndm1"""
    # ... AutoDock Vina pipeline

@mcp.tool()
def predict_admet(smiles: str) -> str:
    """Predict ADMET pharmacokinetic properties for a candidate.
    Returns absorption, distribution, metabolism, excretion, toxicity."""
    # ... pkCSM/SwissADME API call

@mcp.tool()
def assess_resistance(smiles: str, target: str = "pbp2a") -> str:
    """Dock candidate against wild-type and mutant protein targets.
    Returns binding energy comparison and resistance risk assessment."""
    # ... Mutant docking pipeline
```

---

## Effort Estimate

| Component | Setup Time | Per-molecule Time | Dependencies |
|-----------|-----------|-------------------|-------------|
| Docking (Vina) | 3-4 hours | ~5-30 seconds | vina, meeko, PDB files |
| ADMET (API) | 1-2 hours | ~1-2 seconds | requests (HTTP calls) |
| Mutant docking | 2-3 hours (on top of docking) | ~5-30 seconds | Pre-computed mutant PDBs |

Total: ~1 day to set up all three. After that, full simulation pipeline per candidate takes ~30-60 seconds.

---

## Gotchas

1. **AutoDock Vina on Windows:** Works via pip, but may need OpenBabel for some format conversions. Test early.
2. **Protein preparation:** PDB files need cleaning (remove water, add hydrogens, convert to PDBQT). Do this once per target, store pre-processed files.
3. **Binding site definition:** Need to know WHERE on the protein to dock (center coordinates + box size). Use known binding sites from literature.
4. **ADMET API rate limits:** pkCSM and SwissADME may have rate limits. Implement caching and fallback to RDKit-based estimates.
5. **Mutant structure quality:** In-silico mutations are approximations. Real mutant structures (from PDB) are better when available.

## Sources

- AutoDock Vina: https://github.com/ccsb-scripps/AutoDock-Vina
- Meeko: https://github.com/forlilab/Meeko
- PDB: https://www.rcsb.org/
- AlphaFold DB: https://alphafold.ebi.ac.uk/
- pkCSM: https://biosig.lab.uq.edu.au/pkcsm/
- SwissADME: http://www.swissadme.ch/
- ADMETlab: https://admetmesh.scbdd.com/
