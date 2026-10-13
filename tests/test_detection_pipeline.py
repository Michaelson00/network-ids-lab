import unittest
import requests
import time
from src.detection.pipeline import build_alert

# ==========================================
# EXISTING TESTS: CYBERSECURITY LOGIC
# ==========================================
class DetectionPipelineTests(unittest.TestCase):

    def test_benign_prediction_without_rule_match_is_low_risk(self):
        alert = build_alert(
            "BENIGN",
            event={
                "connection_count": 3,
                "connection_window_seconds": 10,
            },
            confidence=0.99,
        )
        self.assertEqual(alert["category"], "BENIGN")
        self.assertEqual(alert["risk_level"], "Low")
        self.assertEqual(alert["detection_source"], "ml")
        self.assertEqual(alert["rule_matches"], [])

    def test_portscan_prediction_and_rule_are_combined(self):
        alert = build_alert(
            "PortScan",
            event={
                "connection_count": 35,
                "connection_window_seconds": 8,
            },
            confidence=0.96,
            exposure=5,
        )
        self.assertEqual(alert["category"], "PORT_SCAN")
        self.assertEqual(alert["detection_source"], "both")
        self.assertTrue(alert["rule_matches"])
        self.assertEqual(alert["risk_score"], 200)
        self.assertIn(alert["risk_level"], {"Medium", "High"})

    def test_benign_ml_label_can_be_overridden_by_dos_rule(self):
        alert = build_alert(
            "BENIGN",
            event={
                "request_count": 1500,
                "request_window_seconds": 1,
            },
            confidence=0.92,
            exposure=8,
        )
        self.assertEqual(alert["category"], "DOS")
        self.assertEqual(alert["detection_source"], "rule")
        self.assertEqual(alert["risk_level"], "High")

    def test_ssh_patator_maps_to_brute_force(self):
        alert = build_alert(
            "SSH-Patator",
            event={
                "failed_logins": 7,
                "login_window_seconds": 30,
            },
            confidence=0.97,
            exposure=6,
        )
        self.assertEqual(alert["category"], "BRUTE_FORCE")
        self.assertEqual(alert["detection_source"], "both")
        self.assertGreater(alert["risk_score"], 0)
        self.assertEqual(alert["risk_score"], 420)


# ==========================================
# NEW TESTS: ISSUE #29 END-TO-END PIPELINE
# ==========================================
class APIIntegrationTests(unittest.TestCase):
    
    def test_full_api_pipeline_end_to_end(self):
        """Tests the API -> Predict -> Score -> DB flow (Issue #29)"""
        API_URL = "http://127.0.0.1:5000/api"
        sample_payload = {
            "features": [[0.1, 45.0, 1.0, 0.0, 80.0, 0.0, 0.0, 1.0]]
        }

        try:
            # 1. Send data to processing endpoint
            post_res = requests.post(f"{API_URL}/process", json=sample_payload)
            self.assertEqual(post_res.status_code, 200, "API /process endpoint failed")
            
            # Allow DB write to complete
            time.sleep(1)
            
            # 2. Verify dashboard fetch endpoint works
            get_res = requests.get(f"{API_URL}/alerts")
            self.assertEqual(get_res.status_code, 200, "API /alerts endpoint failed")
            
            alerts = get_res.json()
            self.assertIsInstance(alerts, list, "Alerts should be returned as a JSON list")
            
        except requests.exceptions.ConnectionError:
            self.skipTest("API is not running. You must start src/api/app.py before running integration tests.")

if __name__ == "__main__":
    unittest.main()
