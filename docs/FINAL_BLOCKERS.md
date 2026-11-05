# Final blocker ownership — 2026-11-05

**Current classification: FULL_MODEL_MODE runtime verified.** Selected benchmark
model/scaler artifacts are checked in; the runtime validates their metadata,
schema and hashes. Benchmark accuracy still needs a labelled holdout evaluation.
Optional synthetic fixtures require explicit opt-in and never replace the
selected model. Existing records and captures are preserved.

| Problem | Code Fix Possible? | Current Status | Required Action | Owner | Required File/Output |
|---|---|---|---|---|---|
| No operational input / empty dashboard | YES | FIXED | Use four dashboard or CLI demos; no automatic traffic generation | Codebase / DevOps | `/api/demo`, dashboard controls, `src/demo.py` |
| Missing demo prediction compatibility | YES | FIXED | Auto-select benchmark ML or explicit rules-only fallback; null labels/confidence when ML absent | Codebase / DevOps | `src/api/app.py`, `src/detection/pipeline.py` |
| API/scoring/storage wiring, initialization and retrieval | YES | FIXED / VERIFIED | Existing pipeline and additive schema reused; no direct frontend alert insertion | Codebase / DevOps | `/api/process`, `/api/demo`, SQLite and `/api/alerts` |
| Selected model blocked by stale schema hash | YES | FIXED / VERIFIED | Corrected the manifest hash; checked-in model loads | Codebase / ML Engineer | `src/models/random_forest_model.pkl`, `src/models/model_metadata.json` |
| Paired scaler unavailable | YES | FIXED / VERIFIED | Checked-in paired scaler passes 78-feature order and hash checks | Codebase / ML Engineer | `src/models/scaler.pkl` |
| Pending / unsafe export and provenance | YES | FIXED / VERIFIED | Export helper protects existing files; checked-in metadata verifies classes, schema and artifact hashes | Codebase / DevOps | `src/models/export.py`, `src/models/model_metadata.json` |
| Feature ordering/types mismatch risk | YES | FIXED / VERIFIED | Existing 78-column contract shared by validation, inference and export; no duplicate schema | Codebase / DevOps | `src/features/schema.json`, finite numeric validation, export/loader checks |
| Raw benchmark dataset unavailable | NO (data) | STILL MISSING / NOT REQUIRED FOR RUNTIME | Supply real cleaned data to retrain, independently reproduce, or build a labelled holdout evaluation | Data Analyst | `data/processed/cicids2017_clean.csv`, or original eight CSVs in `data/raw/` |
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

The selected model/scaler and manifest are now tracked under `src/models/`.
Runtime checks confirm the selected classifier configuration, labels, scaler
feature order and checksums. The raw/cleaned benchmark dataset remains absent,
so no retraining or independent accuracy evaluation was performed.

The current application supports FULL_MODEL_MODE: run benign/scan/brute-force/DoS,
inspect model/rule risk and stored evidence, watch
charts update, then process `scan_nmap_synscan.pcapng` and see a real offline
PORT_SCAN alert. Default rule-only demo risks: 5, 180, 378 and 648 respectively.
Benchmark and optional synthetic model probabilities are never claimed for these
rule-only outcomes. No rule match is not a guarantee that traffic is benign.

The included model's runtime wiring is verified; benchmark accuracy is not.
Actual live isolation, packet-payload privacy and accuracy against a labelled
holdout remain owner validation boundaries, not unresolved application wiring.

## Handoff and validation

Exact ML requirements and notebook cell: [MISSING_ARTIFACTS.md](MISSING_ARTIFACTS.md).
Commands and mode selection: [RUN_AND_TEST.md](../RUN_AND_TEST.md).
Final verification results are recorded in the runbook and implementation notes.

## Final executed checks

- `.venv/bin/python -m unittest discover -s tests -v` → **25 passed, 0 failed**.
- `.venv/bin/python -m compileall -q src rules tests` and `git diff --check` → PASS.
- Selected-model smoke: `/api/health` returned healthy `FULL_MODEL_MODE`; default
  demo used the selected model; sample `/api/process` returned HTTP 200.
- Real Chrome rules-only fallback: four demos, charts/KPIs, evidence, Lucide/mobile
  layout, polling, actual Nmap capture processing and demo reset preserving the
  capture alert → PASS. The test explicitly disables selected-model loading.
  Temporary browser/server state and screenshots removed.
- Export/checksum/schema tests use test-owned fitted objects; they do not export
  synthetic fixtures as real benchmark artifacts. The checked-in model was
  separately loaded and exercised after its manifest hash was corrected; this
  does not establish benchmark accuracy.
- The manifest regression test checks schema and model/scaler checksums. No
  benchmark training or labelled accuracy evaluation was performed.
- The user's tracked database already had two rows at the start and still has
  two rows. It was inspected read-only; no presentation seed/reset was performed
  against it. Existing captures and saved experimental outputs were preserved.
