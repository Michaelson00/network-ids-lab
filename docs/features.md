# Feature Engineering and Data Preparation

## 1. Dataset

This project uses the CIC-IDS-2017 intrusion detection dataset. The raw files are stored in `data/raw/` and cover network traffic captured across multiple days and attack scenarios.

Each row represents a network flow. The dataset contains 78 candidate input features and a `Label` column identifying benign traffic or an attack category.

The exploratory analysis is documented in `notebooks/01_eda.ipynb`.

## 2. Data Cleaning

The notebook records these data preparation steps:

* Checked for missing and infinite values.
* Replaced positive and negative infinity with missing values (`NaN`).
* Removed rows containing missing values using `dropna()`.
* Standardized Web Attack label names by replacing the corrupted character `�` with a hyphen.
* Inspected the resulting labels and data types.
* Saved the cleaned dataset to `data/processed/cicids2017_clean.csv`.

The notebook records a cleaned dataset shape of **2,827,876 rows and 79 columns**. The 79 columns consist of 78 candidate input features and the `Label` column.

## 3. Feature Set

The candidate input features describe network-flow characteristics, including:

* Flow duration and destination port.
* Forward and backward packet counts and byte lengths.
* Packet-length statistics.
* Flow rates and inter-arrival times.
* TCP flag counts and header characteristics.
* Subflow statistics.
* Active and idle time statistics.
* TCP window and segment-size characteristics.

The `Label` column is the target label and must not be included as a model input. If a binary target such as `Attack_Type` is created for a separate experiment, it must also be excluded from the input features.

Feature names, data types, column order, and preprocessing must match the selected model's training requirements.

## 4. Data Preparation Findings

The notebook's saved output contains 15 traffic labels, including `BENIGN`, `DDoS`, `PortScan`, `Bot`, several DoS categories, and web-attack categories.

The notebook identified missing and infinite values before cleaning. Rate-related fields such as `Flow Bytes/s` and `Flow Packets/s` require particular attention because invalid values can affect model training and prediction.

Removing rows with missing values provides a dataset without those missing entries, but it can also discard observations. The effects of this removal should be considered when evaluating the dataset.

## 5. Model Evaluation Context

The saved Week 2 results report the following model metrics:

| Metric                | Reported result |
| --------------------- | --------------: |
| Accuracy              |          99.92% |
| Attack Detection Rate |          99.89% |
| False Alarm Rate      |          0.064% |
| Missed Attacks        |              42 |
| False Alarms          |              53 |

These figures are recorded in `docs/da1-results/week2_results_summary.csv` and `docs/da1-results/model_evaluation.csv`. They should be treated as previously reported model results; the precise evaluation dataset and experimental setup should be confirmed before directly associating them with the cleaned dataset described above.

## 6. Integration Notes and Limitations

* Multiclass classification requires preserving the original attack-category labels.
* Binary classification requires a clearly documented mapping from the original labels to benign and attack classes.
* Training and inference must use consistent feature names, order, data types, and cleaning steps.
* The repository's model documentation differs on whether scaling is required. Confirm the actual model and scaler artifacts before finalizing inference preprocessing.
* The saved model and scaler files were not present in `src/models/` during the repository inspection, so the inference setup remains to be verified.

## 7. Reproducibility

* Notebook: `notebooks/01_eda.ipynb`
* Raw data: `data/raw/`
* Processed dataset output: `data/processed/cicids2017_clean.csv`
* Analysis results: `docs/da1-results/`

The notebook is the reference for the cleaning steps and recorded dataset shape. Any separate binary-classification experiment should document its own data selection, target creation, row counts, and evaluation results.
