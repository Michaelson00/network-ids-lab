# Tests

From repository root with dependencies installed:

```sh
python -m unittest discover -s tests -v
```

Detection regressions cover benign, scan, brute force and DoS. Application tests
use temporary fitted fixture models/scalers, a temporary SQLite database, and
Flask's test client; they do not require a running server. They cover feature
validation/order, artifact failures, class probabilities, rules, risk boundaries,
storage persistence/migration, metrics and dashboard routing.

`python tests/test_real_traffic.py` is a separate manual live-API CSV check with
a 30-second request timeout. It requires the real artifacts and running API.
Automated fixtures do not verify the missing selected model or browser rendering.
See [run guide](../RUN_AND_TEST.md).

## Functional demo coverage

`test_demo.py` exercises actual separate synthetic model/scaler loading, all four
scenario predictions, risk values, evidence, persistence, all-record aggregate
metrics versus recent limits, null risk in empty time buckets, query filters,
asset delivery and demo-only reset preserving submitted records.

Optional: `python tests/browser_smoke.py` uses real headless Chrome, a temporary
profile/database/artifacts, and checks four demos, charts/KPIs, alert evidence,
filters, SVG geometry, mobile overflow, polling, reset and offline handling.
It needs loopback/process permission and Chrome/Chromium installed; it is a
separate browser check, not part of the unittest count. Screenshots default to
`/private/tmp/sentinelnids-browser`. See the runbook for prerequisites.

## Blocker-resolution coverage

`test_blocker_resolution.py` checks rule-only null ML provenance, automatic full
model selection, no silent inference fallback, actual existing captures,
nonfabrication of SSH failures/DoS, reset preserving real observations, sliding
windows, and safe export/metadata mismatch rejection. Existing synthetic tests
now explicitly opt in. Browser checks also verify the mode banner and capture
processing. All capture work is offline, with no attack traffic generated.
