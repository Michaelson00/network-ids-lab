# Final Report

## Security

Owner: Cybersecurity Engineer · Label: `security`

### Threat model

The NIDS prototype monitors an isolated, authorised lab network. Protected
assets are target service availability, authentication accounts, captured
traffic, and the integrity of detection evidence and alerts. The assumed
attacker can reach lab services and generate connection probes, failed login
attempts, or request floods. Routine service use is the benign baseline.

Traffic and supplied event summaries cross a trust boundary into detection;
model outputs and rule matches then become scored alerts for analyst review.
Counts must be aggregated by source IP and target service over the stated
window before calling the rules. The helpers do not perform capture, source
attribution, port deduplication, or authentication-log parsing themselves.
Failed logins therefore require reliable authentication telemetry; encrypted
network traffic alone may not expose them.

The selected threats are reconnaissance (service discovery), brute-force
logins (account compromise), and controlled DoS (availability loss). These
scenarios cover the lab objectives, rather than all intrusion techniques.
Low-rate or distributed attacks, compromised telemetry, and attacks outside
these categories may escape the rules. Benign bursts and authorised scans
may trigger false positives. Thresholds and impact weights are prototype
policy choices; no measured accuracy or production effectiveness is claimed.

### Detection rules

| Scenario    | Trigger                                        | Event fields consumed by the pipeline           |
| ----------- | ---------------------------------------------- | ----------------------------------------------- |
| Port scan   | More than 20 connections in at most 10 seconds | `connection_count`, `connection_window_seconds` |
| Brute force | At least 5 failed logins in at most 60 seconds | `failed_logins`, `login_window_seconds`         |
| DoS         | More than 1000 requests in at most 1 second    | `request_count`, `request_window_seconds`       |

Rules return `(triggered, message)` and run only when both required fields are
present. Missing fields skip a rule; they do not prove that traffic is safe.
The port-scan implementation counts supplied connections, without verifying
that they reach distinct ports. Callers must supply non-negative numeric
counts and positive window durations; the helpers currently do not validate
these constraints.

The pipeline retains every rule match. If ML predicts benign and a rule
matches, the first matching rule selects the category in port scan, brute
force, then DoS order. A non-benign ML category is retained even if a rule
identifies a different category. Detection source is `rule`, `both`, or `ml`;
`both` indicates evidence from both mechanisms, not necessarily agreement.
This ordering can understate a simultaneous higher-impact threat and remains
a prototype limitation.

### Risk scoring logic

`Risk = Likelihood × Impact × Exposure`. Factors are rounded with Python
`round()` and clamped to 1–10, producing scores from 1–1000. Severity is Low
at 1–125, Medium at 126–500, and High at 501–1000.

For non-benign predictions, confidence is clamped to 0–1 and converted to
likelihood with `max(1, min(10, round(confidence * 10)))`. Missing confidence
uses likelihood 6; benign predictions use 1. Any rule match raises likelihood
to at least 9. Confidence is a model signal, not a calibrated probability of
an attack. Exposure defaults to 5 and represents operator-supplied target
criticality/exposure.

| Category       | Impact |
| -------------- | -----: |
| `BENIGN`       |      1 |
| `PORT_SCAN`    |      4 |
| `BRUTE_FORCE`  |      7 |
| `DOS`          |      9 |
| `OTHER_ATTACK` |      6 |

Dataset labels and canonical categories are normalised before scoring;
unrecognised labels become `OTHER_ATTACK`. A direct scorer call with benign
plus a rule match retains category `BENIGN` but uses impact 6; the detection
pipeline instead substitutes the matched rule category first.

For example, `PortScan` with confidence 0.96, a rule match, and exposure 5
scores `10 × 4 × 5 = 200` (Medium). A rule-only DoS event with no confidence
and exposure 8 scores `9 × 9 × 8 = 648` (High).

### Review, validation, and operational boundaries

[Rule documentation](../rules/README.md) and
[scoring documentation](../src/scoring/README.md) describe the implemented
interfaces. Review corrected canonical category handling so pipeline inputs
`PORT_SCAN` and `BRUTE_FORCE` preserve their intended impact weights, and
corrected the scoring README example. Regression assertions cover the exact
port-scan and brute-force scores.

Local verification uses `python3 -m unittest discover -s tests -v` plus
threshold, severity, and scoring checks. This validates deterministic code
behavior; it does not establish detection accuracy on real traffic or a
working capture-to-dashboard deployment. The current API does not call
`build_alert`; prediction, scoring, persistence, and dashboard integration
still require end-to-end verification. Analysts should inspect event evidence,
check whether activity was authorised, and prioritise high-impact targets
before marking an alert triaged.
