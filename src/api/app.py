from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'nids_alerts.db'

def init_db():
    """Set up the SQLite database skeleton for storing alerts."""
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
    """Basic endpoint for health and metrics."""
    return jsonify({"status": "healthy", "service": "NIDS API"})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Endpoint for the dashboard to read alert information."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10')
        alerts = [dict(row) for row in cursor.fetchall()]
    return jsonify(alerts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
