# Rules
# Detection Rules

This directory contains deterministic security rules designed by the Cybersecurity Engineer. 

- **`detection_rules.py`**: Contains the code-based thresholds for our selected NIDS attack scenarios. 
  - **Port Scan:** Triggers if >20 connections occur within 10 seconds.
  - **Brute-Force:** Triggers if >=5 failed logins occur within 60 seconds.
  - **DoS:** Triggers if >1000 requests occur within 1 second.

**Integration Note for DevOps/ML:** When processing network traffic, pass the aggregated event counts and time windows into these functions to receive a boolean `True/False` and an alert string.
