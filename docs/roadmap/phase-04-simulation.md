Back to [Roadmap Index](README.md)

# Phase 4: Simulation Context (Feb 10) -- DONE

Molecular docking, ADMET prediction, resistance assessment.

## 4A. Protein Store
- [x] Manage PDBQT files in `data/proteins/`
- [x] Target registry: PDB ID -> name, organism, center coordinates, box size
- [x] Pre-configure 5 MRSA targets: PBP2a (1VQQ), DHPS (1AD4), DNA Gyrase (2XCT), MurA (1UAE), NDM-1 (3SPU)
- [x] `get_pdbqt(pdb_id)` -- return file path or download
- [x] Tests: target lookup, file existence check (6 tests)

## 4B. Vina Adapter (Optional Extra)
- [x] Dock: SMILES -> conformer (RDKit) -> Meeko prep -> Vina dock -> energy + pose
- [x] Parse results: binding energy (kcal/mol), best pose PDBQT, RMSD
- [x] Interpret energy: excellent (<= -10), strong (-8 to -10), moderate (-6 to -8), weak (> -6)
- [x] Guard: graceful skip if vina/meeko not installed
- [x] Tests: energy interpretation (6 tests in protein_store)

## 4C. ADMET Client
- [x] RDKit-based ADMET: Lipinski violations, mutagenic alerts (SMARTS), hepatotoxicity, hERG, BBB
- [x] Build `ADMETProfile` with absorption, distribution_vd, metabolism, excretion, toxicity
- [x] Toxicity flags: Ames (nitro/azide/quinone alerts), hERG (LogP + MW), hepatotoxicity (LogP + MW + acyl chloride/thioester)
- [x] Tests: aspirin profile, ethanol BBB, nitroaromatic mutagenic, hepatotoxic compound (5 tests)

## 4D. Resistance Assessment
- [x] Knowledge-based mutation risk with compound class pattern matching
- [x] Known mutations: PBP2a S403A/N146K, DHPS F17L, DNA Gyrase S84L, MurA C115D, NDM-1 V73_ins/M154L
- [x] Compound class patterns: beta-lactam ring, fluoroquinolone, sulfonamide -> affected targets
- [x] Build `ResistanceAssessment` with per-mutation `MutationRisk` and overall risk level
- [x] Tests: known target mutations, DNA gyrase, mutations dict (3 tests in simulation_service)

## 4E. Simulation Service + Tools
- [x] `dock(smiles, target_id)` -- Vina with RDKit descriptor-based estimate fallback
- [x] `predict_admet(smiles)` -- RDKit-based via PkCSMClient
- [x] `assess_resistance(smiles, target_id)` -- knowledge-based with compound class risk
- [x] Implement `dock_against_target` tool -- smiles + target -> JSON with energy + interpretation
- [x] Implement `predict_admet` tool -- smiles -> JSON with ADMET profile + toxicity flags
- [x] Implement `assess_resistance` tool -- smiles + target -> JSON with mutation details
- [x] Tests: service integration (6), tool JSON output (3)

**Verification:** `uv run pytest tests/simulation/ -v` -- 20 passed, mypy clean.
