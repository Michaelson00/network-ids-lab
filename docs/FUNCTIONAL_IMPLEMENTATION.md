# Functional implementation — 2026-10-24

Superseding blocker-resolution pass (2026-10-24): default demos now automatically
use installed selected ML or transparent rules-only DEMO MODE. The older synthetic
path below remains explicit opt-in. Offline lab PCAP rule processing is now
implemented and verified; it is not a 78-feature exporter. Current handoffs:
[FINAL_BLOCKERS.md](FINAL_BLOCKERS.md), [MISSING_ARTIFACTS.md](MISSING_ARTIFACTS.md)
and [RUN_AND_TEST.md](../RUN_AND_TEST.md).

## Root cause before implementation

The dashboard only polled `/api/alerts` and `/api/metrics`. No input producer,
simulation controls, live capture adapter or replay job called `/api/process`.
A fresh SQLite database therefore stayed empty. Benign results are deliberately
not stored as alerts. In addition, `src/models/random_forest_model.pkl` and
`scaler.pkl` are absent, so manual processing returns 503. The dashboard's paths
and schema are connected; starting the server alone cannot create detections.

## Implementation boundary

A separately labelled synthetic demo model/scaler enables reproducible local
simulation while the team's selected benchmark artifacts are unavailable. It
never replaces those artifacts and provides no benchmark accuracy evidence.
Simulations must pass actual validation → scaler/classifier → existing rules →
risk scoring → structured alert → SQLite, and retain their demo provenance.
No network attacks, packet captures, or observed traffic evidence are generated.

## Implemented flow and controls

`POST /api/demo` creates a server-defined synthetic 78-feature flow and simulated
rule counters. It initializes separate demo artifacts if needed, then calls the
same feature validation, `predict_traffic` implementation, `build_alert`, risk
policy and transactional storage as manual processing. Nothing inserts
preconstructed alert verdicts. The selected `/api/process` path never silently
falls back to the demo model.

The shared alert table is additively migrated with demo provenance, scenario,
model kind, feature/event evidence and optional IP metadata. Existing/legacy rows
remain non-demo. Benign results return without attack storage. Reset requires an
explicit confirmation and deletes only `is_demo = 1` rows. Persistence and reset
preservation are tested.

The dashboard now has five API-backed KPIs, hourly counts/average risk, severity,
category and source charts, scoped data, recent-table filters, evidence details,
separate selected/demo readiness, actionable empty states, error/staleness states,
and non-overlapping 5-second polling. Official locally bundled Lucide SVG symbols
replace icon substitutes. Chart.js is bundled locally; both licenses are retained.

## Files changed

- Runtime: `src/api/app.py`, `src/models/predict.py`, `src/models/demo.py`,
  `src/demo.py`, `src/detection/pipeline.py` (export existing risk factors).
- Dashboard: `dashboard/index.html`, `style.css`, `app.js`, and pinned vendor
  Chart.js/Lucide assets/licenses. No external CDN or frontend build is needed.
- Tests: `tests/test_demo.py`, `tests/browser_smoke.py`; existing tests preserved.
- Setup/docs: `.gitignore`, root/component READMEs, `RUN_AND_TEST.md`, demo flow,
  this note, and dated annotations on historical audit/report/test narratives.
  Previous experimental claims are retained but not presented as reproduced.

## Verification on 2026-10-24

- Baseline before implementation: **13 tests passed**, 0 failed, 0 skipped,
  `Ran 13 tests in 1.426s`, `OK`.
- Final: `.venv/bin/python -m unittest discover -s tests -v` → **18 passed**,
  0 failed, 0 skipped, `Ran 18 tests in 3.291s`, `OK`.
- `.venv/bin/python tests/browser_smoke.py` → **PASS** in actual headless Chrome:
  initial empty state, benign verdict/no attack, port scan/brute force/DoS,
  stored alert retrieval, KPI/chart aggregates, evidence dialog, filters,
  rendered Lucide SVG geometry, 390px mobile overflow checks, 5-second polling
  after an external API submission, demo reset, offline handling and no unhandled
  JavaScript exceptions. Desktop/mobile screenshots were visually inspected.
- CLI prepare, all four scenario commands and confirmed demo-only reset against
  a temporary local API → **PASS**. Temporary servers/profiles/databases removed;
  no user alert records were deleted or demo-seeded by verification.
- `python -m src.demo prepare` → default separate synthetic model/scaler generated
  under ignored `data/demo/`; both reload with 78 inputs. All four inputs pass
  actual scaler/model predictions. Selected benchmark loader still reports the
  missing artifacts (not passed or replaced).
- Compileall, JavaScript syntax, dependency check (`No broken requirements found`),
  documentation file links, whitespace check and bounded source-secret/path scan
  passed. No new captures, credentials, public-target probes or benchmark results
  were produced.

### Actual synthetic scenario results

| Input | Model label | Final category | Source | Risk | Stored |
|---|---|---|---|---:|---|
| benign | BENIGN | BENIGN | ml | 5 / Low | No |
| port_scan | PortScan | PORT_SCAN | both | 200 / Medium | Yes |
| brute_force | SSH-Patator | BRUTE_FORCE | both | 420 / Medium | Yes |
| dos | DDoS | DOS | both | 720 / High | Yes |

Synthetic-model confidence is 1.0 for these demonstration inputs. This is an
actual predicted-class probability on constructed scenarios, not independent
accuracy, calibrated attack likelihood or measured detection performance.

## Remaining boundaries

The **demo** model loads and the full simulated feature-to-dashboard path works.
The team's **selected benchmark model/scaler remain absent** and their load/
real-data acceptance check is still BLOCKED. No live monitoring or PCAP exporter
is implemented. The separately added historical test report mentions a converter
that is not in this checkout; those claims are explicitly qualified, not recreated.
Existing capture payload privacy, VM isolation and benchmark experimental quality
remain separate owner checks. This remains a local educational prototype.

Launch and first detection: see [RUN_AND_TEST.md](../RUN_AND_TEST.md).
