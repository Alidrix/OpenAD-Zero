from __future__ import annotations

from dataclasses import dataclass

from app.tool_automation.results import ParsedFinding


@dataclass(frozen=True)
class ExploitSearchSuggestion:
    source_tool: str
    target: str
    service: str | None
    port: int | None
    cve: str | None
    keyword: str
    suggested_template_id: str
    reason: str
    risk_level: str


def suggest_metasploit_searches(findings: list[ParsedFinding]) -> list[ExploitSearchSuggestion]:
    out = []
    seen = set()

    def add(f, service, port, cve, keyword, tid, reason, risk='high'):
        key = (f.tool_id, f.target or '', service, port, cve, keyword, tid)
        if key not in seen:
            seen.add(key)
            out.append(
                ExploitSearchSuggestion(f.tool_id, f.target or '', service, port, cve, keyword, tid, reason, risk)
            )

    for f in findings:
        fields = f.parsed_fields or {}
        for cve in (
            fields.get('cves', [])
            if isinstance(fields.get('cves'), list)
            else ([fields.get('cve')] if fields.get('cve') else [])
        ):
            add(
                f,
                fields.get('service') if isinstance(fields.get('service'), str) else None,
                fields.get('port') if isinstance(fields.get('port'), int) else None,
                str(cve),
                str(cve),
                'metasploit_search_by_cve',
                'Parsed finding contains a CVE.',
            )
        service = str(fields.get('service') or f.parsed_fields.get('protocol') or '').lower()
        port = fields.get('port') if isinstance(fields.get('port'), int) else None
        if service in {'microsoft-ds', 'netbios-ssn', 'smb'} or port in {139, 445}:
            add(f, 'smb', port, None, 'smb', 'metasploit_search_smb', 'SMB service detected.')
            add(
                f,
                'smb',
                port,
                None,
                'smb_version',
                'metasploit_smb_version',
                'SMB version scanner can refine exploit research.',
            )
        if service == 'ldap' or port in {389, 636}:
            add(f, 'ldap', port, None, 'ldap', 'metasploit_search_ldap', 'LDAP service detected.')
        if service == 'kerberos' or port == 88:
            add(f, 'kerberos', port, None, 'kerberos', 'metasploit_search_kerberos', 'Kerberos service detected.')
        version = str(fields.get('version') or '').strip()
        if service and version:
            add(
                f,
                service,
                port,
                None,
                service,
                'metasploit_search_by_service',
                'Service and version were parsed from tool output.',
            )
        if (service in {'smb', 'microsoft-ds', 'netbios-ssn'} or port in {139, 445}) and any(
            x in version.lower() for x in ['windows 7', '2008', 'smbv1']
        ):
            add(
                f,
                'smb',
                port,
                None,
                'ms17-010',
                'metasploit_check_ms17_010',
                'Legacy Windows/SMB indicator warrants explicit safe check preview.',
            )
    return out
