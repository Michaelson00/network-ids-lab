# System integration and DevOps architecture

The Flask application factory validates one 78-feature flow per request, calls
the selected scaled Random Forest, passes its label/probability through the
existing deterministic rules and risk pipeline, then stores non-benign alerts
in SQLite. Existing legacy rows survive additive schema migration.

The static dashboard is served at `/` with same-origin `/api` calls. It polls
real alerts/metrics and distinguishes degraded model readiness from API uptime.
Alert rendering uses text nodes. The local server binds to loopback without debug.

Tests exercise the loader/scaler/classifier using temporary fitted fixtures,
all four categories, rule-only overrides, validation, storage, migration and
API/dashboard routing. This is not evidence of selected-model accuracy or raw
packet replay: model/scaler artifacts and capture-to-feature adapters are absent.
No immutable audit log or production SOC capability is claimed.

See [RUN_AND_TEST.md](../RUN_AND_TEST.md) for exact commands and remaining
model-owner requirements. The existing historical evaluation reports are retained.
