# ML Modelling Plan

## Dataset and Target

Dataset: CICIDS2017. Each row is one network flow (a single connection between
two devices). The target variable is the `Label` column, which is either
`BENIGN` (normal traffic) or a specific attack type (e.g. `DDoS`, `PortScan`,
`Brute Force`).

## Models

- **Logistic Regression** — baseline model. Simple and fast, gives a floor
  to compare against.
- **Random Forest** — main model. Better suited to the messy, non-linear
  patterns typical in network traffic data.

## Evaluation Metrics

Accuracy alone is misleading here because the dataset is heavily imbalanced
(most traffic is BENIGN). A model could score high accuracy just by guessing
BENIGN every time, while missing every real attack. Instead, evaluation will
use:

- **Precision** — of flagged attacks, how many were correct
- **Recall** — of real attacks, how many were caught (most important metric
  for an IDS — missing a real attack is worse than a false alarm)
- **F1-score** — balance between precision and recall
- **Confusion matrix** — shows exactly where the model gets confused between
  classes

## Handling Class Imbalance

Models trained naively on imbalanced data tend to just predict the majority
class (BENIGN). To address this, the following will be tested once real
data is available:

- **Class weighting** — makes mistakes on rare (attack) classes count more
  during training. Simple to apply in both Logistic Regression and Random
  Forest.
- **SMOTE (resampling)** — generates synthetic examples of the minority
  (attack) classes to balance the dataset before training.

## Output for DevOps

Once the final model is selected, it will be saved as a single file using
`joblib`, so it can be loaded and used for predictions without retraining.

Alongside the saved model, a short note will document:
- The exact features (and order) the model expects as input
- Any preprocessing/encoding applied before training, so the same steps can
  be applied to new data before prediction