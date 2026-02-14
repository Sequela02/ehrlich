Back to [Roadmap Index](README.md)

# Phase 9: Molecule Visualization Suite (Feb 10) -- DONE

Full visualization: server-side 2D SVG depiction, 3Dmol.js for 3D/docking views, expandable candidate detail panel.

## 9A. Server-Side 2D Depiction
- [x] `RDKitAdapter.depict_2d(smiles, width, height)` -- RDKit `rdMolDraw2D.MolDraw2DSVG`
- [x] `ChemistryService.depict_2d()` thin wrapper
- [x] Tests: returns SVG, custom dimensions, invalid SMILES raises (3 tests)

## 9B. Molecule API Routes
- [x] `GET /molecule/depict?smiles=&w=&h=` -- SVG response, 24h cache, error SVG for invalid SMILES
- [x] `GET /molecule/conformer?smiles=` -- JSON with mol_block, energy, num_atoms
- [x] `GET /molecule/descriptors?smiles=` -- JSON descriptors + passes_lipinski
- [x] `GET /targets` -- JSON list of protein targets (5 pre-configured)
- [x] Router registered in app.py
- [x] Tests: 10 API tests (depict, conformer, descriptors, targets)

## 9C. 3Dmol.js Integration
- [x] Added `3dmol` package to console dependencies
- [x] TypeScript type stubs (`console/src/types/3dmol.d.ts`)
- [x] Dynamic import for code splitting (~575KB separate chunk)

## 9D. Molecule Viewer Components
- [x] `MolViewer2D`: `<img>` tag with server-side SVG, lazy loading, error fallback to SMILES text
- [x] `MolViewer3D`: 3Dmol.js WebGL viewer, stick style, Jmol coloring, cleanup on unmount
- [x] `DockingViewer`: 3Dmol.js protein cartoon (spectrum) + ligand stick (green carbon), zoom to ligand
- [x] Tests: 4 MolViewer2D component tests (src, encoding, dimensions, error fallback)

## 9E. CandidateDetail + CandidateTable
- [x] `CandidateDetail` panel: parallel fetch of conformer + descriptors, 3-column grid (2D | 3D + energy | properties + Lipinski badge)
- [x] `CandidateTable` rewrite: 2D thumbnails (80x60), chevron expand/collapse, click-to-expand detail panel
- [x] Removed raw SMILES column (SMILES in img alt text)
- [x] Updated tests for new table structure

## 9F. Cleanup
- [x] Deleted `useRDKit` hook (dead code)
- [x] Added `CandidateDetail` to barrel export (`index.ts`)

**Verification:** 198 tests, 82.09% coverage, 19 console tests. All quality gates green (ruff 0, mypy 0, tsc 0, vitest 19/19).
