# API
# API & Database Backend

This folder contains the development backend for the NIDS lab project. It handles receiving detection results, calculating or storing risk scores, and serving alerts to the dashboard.

## Current State (Skeleton)
* **`app.py`**: A lightweight Flask application.
* **Database**: An SQLite database (`nids_alerts.db`) is automatically initialized with an `alerts` schema when the app first runs.

## How to Run
1. Ensure your virtual environment is active and dependencies are installed (`pip install -r ../../requirements.txt`).
2. Navigate to this directory: `cd src/api`
3. Run the server: `python app.py`
4. The API will be available at `http://127.0.0.1:5000`.

## Available Endpoints
* `GET /api/health`: Returns API health status.
* `GET /api/alerts`: Retrieves the latest 10 alerts from the SQLite database.

## Team Integration Dependencies
* **Data ML / Cybersecurity Leads**: Before I can build the `POST /api/alerts` endpoint, we must agree on the exact JSON payload structure (Data Contract) your detection engines will send to the API. 
* Let me know once the alert fields (e.g., predicted category, confidence, evidence) are finalized.
