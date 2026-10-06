import joblib
import pandas as pd
import os

# find the folder this file lives in, so paths work no matter where it's called from
_here = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(_here, "random_forest_model.pkl"))
scaler = joblib.load(os.path.join(_here, "scaler.pkl"))

def predict(data):
    data_scaled = scaler.transform(data)
    predictions = model.predict(data_scaled)
    return predictions

