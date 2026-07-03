ALLOWED_SIGNALS = {
    'host_discovered','windows_host_detected','linux_host_detected','smb_open','ldap_open','kerberos_open',
    'http_open','rdp_open','winrm_open','mssql_open','ssh_open','ftp_open','artifact_uploaded',
    'bloodhound_artifact_present','scan_completed',
}

PORT_SIGNAL_MAP = {
    (445, 'tcp'): 'smb_open', (139, 'tcp'): 'smb_open',
    (389, 'tcp'): 'ldap_open', (636, 'tcp'): 'ldap_open',
    (88, 'tcp'): 'kerberos_open', (88, 'udp'): 'kerberos_open',
    (80, 'tcp'): 'http_open', (443, 'tcp'): 'http_open', (8080, 'tcp'): 'http_open', (8443, 'tcp'): 'http_open',
    (3389, 'tcp'): 'rdp_open', (5985, 'tcp'): 'winrm_open', (5986, 'tcp'): 'winrm_open',
    (1433, 'tcp'): 'mssql_open', (22, 'tcp'): 'ssh_open', (21, 'tcp'): 'ftp_open',
}
SERVICE_SIGNAL_TOKENS = {
    'smb': 'smb_open', 'microsoft-ds': 'smb_open', 'netbios-ssn': 'smb_open',
    'ldap': 'ldap_open', 'kerberos': 'kerberos_open', 'http': 'http_open', 'https': 'http_open',
    'rdp': 'rdp_open', 'ms-wbt-server': 'rdp_open', 'winrm': 'winrm_open', 'mssql': 'mssql_open',
    'ms-sql-s': 'mssql_open', 'ssh': 'ssh_open', 'ftp': 'ftp_open',
}

def normalize_signal(signal: object) -> str | None:
    normalized = str(signal or '').strip().lower().replace('-', '_').replace(' ', '_')
    return normalized if normalized in ALLOWED_SIGNALS else None

def service_to_signal(port: object, protocol: object = 'tcp', service_name: object = None) -> str | None:
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        port_int = None
    proto = str(protocol or 'tcp').lower()
    if port_int is not None and (port_int, proto) in PORT_SIGNAL_MAP:
        return PORT_SIGNAL_MAP[(port_int, proto)]
    name = str(service_name or '').lower()
    for token, signal in SERVICE_SIGNAL_TOKENS.items():
        if token in name:
            return signal
    return None
