# Final blocker ownership — 2026-10-24

**Current classification: B — Demo functional.** Default demos automatically use
selected benchmark ML when installed; otherwise they use transparent rules-only
DEMO MODE. Optional synthetic fixtures require explicit opt-in and never stand
in for benchmark artifacts. Existing records and captures are preserved.

| Problem | Code Fix Possible? | Current Status | Required Action | Owner | Required File/Output |
|---|---|---|---|---|---|
| No operational input / empty dashboard | YES | FIXED | Use four dashboard or CLI demos; no automatic traffic generation | Codebase / DevOps | `/api/demo`, dashboard controls, `src/demo.py` |
| Missing demo prediction compatibility | YES | FIXED | Auto-select benchmark ML or explicit rules-only fallback; null labels/confidence when ML absent | Codebase / DevOps | `src/api/app.py`, `src/detection/pipeline.py` |
| API/scoring/storage wiring, initialization and retrieval | YES | FIXED / VERIFIED | Existing pipeline and additive schema reused; no direct frontend alert insertion | Codebase / DevOps | `/api/process`, `/api/demo`, SQLite and `/api/alerts` |
| Selected benchmark model unavailable | PARTIAL | EXTERNAL ARTIFACT NEEDED | Run original notebook final export cell in the actual fitted session; supply trusted same-run forest | ML Engineer | `src/models/random_forest_model.pkl` |
| Paired scaler unavailable | PARTIAL | EXTERNAL ARTIFACT NEEDED | Export same fitted StandardScaler used for training; scaling is required by selected implementation | ML Engineer | `src/models/scaler.pkl` |
| Pending / unsafe export and provenance | YES | EXPORT CODE FIXED; HUMAN EXECUTION NEEDED | Helper checks selected config/order, protects existing files, emits versions/classes/checksums; ML owner runs it | Codebase / DevOps (code); ML Engineer (artifact) | `src/models/export.py`; notebook cell 21; `model_metadata.json` recommended |
| Feature ordering/types mismatch risk | YES | FIXED / VERIFIED | Existing 78-column contract shared by validation, inference and export; no duplicate schema | Codebase / DevOps | `src/features/schema.json`, finite numeric validation, export/loader checks |
| Dataset unavailable for any future retraining | NO (data) | CONDITIONAL HANDOFF | Only if fitted objects/exports cannot be recovered, supply real cleaned dataset; no synthetic benchmark training | Data Analyst | `data/processed/cicids2017_clean.csv`, or original eight CSVs in `data/raw/` |
| Feature list / preprocessing / labels unclear | YES | RESOLVED | Existing schema, notebook scaler/string-label implementation and exact handoff documented; no redo needed | No external action | `docs/MISSING_ARTIFACTS.md`, schema, notebook |
| Existing PCAPs never processed | YES | FIXED / VERIFIED | Offline file reader extracts actual SYN distinct-port/volume counters and calls real rules/risk/storage | Codebase / DevOps | `src/captures/offline.py`, `/api/captures/process`, CLI/UI control |
| Capture filenames/location unknown | YES | RESOLVED | All four authorized captures found and catalogued | No external action | `lab/*.pcapng` exact list in MISSING_ARTIFACTS |
| SSH packet trace cannot prove failed authentication | NO (telemetry) | OPTIONAL REAL-TRAFFIC VALIDATION | Supply timestamped failed-auth server events per source/service if validating real SSH brute force; demo already works | Network Engineer | Authentication failure logs/counters; encrypted PCAP alone insufficient |
| Trimmed DoS sample below threshold | NO (observations) | OPTIONAL REAL-TRAFFIC VALIDATION | Existing 500 packets do not satisfy >1000-in-1s rule; use separately authorized sufficient sample if needed | Network Engineer | Larger authorized capture/telemetry, not needed for DoS demo |
| Benchmark-compatible PCAP feature extraction | PARTIAL | OUTSIDE MINIMAL RULE READER | If benchmark ML must classify raw captures, supply/verify matching CICFlowMeter exporter and resulting 78-feature CSV | Network Engineer + Data Analyst | Compatible labelled flow export/feature semantics, not invented approximations |
| Dashboard misleading healthy status | YES | FIXED | Banner and separate API/DB/rules/risk/ML/mode status; no fabricated confidence in rules mode | Codebase / DevOps | `DEMO MODE` / `FULL MODEL MODE`, `/api/health` |
| Analytics / refresh / alert evidence | YES | FIXED / VERIFIED | Counts/charts/recent records use stored data; polling and capture/demo mutations refresh UI | Codebase / DevOps | Metrics, scoped alerts, details, local Chart.js and Lucide SVGs |
| Safe reset | YES | FIXED / VERIFIED | Confirmed deletion affects only demo rows; actual offline and submitted records survive | Codebase / DevOps | `DELETE /api/demo/alerts` |
| Missing security rules / formula / thresholds | N/A | ALREADY COMPLETE | No repeat work requested; existing policy preserved | No external action | `rules/detection_rules.py`, `src/scoring/risk_scoring.py` |
| Live sniffing unavailable | NOT REQUIRED | NOT A BLOCKER | Primary supported workflow is offline/demo; no capture autostart or privileges required | No external action | Four demos and existing capture reader |
| Startup instructions / external ownership unclear | YES | FIXED | Use runbook and exact artifact handoff; failed benchmark mode is not called healthy | Codebase / DevOps | `RUN_AND_TEST.md`, `docs/MISSING_ARTIFACTS.md` |

## Evidence and code-only completion

The full repository search found only the separate synthetic pair in `data/demo/`,
not hidden/renamed benchmark weights. Current model notebook has saved numeric
outputs and an unexecuted final export cell; those outputs do not serialize its
trees. Export was repaired, not simulated. No training utility was executed or
added to invent missing data; the actual benchmark dataset is absent.

The current application supports a positive demonstration today: open DEMO MODE,
run benign/scan/brute-force/DoS, inspect real rules/risk and stored evidence, watch
charts update, then process `scan_nmap_synscan.pcapng` and see a real offline
PORT_SCAN alert. Default rule-only demo risks: 5, 180, 378 and 648 respectively.
Benchmark and optional synthetic model probabilities are never claimed for these
rule-only outcomes. No rule match is not a guarantee that traffic is benign.

Original benchmark ML was not verified and remains an external artifact handoff.
Actual live isolation, packet-payload privacy and benchmark accuracy remain owner
validation boundaries, not unresolved application wiring.

## Handoff and validation

Exact ML requirements and notebook cell: [MISSING_ARTIFACTS.md](MISSING_ARTIFACTS.md).
Commands and mode selection: [RUN_AND_TEST.md](../RUN_AND_TEST.md).
Final verification results are recorded in the runbook and implementation notes.

## Final executed checks

- Baseline: `python -m unittest discover -s tests -v` → 18 passed, 0 failed.
- Final same command → **24 passed, 0 failed, 0 skipped**, `Ran 24 tests in 4.861s`, `OK`.
- Real Chrome: DEMO MODE banner, four rule-only demos, charts/KPIs, evidence,
  Lucide/mobile layout, polling, actual Nmap capture processing and reset that
  retains the capture alert → PASS. Temporary browser/server state removed.
- Actual CLI commands: four default demos, capture catalogue, real Nmap ingestion
  and demo-only reset → PASS against temporary local storage.
- Export/checksum/schema tests use test-owned fitted objects; they do not export
  synthetic fixtures as real benchmark artifacts. Real benchmark loader remains
  unavailable, and full-mode wiring tests do not claim real-model accuracy.
- Notebook structure/code syntax, shared 78-column sample schema, compileall,
  JavaScript syntax, documentation links, dependency consistency and
  `git diff --check` passed. No benchmark training was executed.
- The user's tracked database already had two rows at the start and still has
  two rows. It was inspected read-only; no presentation seed/reset was performed
  against it. Existing captures and saved experimental outputs were preserved.
