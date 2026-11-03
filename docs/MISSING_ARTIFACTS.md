# Artifact handoff — verified 2026-10-24

## Search performed

Searched the entire working repository, including ignored `data/`, all pickle/
joblib/pickle-extension files, CSVs, PCAP/PCAPNGs, notebook training/export cells,
model/scaler/encoder references, API paths and Git artifact filename history.
The virtualenv also contains NumPy/joblib's package-test pickles; those are not
project models and must not be used as replacements.

Present project artifacts:

- `data/demo/random_forest_model.pkl` and `data/demo/scaler.pkl`: explicitly
  synthetic demo artifacts only; not benchmark artifacts.
- `src/models/sample_input.csv`: five unlabelled feature rows, not a training
  dataset. Historical result/importance CSVs under `docs/da1-results/` are not
  datasets or trained weights.
- Four existing authorized lab captures listed below.
- Notebook training configuration, saved EDA/classification/tuning/importance
  outputs, a 78-feature contract and the selected export cell.

Absent: the selected model/scaler, any alternate benchmark pickle/joblib filename,
raw benchmark CSVs and `data/processed/cicids2017_clean.csv`. Neither a notebook's
rendered estimator summary nor its saved classification report contains reusable
fitted tree weights. No benchmark data or artifact was fabricated/downloaded.

## ML Engineer

**Required file:** `src/models/random_forest_model.pkl`

**Purpose:** selected original multiclass `RandomForestClassifier` trained on
scaled CICIDS2017 features. Notebook configuration: 100 trees, balanced class
weights, random state 42, `n_jobs=-1`, default depth. The tuned 200-tree/depth-30
variant is not the selected export.

**Also required:** `src/models/scaler.pkl`

**Purpose:** the SAME RUN's fitted `StandardScaler`. Although Random Forest does
not inherently need scaling, this selected notebook explicitly fits the forest
on `X_train_scaled`; its paired scaler is therefore required at inference.

**Produced from:** `notebooks/02_model_comparison.ipynb`:

| Cell (1-based) / ID | Actual operation |
|---|---|
| 3 / `initial_id` | Read `../data/processed/cicids2017_clean.csv` |
| 5 / `6df63d82cdb637a3` | 300,000-row sample, seed 42 |
| 6 / `8f1d0dab19a2b77b` | `X = data.drop(columns=['Label'])`, `y = data['Label']` |
| 7 / `d9f5f2974e8c0024` | Stratified 80/20 split, seed 42 |
| 8 / `98cccb1d188cc7d0` | Fit scaler ONLY on training X; transform train/test |
| 13 / `4b34c1d36f5b943c` | Fit `model_rf` on `X_train_scaled` |
| 21 / `91aab743f061a8f6` | Export fitted `model_rf` + `scaler` (unexecuted in saved notebook) |

The final cell originally contained `joblib.dump(model_rf, ...)` and
`joblib.dump(scaler, ...)` but no execution/output. It now calls the checked
export helper. In the actual fitted session (or after reproducing the existing
notebook on the actual benchmark data), run:

```python
from pathlib import Path
import sys
project_root = Path.cwd() if (Path.cwd() / 'src').is_dir() else Path.cwd().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from src.models.export import export_fitted
metadata = export_fitted(model_rf, scaler)
```

This produces the two required files plus recommended
`src/models/model_metadata.json` containing exact classifier classes, package/
Python versions, schema reference/checksum and artifact checksums. Existing files
are protected; review provenance before explicitly passing `overwrite=True`.
The helper exports already-fitted objects; it never trains or invents results.

**Expected loader:** `joblib.load()` in `src/models/predict.py`.
**Expected count:** exactly 78 finite numeric columns.
**Expected names/order:** the EXISTING `src/features/schema.json`; API, export
checks and inference share this contract. `Label`/`Attack_Type` are not inputs.
The scaler must retain that feature-name order; the forest was fitted on arrays.
No duplicate feature-schema file is created.

**Expected labels:** original string dataset labels, not undocumented integer
codes. The cleaned EDA records BENIGN, Bot, DDoS, DoS GoldenEye, DoS Hulk,
DoS Slowhttptest, DoS slowloris, FTP-Patator, Heartbleed, Infiltration, PortScan,
SSH-Patator, Web Attack - Brute Force, Web Attack - Sql Injection and
Web Attack - XSS. The exact classifier `classes_` depends on its training sample;
export metadata records the actual classes. No label encoder is used by the
notebook and no separate encoder file is needed. Existing normalization maps
these into BENIGN / PORT_SCAN / BRUTE_FORCE / DOS / OTHER_ATTACK.

A single sklearn Pipeline could package the two fitted objects, but it is NOT
what this notebook saves and is not required. Preserve the existing two-file
interface; do not deliver an unannounced differently structured pickle.

After copying the artifacts, restart API and check `/api/health` for
`FULL_MODEL_MODE`, then run `python tests/test_real_traffic.py`. If metadata is
supplied, loader checks the schema, label mapping and both checksums. This still
does not prove detection accuracy; use the owner's labelled holdout evaluation.

## Data Analyst

No new feature list, order, cleaning policy or correlation study is requested:
they exist in `src/features/schema.json`, notebook code and saved EDA outputs.
If the ML owner no longer has the fitted session/export and must reproduce it,
provide the real **`data/processed/cicids2017_clean.csv`** (78 ordered columns plus
Label). Alternatively supply the original eight benchmark daily CSVs in
`data/raw/` and run the EXISTING EDA cleaning notebook first. Those source files
are listed in EDA cell 1. Preserve all 78 features; no retraining is run here
because actual benchmark input is absent. The five sample rows cannot replace it.

## Network Engineer

No new capture files are needed for current offline operation. Present files:

- `lab/baseline_normal_traffic.pcapng`
- `lab/scan_nmap_synscan.pcapng`
- `lab/scan_bruteforce_ssh.pcapng`
- `lab/scan_dos_trimmed.pcapng`

The new offline reader extracts actual packet-header rule counters; no live
sniffing, sending, replay or invented 78-feature model data occurs. Actual Nmap
capture produces PORT_SCAN. Existing SSH packets do not disclose failed logins;
real SSH brute-force validation would need timestamped server authentication
failures grouped by source/service (not another invented capture). The trimmed
DoS file has only 500 packets and cannot exceed the existing >1000-in-1s rule.
A separately authorized larger sample is optional for real volumetric validation,
not a prerequisite for the working DoS demo. Do not lower thresholds to force it.

Benchmark ML on captures additionally requires a verified CICFlowMeter-compatible
78-feature export matching training semantics. The minimal rule reader is not
that exporter and does not claim to be one. Capture privacy/publication review
remains with the owner; existing captures have not been moved or deleted.

## Cybersecurity Engineer

No missing rules, thresholds, formula or threat definitions. All three rules,
canonical category handling and Likelihood × Impact × Exposure exist and run.
No redo requested. Rule-only fallback explicitly omits ML labels/probabilities.

## Current classification

**B — Demo functional.** Rules, scoring, API, database, dashboard, four demos and
actual offline Nmap capture analysis work without external files. **A — Fully
functional benchmark-model mode** needs the ML export above. Live capture is
optional and is not a blocker.
