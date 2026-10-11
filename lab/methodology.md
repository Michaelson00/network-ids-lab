# Lab & Methodology

*Section owner: Network Engineer*

## Overview

This section describes the network lab environment used to generate the traffic data underpinning this project's intrusion detection system — including its topology, the tools used, and the methodology followed to capture both normal and malicious traffic.

## Lab Topology

The lab consists of two virtual machines running under Oracle VirtualBox, connected via an isolated **host-only network**:

- **attacker-kali** — Kali Linux (Xfce desktop environment), IP `192.168.56.102`. Hosts the offensive tooling (Nmap, Hydra, hping3) and Wireshark, used to generate and capture traffic.
- **target-ubuntu** — Ubuntu Server 26.04.1 LTS, IP `192.168.56.101`. A minimal installation with OpenSSH server added as the sole exposed service, providing a realistic target for the brute-force and DoS scenarios.

Both VMs sit on the `192.168.56.0/24` subnet via VirtualBox's Host-only Adapter. This configuration allows the two machines to communicate freely with each other and the host, while having **no route to the public internet** — ensuring all simulated attack traffic remains fully contained within the lab and poses no risk outside it.

Internet access (via a temporary switch to NAT mode) was used only for initial software installation (VM Guest Additions, OpenSSH server) and was always reverted to host-only before any traffic was generated or captured.

## Tools Used

| Tool | Purpose |
|---|---|
| Oracle VirtualBox | Virtualization platform hosting both VMs |
| Wireshark | Packet capture and traffic analysis, run on attacker-kali |
| Nmap | Port scanning / reconnaissance simulation |
| Hydra | SSH brute-force simulation |
| hping3 | SYN flood / DoS simulation |
| OpenSSH server | Target service for brute-force and DoS scenarios |

## Capture Methodology

All traffic was captured using Wireshark on the `eth0` interface of `attacker-kali`. For each scenario, a fresh capture was started before the relevant command was run, then stopped and saved immediately after, to keep each `.pcapng` file scoped to a single, identifiable traffic pattern.

Four captures were produced:

1. **Baseline (normal traffic)** — ICMP ping exchanges between the two VMs and the host, representing ordinary background activity with no attack behavior present.
2. **Port scan** — an Nmap SYN scan (`nmap -sS`) against the target, producing a short burst of SYN probes spread across many ports from a single source.
3. **Brute-force** — a Hydra dictionary attack against the target's SSH service, producing repeated authentication attempts against a single port over a sustained period.
4. **Denial of Service** — an hping3 SYN flood against the target's SSH port, producing an extremely high packet rate to a single port in a short, deliberately time-limited window.

Each capture was analyzed to identify the traffic characteristic that distinguishes it from normal activity (breadth of ports touched, repetition against one port, or raw packet volume), forming the basis for the detection indicators used elsewhere in this project.

## Safety Considerations

- No scenario traffic ever left the isolated host-only subnet.
- The DoS scenario was intentionally capped to roughly 10–15 seconds of runtime to avoid excessive load, even though the environment was fully isolated.
- Internet connectivity was never active during any capture, only during unrelated software installation steps.
