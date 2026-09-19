# Lab
Isolated VM lab setup, topology, capture process — owned by Network Engineer.
# Network Lab — Isolated Attack Simulation Environment

## Purpose

This lab provides an isolated network environment for simulating normal and malicious network traffic in support of the team's Network Intrusion Detection System (NIDS) project. All traffic captures generated here are used by the Data Analyst and Cybersecurity Engineer to build detection rules and train the ML model.

## Machines

| VM | Role | OS | IP Address |
|---|---|---|---|
| attacker-kali | Attacker | Kali Linux (Xfce desktop) | 192.168.56.102 |
| target-ubuntu | Target | Ubuntu Server 26.04.1 LTS | 192.168.56.101 |

Both VMs run in Oracle VirtualBox on a Windows host.

## Network Topology

- **Network mode:** VirtualBox Host-only Adapter (`VirtualBox Host-Only Ethernet Adapter`)
- **Subnet:** 192.168.56.0/24
- **Host adapter address:** 192.168.56.1
- **IP assignment:** dynamic (DHCP within the host-only range)

The host-only network allows the two VMs to communicate with each other and the host machine, but has **no route to the internet**. This isolation ensures all attack traffic stays fully contained inside the lab.

> **Note:** Adapters were temporarily switched to NAT solely to install software (Guest Additions, OpenSSH server) via `apt`, then switched back to Host-only before any traffic capture. No captures were taken while either VM had internet access.

## Setup Steps

1. Installed Oracle VirtualBox on the host machine.
2. Created a host-only network (`vboxnet0` / VirtualBox Host-Only Ethernet Adapter) via `VBoxManage hostonlyif create`.
3. Built `attacker-kali` (Kali Linux, Xfce desktop, top10 + default tool collection) — 4GB RAM, 2 CPUs, 25GB disk.
4. Built `target-ubuntu` (Ubuntu Server, minimal/no desktop) — 2GB RAM, 1 CPU, 20GB disk.
5. Attached both VMs' Adapter 1 to the Host-only Adapter.
6. Verified connectivity with `ping` between the two VMs (0% packet loss, both directions).
7. Installed OpenSSH server on `target-ubuntu` to provide a real service for brute-force testing (`sudo apt install openssh-server`), then confirmed with `sudo systemctl status ssh`.

## Traffic Capture Process

All captures were taken with **Wireshark** on `attacker-kali`, interface `eth0`, and saved as `.pcapng` files.

| Capture File | Scenario | Description |
|---|---|---|
| `baseline_normal_traffic.pcapng` | Normal traffic | ICMP ping exchanges between attacker, target, and host — represents ordinary background activity with no attack behavior. |
| `scan_nmap_synscan.pcapng` | Port scan | `nmap -sS 192.168.56.101` — SYN scan across 1000 ports from a single source in under a second. |
| `scan_bruteforce_ssh.pcapng` | Brute-force | `hydra -l benjie-ubuntu -P rockyou.txt ssh://192.168.56.101` — repeated failed login attempts against a single port (22). |
| `scan_dos.pcapng` | Denial of Service | `hping3 -S --flood -p 22 192.168.56.101` — high-rate SYN flood against a single port, run for ~10–15 seconds only. |

### Observed Indicators

- **Port scan:** many distinct destination ports, each hit once, from one source IP, in a very short time window.
- **Brute-force:** repeated connections to a single port (22) from one source, over a longer duration than a scan.
- **DoS:** extreme packet rate to a single port from one source, far higher volume than the brute-force capture, over a very short window.

## Safety Boundaries

- All simulated traffic stayed within the 192.168.56.0/24 host-only subnet.
- Neither VM had internet access during any capture.
- The DoS scenario was deliberately time-limited (10–15 seconds) to avoid unnecessary load, even within the isolated lab.
- Internet access (NAT) was only enabled for software installation, never during traffic generation, and was disabled again before any capture.

## Reproducing This Lab

1. Install VirtualBox.
2. Create a host-only network via VirtualBox's Network Manager or `VBoxManage hostonlyif create`.
3. Create two VMs (Kali + Ubuntu Server), attach both to the host-only adapter.
4. Verify connectivity with `ping`.
5. Install Wireshark (pre-installed on Kali) and capture on the interface showing the 192.168.56.x address.
6. Run the scenarios listed above, saving each as a separate labeled `.pcapng` file.
