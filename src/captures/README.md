# Offline authorized lab captures

`offline.py` reads only existing `.pcap`/`.pcapng` files directly under root
`lab/`, using Scapy's [PcapReader](https://scapy.readthedocs.io/en/stable/api/scapy.utils.html#scapy.utils.PcapReader).
No sniff/send/replay/socket interface is exposed. Size and packet-count limits
bound processing before any results are stored.

IPv4/IPv6 header observations are grouped by source/target. Initial TCP SYNs
without ACK supply distinct destination-port counts in sliding 10-second windows
and per-service SYN attempt volume in sliding 1-second windows. These counters
run the existing rules/scoring, not a new threshold system. SYN attempts are a
connection-volume proxy, not observed HTTP requests; other flood types are not
classified by this minimal reader. Encrypted SSH is not authentication evidence.

The reader is not a CICFlowMeter replacement. It does not invent 78-feature
rows, ML labels/probabilities or failed-login counts. The API preserves capture
hash/times/counts and rule evidence; only actual matched attacks create alerts.
No match is not proof that traffic is benign. Demo-only reset preserves capture
records. See [runbook](../../RUN_AND_TEST.md#5-offline-pcap-mode--actual-supplied-captures).
