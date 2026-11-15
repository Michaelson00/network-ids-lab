"""CICIDS2017 flow-table contract; does not extract flows from packet captures."""
import json
from pathlib import Path
import pandas as pd
from src.preprocessing.validation import numeric_frame

FEATURE_NAMES = json.loads(Path(__file__).with_name('schema.json').read_text())


def prepare_features(data):
    try:
        frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    except (ValueError, TypeError) as exc:
        raise ValueError('features must be rows of 78 values or named records') from exc
    if not isinstance(frame.columns, pd.RangeIndex):
        frame.columns = [str(name).strip() for name in frame.columns]
        if frame.columns.duplicated().any() or set(frame.columns) != set(FEATURE_NAMES):
            raise ValueError('Feature names must match the 78-feature schema; exclude Label/Attack_Type')
        frame = frame[FEATURE_NAMES]
    else:
        if frame.shape[1] != len(FEATURE_NAMES):
            raise ValueError('Expected exactly 78 features in training order')
        frame.columns = FEATURE_NAMES
    return numeric_frame(frame)
