"""Lazy loading of the selected scaled multiclass Random Forest (no fallback)."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
from src.features.prepare import FEATURE_NAMES, prepare_features

MODEL_DIR = Path(__file__).resolve().parent


class ModelUnavailable(RuntimeError):
    pass


def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_artifacts(model, scaler):
    for artifact in (model, scaler):
        if getattr(artifact, 'n_features_in_', None) != len(FEATURE_NAMES):
            raise ValueError('Artifact feature count must be 78')
        names = getattr(artifact, 'feature_names_in_', None)
        if names is not None and list(names) != FEATURE_NAMES:
            raise ValueError('Artifact feature order differs from schema')
    if not hasattr(model, 'predict_proba') or not hasattr(scaler, 'transform'):
        raise ValueError('Expected classifier probabilities and fitted scaler')


@lru_cache(maxsize=1)
def load_artifacts():
    paths = [MODEL_DIR / 'random_forest_model.pkl', MODEL_DIR / 'scaler.pkl']
    if not all(path.is_file() for path in paths):
        raise ModelUnavailable('Supply src/models/random_forest_model.pkl and scaler.pkl from the selected training run')
    try:
        model, scaler = [joblib.load(path) for path in paths]
        validate_artifacts(model, scaler)
        metadata_path = MODEL_DIR / 'model_metadata.json'
        if metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text())
            schema = Path(__file__).resolve().parents[1] / 'features/schema.json'
            if metadata.get('feature_count') != len(FEATURE_NAMES) or metadata.get('feature_schema_sha256') != file_digest(schema):
                raise ValueError('Export metadata does not match the agreed feature schema')
            if metadata.get('labels') != [str(value) for value in model.classes_]:
                raise ValueError('Exported label mapping does not match the classifier')
            for path in paths:
                if metadata.get('artifact_sha256', {}).get(path.name) != file_digest(path):
                    raise ValueError('Model/scaler export checksum mismatch; provide same-run artifacts')
        return model, scaler
    except Exception as exc:
        raise ModelUnavailable(f'Model/scaler could not be loaded: {exc}') from exc


def predict_traffic(data, *, demo=False):
    frame = prepare_features(data)
    if demo:
        from src.models.demo import load_demo_artifacts
        model, scaler = load_demo_artifacts()
    else:
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
