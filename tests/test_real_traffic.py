import csv
import json
import requests
import os

API_URL = "http://127.0.0.1:5000/api"
# Path to the ML team's sample input
SAMPLE_FILE = os.path.join(os.path.dirname(__file__), '..', 'src', 'models', 'sample_input.csv')

def run_real_traffic_test():
    print("Initiating Real Traffic End-to-End Test...")
    
    if not os.path.exists(SAMPLE_FILE):
        print(f"[-] Error: Could not find {SAMPLE_FILE}. Ensure the ML team has pushed it.")
        return

    # Read the first data row from the CSV
    with open(SAMPLE_FILE, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)  # Skip headers
        first_row = next(reader)
        
        # Convert string values to floats
        features = [float(val) for val in first_row]

    payload = {"features": [features]}
    print(f"\n[+] Sending Payload to {API_URL}/process")
    print(json.dumps(payload, indent=2))

    try:
        res = requests.post(f"{API_URL}/process", json=payload)
        print(f"\n[+] API Response Code: {res.status_code}")
        print(f"[+] API Response Body: {json.dumps(res.json(), indent=2)}")
        
        if res.status_code == 200:
            print("\n[SUCCESS] Real traffic successfully processed through the pipeline!")
            print("Check your dashboard in the browser to see if the alert populated.")
        else:
            print("\n[FAILED] The API returned an error.")
            
    except requests.exceptions.ConnectionError:
        print("\n[-] Connection Error: Is src/api/app.py currently running?")

if __name__ == "__main__":
    run_real_traffic_test()
