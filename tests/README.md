# Tests
Unit, data, ML, rule, integration, regression, safety, performance tests.

This folder contains the automated tests for the Network Intrusion Detection System project.

The tests are used to confirm that individual components and integrated parts of the system behave as expected.

## Current Test Files

### `test_detection_pipeline.py`

This file tests the integration between:

```text
ML Prediction
    ↓
Detection Rules
    ↓
Risk Scoring
    ↓
Structured Alert
```

The purpose of the test is to confirm that model predictions can be combined with deterministic cybersecurity rules and then passed through the risk-scoring system correctly.

## What Is Tested

The current integration tests cover the following scenarios:

### 1. Benign Traffic

Checks that a benign ML prediction with no matching security rule:

- Remains classified as `BENIGN`.
- Produces a low risk level.
- Uses `ml` as the detection source.
- Produces no rule matches.

### 2. Port Scan Detection

Checks that a `PortScan` ML prediction combined with port-scan behaviour:

- Maps to `PORT_SCAN`.
- Triggers the port-scan rule.
- Uses `both` as the detection source.
- Produces a valid risk score and risk level.

### 3. DoS Rule Override

Checks that suspicious DoS behaviour can still generate an alert even if the ML prediction is `BENIGN`.

In this case:

```text
ML Prediction = BENIGN
Rule Detection = DOS
Final Category = DOS
```

This helps show how deterministic rules can provide an additional detection layer beside the machine-learning model.

### 4. Brute-Force Detection

Checks that an ML label such as:

```text
SSH-Patator
```

is mapped to:

```text
BRUTE_FORCE
```

and combined with the brute-force detection rule.

## Run the Tests

From the root of the repository, run:

```bash
python -m unittest tests/test_detection_pipeline.py -v
```

Expected result:

```text
Ran 4 tests

OK
```

## Testing Goal

The tests confirm that the Issue #28 integration works end-to-end:

```text
Model Prediction
+ Security Rules
+ Risk Scoring
= Structured Alert
```

The final alert should contain fields such as:

```text
label
category
risk_score
risk_level
detection_source
rule_matches
```

## Future Tests

Additional tests can later be added for:

- API integration.
- Database alert storage.
- Dashboard integration.
- Additional attack categories.
- False-positive cases.
- Invalid or missing input data.
- Model confidence edge cases.

The project testing strategy also includes unit, rule, integration, regression, lab-safety and performance testing as the system develops.