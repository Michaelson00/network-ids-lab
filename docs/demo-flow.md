# Final presentation flow

1. From the root, install dependencies and start `python -m src.api.app`.
2. Open http://127.0.0.1:5000/; distinguish selected versus synthetic model status.
3. Show empty state; click **Benign traffic** and explain low risk/no attack row.
4. Click **Port scan**; show the selected model verdict, matched rule and risk.
5. Inspect stored rule evidence/features and Likelihood × Impact × Exposure.
6. Show KPI/category/severity/source/activity charts update from SQLite.
7. Run **Brute force** and **DoS**; explain scores depend on the selected model
   probability. For deterministic rules-only results, use `model_mode: "rules"`.
8. Filter recent alerts, select Demo scope, and open alert details.
9. Explain runtime model use does not independently measure benchmark quality.
   The offline capture reader uses packet-header rules only; there is no live
   monitoring or packet-to-feature exporter.
10. Confirm **Clear demo alerts** removes only simulated rows, then stop with Ctrl+C.

See [RUN_AND_TEST.md](../RUN_AND_TEST.md#13-final-presentation--demo-procedure).
Do not claim historical multiclass metrics were reproduced by synthetic examples.
