# Final Report: Dataset and Data Preparation

## Dataset Used

The project uses the CIC-IDS-2017 intrusion detection dataset, which contains network-flow records representing benign activity and multiple types of network attacks. The raw CSV files are stored in `data/raw/` and cover traffic captured across different days and attack scenarios.

Each record contains 78 candidate network-flow features and a `Label` field identifying the traffic category. The features describe characteristics such as flow duration, packet and byte counts, packet lengths, traffic rates, inter-arrival times, TCP flags, and active and idle periods.

## Data Cleaning and Preparation

The exploratory analysis in `notebooks/01_eda.ipynb` applies the following preparation steps:

1. Inspects missing and infinite values.
2. Replaces positive and negative infinity with missing values.
3. Removes rows containing missing values.
4. Standardizes Web Attack label names by replacing the corrupted character `�` with a hyphen.
5. Checks the resulting label categories and data types.
6. Saves the cleaned data to `data/processed/cicids2017_clean.csv`.

The notebook records a cleaned dataset containing **2,827,876 rows and 79 columns**. These columns comprise 78 candidate input features and the original `Label` column.

Removing rows with missing or non-finite values helps prevent invalid observations from entering subsequent analysis. However, row removal can reduce the available data, so its impact should be considered when interpreting model results.

## Feature Preparation

The candidate input features describe network-flow behavior, including flow duration, packet counts, byte counts, packet-length statistics, flow rates, inter-arrival times, TCP flags, subflow characteristics, and active and idle periods.

The original `Label` field represents the classification target and should not be included among the model inputs. For a binary classification experiment, the target mapping must be documented separately, with benign traffic distinguished from attack traffic. For multiclass classification, the original attack categories should be preserved.

The feature names, column order, data types, and preprocessing procedure must remain consistent between model training and inference.

## Model Evaluation Results

The project's saved Week 2 summary reports an accuracy of **99.92%**, an attack detection rate of **99.89%**, and a false alarm rate of **0.064%**. It also records 42 missed attacks and 53 false alarms.

These are the results recorded in `docs/da1-results/week2_results_summary.csv` and `docs/da1-results/model_evaluation.csv`. The exact evaluation dataset and experimental setup should be confirmed before treating these figures as results from the full cleaned dataset described in this section.

## Limitations and Reproducibility

The notebook documents the cleaning process and saves the cleaned dataset to `data/processed/cicids2017_clean.csv`. The analysis results are stored in `docs/da1-results/`.

The repository's model documentation differs on whether scaling is required, and the expected model and scaler artifacts were not present in `src/models/` during inspection. Therefore, the inference preprocessing procedure still requires verification.

Future reporting should distinguish the full cleaned dataset from any smaller subset used in a separate experiment and should record the sample size, target definition, preprocessing steps, and evaluation setup for each experiment.
