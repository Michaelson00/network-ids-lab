# Detection

This folder connects the machine-learning prediction, deterministic security rules, and risk scoring into one detection pipeline.

## Pipeline

```text
ML Prediction
    ↓
Detection Rules
    ↓
Risk Scoring
    ↓
Structured Alert
```

## Main File

The integration logic is located in:

```text
src/detection/pipeline.py
```

This file receives the ML prediction, checks the existing cybersecurity rules, calculates the risk score, and returns one structured alert.

## Example Usage

```python
from src.detection.pipeline import build_alert

alert = build_alert(
    predicted_label="PortScan",
    confidence=0.96,
    event={
        "connection_count": 35,
        "connection_window_seconds": 8,
    },
    exposure=5,
)

print(alert)
```

## Example Output

```python
{
    "label": "PortScan",
    "category": "PORT_SCAN",
    "risk_score": 200,
    "risk_level": "Medium",
    "detection_source": "both",
    "rule_matches": [
        {
            "rule": "port_scan",
            "message": "Port Scan Detected"
        }
    ]
}
```

## Detection Sources

The final alert can show one of three detection sources:

- `ml` — only the machine-learning prediction detected suspicious activity.
- `rule` — only a deterministic security rule detected suspicious activity.
- `both` — both the ML prediction and a security rule detected suspicious activity.

## Rule Input Fields

The pipeline only runs a rule when the required event fields are available.

### Port Scan

```text
connection_count
connection_window_seconds
```

### Brute Force

```text
failed_logins
login_window_seconds
```

### DoS

```text
request_count
request_window_seconds
```

## Supported Detection Categories

The pipeline currently works with the following broad categories:

- `BENIGN`
- `PORT_SCAN`
- `BRUTE_FORCE`
- `DOS`
- `OTHER_ATTACK`

ML labels are normalised before risk scoring.

Examples:

```text
PortScan      → PORT_SCAN
SSH-Patator   → BRUTE_FORCE
DDoS          → DOS
DoS Hulk      → DOS
BENIGN        → BENIGN
```

## Testing

The integration tests are located in:

```text
tests/test_detection_pipeline.py
```

Run the tests from the root of the repository:

```bash
python -m unittest tests/test_detection_pipeline.py -v
```

The tests cover:

- Benign ML prediction with no rule match.
- Port-scan ML prediction with a matching rule.
- A DoS rule detecting suspicious traffic even when ML predicts benign.
- SSH brute-force prediction with a matching rule.

## Purpose

This module connects the cybersecurity rule layer with the ML prediction and risk-scoring components so that the system can produce a single structured alert for the API and dashboard.