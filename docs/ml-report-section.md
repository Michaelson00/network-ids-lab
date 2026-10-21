Machine Learning Section

Evidence note: the results below were reproduced on 21 October 2026 by rerunning notebooks/02_model_comparison.ipynb on the same 300,000 row sample. The numbers match the original report.

Goal. Train a model that looks at one network flow and says whether it is normal traffic or a specific type of attack.

Data. We used the cleaned CICIDS2017 dataset, which has about 2.8 million flows and 15 labels (normal traffic plus 14 attack types). Because of hardware limits, we trained on a random sample of 300,000 flows. We used 80% for training and 20% for testing, and kept the same mix of labels in both. All features were scaled before training.

Models. We tried two models. Logistic Regression was the simple baseline. Random Forest was the main model. Both used class weights so the rare attacks were not ignored.

Why not accuracy. Most traffic is normal, so a model that always said “normal” would score high and still miss every attack. We used precision, recall, F1 score and a confusion matrix instead. Recall matters most, because missing a real attack is worse than a false alarm.

Results.

Logistic Regression caught most attacks, but raised many false alarms. For example, only 1% of its “Bot” alerts were correct.
Random Forest was much better. It scored close to perfect on DDoS, PortScan, DoS Hulk, FTP Patator and SSH Patator, and its normal traffic results were perfect.
Tuning Random Forest (200 trees, max depth 30) gave nearly the same results, so we kept the original model.

Limits. Important features. The features that mattered most were Destination Port (6.5%), Init_Win_bytes_backward (4.9%) and Fwd Packet Length Std (3.3%). No single feature dominates, because many features each add 2% to 3%. Many features are near copies of each other, so their exact order should not be over read.

Random Forest is weaker on rare attacks: Bot (precision 0.29), Web Attack XSS (about 0.20) and Web Attack Brute Force (about 0.6). Infiltration had only one test example, so we could not judge it. This is a data problem, because there are too few examples of these attacks for any model to learn well.

Final model. The paired Random Forest and scaler were loaded by the API on 21 October 2026, and the health check reported healthy. A real port scan flow was labelled PortScan with 99.99% confidence, and a normal flow was labelled BENIGN with confidence 1.0 and no alert. When we converted our own lab nmap scan capture into flows, the model alone labelled it BENIGN, so it did not carry over from the benchmark to our lab. The port scan rule detected it (1,000 ports in under 10 seconds), and the combined result was PORT_SCAN. This is why the system uses both the model and the rules. The capture converter is a Python copy of the original CICFlowMeter tool, so small differences in feature values are possible.