"""Exercise the real synthetic demo ML → rules → risk → storage, not mocked labels."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch
from src.api.app import create_app
from src.models.demo import load_demo_artifacts, prepare_demo_model
from src.models.predict import predict_traffic


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)
        cls.environment = patch.dict(os.environ, {'NIDS_DEMO_MODEL_DIR': str(cls.directory / 'model')})
        cls.environment.start()
        load_demo_artifacts.cache_clear()
        prepare_demo_model()

    @classmethod
    def tearDownClass(cls):
        load_demo_artifacts.cache_clear()
        cls.environment.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.temp_db = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_db.cleanup)
        self.db = Path(self.temp_db.name) / 'alerts.db'
        self.client = create_app(self.db).test_client()

    def demo(self, name):
        response = self.client.post('/api/demo', json={'scenario': name, 'model_mode':'synthetic'})
        self.assertEqual(response.status_code, 200, response.json)
        return response.json

    def test_four_scenarios_real_demo_predictions_and_evidence(self):
        expected = [('benign','BENIGN',5,'Low'), ('port_scan','PORT_SCAN',200,'Medium'),
                    ('brute_force','BRUTE_FORCE',420,'Medium'), ('dos','DOS',720,'High')]
        for name, category, score, severity in expected:
            with self.subTest(scenario=name):
                result = self.demo(name)
                self.assertEqual(result['category'], category)
                self.assertEqual(result['risk_score'], score)
                self.assertEqual(result['severity'], severity)
                self.assertTrue(result['is_demo'])
                self.assertEqual(result['model_kind'], 'synthetic_demo')
                self.assertTrue(0<=result['confidence']<=1)
                if category=='BENIGN':
                    self.assertFalse(result['alert_generated'])
                    self.assertEqual(result['rule_matches'], [])
                else:
                    self.assertEqual(result['detection_source'], 'both')
                    detail=self.client.get(f"/api/alerts/{result['alert_id']}").json
                    self.assertEqual(detail['category'], category)
                    self.assertEqual(len(detail['evidence']['features']),78)
                    self.assertTrue(detail['evidence']['event'])
                    self.assertEqual(detail['evidence']['risk_factors'], result['risk_factors'])
                    self.assertTrue(detail['timestamp'])
                    self.assertEqual(detail['source_ip'],'192.168.56.102')
        metrics=self.client.get('/api/metrics').json
        self.assertEqual(metrics['total_alerts'],3)
        self.assertEqual(metrics['demo_alerts'],3)
        self.assertEqual(metrics['active_alerts'],3)
        self.assertEqual(metrics['by_severity'],{'Medium':2,'High':1})
        self.assertEqual(metrics['by_source'],{'both':3})
        self.assertEqual(sum(row['count'] for row in metrics['timeline']),3)
        self.assertEqual(create_app(self.db).test_client().get('/api/metrics').json['total_alerts'],3)

    def test_filters_and_demo_only_reset_preserve_submitted(self):
        self.demo('port_scan'); self.demo('dos')
        # Same real inference path with test-owned fitted artifacts, submitted provenance.
        from src.models.demo import scenario_input
        with patch('src.models.predict.load_artifacts', side_effect=load_demo_artifacts):
            response=self.client.post('/api/process',json=scenario_input('brute_force'))
        self.assertEqual(response.status_code,200,response.json)
        self.assertFalse(response.json['is_demo'])
        self.assertEqual(self.client.get('/api/metrics?mode=observed').json['total_alerts'],1)
        high=self.client.get('/api/alerts?severity=High&mode=demo').json
        self.assertEqual(len(high),1)
        self.assertEqual(high[0]['category'],'DOS')
        self.assertEqual(len(self.client.get('/api/alerts?category=PORT_SCAN&source=both').json),1)
        self.assertEqual(self.client.delete('/api/demo/alerts',json={}).status_code,400)
        reset=self.client.delete('/api/demo/alerts',json={'confirm':True})
        self.assertEqual(reset.json,{'deleted':2,'scope':'demo_only'})
        remaining=self.client.get('/api/alerts').json
        self.assertEqual(len(remaining),1)
        self.assertFalse(remaining[0]['is_demo'])
        self.assertEqual(self.client.get('/api/metrics').json['demo_alerts'],0)

    def test_metrics_cover_all_records_and_empty_hour_risk_is_unknown(self):
        for _ in range(21):
            self.demo('port_scan')
        self.assertEqual(len(self.client.get('/api/alerts').json),20)
        metrics=self.client.get('/api/metrics').json
        self.assertEqual(metrics['total_alerts'],21)
        self.assertEqual(sum(row['count'] for row in metrics['timeline']),21)
        self.assertEqual(len(metrics['timeline']),25)
        self.assertTrue(all(row['average_risk'] is None for row in metrics['timeline'] if row['count']==0))
        self.assertEqual(metrics['by_category'],{'PORT_SCAN':21})

    def test_invalid_demo_filters_and_unknown_details(self):
        for data in [None,[],{}, {'scenario':'public_target'}, {'scenario':False}]:
            self.assertEqual(self.client.post('/api/demo',json=data).status_code,400)
        for path in ['/api/alerts?limit=0','/api/alerts?limit=bad','/api/alerts?mode=bad','/api/metrics?mode=bad']:
            self.assertEqual(self.client.get(path).status_code,400)
        self.assertEqual(self.client.get('/api/alerts/999').status_code,404)
        self.assertEqual(self.client.get('/api/alerts').json,[])

    def test_demo_model_first_use_and_asset_delivery(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ,{'NIDS_DEMO_MODEL_DIR':directory}):
            load_demo_artifacts.cache_clear()
            self.assertFalse(self.client.get('/api/health').json['demo_model']['ready'])
            result=self.demo('port_scan')
            self.assertTrue(result['alert_generated'])
            self.assertTrue(self.client.get('/api/health').json['demo_model']['ready'])
            self.assertTrue((Path(directory)/'scaler.pkl').exists())
            load_demo_artifacts.cache_clear()
        selected = Path(__file__).resolve().parents[1] / 'src/models'
        with patch.dict(os.environ, {'NIDS_DEMO_MODEL_DIR': str(selected)}):
            load_demo_artifacts.cache_clear()
            with self.assertRaises(ValueError):
                prepare_demo_model()
            health = self.client.get('/api/health')
            self.assertEqual(health.status_code, 200)
            self.assertFalse(health.json['demo_model']['ready'])
        for asset in ['style.css','app.js','vendor/chart.umd.min.js','vendor/lucide.svg']:
            response=self.client.get('/assets/'+asset)
            self.addCleanup(response.close)
            self.assertEqual(response.status_code,200,asset)
        self.assertEqual(self.client.get('/assets/../../src/api/app.py').status_code,404)
        load_demo_artifacts.cache_clear()


if __name__ == '__main__':
    unittest.main()
