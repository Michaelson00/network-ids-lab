"""Local educational API: validated flow features → ML → rules → SQLite."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
import json
import os
from pathlib import Path
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from src.models.predict import ModelUnavailable, load_artifacts, predict_traffic
from src.features.prepare import prepare_features
from src.detection.pipeline import build_alert
from src.models.demo import SCENARIOS, ensure_demo_model, load_demo_artifacts, scenario_input
from src.captures.offline import analyze_capture, list_captures

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
                           ('detection_source', 'TEXT'), ('rule_matches', 'TEXT'),
                           ('is_demo', 'INTEGER NOT NULL DEFAULT 0'), ('scenario', 'TEXT'),
                           ('model_kind', 'TEXT'), ('evidence', 'TEXT'),
                           ('source_ip', 'TEXT'), ('destination_ip', 'TEXT')]:
            if name not in columns:
                conn.execute(f'ALTER TABLE alerts ADD COLUMN {name} {kind}')

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error=exc.description), exc.code

    @app.errorhandler(sqlite3.Error)
    def storage_error(exc):
        app.logger.exception('Alert storage failed')
        return jsonify(error='Alert storage unavailable; check database path and permissions'), 503

    @app.get('/assets/<path:filename>')
    def assets(filename):
        return send_from_directory(ROOT / 'dashboard', filename)

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
        try:
            load_demo_artifacts()
            demo_model = {'ready': True, 'kind': 'synthetic_demo', 'label': 'Demo / Simulated'}
        except (ModelUnavailable, ValueError) as exc:
            demo_model = {'ready': False, 'kind': 'synthetic_demo', 'error': str(exc)}
        with connect() as conn:
            conn.execute('SELECT COUNT(*) FROM alerts').fetchone()
        return jsonify(status='healthy' if model['ready'] else 'degraded',
                       service='NIDS API', model=model, demo_model=demo_model,
                       storage='ready', detection_engine='ready',
                       scenarios=list(SCENARIOS), live_capture=False, offline_capture=True,
                       rules_engine='ready', risk_engine='ready',
                       operating_mode='FULL_MODEL_MODE' if model['ready'] else 'DEMO_MODE',
                       mode_message='Benchmark model loaded successfully.' if model['ready'] else
                           'Benchmark ML model unavailable. Demo detection mode active. Rule-based detection and risk scoring available.')

    def save_result(alert, evidence, *, demo=False, scenario=None, kind='selected', source_ip=None, destination_ip=None):
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        alert_id = None
        if alert['category'] != 'BENIGN':
            with connect() as conn:
                cursor = conn.execute('''INSERT INTO alerts
                    (title,severity,risk_score,source,label,category,confidence,detection_source,rule_matches,
                     is_demo,scenario,model_kind,evidence,source_ip,destination_ip,timestamp)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (f"{'Demo / Simulated: ' if demo else 'Suspicious Activity: '}{alert['category']}",
                     alert['risk_level'], alert['risk_score'], alert['detection_source'], alert['label'],
                     alert['category'], alert['confidence'], alert['detection_source'], json.dumps(alert['rule_matches']),
                     int(demo), scenario, kind, json.dumps(evidence), source_ip, destination_ip, timestamp))
                alert_id = cursor.lastrowid
        return dict(**alert, status='processed', prediction=alert['label'], severity=alert['risk_level'],
                    timestamp=timestamp, alert_generated=alert_id is not None, alert_id=alert_id,
                    is_demo=demo, scenario=scenario, model_kind=kind,
                    ml_applied=kind not in {'rules_only', 'offline_rules'},
                    source_ip=source_ip, destination_ip=destination_ip)

    def process_flow(data, *, demo=False, scenario=None, engine='selected'):
        frame = prepare_features(data['features'])
        if len(frame) != 1:
            raise ValueError('/api/process accepts exactly one flow per request')
        event, exposure = data.get('event'), data.get('exposure', 5)
        build_alert(None, event=event, exposure=exposure)
        source_ip, destination_ip = data.get('source_ip'), data.get('destination_ip')
        for value in (source_ip, destination_ip):
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError("IP metadata must be an address string")
                ip_address(value)
        if engine == 'rules_only':
            prediction = {'label': None, 'confidence': None}
        elif engine == 'synthetic_demo':
            prediction = predict_traffic(frame, demo=True)[0]
        else:
            prediction = predict_traffic(frame)[0]
        alert = build_alert(prediction['label'], event=event,
                            confidence=prediction['confidence'], exposure=exposure)
        evidence = {'features': frame.iloc[0].to_dict(), 'event': event or {},
                    'risk_factors': alert['risk_factors'], 'ml_applied': engine != 'rules_only',
                    'input_kind': 'simulated flow features' if demo else 'submitted flow features'}
        return save_result(alert, evidence, demo=demo, scenario=scenario, kind=engine,
                           source_ip=source_ip, destination_ip=destination_ip)

    @app.post('/api/process')
    def process():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or 'features' not in data:
            return jsonify(error="JSON object with 'features' is required"), 400
        try:
            return jsonify(process_flow(data))
        except (ValueError, TypeError) as exc:
            return jsonify(error=str(exc)), 400
        except ModelUnavailable as exc:
            return jsonify(error=str(exc)), 503

    @app.post('/api/demo')
    def demo():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='JSON object with scenario is required'), 400
        try:
            name = data.get('scenario')
            payload = scenario_input(name)
            strategy = data.get('model_mode', 'auto')
            if strategy == 'synthetic':
                ensure_demo_model()
                engine = 'synthetic_demo'
            elif strategy == 'rules':
                engine = 'rules_only'
            elif strategy == 'auto':
                try:
                    load_artifacts()
                    engine = 'selected'
                except ModelUnavailable:
                    engine = 'rules_only'
            else:
                raise ValueError('model_mode must be auto, rules or synthetic')
            # These addresses are simulated metadata; no packets are sent.
            payload.update(source_ip='192.168.56.102', destination_ip='192.168.56.101')
            return jsonify(process_flow(payload, demo=True, scenario=name, engine=engine))
        except (ValueError, TypeError) as exc:
            return jsonify(error=str(exc)), 400
        except (ModelUnavailable, OSError) as exc:
            return jsonify(error=str(exc)), 503

    @app.get('/api/captures')
    def captures():
        return jsonify(captures=list_captures(), processing='offline_rules', live_capture=False)

    @app.post('/api/captures/process')
    def process_capture():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='JSON object with capture filename is required'), 400
        try:
            exposure = data.get('exposure', 5)
            build_alert(None, exposure=exposure)
            analysis = analyze_capture(data.get('capture'))
        except ImportError:
            return jsonify(error='Offline capture reader unavailable; install requirements.txt'), 503
        except (ValueError, TypeError, OSError) as exc:
            return jsonify(error=str(exc)), 400
        results = []
        for item in analysis.pop('events'):
            alert = build_alert(None, event=item['event'], exposure=exposure)
            evidence = {'input_kind': 'offline packet-header telemetry', 'capture': analysis,
                        'event': item['event'], 'observations': item['observations'],
                        'risk_factors': alert['risk_factors'], 'ml_applied': False}
            results.append(save_result(alert, evidence, kind='offline_rules',
                           source_ip=item['source_ip'], destination_ip=item['destination_ip']))
        return jsonify(analysis=analysis, results=results,
                       alerts_generated=sum(result['alert_generated'] for result in results))

    @app.delete('/api/demo/alerts')
    def clear_demo_alerts():
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or data.get('confirm') is not True:
            return jsonify(error='Send {"confirm": true} to delete only simulated demo alerts'), 400
        with connect() as conn:
            count = conn.execute('DELETE FROM alerts WHERE is_demo = 1').rowcount
        return jsonify(deleted=count, scope='demo_only')

    def scope_where():
        mode = request.args.get('mode', 'all')
        if mode not in {'all', 'demo', 'observed'}:
            raise ValueError('mode must be all, demo or observed')
        return ('is_demo = 1' if mode == 'demo' else 'is_demo = 0' if mode == 'observed' else '1=1')

    def decode(row, details=False):
        result = dict(row)
        result['rule_matches'] = json.loads(result['rule_matches'] or '[]')
        result['risk_level'] = result['severity']
        result['is_demo'] = bool(result['is_demo'])
        raw = result.pop('evidence', None)
        if details:
            result['evidence'] = json.loads(raw or '{}')
        return result

    @app.get('/api/alerts')
    def alerts():
        try:
            where, values = scope_where(), []
            filters = {'severity': 'severity', 'category': 'category',
                       'source': 'detection_source', 'status': 'status'}
            for parameter, column in filters.items():
                value = request.args.get(parameter)
                if value:
                    where += f' AND {column} = ?'
                    values.append(value)
            limit = int(request.args.get('limit', 20))
            if not 1 <= limit <= 100:
                raise ValueError('limit must be between 1 and 100')
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        with connect() as conn:
            rows = conn.execute(f'SELECT * FROM alerts WHERE {where} ORDER BY id DESC LIMIT ?', [*values, limit]).fetchall()
        return jsonify([decode(row) for row in rows])

    @app.get('/api/alerts/<int:alert_id>')
    def alert_detail(alert_id):
        with connect() as conn:
            row = conn.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,)).fetchone()
        if row is None:
            return jsonify(error='Alert not found'), 404
        return jsonify(decode(row, details=True))

    @app.get('/api/metrics')
    def metrics():
        try:
            where = scope_where()
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        with connect() as conn:
            total = conn.execute(f'SELECT COUNT(*) FROM alerts WHERE {where}').fetchone()[0]
            def groups(column):
                return {row[0] or 'legacy': row[1] for row in conn.execute(
                    f'SELECT {column}, COUNT(*) FROM alerts WHERE {where} GROUP BY {column}')}
            categories, severities, sources = groups('category'), groups('severity'), groups('detection_source')
            active = conn.execute(f"SELECT COUNT(*) FROM alerts WHERE {where} AND status = 'investigation required'").fetchone()[0]
            demo_count = conn.execute(f'SELECT COUNT(*) FROM alerts WHERE {where} AND is_demo = 1').fetchone()[0]
            timeline = [dict(row) for row in conn.execute(f'''SELECT
                strftime('%Y-%m-%dT%H:00:00Z', timestamp) AS hour, COUNT(*) AS count,
                ROUND(AVG(risk_score), 1) AS average_risk FROM alerts
                WHERE {where} AND datetime(timestamp) >= datetime('now', '-24 hours')
                GROUP BY hour ORDER BY hour''')]
        # Empty hours really contain zero stored alerts; absent risk is unknown, not zero.
        indexed = {row['hour']: row for row in timeline}
        end_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        timeline = []
        for offset in range(24, -1, -1):
            hour = (end_hour - timedelta(hours=offset)).strftime('%Y-%m-%dT%H:00:00Z')
            timeline.append(indexed.get(hour, {'hour': hour, 'count': 0, 'average_risk': None}))
        return jsonify(total_alerts=total, by_category=categories, by_severity=severities,
                       by_source=sources, active_alerts=active, demo_alerts=demo_count,
                       observed_alerts=total-demo_count, timeline=timeline,
                       scope=request.args.get('mode', 'all'), timeline_window='24h UTC')

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
