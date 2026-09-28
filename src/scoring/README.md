# Scoring
# Risk Scoring

This directory handles the evaluation and severity assignment for suspicious events detected by the ML models or static rules.

- **`risk_scoring.py`**: Implements the official project scoring logic.
  - **Formula:** `Risk = Likelihood x Impact x Exposure`
  - **Scale:** Each metric is rated 1-10, making the maximum possible score 1000.
  - **Severity Thresholds:**
    - Low: 1 - 125
    - Medium: 126 - 500
    - High: 501 - 1000

**Integration Note for DevOps:** Pass the three metric integers into `evaluate_event(likelihood, impact, exposure)` to receive a dictionary containing the final calculated `risk_score` and the `severity` label for the database/dashboard.