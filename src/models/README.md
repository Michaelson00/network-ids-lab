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
