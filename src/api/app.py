"""Local educational API: validated flow features → ML → rules → SQLite."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from src.models.predict import ModelUnavailable, load_artifacts, predict_traffic
from src.features.prepare import prepare_features
from src.detection.pipeline import build_alert

ROOT = Path(__file__).resolve().parents[2]


def create_app(database_path=None):
    app = Flask(__name__)
    app.config.update(DATABASE=str(database_path or os.environ.get('NIDS_DB_PATH', ROOT / 'nids_alerts.db')),
                      MAX_CONTENT_LENGTH=1024 * 1024)

    @contextmanager
    def connect():
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    with connect() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            severity TEXT, risk_score REAL, source TEXT,
            status TEXT DEFAULT 'investigation required',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(alerts)')}
        for name, kind in [('label', 'TEXT'), ('category', 'TEXT'), ('confidence', 'REAL'),
                           ('detection_source', 'TEXT'), ('rule_matches', 'TEXT')]:
            if name not in columns:
                conn.execute(f'ALTER TABLE alerts ADD COLUMN {name} {kind}')

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.errorhandler(sqlite3.Error)
    def storage_error(exc):
        app.logger.exception('Alert storage failed')
        return jsonify(error='Alert storage unavailable; check database path and permissions'), 503

    @app.get('/')
    def dashboard():
        return send_from_directory(ROOT / 'dashboard', 'index.html')

    @app.get('/api/health')
    def health():
        try:
            load_artifacts()
            model = {'ready': True}
        except ModelUnavailable as exc:
            model = {'ready': False, 'error': str(exc)}
        with connect() as conn:
            conn.execute('SELECT COUNT(*) FROM alerts').fetchone()
        return jsonify(status='healthy' if model['ready'] else 'degraded',
                       service='NIDS API', model=model, storage='ready')

    @app.post('/api/process')
    def process():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or 'features' not in data:
            return jsonify(error="JSON object with 'features' is required"), 400
        try:
            frame = prepare_features(data['features'])
            if len(frame) != 1:
                raise ValueError('/api/process accepts exactly one flow per request')
            # Validate rule telemetry before attempting unavailable model inference.
            event = data.get('event')
            exposure = data.get('exposure', 5)
            build_alert('BENIGN', event=event, exposure=exposure)
            prediction = predict_traffic(frame)[0]
            alert = build_alert(prediction['label'], event=event,
                                confidence=prediction['confidence'], exposure=exposure)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except ModelUnavailable as exc:
            return jsonify(error=str(exc)), 503
        alert_id = None
        if alert['category'] != 'BENIGN':
            with connect() as conn:
                cursor = conn.execute('''INSERT INTO alerts
                    (title,severity,risk_score,source,label,category,confidence,detection_source,rule_matches)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (f"Suspicious Activity: {alert['category']}", alert['risk_level'],
                     alert['risk_score'], alert['detection_source'], alert['label'],
                     alert['category'], alert['confidence'], alert['detection_source'],
                     json.dumps(alert['rule_matches'])))
                alert_id = cursor.lastrowid
        return jsonify(**alert, status='processed', prediction=alert['label'],
                       severity=alert['risk_level'], alert_generated=alert_id is not None,
                       alert_id=alert_id)

    @app.get('/api/alerts')
    def alerts():
        with connect() as conn:
            rows = [dict(row) for row in conn.execute('SELECT * FROM alerts ORDER BY id DESC LIMIT 20')]
        for row in rows:
            row['rule_matches'] = json.loads(row['rule_matches'] or '[]')
            row['risk_level'] = row['severity']
        return jsonify(rows)

    @app.get('/api/metrics')
    def metrics():
        with connect() as conn:
            total = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
            counts = {row[0] or 'legacy': row[1] for row in conn.execute(
                'SELECT category, COUNT(*) FROM alerts GROUP BY category')}
        return jsonify(total_alerts=total, by_category=counts)

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
