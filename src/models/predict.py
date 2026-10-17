"""Lazy loading of the selected scaled multiclass Random Forest (no fallback)."""
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
from src.features.prepare import FEATURE_NAMES, prepare_features

MODEL_DIR = Path(__file__).resolve().parent


class ModelUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_artifacts():
    paths = [MODEL_DIR / 'random_forest_model.pkl', MODEL_DIR / 'scaler.pkl']
    if not all(path.is_file() for path in paths):
        raise ModelUnavailable('Supply src/models/random_forest_model.pkl and scaler.pkl from the selected training run')
    try:
        model, scaler = [joblib.load(path) for path in paths]
        for artifact in (model, scaler):
            if getattr(artifact, 'n_features_in_', None) != len(FEATURE_NAMES):
                raise ValueError('Artifact feature count must be 78')
            names = getattr(artifact, 'feature_names_in_', None)
            if names is not None and list(names) != FEATURE_NAMES:
                raise ValueError('Artifact feature order differs from schema')
        if not hasattr(model, 'predict_proba') or not hasattr(scaler, 'transform'):
            raise ValueError('Expected classifier probabilities and fitted scaler')
        return model, scaler
    except Exception as exc:
        raise ModelUnavailable(f'Model/scaler could not be loaded: {exc}') from exc


def predict_traffic(data):
    frame = prepare_features(data)
    model, scaler = load_artifacts()
    try:
        scaled = scaler.transform(frame)
        labels = model.predict(scaled)
        probabilities = model.predict_proba(scaled)
        results = []
        for label, row in zip(labels, probabilities):
            confidence = float(row[list(model.classes_).index(label)])
            if not np.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError('Invalid model probability')
            results.append({'label': str(label), 'confidence': confidence})
        return results
    except Exception as exc:
        raise ModelUnavailable(f'Model inference failed: {exc}') from exc


def predict(data):
    """Preserve the notebook-facing batch-label interface."""
    return np.array([result['label'] for result in predict_traffic(data)])
