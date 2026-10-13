# NIDS Final Demonstration Flow

**Total Time:** 5–10 minutes

### 1. Introduction (Network Engineer)
*   **Action:** Display the dashboard on screen (empty state).
*   **Script:** "Welcome to our Adaptive Network Intrusion Detection System demonstration. Our goal was to build a system that analyzes network traffic, detects malicious behavior using machine learning and rule-based logic, and visualizes threats for analysts."

### 2. Architecture Overview (DevOps)
*   **Action:** Show the system architecture diagram.
*   **Script:** "Our pipeline is fully decoupled. Traffic data flows into our feature extractor, passes to our Scikit-Learn ML engine for classification, moves through our Cybersecurity team's risk-scoring algorithm, and is finally served via a Flask REST API to our frontend dashboard."

### 3. Benign Telemetry (Network Engineer)
*   **Action:** Run `test_detection_pipeline.py` using benign traffic.
*   **Script:** "First, we will establish a baseline by sending normal network traffic through the system. As you can see, the ML model classifies it as 'normal', the risk score evaluates to 0, and no alerts trigger on the dashboard."

### 4. Simulated Intrusion (Cybersecurity)
*   **Action:** Execute the controlled attack simulation (e.g., DoS or SSH Brute Force).
*   **Script:** "We will now launch a controlled SSH brute-force attack from our isolated attacker VM targeting our lab server."

### 5. Detection & Risk Scoring (Data ML / Cybersecurity)
*   **Action:** Show the API terminal logs capturing the incoming attack traffic.
*   **Script:** "The traffic is captured and its features are extracted. Our ML model intercepts the packet data and accurately classifies it as anomalous. Our deterministic security rules then evaluate the payload, calculating a critical risk score based on likelihood, impact, and exposure."

### 6. Alert Generation & Dashboard (DevOps)
*   **Action:** Switch back to the dashboard. Wait 5 seconds for the polling script to automatically update the UI.
*   **Script:** "Our Flask API commits this event to the SQLite database. The dashboard, which polls the API asynchronously, instantly visualizes the threat, highlighting its High severity and Risk Score for immediate triage."

### 7. Evaluation & Metrics (Data ML)
*   **Action:** Display the `confusion_matrix.png` and `model_evaluation.csv`.
*   **Script:** "Our system doesn't just detect this one attack. During offline evaluation, our model achieved high Precision and F1-scores across multiple attack classes, keeping false positives to a minimum to avoid alert fatigue."

### 8. Reflection & Conclusion (Team)
*   **Script:** "While this is a functional prototype, a production-grade SOC deployment would require a distributed database instead of SQLite, a message broker like Kafka to handle high-throughput traffic, and HTTPS encryption for the API. This concludes our demonstration."
