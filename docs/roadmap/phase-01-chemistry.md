Back to [Roadmap Index](README.md)

# Phase 1: Chemistry Context (Feb 10) -- DONE

Foundation for the Molecular Science domain. Provides RDKit cheminformatics for SMILES processing, descriptors, fingerprints, and 3D conformers.

## 1A. RDKit Adapter -- Core Operations
- [x] `validate_smiles(smiles)` -- `Chem.MolFromSmiles`, null-check, return bool
- [x] `canonicalize(smiles)` -- canonical SMILES via RDKit
- [x] `to_inchikey(smiles)` -- SMILES -> InChI -> InChIKey
- [x] Tests: valid/invalid SMILES, canonicalization consistency (24 tests)

## 1B. RDKit Adapter -- Descriptors & Fingerprints
- [x] `compute_descriptors(smiles)` -- MW, LogP, TPSA, HBD, HBA, RotatableBonds, QED, NumRings
- [x] `compute_fingerprint(smiles, fp_type)` -- Morgan/ECFP (radius=2, 2048-bit) + MACCS (166-bit)
- [x] `tanimoto_similarity(fp1, fp2)` -- similarity score (0.0-1.0)
- [x] Tests: aspirin descriptors match known values, fingerprint bit counts

## 1C. RDKit Adapter -- 3D & Substructure
- [x] `generate_conformer(smiles)` -- AddHs, EmbedMolecule(ETKDGv3), MMFFOptimize, MolToMolBlock
- [x] `substructure_match(smiles, pattern)` -- returns bool + matching atom indices
- [x] Tests: 3D conformer has coordinates, substructure match on known patterns

## 1D. Chemistry Service + Tools
- [x] Wire `ChemistryService` to `RDKitAdapter` via dependency injection
- [x] Implement `generate_3d` tool -- SMILES -> JSON with MolBlock + energy
- [x] Implement `substructure_match` tool -- SMILES + pattern -> JSON with match + atoms
- [x] Added `validate_smiles`, `compute_descriptors`, `compute_fingerprint`, `tanimoto_similarity` tools
- [x] Tests: service integration tests (9), tool JSON output validation (11)

**Verification:** `uv run pytest tests/chemistry/ -v` -- 44 passed, mypy clean.
