"""Manual live-API check using a supplied flow CSV, not packet capture replay."""
import csv
from pathlib import Path
import requests

API_URL = 'http://127.0.0.1:5000/api'
SAMPLE_FILE = Path(__file__).resolve().parents[1] / 'src/models/sample_input.csv'


def run_real_traffic_test():
    with SAMPLE_FILE.open() as stream:
        row = next(csv.DictReader(stream))
    response = requests.post(f'{API_URL}/process', json={
        'features': [{name.strip(): float(value) for name, value in row.items()}]}, timeout=30)
    response.raise_for_status()
    result = response.json()
    assert result['status'] == 'processed', result
    if result['alert_generated']:
        stored = requests.get(f'{API_URL}/alerts', timeout=10)
        stored.raise_for_status()
        assert any(alert['id'] == result['alert_id'] for alert in stored.json())
    print(result)


if __name__ == '__main__':
    run_real_traffic_test()
