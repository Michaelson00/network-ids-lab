# API and SQLite backend

Run `python -m src.api.app` from the root; factory: `src.api.app:create_app`.
Schema initialization and additive migration happen automatically. Existing rows
retain submitted/legacy provenance; no startup deletion occurs. SQLite default:
root `nids_alerts.db`, configurable with `NIDS_DB_PATH`.

- `GET /`: dashboard; `GET /assets/<path>` serves local CSS/JS/vendor assets.
- `GET /api/health`: selected/demo model readiness, rule/risk engine and storage.
- `POST /api/process`: selected-model prediction of one validated `features` row;
  optional `event`, `exposure`, `source_ip` and `destination_ip` metadata.
- `POST /api/demo`: `{scenario: benign|port_scan|brute_force|dos}`. Uses separate
  selected benchmark model when available, otherwise rules-only classification
  with null ML output. `model_mode` accepts `auto` (default), `rules`, or explicitly
  `synthetic` for the earlier optional fixture model.
- `GET /api/captures`: list available authorized lab PCAP/PCAPNG files.
- `POST /api/captures/process`: `{capture: filename}` reads actual packet headers,
  extracts distinct-port/SYN-volume counters and uses rules/risk/storage with
  `model_kind: offline_rules`, no guessed 78-feature ML table or SSH failures.
- `GET /api/alerts`: newest first, default 20; `limit` 1–100, optional `mode`
  (`all`, `demo`, `observed`), `severity`, `category`, `source`, `status` filters.
- `GET /api/alerts/<id>`: stored evidence including features, rule inputs and risk factors.
- `GET /api/metrics`: all stored-alert totals, severity/category/source groups,
  active/demo/submitted counts and last-24-hour UTC buckets (25 hourly labels
  with partial endpoint hours). Empty hours have zero count and null average risk.
  Optional `mode` applies to all aggregates; recent-table filters do not.
- `DELETE /api/demo/alerts`: requires JSON `{confirm: true}`, deletes only demo rows.

Both input paths call `predict_traffic` → `build_alert` → original rules/risk →
SQLite. Benign results are returned without attack storage. Demo provenance,
model kind, scenario, available IPs, timestamp and detailed evidence are retained.
Missing selected artifacts return 503, never silent synthetic substitution.
Invalid inputs return 400; storage/model errors return 503. Local prototype only.
See [runbook](../../RUN_AND_TEST.md).

Health exposes `operating_mode`, `rules_engine` and `risk_engine` separately.
Selected model missing is `DEMO_MODE`, never a healthy full benchmark system.
See [blocker ownership](../../docs/FINAL_BLOCKERS.md).
