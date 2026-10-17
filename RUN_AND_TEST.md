# Run and test the NIDS lab

Educational local prototype. Run all shell commands from the repository root.
No traffic generators or external attack targets are needed for these checks.

## A–C. Prerequisites and installation

Use Python 3.11+ and a POSIX shell (macOS/Linux). The model owner must supply
the Python, scikit-learn, numpy and joblib versions used for serialization;
use those versions if the artifacts cannot load in a current environment.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## D. Required files and input

Obtain these two trusted artifacts from the **same selected training run**:

- `src/models/random_forest_model.pkl`
- `src/models/scaler.pkl`

They are absent from this checkout and intentionally ignored by Git. Never
load untrusted pickle/joblib files. Do not substitute the separate binary
model described in older DA1 notes. No retraining is necessary for this repair.
`notebooks/02_model_comparison.ipynb` trains the selected multiclass forest on
StandardScaler output and saves both artifacts at the paths above.

`src/features/schema.json` records the 78 training columns, checked against
`src/models/sample_input.csv` and the documented feature list. Named inputs
are stripped of surrounding column whitespace and reordered. Positional
inputs must already follow this order. Missing/extra/duplicate columns,
labels, nonnumeric, boolean, NaN and infinite values are rejected. Inference
rejects bad rows rather than dropping them silently; EDA drops invalid rows.
The loader checks artifact feature counts and feature names where available.
The notebook's forest receives arrays, so only its scaler retains names;
artifact provenance still requires the model owner's confirmation.

The sample CSV is supplied; raw CICIDS data is only needed for notebook work.
There is **no automatic packet capture → CICIDS2017 flow extractor** in this
repository. PCAPs alone cannot be POSTed to the model. Export matching flow
features externally; failed-login counts additionally require auth logs.
Rules expect already aggregated per-source/service telemetry, including
distinct-port connection counts. They do not aggregate packets themselves.

## E. Environment

No secrets or environment variables are required. Optional database location:

```sh
export NIDS_DB_PATH="$PWD/nids_alerts.db"
```

Default is `nids_alerts.db` in the repository root regardless of working
directory. Existing legacy alert rows are preserved with additive columns.
Database initialization also occurs under the Flask application factory.

## F. Tests

```sh
python -m unittest discover -s tests -v
python -m compileall -q src rules tests
python -m pip check
```

Automated integration tests fit tiny temporary fixture artifacts and exercise
the real scaler/model loader, prediction, rules, scoring, API, SQLite and
dashboard route. They never replace or validate the team's selected model.
No running server is required and API tests do not silently skip.

## G–H. Start API and dashboard together

```sh
python -m src.api.app
```

Open **http://127.0.0.1:5000/**. The API serves the existing dashboard at `/`
so calls remain on the same origin. Do not open the HTML as a `file://` URL.
The server binds only to loopback, without debug mode. This is a local demo
server, with no authentication or production deployment guarantees.

In a second terminal, activate the same environment and check readiness:

```sh
source .venv/bin/activate
curl --fail http://127.0.0.1:5000/api/health
curl --fail http://127.0.0.1:5000/api/alerts
curl --fail http://127.0.0.1:5000/api/metrics
```

Health returns HTTP 200 with `status: degraded` and `model.ready: false` if
artifacts are absent or incompatible. `/api/process` then returns HTTP 503;
there is no dummy prediction fallback. Healthy requires model and storage.

## I. One complete detection example

With trusted artifacts installed and the server running:

```sh
python tests/test_real_traffic.py
```

This POSTs the first supplied CSV flow, prints the structured result, and
checks storage if an attack was detected. A benign result does not create a
stored alert. This is a flow-table test, not raw packet replay.

## J–K. Safe benign, port scan, brute-force and DoS checks

Run the deterministic automated four-scenario test (temporary fixture model):

```sh
python -m unittest discover -s tests -p test_integration.py -v
```

For a live demonstration with the selected model, POST the same real sample
flow with controlled rule telemetry. These requests simulate metadata only:

```sh
python - <<'PY'
import csv
import requests
with open('src/models/sample_input.csv') as stream:
    row = next(csv.DictReader(stream))
features = [{key.strip(): float(value) for key, value in row.items()}]
cases = {
    'baseline (model decides label)': {},
    'port scan': {'connection_count': 35, 'connection_window_seconds': 8},
    'brute force': {'failed_logins': 7, 'login_window_seconds': 30},
    'DoS': {'request_count': 1500, 'request_window_seconds': 1},
}
for name, event in cases.items():
    response = requests.post('http://127.0.0.1:5000/api/process',
        json={'features': features, 'event': event, 'exposure': 8}, timeout=30)
    print(name, response.status_code, response.json())
    response.raise_for_status()
PY
```

The real sample's label is not assumed benign. Use a known labelled benign
holdout flow from the model owner to establish a true benign baseline.
Rules override a benign ML category; a non-benign ML category remains as
implemented, with all rule matches retained. Multiple matches use the first
rule category for a benign prediction: scan, brute force, then DoS.

Expected fields: `label`, `prediction`, `category`, `confidence`, `risk_score`,
`risk_level`, `severity`, `detection_source`, `rule_matches`, `status`,
`alert_generated`, `alert_id`. Risk remains Likelihood × Impact × Exposure,
factors 1–10. Benign confidence does not imply zero risk (default score 5).
Low is ≤125, Medium ≤500, High >500. Attacks are stored, benign results are
returned without storage. Stored alerts include timestamp and triage status.
Metrics count stored attack alerts, not total processed/benign traffic.
Dashboard polls alerts/metrics every 5 seconds and health every 10 seconds.

## L. Troubleshooting

- `ModuleNotFoundError`: activate `.venv`, install requirements, run from root.
- HTTP 400: check 78-column schema, numeric finite data, exactly one flow,
  exposure 1–10, and complete count/window pairs with nonnegative counts
  and positive windows. Batch `predict()` remains available for Python use.
- HTTP 503/model unavailable: provide both artifacts, restart the server,
  and match training library versions. Never bypass scaling to silence errors.
- Storage unavailable: check `NIDS_DB_PATH` parent directory and permissions.
- Port 5000 occupied: stop the other process, or use
  `python -m flask --app src.api.app:create_app run --host 127.0.0.1 --port 5001`
  and open that port in the browser (manual scripts use 5000).
- No dashboard rows: benign flows are not stored; check readiness and API
  response. Missing models do not manufacture demo alerts.
- Offline installs require an approved local wheel cache or network access.
- Existing tracked lab captures are retained; new captures and databases are
  ignored. Review existing captures privately before any publication.

## M. Stop services

Press **Ctrl+C** in the server terminal. `deactivate` exits the virtualenv.
SQLite persists across restarts; use a separate `NIDS_DB_PATH` for a fresh demo.

## N. Final demo procedure

1. Obtain the paired artifacts and their training dependency versions.
2. Install dependencies and run all tests above.
3. Start the server; confirm healthy model/storage, then open the dashboard.
4. POST a known benign holdout flow; verify low risk and no stored attack.
5. Run the controlled metadata cases; inspect rule evidence and risk formula.
6. Verify `/api/alerts`, `/api/metrics` and dashboard agree after polling.
7. Explain that capture-to-feature extraction and real failed-login telemetry
   remain external steps; offline evaluation figures are historical reports.
8. Stop the server. Keep all actual traffic simulations inside the authorized,
   isolated host-only lab described in `lab/`; never target public systems.

## Audit scope and remaining handoffs

Reviewed the source, tests, dashboard, notebook code/recorded outputs, lab
instructions/capture file headers, model handoff, feature contract, historical
result tables and project documentation. Existing lab captures and evaluation
artifacts were preserved. No credentials/private-key markers or machine-specific
absolute paths were found in the reviewed source/docs; existing packet payloads
have not been certified free of sensitive data.

Main repairs: nonexistent API imports/signatures; missing Flask/joblib/requests
dependencies; eager loading of absent artifacts; missing feature validation;
API bypass of rule detection; loss of confidence/category/evidence in storage;
database initialization limited to direct execution; cross-origin dashboard
requests; unsafe HTML interpolation; and a server-dependent skipped API test.
The existing risk formula, weights, categories, thresholds and rule precedence
are preserved. No selected-model retraining, packet generator or live capture
service was added.

Model owner: supply the paired selected artifacts and training package versions,
then run the live sample and known labelled holdout cases. Network/data owners:
provide compatible flow exports and aggregated/authentication telemetry to
connect existing captures to inference. Real browser rendering/responsiveness
and capture payload privacy require separate verification.

## Validation recorded on 2026-10-17

- Full suite: `Ran 13 tests in 1.076s`, `OK` (no skips or resource warnings).
- All four scenarios exercised with temporary fitted artifacts, not the missing
  selected model. Scoring/canonical-label regressions retained.
- Dependency check: `No broken requirements found.`
- Compileall, dashboard JavaScript syntax, local Markdown links and
  `git diff --check` passed.
- JavaScript mocked-DOM checks passed for degraded health, null severity,
  safe text rendering and offline handling; no real-browser check was run.
- Local HTTP smoke: dashboard/health/alerts/metrics return 200; missing artifacts
  produce processing 503. Temporary fitted-model HTTP checks return all four
  expected categories, persist three attack alerts and show matching metrics.
  Both temporary servers stopped; the selected model was not tested.
- This environment required execution permission for package downloads and
  loopback sockets. Initial native SciPy imports were slow but completed.

## Weeks 1–4 issue audit

See [docs/FINAL_ISSUE_AUDIT.md](docs/FINAL_ISSUE_AUDIT.md) for every supplied
role/week requirement and [consolidated final report](docs/final-report.md).
The percentage counts only fully evidenced role requirements and does not imply
that missing selected artifacts, benchmark analysis, VM checks, capture privacy
or browser validation have been completed.

The EDA's duplicate/constant/correlation cells were added during the final audit
and have no benchmark outputs. The ML notebook contains experiment code but no
saved numeric evaluation outputs. Run notebooks only when the data owner provides
the required benchmark inputs; avoid overwriting selected artifacts during demos.
Historical selected-model metric/tuning claims need the ML owner's outputs.

Notebook syntax and structure can be checked without running training:

```sh
python - <<'PYCODE'
import ast
import json
from pathlib import Path
import nbformat
for path in Path('notebooks').glob('*.ipynb'):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            ast.parse(cell.source)
    print(path, 'structure and code syntax OK; not executed')
PYCODE
```
