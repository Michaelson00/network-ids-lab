# Model Handoff — ML to DevOps

## Files

- `src/models/random_forest_model.pkl` — the trained Random Forest classifier
- `src/models/scaler.pkl` — the StandardScaler used to preprocess features before training

Both are saved using `joblib` and must be loaded with `joblib.load()`.

## How to use

```python
import joblib

model = joblib.load("random_forest_model.pkl")
scaler = joblib.load("scaler.pkl")

# new_data must be a table with the same 78 feature columns,
# in the same order, as the training data (all columns from the
# original dataset except 'Label')

new_data_scaled = scaler.transform(new_data)
predictions = model.predict(new_data_scaled)
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