# SentinelNIDS dashboard

Start `python -m src.api.app` at the root, then open http://127.0.0.1:5000/.
The same-origin API serves HTML, CSS, JS, local Chart.js and official Lucide SVG
symbols. No CDN, frontend build or direct file opening is required.

The dashboard starts with a short welcome, a clear safe-demo action and a
two-step path: try an example, then review its saved result. Charts, filters,
offline capture analysis and detailed system status are available in optional
expandable sections so first-time users are not overwhelmed. Plain-language
labels explain that examples are simulated and no live network is monitored.
Alerts refresh from SQLite every five seconds; the confirmed reset only removes
demo rows. API failures identify stale/unavailable data.

Charts aggregate persisted attack alerts, not processed/benign flows or accuracy.
All demo records are explicitly labelled. Desktop/mobile Chrome rendering,
Lucide geometry and complete input-to-dashboard flow are tested with
`python tests/browser_smoke.py`. Licenses: [vendor README](vendor/README.md).
See [run guide](../RUN_AND_TEST.md) for operational limits.
