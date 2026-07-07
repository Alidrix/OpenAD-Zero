from app.tool_automation.correlation import suggest_metasploit_searches
from app.tool_automation.results import make_finding


def test_correlation_cve_to_metasploit_search():
    f = make_finding(
        'nuclei_safe_templates',
        'nuclei_safe_templates',
        '10.0.0.5',
        'vulnerability',
        'high',
        'CVE',
        'desc',
        'raw',
        {'cves': ['CVE-2020-1472']},
    )
    assert any(s.suggested_template_id == 'metasploit_search_by_cve' for s in suggest_metasploit_searches([f]))


def test_correlation_smb_ldap_kerberos():
    fs = [
        make_finding(
            'nmap',
            'nmap',
            '10.0.0.5',
            'service',
            'info',
            'smb',
            'raw',
            'raw',
            {'service': 'microsoft-ds', 'port': 445, 'version': 'Windows Server 2008'},
        ),
        make_finding(
            'nmap', 'nmap', '10.0.0.5', 'service', 'info', 'ldap', 'raw', 'raw', {'service': 'ldap', 'port': 389}
        ),
        make_finding(
            'nmap', 'nmap', '10.0.0.5', 'service', 'info', 'kerb', 'raw', 'raw', {'service': 'kerberos', 'port': 88}
        ),
    ]
    ids = {s.suggested_template_id for s in suggest_metasploit_searches(fs)}
    assert {
        'metasploit_search_smb',
        'metasploit_smb_version',
        'metasploit_search_ldap',
        'metasploit_search_kerberos',
        'metasploit_check_ms17_010',
    } <= ids
