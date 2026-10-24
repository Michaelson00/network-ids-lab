# Final presentation flow

1. From the root, install dependencies and start `python -m src.api.app`.
2. Open http://127.0.0.1:5000/; distinguish selected versus synthetic model status.
3. Show empty state; click **Benign traffic** and explain low risk/no attack row.
4. Click **Port scan**; show the actual synthetic-model verdict and risk 200.
5. Inspect stored rule evidence/features and Likelihood × Impact × Exposure.
6. Show KPI/category/severity/source/activity charts update from SQLite.
7. Run **Brute force** (risk 420) and **DoS** (risk 720), or use CLI equivalents.
8. Filter recent alerts, select Demo scope, and open alert details.
9. Explain this synthetic demonstrator does not measure benchmark quality, analyze
   PCAPs or run live attacks; selected artifacts remain missing.
10. Confirm **Clear demo alerts** removes only simulated rows, then stop with Ctrl+C.

See [RUN_AND_TEST.md](../RUN_AND_TEST.md#13-final-presentation--demo-procedure).
Do not claim historical multiclass metrics were reproduced by synthetic examples.
