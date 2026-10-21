# API and SQLite backend

From the repository root: `python -m src.api.app`.
The application factory is `src.api.app:create_app`; it initializes/migrates
SQLite on startup. Database default: root `nids_alerts.db`; override with
`NIDS_DB_PATH`.

- `GET /`: dashboard, same origin as API.
- `GET /api/health`: model readiness and storage; degraded if models missing.
- `POST /api/process`: one flow in `features` (one 78-value row or named record),
  optional `event` rule telemetry and `exposure` (1–10).
- `GET /api/alerts`: latest 20 stored attack alerts, newest ID first.
- `GET /api/metrics`: stored attack totals and counts per category.

The endpoint calls `predict_traffic` → `build_alert` → rules/risk → SQLite.
Benign results are returned without storage. Errors use JSON, invalid inputs
return 400, model/storage failures 503. No client-supplied labels are trusted.
See [complete instructions](../../RUN_AND_TEST.md).
