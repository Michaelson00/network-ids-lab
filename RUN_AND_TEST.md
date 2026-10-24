# Run and test SentinelNIDS

Current classification: **B — Demo functional.** Rules, risk scoring, API, SQLite,
dashboard, four demo scenarios and offline lab-capture analysis work today.
The selected benchmark model/scaler must still be exported by the ML owner.
See [FINAL_BLOCKERS.md](docs/FINAL_BLOCKERS.md) and
[exact artifact handoff](docs/MISSING_ARTIFACTS.md).

## 1. Install and start

From repository root, with Python 3.11+ and a POSIX shell:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.api.app
```

Open **http://127.0.0.1:5000/**. The same loopback server serves API, dashboard,
local Chart.js and official Lucide SVGs. No frontend build, CDN or separate UI
server is required. Do not open the HTML as a local file.

SQLite initialization/migration is automatic and preserves existing records.
No model files, traffic producer, live capture, root access or real attacks are
required for default demos. Scapy is used only to read stored captures offline.

Optional settings (set before startup):

```sh
export NIDS_DB_PATH="$PWD/nids_alerts.db"
export NIDS_DEMO_MODEL_DIR="$PWD/data/demo"
```

The defaults are those repository-root locations. The second variable is for
optional synthetic fixtures, not default DEMO MODE, and cannot point at
`src/models`. No secrets are required. Stop with **Ctrl+C**; `deactivate` exits
the environment. Database records survive restarts.

## 2. Current operating mode

```sh
curl --fail http://127.0.0.1:5000/api/health
```

- **FULL MODEL MODE** / `FULL_MODEL_MODE`: the paired selected classifier/scaler
  loaded and passed feature-contract/available export-metadata checks. Default
  demo inputs call that model, then the existing rules/risk path.
- **DEMO MODE** / `DEMO_MODE`: benchmark ML is missing or incompatible. The
  dashboard states “Benchmark ML model unavailable. Demo detection mode active.”
  Default demos run **rules only**. `label` and `confidence` are null,
  `ml_applied` is false, `model_kind` is `rules_only`. No synthetic classifier is
  silently substituted, and no benchmark accuracy is claimed.

API, database, rules engine, risk engine, selected model and mode have separate
indicators. Health remains `status: degraded` without benchmark ML even when
rules-only operation works. Loading errors are shown; startup does not pretend
all components are healthy. A selected-model inference failure returns 503,
not a hidden fallback verdict.

## 3. First detection and all four demos

Open **Detection demo**, click **Benign traffic**, then **Port scan**, **Brute
force**, and **Denial of service**. Each request goes through feature validation,
ML when available, actual deterministic rules, risk scoring and transactional
storage. Dashboard KPIs/charts/recent alerts refresh immediately and poll every
5 seconds. Generated inputs/IPs are marked **Demo / Simulated**.

Or use a second terminal, from root:

```sh
source .venv/bin/activate
python -m src.demo run benign
python -m src.demo run port_scan
python -m src.demo run brute_force
python -m src.demo run dos
```

Equivalent API first detection:

```sh
curl --fail -X POST http://127.0.0.1:5000/api/demo \
  -H 'Content-Type: application/json' -d '{"scenario":"port_scan"}'
```

Expected **rules-only DEMO MODE** results:

| Scenario | Category / assessment | ML label/confidence | Risk | Stored |
|---|---|---|---:|---|
| benign | BENIGN / no matched rule | null / null | 5 / Low | No |
| port_scan | PORT_SCAN | null / null | 180 / Medium | Yes |
| brute_force | BRUTE_FORCE | null / null | 378 / Medium | Yes |
| dos | DOS | null / null | 648 / High | Yes |

After all four once in a fresh database: **3 alerts, 1 High, 2 Medium, 0 Low,
3 Untriaged**, source `rule`. Existing records increase totals. BENIGN here
means no supported attack rule matched, not a benchmark prediction or a safety
guarantee. Benign results do not create attack records.

The original risk model remains Likelihood × Impact × Exposure, factors 1–10.
A rule match raises likelihood to at least 9. Impact weights remain 1/4/7/9/6
for BENIGN/PORT_SCAN/BRUTE_FORCE/DOS/OTHER_ATTACK. Severity bands: Low 1–125,
Medium 126–500, High 501–1000. Full-model scores depend on actual ML probability;
non-benign ML categories and the existing rule precedence remain unchanged.

## 4. Full Model Mode — exact handoff

Place trusted SAME-RUN files at:

```text
src/models/random_forest_model.pkl
src/models/scaler.pkl
```

Both use `joblib.load`. The selected model was trained on StandardScaler output;
this scaler is required even though forests do not intrinsically require scaling.
No encoder is used. The 78 ordered finite numeric inputs are defined once in
`src/features/schema.json` and shared by API/export/inference. Named inputs are
reordered; positional arrays must already be ordered. Missing/extra/duplicate
columns, target labels, booleans, NaN/infinity and nonnumeric data are rejected.

The ML notebook currently includes saved results but its final export cell was
not executed. In the actual fitted notebook session, run cell 21
(`91aab743f061a8f6`) using `export_fitted(model_rf, scaler)` as documented in
[MISSING_ARTIFACTS.md](docs/MISSING_ARTIFACTS.md). This exports the selected
original 100-tree model, scaler and recommended `src/models/model_metadata.json`
with versions, classes and checksums. Existing files require explicit overwrite
consent in code. Metadata, when supplied, is checked at load time.

If the fitted session is unavailable, the real cleaned benchmark CSV is needed
to reproduce the existing notebook. It is absent here; no retraining script is
run or artificial benchmark generated. Saved notebook outputs are historical
experimental evidence, not trained weights or a fresh accuracy validation.

Restart the server, check `FULL_MODEL_MODE`, then run:

```sh
python tests/test_real_traffic.py
```

This submits the first existing sample CSV row through `/api/process`; its
unlabelled row is not assumed benign. The endpoint stays strict and returns 503
without real benchmark artifacts. Default `/api/demo` uses selected inference
when available, while retaining simulated-input provenance.

## 5. Offline PCAP mode — actual supplied captures

In **Offline capture analysis**, choose `scan_nmap_synscan.pcapng` and click
**Process offline capture**. Or:

```sh
python -m src.demo captures
python -m src.demo capture scan_nmap_synscan.pcapng
```

Equivalent API request:

```sh
curl --fail -X POST http://127.0.0.1:5000/api/captures/process \
  -H 'Content-Type: application/json' -d '{"capture":"scan_nmap_synscan.pcapng"}'
```

Only existing authorized files directly under `lab/` are accepted; no arbitrary
filesystem path, upload, live sniffing or replay is supported. Processing is
bounded to 50 MiB/200,000 packets. Packet headers are read offline, grouped by
source/target; distinct SYN destination ports use sliding 10-second windows,
SYN attempt volume is grouped by destination service in 1-second windows.
Counters run through the EXISTING security rules/risk and the same alert store.
These are real packet observations, not demo rows; demo reset preserves them.

Actual checks on supplied files:

| File in `lab/` | Packets read | Supported rule outcome |
|---|---:|---|
| `baseline_normal_traffic.pcapng` | 128 | No matching rule |
| `scan_nmap_synscan.pcapng` | 2017 | 1000 distinct SYN destination ports in window → PORT_SCAN, risk 180 |
| `scan_bruteforce_ssh.pcapng` | 1297 | No failed-auth evidence inferred from encrypted SSH |
| `scan_dos_trimmed.pcapng` | 500 | Below >1000-in-1s threshold; no DoS manufactured |

The volume counter is initial SYN attempts, a connection-request proxy, not an
HTTP request count. This is **not a CICFlowMeter clone or 78-feature exporter**.
Benchmark ML is not applied to packet-counter summaries even in full-model mode.
Compatible flow export and real authentication failures would be required for
those additional validations. No rule match does not establish benign traffic.
Stored evidence includes file hash, capture time range, counts and rule inputs;
alert timestamps show analysis time. Reprocessing creates a new analysis alert.

## 6. Analytics, evidence and reset

KPIs, severity/category/source charts and recent records come from SQLite.
Counts describe stored attack alerts, not processed/benign flows, throughput or
accuracy. Activity shows hourly counts and mean risk in the last 24 hours (25
hour labels with partial endpoints). Empty-hour risk is null, not fake zero.

Scope affects overview/table data; severity/category/source filters affect only
the recent 50 matching rows. “Submitted / Legacy” scope also includes real offline
capture observations. Demo, offline-rule and selected-model provenance remain
visible. Open an alert to inspect actual stored evidence and risk factors.

Use **Clear demo alerts** and confirm, or:

```sh
python -m src.demo reset --confirm
```

Only `is_demo = 1` records are deleted. Offline capture, manual and legacy
records are preserved. Nothing is deleted at startup. API failures label
stale/unavailable values instead of inventing zeros. Lucide SVGs and Chart.js are
bundled under `dashboard/vendor/` with licenses; no runtime CDN is needed.

## 7. Optional synthetic fixture compatibility

The earlier synthetic model remains available ONLY by explicit opt-in, not as a
benchmark or automatic fallback:

```sh
python -m src.demo prepare
python -m src.demo run port_scan --model-mode synthetic
```

It saves only under ignored `data/demo/`, never the selected-model directory.
Records carry `model_kind: synthetic_demo` and simulated provenance. Synthetic
confidence is not benchmark accuracy. Default `run` uses `--model-mode auto`;
`--model-mode rules` explicitly skips ML even when selected artifacts exist.

## 8. Tests and final presentation

```sh
python -m unittest discover -s tests -v
python -m compileall -q src rules tests
python -m pip check
python tests/browser_smoke.py --output /private/tmp/sentinelnids-browser
```

The unittest suite uses temporary DBs/artifacts and actual capture files; it
checks mode selection, null ML provenance, rules/scoring, export/schema/checksum
validation, persistence/reset protection, filters, analytics and error responses.
The optional real Chrome check verifies mode banner, all four scenarios, real
charts/KPIs, evidence, capture ingestion, mobile/Lucide rendering, polling and
reset preserving actual capture rows. Chrome/Chromium and loopback/subprocess
permission are needed; set `NIDS_CHROME_BINARY` if not found. `websocket-client`
is already included through the notebook dependencies. No benchmark model is
claimed verified; full-mode wiring is tested with explicitly test-owned fixtures.

Presentation: start → show DEMO MODE → benign/no attack → port scan/180 → open
rule evidence → charts update → brute force/DoS → process real Nmap capture →
inspect packet counters → clear demo rows while retaining capture alert → explain
missing ML export and external auth/feature validation boundaries → Ctrl+C.

## 9. Troubleshooting

- Zero alerts: run a demo or process a stored capture; startup is not a traffic
  producer. Check scope/table filters. Benign events deliberately create no alerts.
- No selected model: use working DEMO MODE, or obtain the exact ML export. Never
  copy synthetic artifacts into `src/models` or treat package-test pickles as ML.
- Full-model load fails: check paired files, training package versions and optional
  metadata checksums/schema. Restart after changing artifacts.
- Capture request rejected: select a filename listed by `/api/captures`; ensure
  Scapy is installed through requirements, readable file, and bounded size.
- SSH/trimmed DoS produces no alert: this is the actual evidence/threshold result,
  not a broken pipeline. Use supported demos for reproducible scenarios.
- HTTP 400: check feature count/types, valid IP strings, exposure 1–10 and complete
  count/window pairs with positive durations.
- Storage failure: check database parent/path permissions; use a separate DB path
  for a fresh presentation rather than deleting existing records.
- API offline: start from root in `.venv`; inspect `/api/health`. Port 5000 busy:
  `python -m flask --app src.api.app:create_app run --host 127.0.0.1 --port 5001`,
  then use `python -m src.demo --url http://127.0.0.1:5001 run port_scan`.
- Offline dependency install requires a wheel cache or approved network access.

Exact external ownership: [FINAL_BLOCKERS.md](docs/FINAL_BLOCKERS.md).
This is a local educational prototype, not an authenticated production SOC.

### Latest executed validation (2026-10-24)

`python -m unittest discover -s tests -v`: **24 passed, 0 failed, 0 skipped**,
`Ran 24 tests in 4.861s`, `OK`. Real Chrome and CLI end-to-end checks passed,
including DEMO MODE, four scenarios, actual Nmap capture analysis and reset
preserving offline observations. Full benchmark artifacts remain an external
handoff; no real benchmark-model success is claimed. Existing user data was
preserved; all operational verification used temporary databases.
