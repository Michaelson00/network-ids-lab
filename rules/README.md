# Detection Rules

`detection_rules.py` supplies stateless threshold helpers:

| Function                                                  | Trigger                             | Alert message          |
| --------------------------------------------------------- | ----------------------------------- | ---------------------- |
| `detect_port_scan(connection_count, time_window_seconds)` | count > 20 and window <= 10 seconds | `Port Scan Detected`   |
| `detect_brute_force(failed_logins, time_window_seconds)`  | count >= 5 and window <= 60 seconds | `Brute-Force Detected` |
| `detect_dos_traffic(request_count, time_window_seconds)`  | count > 1000 and window <= 1 second | `DoS Traffic Detected` |

Each returns `(True, message)` when triggered, otherwise `(False, "Normal")`.
Exactly 20 connections or 1000 requests do not trigger; exactly 5 failures do.

Callers must aggregate counts by source IP and target service and provide
non-negative numeric counts and positive durations in seconds. Helpers do
not validate inputs, track windows, identify sources, or verify distinct
ports. Login failure counts require authentication telemetry.

```python
from rules.detection_rules import detect_port_scan

assert detect_port_scan(21, 10) == (True, "Port Scan Detected")
```

`src/detection/pipeline.py` consumes the field pairs
`connection_count` / `connection_window_seconds`,
`failed_logins` / `login_window_seconds`, and
`request_count` / `request_window_seconds`. Missing pairs skip their rule.
All matches are retained; benign ML predictions use the first matching
category (port scan, brute force, then DoS). Non-benign ML categories remain.

These fixed lab thresholds can miss slow/distributed attacks and flag benign
bursts. See the [final report security section](../docs/final-report.md#security)
for the threat model, scoring policy, and integration limitations.

Run local regression tests from the repository root:

```bash
python3 -m unittest discover -s tests -v
```
