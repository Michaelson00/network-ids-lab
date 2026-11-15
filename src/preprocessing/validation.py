"""Reject invalid inference rows rather than dropping or imputing traffic."""
import numpy as np
import pandas as pd


def numeric_frame(frame):
    if frame.empty:
        raise ValueError('At least one feature row is required')
    if frame.map(lambda value: isinstance(value, (bool, np.bool_))).any().any():
        raise ValueError('Boolean features are not accepted')
    try:
        frame = frame.apply(pd.to_numeric, errors='raise').astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError('Features must be numeric') from exc
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError('Features must be finite; missing/NaN/infinite values are invalid')
    return frame
