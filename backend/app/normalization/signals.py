PORT_SIGNALS = {
    445: 'smb_detected',
    389: 'ldap_detected',
    636: 'ldap_detected',
    88: 'kerberos_detected',
    3268: 'global_catalog',
    3269: 'global_catalog',
    3389: 'rdp_detected',
    5985: 'winrm_detected',
    5986: 'winrm_detected',
    1433: 'mssql_detected',
    53: 'dns_detected',
    123: 'ntp_detected',
}
HTTP_PORTS = {80, 443, 8080, 8443, 8000, 8081, 8888}
DANGEROUS_RELATIONS = {
    'AdminTo',
    'GenericAll',
    'GenericWrite',
    'WriteDacl',
    'WriteOwner',
    'AddMember',
    'AllowedToDelegate',
    'Enroll',
}
