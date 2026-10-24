# SentinelNIDS dashboard

Start `python -m src.api.app` at the root, then open http://127.0.0.1:5000/.
The same-origin API serves HTML, CSS, JS, local Chart.js and official Lucide SVG
symbols. No CDN, frontend build or direct file opening is required.

The dashboard offers auto-selected benchmark/rules-only demo controls, database-backed KPIs/4 charts,
5-second polling, recent-table filters, provenance, evidence dialog and a
confirmed demo-only reset. An operating-mode banner and separate rules/risk/ML
status distinguish DEMO MODE from FULL MODEL MODE. Offline capture controls
process existing authorized packet files through actual rule counters. Selected and synthetic model readiness are distinct.
Zero counts are real empty-state data; API failures identify stale/unavailable data.

Charts aggregate persisted attack alerts, not processed/benign flows or accuracy.
All demo records are explicitly labelled. Desktop/mobile Chrome rendering,
Lucide geometry and complete input-to-dashboard flow are tested with
`python tests/browser_smoke.py`. Licenses: [vendor README](vendor/README.md).
See [run guide](../RUN_AND_TEST.md) for operational limits.
