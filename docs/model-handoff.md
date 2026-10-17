# Model Handoff — ML to DevOps

## Files

- `src/models/random_forest_model.pkl` — the trained Random Forest classifier
- `src/models/scaler.pkl` — the StandardScaler used to preprocess features before training

Both are saved using `joblib` and must be loaded with `joblib.load()`.

## How to use

```python
from src.models.predict import predict, predict_traffic

# Run from the repository root; new_data has the 78 training feature columns.
# Both functions validate/order named columns and apply the paired scaler.
labels = predict(new_data)                  # ndarray of labels
records = predict_traffic(new_data)          # list of {label, confidence}
```

## Important notes

- Input must have exactly 78 feature columns, matching the original CICIDS2017
  feature set (all columns except `Label`), in the same column order used
  during training.
- Data must be passed through `scaler.transform()` before prediction — do not
  skip this step, even though Random Forest doesn't strictly require scaling,
  since the model was trained on scaled data.
- Column names must be cleaned the same way as during training (no leading/
  trailing whitespace) — see `notebooks/01_eda.ipynb` for the exact cleaning
  steps applied.

## Performance summary

Trained on a 300,000-row sample of CICIDS2017 (80/20 train/test split).
Strong precision and recall (≥0.95) on most attack types: DDoS, PortScan,
DoS Hulk, DoS GoldenEye, DoS slowloris, DoS Slowhttptest, FTP-Patator,
SSH-Patator. Weaker performance on rare classes with very little training
data: Bot (precision 0.29), Web Attack - XSS (~0.20), Web Attack - Brute
Force (~0.6-0.7), and Infiltration (insufficient data in test set to
evaluate reliably).

## Hyperparameter tuning (Week 2)

Tried increasing n_estimators to 200 and setting max_depth=30. Results were
nearly identical to the original model — weak classes (Bot, Web Attack - XSS,
Web Attack - Brute Force) did not improve. This suggests the limitation is
insufficient training data for these rare classes, not a tuning issue.
Sticking with the original model (random_forest_model.pkl).

## DA1 cross-check

DA1 also ran a binary classification approach (ATTACK vs BENIGN) as a
cross-check — 99.92% accuracy, 42 missed attacks, 53 false alarms.
Feature importance broadly overlapped with the multiclass model above.
See docs/da1-results/ for full outputs.
## Current evidence and integration boundary

Both artifacts above are absent from this checkout. They must come from the
same selected training run, with its Python/scikit-learn/numpy/joblib versions.
`predict.py` uses `joblib.load` at module-relative paths, lazily; it checks
78-feature counts and available feature names and fails explicitly if unavailable.
The API calls `predict_traffic`, then `build_alert`; clients cannot supply labels.
The model probability is taken from the predicted class's `predict_proba` column.

The multiclass performance figures and tuning outcome above are the ML owner's
reported historical observations. The model notebook has code but **no saved
numeric evaluation outputs**, and these results have not been reproduced in this
audit. Do not present the DA1 binary CSVs as multiclass verification. Temporary
fixture model predictions pass the application tests; real-model sample/holdout
predictions remain blocked. See [run guide](../RUN_AND_TEST.md).
