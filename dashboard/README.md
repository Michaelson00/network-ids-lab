# Dashboard
# NIDS Security Dashboard

This folder contains the frontend interface for visualizing NIDS alerts, traffic metrics, and system health.

## Current State (Skeleton)
* **`index.html`**: The primary dashboard view containing the UI layout and an API health-check script.

## How to View
Simply open `index.html` in any modern web browser. 

*Note: For the "API Status" indicator to show as Healthy, the Flask backend in `src/api/` must be running concurrently on port 5000.*

## Team Integration Dependencies
* The alerts table currently expects the following standard fields: **ID, Title, Severity, Risk Score, Status, and Timestamp**[cite: 3].
* Once the API is receiving real detection events from the ML/Rules engines, the JavaScript logic in this file will be updated to fetch and dynamically populate the table with live data.

  
Frontend that reads alerts via the API — owned by DevOps.
