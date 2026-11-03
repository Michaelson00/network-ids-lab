"""Local synthetic demo setup and API submission (no packets or attacks)."""
import argparse
import json
import requests
from src.models.demo import SCENARIOS, prepare_demo_model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:5000')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare', help='Create separate synthetic model/scaler, never the selected artifacts')
    run = sub.add_parser('run', help='Submit a simulated scenario through the real API pipeline')
    run.add_argument('scenario', choices=SCENARIOS)
    run.add_argument('--model-mode', choices=['auto','rules','synthetic'], default='auto')
    sub.add_parser('captures', help='List existing authorized offline captures')
    capture = sub.add_parser('capture', help='Analyze one existing lab capture using rules, not invented ML features')
    capture.add_argument('filename')
    reset = sub.add_parser('reset', help='Delete only demo alerts; preserve submitted/legacy data')
    reset.add_argument('--confirm', action='store_true', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(f'Synthetic demo model/scaler ready: {prepare_demo_model()} (not a benchmark model)')
        return
    try:
        if args.command == 'run':
            response = requests.post(args.url.rstrip('/') + '/api/demo', json={'scenario': args.scenario, 'model_mode': args.model_mode}, timeout=60)
        elif args.command == 'captures':
            response = requests.get(args.url.rstrip('/') + '/api/captures', timeout=15)
        elif args.command == 'capture':
            response = requests.post(args.url.rstrip('/') + '/api/captures/process', json={'capture': args.filename}, timeout=60)
        else:
            response = requests.delete(args.url.rstrip('/') + '/api/demo/alerts', json={'confirm': True}, timeout=15)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except requests.RequestException as exc:
        parser.exit(1, f'API request failed: {exc}\n')


if __name__ == '__main__':
    main()
