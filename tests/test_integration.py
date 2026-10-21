"""Application tests use temporary fitted artifacts, never the team's model."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from src.api.app import create_app
from src.features.prepare import FEATURE_NAMES, prepare_features
from src.models import predict as predictor
from src.detection.pipeline import build_alert
from src.scoring.risk_scoring import calculate_risk_score, determine_severity_label
from rules.detection_rules import detect_port_scan, detect_brute_force, detect_dos_traffic


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        frame = pd.DataFrame([np.full(78, n) for n in range(4)], columns=FEATURE_NAMES)
        scaler = StandardScaler().fit(frame)
        model = RandomForestClassifier(n_estimators=10, random_state=42).fit(
            scaler.transform(frame), ['BENIGN', 'PortScan', 'SSH-Patator', 'DDoS'])
        joblib.dump(model, self.root / 'random_forest_model.pkl')
        joblib.dump(scaler, self.root / 'scaler.pkl')
        self.patch = patch.object(predictor, 'MODEL_DIR', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        predictor.load_artifacts.cache_clear()
        self.addCleanup(predictor.load_artifacts.cache_clear)
        self.db = self.root / 'alerts.db'
        self.client = create_app(self.db).test_client()

    def post(self, value=0, **kwargs):
        return self.client.post('/api/process', json={'features': [[value]*78], **kwargs})

    def test_four_scenarios_storage_metrics_dashboard(self):
        cases = [(0, {}, 'BENIGN', False),
                 (1, {'connection_count': 35, 'connection_window_seconds': 8}, 'PORT_SCAN', True),
                 (2, {'failed_logins': 7, 'login_window_seconds': 30}, 'BRUTE_FORCE', True),
                 (3, {'request_count': 1500, 'request_window_seconds': 1}, 'DOS', True)]
        for value, event, category, stored in cases:
            with self.subTest(category=category):
                response = self.post(value, event=event)
                self.assertEqual(response.status_code, 200, response.json)
                self.assertEqual(response.json['category'], category)
                self.assertEqual(response.json['alert_generated'], stored)
                self.assertTrue(0 <= response.json['confidence'] <= 1)
                self.assertEqual(response.json['detection_source'], 'both' if stored else 'ml')
        alerts = self.client.get('/api/alerts').json
        self.assertEqual(len(alerts), 3)
        self.assertTrue(all(isinstance(a['rule_matches'], list) for a in alerts))
        self.assertEqual(self.client.get('/api/metrics').json['total_alerts'], 3)
        self.assertEqual(create_app(self.db).test_client().get('/api/metrics').json['total_alerts'], 3)
        self.assertEqual(self.client.get('/api/health').json['status'], 'healthy')
        page = self.client.get('/')
        self.addCleanup(page.close)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"const API_URL = '/api'", page.data)
        self.assertNotIn(b'tbody.innerHTML +=', page.data)

    def test_rule_only_and_ml_only(self):
        self.assertEqual(self.post(event={'failed_logins': 5, 'login_window_seconds': 60}).json['detection_source'], 'rule')
        self.assertEqual(self.post(1).json['detection_source'], 'ml')

    def test_invalid_requests(self):
        for body in [None, [], {}, {'features': [[0]*8]}, {'features': [[0]*78]*2},
                     {'features': [[None]*78]}, {'features': [[True]*78]},
                     {'features': [[0]*78], 'event': []},
                     {'features': [[0]*78], 'exposure': '5'},
                     {'features': [[0]*78], 'event': {'failed_logins': 5}},
                     {'features': [[0]*78], 'event': {'failed_logins': 5, 'login_window_seconds': 0}}]:
            with self.subTest(body=body):
                self.assertEqual(self.client.post('/api/process', json=body).status_code, 400)
        self.assertEqual(self.client.post('/api/process', data='{', content_type='application/json').status_code, 400)

    def test_feature_order_and_rejection(self):
        record = dict(reversed(list(zip(FEATURE_NAMES, range(78)))))
        frame = prepare_features([record])
        self.assertEqual(frame.iloc[0].tolist(), list(range(78)))
        for value in [np.nan, np.inf, -np.inf, 'oops']:
            with self.assertRaises(ValueError):
                prepare_features([[value]*78])
        with self.assertRaises(ValueError):
            prepare_features([{**record, 'Label': 'BENIGN'}])
        self.assertEqual(predictor.predict([[0]*78]).tolist(), ['BENIGN'])

    def test_supplied_sample_schema(self):
        sample = pd.read_csv(Path(__file__).resolve().parents[1] / 'src/models/sample_input.csv')
        self.assertEqual(list(sample.columns), FEATURE_NAMES)
        self.assertEqual(prepare_features(sample).shape, sample.shape)
        self.assertEqual(len(predictor.predict_traffic(sample.iloc[:1])), 1)

    def test_missing_and_incompatible_artifacts(self):
        (self.root / 'scaler.pkl').unlink()
        predictor.load_artifacts.cache_clear()
        self.assertEqual(self.post().status_code, 503)
        self.assertEqual(self.client.get('/api/health').json['status'], 'degraded')
        joblib.dump(StandardScaler().fit(np.zeros((2, 8))), self.root / 'scaler.pkl')
        predictor.load_artifacts.cache_clear()
        self.assertEqual(self.post().status_code, 503)

    def test_legacy_database_migration(self):
        legacy = self.root / 'legacy.db'
        with closing(sqlite3.connect(legacy)) as conn, conn:
            conn.execute('CREATE TABLE alerts (id INTEGER PRIMARY KEY, title TEXT, severity TEXT, risk_score REAL, source TEXT, status TEXT, timestamp TEXT)')
            conn.execute("INSERT INTO alerts VALUES (1,'old','High',600,'ML Engine','investigation required','2026-01-01')")
        client = create_app(legacy).test_client()
        self.assertEqual(client.get('/api/alerts').json[0]['title'], 'old')
        self.assertEqual(client.get('/api/metrics').json['total_alerts'], 1)

    def test_storage_errors_and_wrong_artifact_names(self):
        self.db.unlink()
        self.db.mkdir()
        with self.assertLogs('src.api.app', level='ERROR'):
            self.assertEqual(self.client.get('/api/alerts').status_code, 503)
            self.assertEqual(self.client.get('/api/health').status_code, 503)
        scaler = StandardScaler().fit(pd.DataFrame(np.zeros((2, 78)), columns=list(reversed(FEATURE_NAMES))))
        joblib.dump(scaler, self.root / 'scaler.pkl')
        predictor.load_artifacts.cache_clear()
        with self.assertRaises(predictor.ModelUnavailable):
            predictor.load_artifacts()

    def test_boundaries_and_canonical_labels(self):
        self.assertFalse(detect_port_scan(20, 10)[0])
        self.assertTrue(detect_port_scan(21, 10)[0])
        self.assertFalse(detect_brute_force(4, 60)[0])
        self.assertTrue(detect_brute_force(5, 60)[0])
        self.assertFalse(detect_dos_traffic(1000, 1)[0])
        self.assertTrue(detect_dos_traffic(1001, 1)[0])
        self.assertEqual(calculate_risk_score(11, 11, 11), 1000)
        self.assertEqual([determine_severity_label(n) for n in [125,126,500,501]], ['Low','Medium','Medium','High'])
        for label in ['BENIGN','PORT_SCAN','BRUTE_FORCE','DOS','OTHER_ATTACK']:
            self.assertEqual(build_alert(label)['category'], label)
        self.assertEqual(build_alert('BENIGN', event={'request_count':1500,'request_window_seconds':1}, confidence=.92, exposure=8)['risk_score'],648)


if __name__ == '__main__':
    unittest.main()
