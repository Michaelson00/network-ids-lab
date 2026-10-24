"""Verify model-mode compatibility, real offline captures and fitted-artifact export."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from src.api.app import create_app
from src.models.predict import ModelUnavailable
from src.models import predict as predictor
from src.models.export import export_fitted
from src.features.prepare import FEATURE_NAMES
from src.captures.offline import analyze_capture, peak_window


class BlockerResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.client=create_app(self.root/'alerts.db').test_client()

    def test_auto_demo_without_benchmark_never_calls_synthetic_predictor(self):
        with patch('src.api.app.load_artifacts', side_effect=ModelUnavailable('missing')), patch('src.api.app.predict_traffic') as predict:
            for scenario,category,risk in [('benign','BENIGN',5),('port_scan','PORT_SCAN',180),('brute_force','BRUTE_FORCE',378),('dos','DOS',648)]:
                response=self.client.post('/api/demo',json={'scenario':scenario})
                self.assertEqual(response.status_code,200,response.json)
                self.assertEqual(response.json['category'],category)
                self.assertEqual(response.json['risk_score'],risk)
                self.assertIsNone(response.json['label'])
                self.assertIsNone(response.json['confidence'])
                self.assertFalse(response.json['ml_applied'])
                self.assertEqual(response.json['model_kind'],'rules_only')
                self.assertEqual(response.json['detection_source'],'rule')
            predict.assert_not_called()
            health=self.client.get('/api/health').json
            self.assertEqual(health['operating_mode'],'DEMO_MODE')
            self.assertEqual(health['rules_engine'],'ready')
            self.assertEqual(health['risk_engine'],'ready')
        self.assertEqual(self.client.get('/api/metrics').json['total_alerts'],3)

    def fitted_pair(self):
        frame=pd.DataFrame([np.full(78,n) for n in range(4)],columns=FEATURE_NAMES)
        scaler=StandardScaler().fit(frame)
        model=RandomForestClassifier(n_estimators=100,class_weight='balanced',random_state=42).fit(
            scaler.transform(frame),['BENIGN','PortScan','SSH-Patator','DDoS'])
        return model,scaler

    def test_auto_demo_prefers_actual_selected_loader_and_no_silent_inference_fallback(self):
        pair=self.fitted_pair()
        with patch('src.api.app.load_artifacts',return_value=pair), patch('src.models.predict.load_artifacts',return_value=pair):
            health=self.client.get('/api/health').json
            self.assertEqual(health['operating_mode'],'FULL_MODEL_MODE')
            response=self.client.post('/api/demo',json={'scenario':'port_scan'})
            self.assertEqual(response.status_code,200,response.json)
            self.assertEqual(response.json['model_kind'],'selected')
            self.assertTrue(response.json['ml_applied'])
            self.assertIsNotNone(response.json['confidence'])
        with patch('src.api.app.load_artifacts',return_value=pair), patch('src.api.app.predict_traffic',side_effect=ModelUnavailable('inference failed')):
            self.assertEqual(self.client.post('/api/demo',json={'scenario':'port_scan'}).status_code,503)

    def test_actual_lab_capture_rules_and_reset_preserves_capture_alert(self):
        catalog=self.client.get('/api/captures').json['captures']
        self.assertEqual(len(catalog),4)
        response=self.client.post('/api/captures/process',json={'capture':'scan_nmap_synscan.pcapng'})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(response.json['analysis']['packets'],2017)
        self.assertEqual(response.json['alerts_generated'],1)
        result=next(item for item in response.json['results'] if item['alert_generated'])
        self.assertEqual((result['category'],result['risk_score']),('PORT_SCAN',180))
        self.assertEqual(result['model_kind'],'offline_rules')
        self.assertFalse(result['is_demo'])
        self.assertIsNone(result['confidence'])
        detail=self.client.get(f"/api/alerts/{result['alert_id']}").json
        self.assertEqual(detail['evidence']['observations']['distinct_ports_peak_10s'],1000)
        self.assertNotIn('features',detail['evidence'])
        self.assertEqual(len(detail['evidence']['capture']['sha256']),64)
        self.client.delete('/api/demo/alerts',json={'confirm':True})
        self.assertEqual(self.client.get('/api/metrics').json['total_alerts'],1)

    def test_captures_do_not_invent_authentication_failures_or_dos(self):
        for name in ['baseline_normal_traffic.pcapng','scan_bruteforce_ssh.pcapng','scan_dos_trimmed.pcapng']:
            response=self.client.post('/api/captures/process',json={'capture':name})
            self.assertEqual(response.status_code,200,response.json)
            self.assertEqual(response.json['alerts_generated'],0)
            self.assertTrue(all(item['label'] is None for item in response.json['results']))
        self.assertEqual(self.client.get('/api/alerts').json,[])
        with patch('src.api.app.analyze_capture',side_effect=ImportError('scapy missing')):
            self.assertEqual(self.client.post('/api/captures/process',json={'capture':'baseline_normal_traffic.pcapng'}).status_code,503)
        for name in ['../README.md','/etc/passwd','missing.pcapng',None]:
            self.assertEqual(self.client.post('/api/captures/process',json={'capture':name}).status_code,400)

    def test_window_distinct_ports_and_service_volume(self):
        self.assertEqual(peak_window([(0,22),(1,22),(11,80)],10,distinct=True)[0],2)
        self.assertEqual(peak_window([(0,22),(1,22),(1.01,22)],1)[0],2)
        self.assertGreater(peak_window([(0,22),(0,80)],10,distinct=True)[1],0)

    def test_export_is_validated_non_overwriting_and_schema_referenced(self):
        model,scaler=self.fitted_pair()
        metadata=export_fitted(model,scaler,directory=self.root/'export')
        self.assertEqual(metadata['feature_count'],78)
        self.assertEqual(metadata['feature_schema'],'src/features/schema.json')
        self.assertEqual(len(metadata['feature_schema_sha256']),64)
        reloaded=joblib.load(self.root/'export/random_forest_model.pkl')
        self.assertEqual(reloaded.n_features_in_,78)
        with patch.object(predictor, 'MODEL_DIR', self.root/'export'):
            predictor.load_artifacts.cache_clear()
            self.addCleanup(predictor.load_artifacts.cache_clear)
            self.assertEqual(predictor.load_artifacts()[0].n_features_in_,78)
            meta_path=self.root/'export/model_metadata.json'
            metadata['feature_schema_sha256']='wrong'
            meta_path.write_text(json.dumps(metadata))
            predictor.load_artifacts.cache_clear()
            with self.assertRaises(ModelUnavailable):predictor.load_artifacts()
        with self.assertRaises(FileExistsError):export_fitted(model,scaler,directory=self.root/'export')
        model.n_estimators=32
        with self.assertRaises(ValueError):export_fitted(model,scaler,directory=self.root/'invalid')


if __name__=='__main__':unittest.main()
