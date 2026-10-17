# Notebooks

- `01_eda.ipynb`: historical dataset inspection/cleaning outputs; final duplicate,
  constant-feature and correlation cells are added but not executed.
- `02_model_comparison.ipynb`: scaled Logistic Regression/Random Forest comparison,
  tuning and artifact export code; saved numeric evaluation outputs are absent.

From the root, activate the environment and run `jupyter notebook`, then open
notebooks here. The notebook kernel should use `notebooks/` as its working
folder for the existing `../data/` paths. Supply benchmark CSVs in `data/raw/`
for EDA, or the existing cleaned CSV in `data/processed/` for modelling.
No benchmark data is supplied. Running ML cells retrains/overwrites artifacts;
application setup does not require running these notebooks. See
[RUN_AND_TEST.md](../RUN_AND_TEST.md) and [issue audit](../docs/FINAL_ISSUE_AUDIT.md).
