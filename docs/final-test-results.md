# SentinelNIDS: Final Test Results

Verification note (2026-10-24): the 2026-10-21 account below is retained as a
teammate's historical report. Its selected artifacts and `pcap_to_flows.py` are
absent from this checkout, so its real-model/capture results cannot be reproduced
here. Do not run the missing converter command as current setup instructions.
Current actual verification is in [FUNCTIONAL_IMPLEMENTATION.md](FUNCTIONAL_IMPLEMENTATION.md)
and [RUN_AND_TEST.md](../RUN_AND_TEST.md); synthetic demo results are not confirmation
of the historical benchmark figures.

Date tested: 21 October 2026. Branch: test.

## System checks

All 13 automated tests passed. The real trained model loaded and the health check reported healthy. A real port scan flow from the dataset was classified as PortScan with 99.99% confidence and saved as an alert. A normal flow was classified as BENIGN with confidence 1.0, a low risk score of 8, and no alert was stored. The port scan, brute force and DoS rules each fired correctly, and every alert appeared on the dashboard.

## Model results

On 60,000 test flows, Logistic Regression reached 87% accuracy but flagged 16% of normal traffic as attacks. The Random Forest reached about 100% accuracy, and the tuned version (200 trees, depth 30) gave nearly the same results. The weak classes are rare attacks with few test examples: Bot (precision 0.29), Web Attack Brute Force (F1 0.65), Web Attack XSS (F1 0.20) and Infiltration (1 test example). The most important features were Destination Port (6.5%) and Init_Win_bytes_backward (4.9%).

## Data findings

The cleaned dataset has 307,078 duplicate rows, which may make the scores look slightly better than they really are. Eight features are constant and many pairs of features are highly correlated, but all 78 features were kept to match the trained model.

## Capture test

We built a converter (pcap_to_flows.py) that turns Wireshark captures into model input. On the lab nmap scan (1,005 flows), the model alone said BENIGN, but the port scan rule detected 1,000 ports contacted within 10 seconds, and the final result was PORT_SCAN (risk 288, Medium). Background traffic from other machines stayed BENIGN with a low risk score. This shows the model and the rules work best together.

## Limits

The model did not recognise the lab scan on its own. The converter is a Python copy of the original CICFlowMeter tool, so some feature values may differ slightly. The brute force rule needs failed login counts from server logs, which a capture cannot provide. The DoS capture was too small to reach the rule threshold of 1,000 requests in one second. The privacy of the capture files was not checked.

## How to repeat these tests

Run these from the project folder with the virtual environment on:

```
python -m unittest discover -s tests -v
python -m src.api.app
python tests\test_real_traffic.py
python pcap_to_flows.py lab\scan_nmap_synscan.pcapng --send 6 --rules
```

The model files random_forest_model.pkl and scaler.pkl must be in src\models before starting the server.
