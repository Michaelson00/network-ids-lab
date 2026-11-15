"""Export an already-fitted selected notebook model/scaler; never fabricate or retrain."""
import json
from pathlib import Path
import platform
import importlib.metadata
import joblib
from src.features.prepare import FEATURE_NAMES
from src.models.predict import MODEL_DIR, validate_artifacts, file_digest


def export_fitted(model, scaler, *, directory=MODEL_DIR, overwrite=False):
    """Call from the actual fitted notebook session after reviewing its evaluation."""
    validate_artifacts(model, scaler)
    if list(getattr(scaler, 'feature_names_in_', [])) != FEATURE_NAMES:
        raise ValueError('Scaler must retain the exact agreed feature names/order')
    if model.__class__.__name__ != 'RandomForestClassifier' or getattr(model, 'n_estimators', None) != 100:
        raise ValueError('Export the selected original 100-tree Random Forest, not the tuned/synthetic model')
    if getattr(model, 'class_weight', None) != 'balanced' or getattr(model, 'random_state', None) != 42:
        raise ValueError('Selected notebook model requires balanced class weights and seed 42')
    directory = Path(directory)
    paths = [directory / name for name in ['random_forest_model.pkl','scaler.pkl','model_metadata.json']]
    if any(path.exists() for path in paths) and not overwrite:
        raise FileExistsError('Artifacts exist; review provenance and explicitly set overwrite=True')
    directory.mkdir(parents=True, exist_ok=True)
    for path, artifact in zip(paths, (model,scaler)):
        temporary=path.with_suffix(path.suffix+'.tmp')
        joblib.dump(artifact,temporary)
        temporary.replace(path)
    schema=Path(__file__).resolve().parents[1]/'features/schema.json'
    metadata={'model':'selected multiclass RandomForestClassifier', 'training':'notebooks/02_model_comparison.ipynb',
              'feature_schema':'src/features/schema.json', 'feature_schema_sha256':file_digest(schema),
              'feature_count':len(FEATURE_NAMES), 'feature_dtype':'finite numeric', 'labels':[str(value) for value in model.classes_],
              'preprocessing':'paired fitted StandardScaler.transform before prediction',
              'python':platform.python_version(),
              'packages':{name:importlib.metadata.version(name) for name in ['scikit-learn','numpy','pandas','joblib']},
              'artifact_sha256':{path.name:file_digest(path) for path in paths[:2]}}
    paths[2].write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata
