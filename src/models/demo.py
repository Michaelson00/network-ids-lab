"""Explicit synthetic demo artifacts. Never a substitute for CICIDS2017 training."""
from functools import lru_cache
import os
from pathlib import Path
from threading import Lock
import joblib
import numpy as np
import pandas as pd
from src.features.prepare import FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[2]
_LOCK = Lock()
SCENARIOS = {
    'benign': {'label': 'BENIGN', 'event': {}, 'exposure': 5,
               'values': [443, 500000, 6, 4, 600, 1200, 3600, 20]},
    'port_scan': {'label': 'PortScan', 'event': {'connection_count': 35, 'connection_window_seconds': 8},
                  'exposure': 5, 'values': [22, 1000, 35, 0, 0, 0, 0, 35000]},
    'brute_force': {'label': 'SSH-Patator', 'event': {'failed_logins': 7, 'login_window_seconds': 30},
                    'exposure': 6, 'values': [22, 30000000, 70, 70, 7000, 7000, 467, 5]},
    'dos': {'label': 'DDoS', 'event': {'request_count': 1500, 'request_window_seconds': 1},
            'exposure': 8, 'values': [80, 1000000, 1500, 0, 60000, 0, 60000, 1500]},
}
COLUMNS = ['Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
           'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Flow Bytes/s', 'Flow Packets/s']


def artifact_dir():
    directory = Path(os.environ.get('NIDS_DEMO_MODEL_DIR', ROOT / 'data/demo'))
    if directory.resolve() == (ROOT / 'src/models').resolve():
        raise ValueError('Demo artifacts must not overwrite the selected-model directory')
    return directory


def scenario_input(name):
    if not isinstance(name, str) or name not in SCENARIOS:
        raise ValueError('scenario must be benign, port_scan, brute_force or dos')
    scenario = SCENARIOS[name]
    row = dict.fromkeys(FEATURE_NAMES, 0.0)
    row.update(zip(COLUMNS, scenario['values']))
    return {'features': [row], 'event': dict(scenario['event']), 'exposure': scenario['exposure']}


def prepare_demo_model():
    """Fit and save a small reproducible synthetic forest/scaler in a separate folder."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    directory = artifact_dir()
    with _LOCK:
        directory.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(42)
        rows, labels = [], []
        for name, scenario in SCENARIOS.items():
            base = scenario_input(name)['features'][0]
            for _ in range(32):
                row = dict(base)
                for column in COLUMNS[1:]:
                    row[column] *= float(rng.uniform(.9, 1.1))
                rows.append(row)
                labels.append(scenario['label'])
        frame = pd.DataFrame(rows, columns=FEATURE_NAMES)
        scaler = StandardScaler().fit(frame)
        model = RandomForestClassifier(n_estimators=32, random_state=42, n_jobs=1).fit(
            scaler.transform(frame), labels)
        for filename, value in [('random_forest_model.pkl', model), ('scaler.pkl', scaler)]:
            temporary = directory / (filename + '.tmp')
            joblib.dump(value, temporary)
            temporary.replace(directory / filename)
        load_demo_artifacts.cache_clear()
    return directory


@lru_cache(maxsize=1)
def load_demo_artifacts():
    from src.models.predict import ModelUnavailable, validate_artifacts
    directory = artifact_dir()
    paths = [directory / 'random_forest_model.pkl', directory / 'scaler.pkl']
    if not all(path.is_file() for path in paths):
        raise ModelUnavailable('Synthetic demo model not initialized; run a demo or python -m src.demo prepare')
    try:
        artifacts = tuple(joblib.load(path) for path in paths)
        validate_artifacts(*artifacts)
        return artifacts
    except Exception as exc:
        raise ModelUnavailable('Demo artifacts incompatible; run python -m src.demo prepare') from exc


def ensure_demo_model():
    paths = [artifact_dir() / name for name in ['random_forest_model.pkl', 'scaler.pkl']]
    if not all(path.is_file() for path in paths):
        prepare_demo_model()
    return load_demo_artifacts()
