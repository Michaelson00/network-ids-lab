# SentinelNIDS / Network IDS Lab — Final Report

Educational prototype. This report separates repository evidence, owner-reported
historical observations, and checks run during the final audit. Completion is
tracked in [FINAL_ISSUE_AUDIT.md](FINAL_ISSUE_AUDIT.md).

## Lab and methodology

The network owner documents Kali (`192.168.56.102`) and Ubuntu
(`192.168.56.101`) VirtualBox VMs on a host-only `192.168.56.0/24` network,
Wireshark capture on `eth0`, and temporary NAT solely for package installation.
See [lab setup](../lab/README.md) and [methodology](../lab/methodology.md).
These are documented owner observations; the audit did not boot or test the VMs.

Four existing PCAPNG artifacts cover baseline ICMP, SYN port scanning, repeated
SSH connections, and trimmed DoS traffic. Their filenames and file headers were
checked; packet-level scenario attribution and payload privacy were not certified.
They are already tracked, despite the current ignore rule for new captures.
Publication/storage review remains with the network owner. The selected ML model
uses the separate benchmark below, not demonstrated ingestion of these captures.

## Dataset, cleaning and features

The benchmark is CICIDS2017 from the [UNB Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html).
The notebooks expect the MachineLearningCSV flow tables under `data/raw/`.
The historical EDA output records 2,830,743 rows and 79 columns before cleaning,
1,358 missing cells, and 4,376 positive-infinity cells (these counts may overlap).
Whitespace is stripped from column names, infinities become NaN, incomplete rows
are dropped, and corrupted Web Attack label separators are normalized.

Saved cleaned output records 2,827,876 rows, 78 numeric features plus `Label`,
54 integer columns, 24 float columns and one string column. The 15-class
distribution is strongly imbalanced: 2,271,320 BENIGN flows versus rare classes
including Infiltration (36), SQL injection (21), and Heartbleed (11). Full counts
remain in [EDA](../notebooks/01_eda.ipynb); these historical outputs were not rerun.

All 78 inputs remain in the selected model. [Feature notes](features.md) and
[`schema.json`](../src/features/schema.json) define exact names/order;
`Label` and a separate binary `Attack_Type` target are excluded. Duplicate header
variant `Fwd Header Length.1` remains intentionally. Zero-importance features in
the separate DA1 CSV were considered, but cannot justify changing this model.
New duplicate/constant/correlation diagnostic cells are unexecuted because
benchmark data is absent; no new findings or feature reduction is claimed.
Inference rejects invalid rows rather than silently dropping them.

## ML, modelling and reported results

The [modelling notebook](../notebooks/02_model_comparison.ipynb) defines
`X = data.drop(columns=["Label"])`, `y = data["Label"]`, a 300,000-row sample
(seed 42), an 80/20 stratified split, and a StandardScaler fitted on training
data only. Class-weighted Logistic Regression is the baseline; a 100-tree
class-weighted Random Forest is selected. A 200-tree/depth-30 variant is defined
for tuning. Feature importance and classification reports are computed by code.

The owner reports weak Bot/XSS/Web Attack Brute Force results and little tuning
improvement, attributing them to limited minority samples. These observations
and per-class figures in [model-handoff.md](model-handoff.md) lack saved numeric
outputs in the model notebook and were not independently reproduced. Insufficient
samples are a plausible explanation, not a demonstrated sole cause. The original
forest is preserved; no audit retraining or model substitution was performed.

The separate historical DA1 binary result CSV reports accuracy 99.92%, attack
detection rate 99.89%, false-alarm rate 0.064%, 42 missed attacks and 53 false
alarms. Those files are retained as reported outputs, not fresh multiclass or
end-to-end accuracy evidence; exact split/provenance needs the data owner.
Both selected `random_forest_model.pkl` and `scaler.pkl`, plus training package
versions, are missing. Real selected-model loading/prediction is therefore blocked.


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
present. Absent pairs skip a rule; incomplete pairs are rejected by the pipeline. Neither proves that traffic is safe.
The port-scan implementation counts supplied connections, without verifying
that they reach distinct ports. Callers must supply non-negative numeric
counts and positive window durations; the pipeline validates these constraints before calling the helpers.

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
working capture-to-dashboard deployment. The API now calls `build_alert`; automated tests exercise model/scaler loading,
prediction, scoring, persistence and dashboard routing with temporary fixture
artifacts. The selected model/scaler are missing, and raw capture-to-feature
extraction remains external. See [RUN_AND_TEST.md](../RUN_AND_TEST.md). Analysts should inspect event evidence,
check whether activity was authorised, and prioritise high-impact targets
before marking an alert triaged.


## DevOps and integrated application

The Flask application factory serves the dashboard at `/` and the local API at
`/api`. `POST /api/process` accepts exactly one validated flow in `features`,
optional aggregated rule telemetry in `event`, and exposure 1–10. The path is:

Flow feature input → API validation → `predict_traffic` → paired scaler/model
→ label/class probability → `build_alert` → rules → risk → SQLite → dashboard.

Non-benign alerts are saved transactionally; benign results are returned without
creating attack rows. `GET /api/alerts` returns the latest 20 stored alerts and
`GET /api/metrics` counts stored attacks by category. SQLite stores original
label, normalized category, confidence, source, rule matches, risk/severity,
triage status and UTC SQLite timestamp; legacy rows survive additive migration.
Connections are closed explicitly. `GET /api/health` reports degraded model
readiness while artifacts are missing; processing returns a useful 503.

The existing dashboard fetches same-origin endpoints, polls stored alerts/counts,
uses text nodes for data, and supports horizontal table scrolling. There is no
dummy data fallback. A source, category and severity are shown. Triage status is
displayed, but there is no status-update endpoint or recommended-action engine.
See [integration notes](devops-final-report.md) and [runbook](../RUN_AND_TEST.md).

## Testing and evaluation

The audit ran existing tests first: 13 passed, 0 failed, 0 skipped. The same
suite is rerun after final changes; exact final results and smoke commands are
recorded in [FINAL_ISSUE_AUDIT.md](FINAL_ISSUE_AUDIT.md). Tests fit tiny temporary
Random Forest/scaler artifacts and use Flask's test client and temporary SQLite.
They cover validation/order, sample CSV shape, artifact failures, benign, scan,
brute force, DoS, rule-only/ML-only detections, risk boundaries, migrations,
persistence, health/metrics, and dashboard routing. This proves application
integration with fixtures; it does not establish selected-model detection quality.

Loopback HTTP and mocked-DOM JavaScript checks exercise connectivity/error paths;
actual browser layout, VM isolation, benchmark reruns, and real-model holdout
performance are separate unverified boundaries. No live attack was generated.

## Limitations and remaining handoffs

- ML owner: paired trained artifacts, training versions, saved evaluation/tuning
  outputs and labelled holdout examples. The system is not real-model demo-ready
  until this handoff is complete and the live sample test succeeds.
- Data owner: benchmark inputs and reproducible duplicate/correlation findings;
  confirm DA1 experiment provenance. Do not fabricate missing results.
- Network/data owners: external compatible PCAP-to-flow exports and authentication
  telemetry for rule counters; no raw packet-to-feature service is implemented.
- Network owner: existing capture privacy/publication review and actual VM checks.
- Presenter: verify real browser layout and final demo on the target machine.

This loopback Flask/SQLite educational prototype has no production SOC security,
scalability, availability or detection-accuracy guarantee. The test suite is not
a substitute for these missing experimental and operational checks.
