Back to [Roadmap Index](README.md)

# Phase 3: Prediction Context (Feb 10) -- DONE

ML models for activity/outcome prediction (domain-agnostic scoring).

## 3A. XGBoost Adapter
- [x] Train: Morgan fingerprints (2048-bit) + activities -> XGBoost classifier
- [x] Scaffold split: train/val/test by Murcko scaffold (prevents data leakage)
- [x] Metrics: AUROC, AUPRC, accuracy, F1, confusion matrix
- [x] Feature importance: top fingerprint bits -> interpret as substructures
- [x] Predict: fingerprints -> probabilities
- [x] Tests: small fixture dataset, verify model trains and predicts (5 tests)

## 3B. Model Store
- [x] Save: `TrainedModel` metadata + joblib artifact -> disk
- [x] Load: model_id -> `TrainedModel` + artifact
- [x] List: all saved models with metrics
- [x] Tests: save/load roundtrip (4 tests)

## 3C. Prediction Service -- Train & Predict
- [x] `train(target, model_type)` -- load dataset, compute fingerprints, scaffold split, train, save
- [x] `predict(smiles_list, model_id)` -- load model, compute fingerprints, predict, rank
- [x] `cluster(smiles_list, n_clusters)` -- Butina clustering on Tanimoto distances
- [x] Tests: full train -> predict pipeline with fixture data (8 tests)

## 3D. Chemprop Adapter (Optional Extra)
- [x] Train: SMILES + activities -> Chemprop D-MPNN (requires `deeplearning` extra)
- [x] Predict: SMILES -> probabilities
- [x] Guard: graceful skip if chemprop not installed
- [x] Tests: mock or skip if extra not available

## 3E. Ensemble & Tools
- [x] `ensemble(smiles_list)` -- average XGBoost + Chemprop (0.5 each), fallback to single
- [x] Implement `train_model` tool -- target + model_type -> JSON with metrics
- [x] Implement `predict_candidates` tool -- smiles_list + model_id -> JSON with ranked predictions
- [x] Implement `cluster_compounds` tool -- smiles_list -> JSON with clusters
- [x] Tests: ensemble logic, tool JSON output (3 tests)

**Verification:** `uv run pytest tests/prediction/ -v` -- 20 passed, mypy clean.
