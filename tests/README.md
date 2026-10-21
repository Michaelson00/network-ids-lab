# Tests

From repository root with dependencies installed:

```sh
python -m unittest discover -s tests -v
```

Detection regressions cover benign, scan, brute force and DoS. Application tests
use temporary fitted fixture models/scalers, a temporary SQLite database, and
Flask's test client; they do not require a running server. They cover feature
validation/order, artifact failures, class probabilities, rules, risk boundaries,
storage persistence/migration, metrics and dashboard routing.

`python tests/test_real_traffic.py` is a separate manual live-API CSV check with
a 30-second request timeout. It requires the real artifacts and running API.
Automated fixtures do not verify the missing selected model or browser rendering.
See [run guide](../RUN_AND_TEST.md).
