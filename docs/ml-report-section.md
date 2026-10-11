Machine Learning Section

Goal. Train a model that looks at one network flow and says whether it is normal traffic or a specific type of attack.

Data. We used the cleaned CICIDS2017 dataset, which has about 2.8 million flows and 15 labels (normal traffic plus 14 attack types). Because of hardware limits, we trained on a random sample of 300,000 flows. We used 80% for training and 20% for testing, and kept the same mix of labels in both. All features were scaled before training.

Models. We tried two models. Logistic Regression was the simple baseline. Random Forest was the main model. Both used class weights so the rare attacks were not ignored.

Why not accuracy. Most traffic is normal, so a model that always said “normal” would score high and still miss every attack. We used precision, recall, F1 score and a confusion matrix instead. Recall matters most, because missing a real attack is worse than a false alarm.

Results.

Logistic Regression caught most attacks, but raised many false alarms. For example, only 1% of its “Bot” alerts were correct.
Random Forest was much better. It scored close to perfect on DDoS, PortScan, DoS Hulk, FTP Patator and SSH Patator, and its normal traffic results were perfect.
Tuning Random Forest (200 trees, max depth 30) gave nearly the same results, so we kept the original model.

Limits. Random Forest is weaker on rare attacks: Bot (precision 0.29), Web Attack XSS (about 0.20) and Web Attack Brute Force (about 0.6). Infiltration had only one test example, so we could not judge it. This is a data problem, because there are too few examples of these attacks for any model to learn well.

Final model. Random Forest and its scaler are saved as files, and predict.py lets DevOps use them to label new traffic.