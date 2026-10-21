# Dashboard

Start `python -m src.api.app` from the repository root and open
http://127.0.0.1:5000/. The API serves this HTML with same-origin requests.
Do not open it directly as a local file.

Live endpoints supply readiness, stored-alert counts, category, severity, risk,
detection source and triage information. No dummy data is used. Missing models
show a degraded status. See [run guide](../RUN_AND_TEST.md).
