## System Integration and DevOps Architecture

The DevOps and Software Engineering phase was critical for transitioning the project from isolated data science notebooks and theoretical security rules into a functional, automated Network Intrusion Detection System (NIDS). The architecture was designed around a decoupled, microservice-inspired paradigm, ensuring that the machine learning classification, rule-based threat modeling, data persistence, and user interface operated independently while communicating seamlessly via a RESTful API.

### RESTful API & Orchestration Layer
The core routing infrastructure was engineered using the Flask web framework in Python. Serving as the central orchestrator, the API (`src/api/app.py`) bridges the gap between raw network telemetry and actionable security intelligence.
*   **Dynamic Component Loading:** The backend is configured to dynamically deserialize the ML components (`model.pkl` and `scaler.pkl`) and import the isolated Python modules (`predict_traffic`, `calculate_risk`) upon startup, ensuring the API always serves the latest models provided by the data team.
*   **The Processing Pipeline:** The primary `/api/process` endpoint dictates the system's operational flow. When network feature arrays are ingested, the API standardizes the data using the loaded scaler, retrieves the ML prediction label, routes the payload through the cybersecurity risk-scoring algorithm, and generates a finalized threat verdict in real-time.

### Lightweight Data Persistence
To maintain an immutable historical log of security events for analyst triage, an automated database layer was integrated directly into the API lifecycle.
*   **Embedded Database Engine:** SQLite was selected (`nids_alerts.db`) for its zero-configuration, file-based architecture, which perfectly satisfied the prototype's requirements for lightweight, transactional storage without the overhead of deploying a dedicated SQL server.
*   **Optimized Alert Schema:** The relational schema tracks the `id`, `title`, `severity`, `risk_score`, `source`, `status`, and `timestamp` of every malicious event. To optimize storage and prevent database bloat, the API logic explicitly bypasses persistence for traffic classified as "normal," ensuring that analysts only interface with high-fidelity, actionable intelligence.

### Asynchronous Security Dashboard
To visualize network threats, a modern frontend interface was developed using raw HTML, CSS, and vanilla JavaScript, eliminating the need for heavy frontend frameworks.
*   **UI/UX Design:** The interface was built with a strict minimalist aesthetic—utilizing geometric typography (`Space Grotesk`), structured grid layouts, and a dark-mode color palette. This design reduces eye strain during prolonged monitoring while visually elevating critical, high-severity alerts.
*   **Real-Time Telemetry:** The dashboard relies on asynchronous client-side rendering. It utilizes the JavaScript Fetch API to poll the backend `/api/alerts` endpoint every 5 seconds. This creates a near real-time monitoring experience, dynamically appending new security events to the DOM as the detection engine processes them, entirely bypassing manual page refreshes.

### Automated Pipeline Validation
To maintain pipeline stability and ensure continuous integration as disparate team components were merged into the `dev` branch, a robust testing suite was established.
*   **Integration Testing:** Utilizing Python's `unittest` framework (`test_detection_pipeline.py`), automated assertions were written to verify the end-to-end API pipeline alongside the cybersecurity deterministic logic. 
*   **Real-World Traffic Simulation:** A dedicated execution script (`test_real_traffic.py`) was engineered to parse the ML team's actual sample datasets (`sample_input.csv`), dynamically POST the structured features to the API, and validate the resulting database commit and dashboard output. This verified that the NIDS could successfully ingest and evaluate realistic network data structures outside of mocked testing environments.
