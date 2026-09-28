# rules/detection_rules.py

def detect_port_scan(connection_count, time_window_seconds):
    """
    Detects reconnaissance/port scanning activity.
    Rule: More than 20 connection attempts to different ports from a single IP within 10 seconds.
    """
    THRESHOLD_CONNECTIONS = 20
    THRESHOLD_WINDOW = 10
    
    if connection_count > THRESHOLD_CONNECTIONS and time_window_seconds <= THRESHOLD_WINDOW:
        return True, "Port Scan Detected"
    return False, "Normal"

def detect_brute_force(failed_logins, time_window_seconds):
    """
    Detects brute-force login simulations.
    Rule: 5 or more failed authentication attempts from a single IP within 60 seconds.
    """
    THRESHOLD_FAILURES = 5
    THRESHOLD_WINDOW = 60
    
    if failed_logins >= THRESHOLD_FAILURES and time_window_seconds <= THRESHOLD_WINDOW:
        return True, "Brute-Force Detected"
    return False, "Normal"

def detect_dos_traffic(request_count, time_window_seconds):
    """
    Detects Denial-of-Service (DoS) volumetric floods.
    Rule: More than 1000 requests from a single IP within 1 second.
    """
    THRESHOLD_REQUESTS = 1000
    THRESHOLD_WINDOW = 1
    
    if request_count > THRESHOLD_REQUESTS and time_window_seconds <= THRESHOLD_WINDOW:
        return True, "DoS Traffic Detected"
    return False, "Normal"