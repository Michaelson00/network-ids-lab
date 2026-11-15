# Selected model inference

`predict.py` lazily loads `random_forest_model.pkl` and `scaler.pkl` from this
folder. They must be trusted paired artifacts from the selected multiclass
training run in `notebooks/02_model_comparison.ipynb`. Neither is in Git.

`predict(data)` preserves batch labels; `predict_traffic(data)` returns a list
of `{label, confidence}` records using the probability of each predicted class.
Inputs are validated and ordered by `src/features/schema.json`, then scaled.
Missing/incompatible artifacts raise `ModelUnavailable`; no fallback model is
created. See [run guide](../../RUN_AND_TEST.md) for dependency provenance and
selected-model verification limits.

## Separate synthetic demo model

`demo.py` defines four explicitly simulated feature scenarios. `python -m src.demo
prepare` fits a small seeded Random Forest/scaler on 128 synthetic rows and saves
only under `data/demo/` (override `NIDS_DEMO_MODEL_DIR`). Only explicitly opted-in `model_mode: synthetic` POSTs initialize
these artifacts on first use if missing, then call `predict_traffic(..., demo=True)`.
Neither `predict()` nor the default `predict_traffic()` uses this model, and
`/api/process` continues to require selected artifacts. The shared validator and
probability/scaling implementation are used for both paths. This is a demonstrator,
not a retrained benchmark model or a source of model-quality metrics.

## Export from the real fitted session

`export.py: export_fitted(model_rf, scaler)` validates the selected 100-tree
configuration and shared feature order, protects existing files and emits the
model/scaler plus provenance/checksum metadata. It does not train a model.
Default demos use the selected pair when available; otherwise they skip ML and
run rules-only. [Exact handoff](../../docs/MISSING_ARTIFACTS.md).
