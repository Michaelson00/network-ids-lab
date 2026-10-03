# Model Integration Requirements

## Purpose

This document records the data and model requirements for integrating the trained Network Intrusion Detection System (NIDS) Random Forest model with the API and detection components.

## Trained Model

* Model: Random Forest Classifier
* Model file: `notebooks/nids_random_forest.pkl`
* Number of input features: **78**
* Scaling: **Not used**
* Target columns: `Label` and `Attack_Type`
* `Label` and `Attack_Type` must **not** be sent to the model as input features.

## Required Feature List and Order

The model expects exactly these 78 features in this order:

1. Destination Port
2. Flow Duration
3. Total Fwd Packets
4. Total Backward Packets
5. Total Length of Fwd Packets
6. Total Length of Bwd Packets
7. Fwd Packet Length Max
8. Fwd Packet Length Min
9. Fwd Packet Length Mean
10. Fwd Packet Length Std
11. Bwd Packet Length Max
12. Bwd Packet Length Min
13. Bwd Packet Length Mean
14. Bwd Packet Length Std
15. Flow Bytes/s
16. Flow Packets/s
17. Flow IAT Mean
18. Flow IAT Std
19. Flow IAT Max
20. Flow IAT Min
21. Fwd IAT Total
22. Fwd IAT Mean
23. Fwd IAT Std
24. Fwd IAT Max
25. Fwd IAT Min
26. Bwd IAT Total
27. Bwd IAT Mean
28. Bwd IAT Std
29. Bwd IAT Max
30. Bwd IAT Min
31. Fwd PSH Flags
32. Bwd PSH Flags
33. Fwd URG Flags
34. Bwd URG Flags
35. Fwd Header Length
36. Bwd Header Length
37. Fwd Packets/s
38. Bwd Packets/s
39. Min Packet Length
40. Max Packet Length
41. Packet Length Mean
42. Packet Length Std
43. Packet Length Variance
44. FIN Flag Count
45. SYN Flag Count
46. RST Flag Count
47. PSH Flag Count
48. ACK Flag Count
49. URG Flag Count
50. CWE Flag Count
51. ECE Flag Count
52. Down/Up Ratio
53. Average Packet Size
54. Avg Fwd Segment Size
55. Avg Bwd Segment Size
56. Fwd Header Length.1
57. Fwd Avg Bytes/Bulk
58. Fwd Avg Packets/Bulk
59. Fwd Avg Bulk Rate
60. Bwd Avg Bytes/Bulk
61. Bwd Avg Packets/Bulk
62. Bwd Avg Bulk Rate
63. Subflow Fwd Packets
64. Subflow Fwd Bytes
65. Subflow Bwd Packets
66. Subflow Bwd Bytes
67. Init_Win_bytes_forward
68. Init_Win_bytes_backward
69. act_data_pkt_fwd
70. min_seg_size_forward
71. Active Mean
72. Active Std
73. Active Max
74. Active Min
75. Idle Mean
76. Idle Std
77. Idle Max
78. Idle Min

## Integration Requirements

1. Incoming data must contain exactly the 78 required model features.
2. Feature names must match the names listed above.
3. Feature order must match the order used during model training.
4. All model input features must be numeric.
5. `Label` and `Attack_Type` must be excluded from the model input.
6. Missing values must be handled before prediction.
7. Infinite (`inf` or `-inf`) values must be handled before prediction.
8. No feature scaling is required because the saved Random Forest model does not contain a scaler.
9. The API/detection layer should validate the feature names and feature count before sending data to the model.
10. The model contains `feature_names_in_`, so feature-name mismatches should be treated as an integration error.

## Data Cleaning Notes

During dataset preparation, missing values were encountered in `Flow Bytes/s`. Infinite values were also encountered in `Flow Bytes/s` and `Flow Packets/s`.

For integration, incoming data should therefore be checked for:

* Missing values
* `inf` values
* `-inf` values
* Incorrect column names
* Missing features
* Extra features
* Incorrect feature order
* Non-numeric values

The same cleaning assumptions used during model training should be maintained when preparing data for prediction.

## Integration Flow

```text
Incoming Network Data
        ↓
Data Validation
        ↓
Handle Missing / Infinite Values
        ↓
Select the 78 Required Features
        ↓
Arrange Features in Training Order
        ↓
Random Forest Model
        ↓
Prediction
        ↓
Risk Scoring / Security Alert
```

## Important Note for API Integration
