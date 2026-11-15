# Developer handoff and review guide

Status checked: 2026-11-05. This is a local educational NIDS prototype, not a
production monitoring service.

## What currently works

- The Flask app serves the dashboard and API locally.
- Four safe, simulated flows run through validation, the selected model when
  available, existing rules, risk scoring, SQLite storage and dashboard results.
- The checked-in Random Forest and paired scaler load in `FULL_MODEL_MODE`.
  The model manifest, 78-feature schema and artifact hashes are checked at
  runtime. This proves integration, **not detection accuracy**.
- If selected-model loading is unavailable, the default demo uses transparent
  rules-only behavior; it does not silently substitute synthetic ML predictions.
- Existing lab PCAPs can be analyzed offline with packet-header counters and
  rules. This is not a PCAP-to-model-feature converter.
- Demo reset is limited to demo records; submitted/imported records are retained.
- The dashboard is designed for local, manual use. It does not monitor live
  network traffic or generate traffic.

## Suggested review path

1. Read [RUN_AND_TEST.md](../RUN_AND_TEST.md) for setup, API behavior and
   validation commands. Start the server on a feature branch with a temporary
   `NIDS_DB_PATH`; do not clear or repurpose a shared database.
2. Trace the data path in `src/api/app.py`: request validation, model handling,
   detection, storage, retrieval and error responses.
3. Check `src/features/schema.json` against `src/features/prepare.py` and
   `src/models/predict.py`. The model contract is exactly 78 ordered numeric
   features; preserve ordering and reject invalid inputs.
4. Review `src/detection/pipeline.py`, `rules/detection_rules.py` and
   `src/scoring/risk_scoring.py` together. Benign flows do not create attack
   alerts, and a rules-only result must not claim an ML label or confidence.
5. Review `src/captures/offline.py` separately from model inference. It uses
   observed packet-header counters for existing rules; do not describe its
   output as benchmark-model classification.
6. For UI changes, check `dashboard/index.html`, `dashboard/app.js` and
   `dashboard/style.css`; verify both a demo result and an empty/error state at
   desktop and mobile widths.
7. In a pull request, state the behavior changed, the tests run, and any
   limitations. Keep changes focused and do not commit local databases,
   capture data, credentials or generated model artifacts without review.

## Validation to run before merging

From the repository root, with the project environment installed:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q src rules tests
node --check dashboard/app.js
git diff --check
```

For browser-facing changes, also run
`.venv/bin/python tests/browser_smoke.py --output /private/tmp/sentinelnids-browser`
with Chrome/Chromium available. It exercises the dashboard in an isolated
database and explicitly tests the rules-only fallback. The selected-model path
has been separately smoke-tested against the checked-in artifacts. Do not treat
the browser smoke's mocked rules-only run as model-accuracy evidence.

Latest recorded validation on 2026-11-05: 25 unit/integration tests passed;
Python compilation, JavaScript syntax and diff checks passed; Chrome smoke
covered demos, charts, alert details, filters, offline capture processing,
reset, desktop and mobile. A separate selected-model smoke reached
`FULL_MODEL_MODE` and a sample `/api/process` request returned HTTP 200.
These checks do not measure benchmark accuracy.

## Remaining work, by goal

### Needed to claim model detection quality

- Obtain a trusted, labelled holdout that was not used to train or tune the
  checked-in model. The raw benchmark dataset and an independent holdout are not
  in this checkout, so its real-world quality cannot currently be reproduced.
- Agree on acceptance criteria before evaluating. Report per-class precision,
  recall and F1, confusion matrix, benign false-positive rate, and dataset
  provenance; do not rely on overall accuracy alone, especially for rare
  classes.
- Record the evaluation command, package/runtime versions and data/model
  checksums. Do not replace the checked-in model or scaler until provenance,
  schema compatibility and evaluation results have been reviewed.

### Needed only if raw captures should use the ML model

- Build or adopt a verified CICFlowMeter-compatible PCAP-to-flow exporter that
  produces the same 78 features with matching definitions and ordering.
- Validate extracted flows against known labelled examples. The current offline
  reader supports a narrower packet-header/rule workflow and must remain
  labelled as such.

### Needed only if live monitoring is a product goal

- Define the authorized capture environment, interface selection, service
  privileges, start/stop behavior, flow-windowing and failure handling before
  implementation.
- Add explicit consent/authorization, resource limits, privacy-aware retention,
  and tests using isolated, approved traffic. No live capture is currently
  implemented; do not enable it implicitly.

### Needed before use beyond a local educational demo

- Choose a supported deployment target and production WSGI/server setup; the
  current documented workflow runs a local Flask development server.
- Review authentication/authorization, TLS and network exposure, database
  concurrency/backups/retention, operational logging, dependency maintenance
  and incident handling for that target.
- Perform a privacy review of any capture or flow data before sharing it.

These are scope and readiness items, not claims that a specific exploitable
vulnerability was found. If the project remains a local educational demo, the
first priority is a labelled holdout evaluation; live capture and production
deployment can remain explicitly out of scope.

## Where to find the detailed handoffs

- [Current operating blockers and ownership](FINAL_BLOCKERS.md)
- [Model/data and network-capture requirements](MISSING_ARTIFACTS.md)
- [Runbook and API usage](../RUN_AND_TEST.md)
- [Historical checklist audit](FINAL_ISSUE_AUDIT.md) — dated audit evidence is
  not a substitute for the current status above.
