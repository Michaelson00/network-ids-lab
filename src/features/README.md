# Flow features

`schema.json` lists the 78 CICIDS2017 training columns, matching the supplied
sample CSV and selected model contract. `prepare.py` validates column membership,
rejects duplicates and orders named inputs. Arrays must already follow this order.

Raw packet-to-flow extraction is not implemented here; packet captures require
an external compatible exporter. Rule counters require aggregated telemetry;
failed login counts require authentication logs. See [run guide](../../RUN_AND_TEST.md).
