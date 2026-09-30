# Risk Scoring

This folder contains the risk-scoring logic used by the Network Intrusion Detection System.

## Formula

The project uses:

```text
Risk = Likelihood × Impact × Exposure
```

Each factor uses a scale from `1` to `10`.

Therefore, the final risk score ranges from:

```text
1 to 1000
```

## Risk Levels

The current prototype uses:

```text
Low     = 1 - 125
Medium  = 126 - 500
High    = 501 - 1000
```

## Main File

The scoring logic is located in:

```text
src/scoring/risk_scoring.py
```

## Main Functions

### `calculate_risk_score()`

Calculates the numerical risk score.

Example:

```python
from src.scoring.risk_scoring import calculate_risk_score

score = calculate_risk_score(
    likelihood=8,
    impact=7,
    exposure=5
)

print(score)
```

### `determine_severity_label()`

Converts the numerical score into:

```text
Low
Medium
High
```

### `evaluate_event()`

Use this when the three risk factors are already known.

```python
from src.scoring.risk_scoring import evaluate_event

result = evaluate_event(
    likelihood=8,
    impact=7,
    exposure=5
)

print(result)
```

Example result:

```python
{
    "risk_score": 280,
    "severity": "Medium"
}
```

### `evaluate_prediction()`

This is the main integration function for Issue #28.

It accepts the ML prediction directly and converts it into the information needed for risk scoring.

```python
from src.scoring.risk_scoring import evaluate_prediction

result = evaluate_prediction(
    label="PortScan",
    confidence=0.96,
    rule_triggered=True,
    exposure=5
)

print(result)
```

Example result:

```python
{
    "risk_score": 180,
    "severity": "Medium",
    "category": "PORT_SCAN",
    "likelihood": 9,
    "impact": 4,
    "exposure": 5
}
```

## Prediction Label Normalisation

The machine-learning model may return dataset-specific labels.

The scoring layer converts them into the project's common attack categories.

Examples:

```text
BENIGN          → BENIGN
Normal          → BENIGN
PortScan        → PORT_SCAN
SSH-Patator     → BRUTE_FORCE
FTP-Patator     → BRUTE_FORCE
DDoS            → DOS
DoS Hulk        → DOS
DoS GoldenEye   → DOS
```

Labels that do not match the current core categories are mapped to:

```text
OTHER_ATTACK
```

## Attack Impact Values

The current prototype uses these impact values:

```text
BENIGN         = 1
PORT_SCAN      = 4
BRUTE_FORCE    = 7
DOS            = 9
OTHER_ATTACK   = 6
```

These values represent the relative impact used by the prototype risk model.

## ML Confidence

When model confidence is available, it is converted from a value between:

```text
0.0 - 1.0
```

into the project's likelihood scale:

```text
1 - 10
```

For example:

```text
0.96 confidence → likelihood approximately 10
```

If a deterministic security rule also triggers, the likelihood is raised to at least `9`.

This allows the system to combine the ML prediction and rule-based evidence.

## Integration

The full flow is:

```text
ML Prediction
    ↓
Detection Rules
    ↓
Risk Scoring
    ↓
Structured Alert
```

The integration logic is located in:

```text
src/detection/pipeline.py
```

The final alert includes:

```text
label
category
risk_score
risk_level
detection_source
rule_matches
```

## Testing

Run the detection pipeline tests from the repository root:

```bash
python -m unittest tests/test_detection_pipeline.py -v
```

These tests verify that the scoring system works correctly with sample ML predictions and cybersecurity rule results.