"""Read existing lab captures offline; extract rule telemetry, never invented ML flows."""
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parents[2] / 'lab'
MAX_BYTES = 50 * 1024 * 1024
MAX_PACKETS = 200000


def capture_path(name):
    if not isinstance(name, str) or Path(name).name != name:
        raise ValueError('Choose a capture filename from /api/captures')
    path = LAB_DIR / name
    if path.suffix.lower() not in {'.pcap', '.pcapng'} or not path.is_file() or path.resolve().parent != LAB_DIR.resolve():
        raise ValueError('Capture is not an available authorized lab file')
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Capture exceeds the 50 MiB offline processing limit')
    return path


def list_captures():
    return [{'filename': p.name, 'bytes': p.stat().st_size} for p in sorted(LAB_DIR.iterdir())
            if p.suffix.lower() in {'.pcap', '.pcapng'} and p.is_file() and p.resolve().parent == LAB_DIR.resolve()]


def peak_window(samples, seconds, distinct=False):
    """Peak sliding window; counts distinct ports for scans, SYN attempts for volume."""
    window, ports = deque(), Counter()
    best_count, best_span = 0, seconds
    for timestamp, port in sorted(samples):
        while window and timestamp - window[0][0] > seconds:
            _, old_port = window.popleft()
            ports[old_port] -= 1
            if not ports[old_port]: del ports[old_port]
        window.append((timestamp, port)); ports[port] += 1
        count = len(ports) if distinct else len(window)
        if count > best_count:
            best_count, best_span = count, max(.000001, timestamp - window[0][0])
    return best_count, best_span


def analyze_capture(name):
    # PcapReader is a file reader; no sniff/send/socket APIs are used.
    from scapy.layers.inet import IP, TCP
    from scapy.layers.inet6 import IPv6
    from scapy.layers.l2 import Ether  # Registers Ethernet decoding for PCAP readers.
    from scapy.utils import PcapReader
    path = capture_path(name)
    pairs = defaultdict(lambda: {'packets': 0, 'syn': []})
    total, ip_packets, start, end = 0, 0, None, None
    try:
        with PcapReader(str(path)) as reader:
            for packet in reader:
                total += 1
                if total > MAX_PACKETS:
                    raise ValueError('Capture exceeds the 200,000 packet limit; no partial results stored')
                timestamp = float(packet.time)
                if not math.isfinite(timestamp):
                    raise ValueError('Capture contains non-finite timestamps')
                start = timestamp if start is None else min(start, timestamp)
                end = timestamp if end is None else max(end, timestamp)
                network = packet.getlayer(IP) or packet.getlayer(IPv6)
                if network is None: continue
                ip_packets += 1
                pair = pairs[(str(network.src), str(network.dst))]
                pair['packets'] += 1
                tcp = network.getlayer(TCP)
                # Only initial SYN connection attempts, not ACKs or encrypted login guesses.
                if tcp is not None and int(tcp.flags) & 0x02 and not int(tcp.flags) & 0x10:
                    pair['syn'].append((timestamp, int(tcp.dport)))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f'Capture could not be read: {path.name}') from exc
    if total == 0:
        raise ValueError('Capture contains no readable packets')
    events = []
    for (source, destination), pair in sorted(pairs.items()):
        event = {}
        scan_count, scan_window = peak_window(pair['syn'], 10, distinct=True)
        by_service = defaultdict(list)
        for sample in pair['syn']: by_service[sample[1]].append(sample)
        service_peaks = [(peak_window(samples, 1), port) for port, samples in by_service.items()]
        volume, service = max(service_peaks, default=((0, 1), None))
        if pair['syn']:
            event.update(connection_count=scan_count, connection_window_seconds=scan_window,
                         request_count=volume[0], request_window_seconds=volume[1])
        events.append({'source_ip': source, 'destination_ip': destination, 'event': event,
                       'observations': {'ip_packets': pair['packets'], 'initial_syn_attempts': len(pair['syn']),
                                        'distinct_ports_peak_10s': scan_count, 'syn_service_port_peak_1s': service,
                                        'syn_attempts_peak_1s': volume[0]}})
    stamp = lambda value: datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None
    return {'capture': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'packets': total, 'ip_packets': ip_packets, 'capture_start': stamp(start), 'capture_end': stamp(end),
            'events': events, 'ml_applied': False,
            'limitations': ['Offline packet-header rule telemetry, not CICFlowMeter 78-feature extraction.',
                            'SYN volume is a connection-attempt proxy, not observed HTTP requests.',
                            'Encrypted SSH does not reveal failed logins; no brute-force failures inferred.',
                            'No rule match does not establish that traffic is benign.']}
