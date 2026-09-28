import os
import pickle
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = 'nids_alerts.db'

# Task: Load the saved model + scaler (from src/models/) into the API
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'scaler.pkl')

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    model_loaded = True
except FileNotFoundError:
    model_loaded = False
    print("Warning: model.pkl or scaler.pkl not found in src/models/. Prediction will fail until ML Engineer provides them.")

def init_db():
    """Task: Set up SQLite database schema for storing alerts."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                severity TEXT,
                risk_score REAL,
                source TEXT,
                status TEXT DEFAULT 'investigation required',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.route('/api/predict', methods=['POST'])
def predict():
    """Task: Build API endpoint to receive traffic data and return a prediction."""
    if not model_loaded:
        return jsonify({"error": "ML model not loaded from src/models/"}), 503
    
    data = request.json
    if not data or 'features' not in data:
        return jsonify({"error": "Invalid input, 'features' array is required"}), 400
    
    try:
        features = data['features']
        scaled_features = scaler.transform(features)
        prediction = model.predict(scaled_features)
        # Convert numpy integer to standard python integer for JSON response
        result = [int(p) for p in prediction]
        return jsonify({"prediction": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def save_alert():
    """Task: Build endpoint to save an alert to the database."""
    data = request.json
    if not data or 'title' not in data:
        return jsonify({"error": "Alert 'title' is required"}), 400

    title = data.get('title')
    severity = data.get('severity', 'low')
    risk_score = data.get('risk_score', 0.0)
    source = data.get('source', 'unknown')
    status = data.get('status', 'investigation required')

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (title, severity, risk_score, source, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, severity, risk_score, source, status))
            conn.commit()
            alert_id = cursor.lastrowid
        return jsonify({"message": "Alert saved", "id": alert_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Task: Build endpoint to fetch all alerts (for the dashboard later)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts ORDER BY timestamp DESC')
        alerts = [dict(row) for row in cursor.fetchall()]
    return jsonify(alerts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
