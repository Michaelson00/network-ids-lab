import os
import sys
import sqlite3
from flask import Flask, request, jsonify

# Add project root to path so we can import from other src directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import from ML and Cybersecurity team modules
try:
    from src.models.predict import predict_traffic
    from src.scoring.risk_scoring import calculate_risk
    modules_loaded = True
except ImportError:
    modules_loaded = False
    print("Warning: Could not import predict_traffic or calculate_risk. Ensure they exist in src/models and src/scoring.")

app = Flask(__name__)
DB_PATH = 'nids_alerts.db'

def init_db():
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "NIDS API"})

@app.route('/api/process', methods=['POST'])
def process_traffic():
    """Full pipeline: Receive Data -> Predict -> Score -> Save Alert"""
    if not modules_loaded:
        return jsonify({"error": "Integration modules missing"}), 503
    
    data = request.json
    if not data or 'features' not in data:
        return jsonify({"error": "Invalid input, 'features' array is required"}), 400
    
    try:
        features = data['features']
        
        # 1. ML Prediction
        label = predict_traffic(features)
        
        # 2. Risk Scoring
        risk_score, severity = calculate_risk(label, features)
        
        # 3. Save to Database if it's an attack (e.g., label != 'normal')
        alert_id = None
        if label.lower() != 'normal':
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts (title, severity, risk_score, source, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (f"Suspicious Activity: {label}", severity, risk_score, "ML Engine", "investigation required"))
                conn.commit()
                alert_id = cursor.lastrowid
                
        return jsonify({
            "status": "processed",
            "prediction": label,
            "risk_score": risk_score,
            "alert_generated": bool(alert_id),
            "alert_id": alert_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Fetch all alerts for the dashboard"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 20')
        alerts = [dict(row) for row in cursor.fetchall()]
    return jsonify(alerts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
