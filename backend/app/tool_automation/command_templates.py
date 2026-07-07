"""Executable command templates for the Tool Automation Library.

Templates are argv lists only. The backend reconstructs commands from these
allowlisted templates; no raw shell commands are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandTemplate:
    id: str
    tool_id: str
    name: str
    description: str
    argv: list[str]
    required_params: list[str]
    optional_params: list[str]
    parser: str
    risk_level: str = 'low'
    output_artifact_type: str | None = None
    scope_sensitive_params: list[str] = field(default_factory=list)
    file_input_params: list[str] = field(default_factory=list)
    file_output_params: list[str] = field(default_factory=list)
    credential_params: list[str] = field(default_factory=list)
    free_text_params: list[str] = field(default_factory=list)
    enum_params: dict[str, list[str]] = field(default_factory=dict)
    allow_hostnames: bool = False
    allow_urls: bool = False


COMMAND_TEMPLATE_DEFINITIONS: dict[str, CommandTemplate] = {
    'nmap_safe_discovery': CommandTemplate(
        'nmap_safe_discovery',
        'nmap_safe_discovery',
        'Nmap safe discovery',
        'Lightweight service/version discovery against one validated target.',
        ['nmap', '-sV', '--version-light', '{target}'],
        ['target'],
        [],
        'nmap',
        'low',
        'scan',
    ),
    'netexec_smb_fingerprint': CommandTemplate(
        'netexec_smb_fingerprint',
        'netexec_smb_fingerprint',
        'NetExec SMB fingerprint',
        'Read-only SMB fingerprinting.',
        ['nxc', 'smb', '{target}', '--shares', '--no-bruteforce'],
        ['target'],
        [],
        'netexec',
        'low',
        'smb',
    ),
    'netexec_smb_signing_check': CommandTemplate(
        'netexec_smb_signing_check',
        'netexec_smb_signing_check',
        'NetExec SMB signing',
        'Generate a relay list for SMB signing state review.',
        ['nxc', 'smb', '{target}', '--gen-relay-list', '{output}'],
        ['target', 'output'],
        [],
        'netexec',
        'low',
        'smb',
    ),
    'netexec_smb_null_session_check': CommandTemplate(
        'netexec_smb_null_session_check',
        'netexec_smb_null_session_check',
        'NetExec null session',
        'Check null-session exposure without brute force.',
        ['nxc', 'smb', '{target}', '-u', '', '-p', ''],
        ['target'],
        [],
        'netexec',
        'low',
        'smb',
    ),
    'netexec_smb_null_session_shares': CommandTemplate(
        'netexec_smb_null_session_shares',
        'netexec_smb_null_session_shares',
        'NetExec null-session shares',
        'Check null-session share exposure without brute force.',
        ['nxc', 'smb', '{target}', '-u', '', '-p', '', '--shares'],
        ['target'],
        [],
        'netexec',
        'low',
        'smb',
    ),
    'nuclei_safe_templates': CommandTemplate(
        'nuclei_safe_templates',
        'nuclei_safe_templates',
        'Nuclei safe templates',
        'Run the curated safe template directory only.',
        ['nuclei', '-target', '{target}', '-t', 'nuclei-templates-safe/'],
        ['target'],
        [],
        'nuclei',
        'low',
        'scan',
    ),
    'nuclei_web_exposure_scan': CommandTemplate(
        'nuclei_web_exposure_scan',
        'nuclei_web_exposure_scan',
        'Nuclei web exposure scan',
        'Run curated safe web exposure templates only.',
        ['nuclei', '-target', '{target}', '-t', 'nuclei-templates-safe/exposures/'],
        ['target'],
        [],
        'nuclei',
        'low',
        'scan',
        allow_urls=True,
        allow_hostnames=True,
    ),
    'enum4linux_ng_basic': CommandTemplate(
        'enum4linux_ng_basic',
        'enum4linux_ng_basic',
        'enum4linux-ng basic',
        'Basic read-only SMB enumeration with JSON output.',
        ['enum4linux-ng', '-A', '-oJ', '{output}', '{target}'],
        ['target', 'output'],
        [],
        'enum4linux',
        'low',
        'json',
    ),
    'bloodhound_sharphound_upload': CommandTemplate(
        'bloodhound_sharphound_upload',
        'bloodhound_sharphound_upload',
        'BloodHound upload',
        'Import an existing SharpHound archive for path analysis.',
        ['bloodhound-import', '{artifact}'],
        ['artifact'],
        [],
        'bloodhound',
        'low',
        'bloodhound',
    ),
    'bloodhound_explorer': CommandTemplate(
        'bloodhound_explorer',
        'bloodhound_explorer',
        'BloodHound explorer',
        'Explore already-imported BloodHound data.',
        ['bloodhound-query', 'explore', '{query}'],
        ['query'],
        [],
        'bloodhound',
        'low',
        'bloodhound',
    ),
    'bloodhound_pathfinding': CommandTemplate(
        'bloodhound_pathfinding',
        'bloodhound_pathfinding',
        'BloodHound pathfinding',
        'Find paths in already-imported BloodHound data.',
        ['bloodhound-query', 'path', '--from', '{source}', '--to', '{target}'],
        ['source', 'target'],
        [],
        'bloodhound',
        'low',
        'bloodhound_path',
    ),
    'kerbrute_userenum': CommandTemplate(
        'kerbrute_userenum',
        'kerbrute',
        'Kerbrute userenum',
        'Enumerate valid users via Kerberos pre-auth responses.',
        ['kerbrute', 'userenum', '--dc', '{dc_ip}', '-d', '{domain}', '{userlist}'],
        ['dc_ip', 'domain', 'userlist'],
        [],
        'kerbrute',
        'high',
        'users',
    ),
    'kerbrute_passwordspray_safe_preview': CommandTemplate(
        'kerbrute_passwordspray_safe_preview',
        'kerbrute',
        'Kerbrute password spray preview',
        'Account-lockout risk: password spraying requires reinforced human validation.',
        ['kerbrute', 'passwordspray', '--dc', '{dc_ip}', '-d', '{domain}', '{userlist}', '{password}'],
        ['dc_ip', 'domain', 'userlist', 'password'],
        [],
        'kerbrute',
        'high',
        'users',
    ),
    'gmsadumper_assessment_password': CommandTemplate(
        'gmsadumper_assessment_password',
        'gmsadumper',
        'gMSADumper password',
        'Assess readable gMSA secrets using a password.',
        ['python3', 'gMSADumper.py', '-u', '{username}', '-p', '{password}', '-d', '{domain}', '-l', '{dc_ip}'],
        ['username', 'password', 'domain', 'dc_ip'],
        [],
        'gmsadumper',
        'high',
        'credential_artifact',
    ),
    'gmsadumper_assessment_hash': CommandTemplate(
        'gmsadumper_assessment_hash',
        'gmsadumper',
        'gMSADumper hash',
        'Assess readable gMSA secrets using an NTLM hash.',
        ['python3', 'gMSADumper.py', '-u', '{username}', '-H', '{ntlm_hash}', '-d', '{domain}', '-l', '{dc_ip}'],
        ['username', 'ntlm_hash', 'domain', 'dc_ip'],
        [],
        'gmsadumper',
        'high',
        'credential_artifact',
    ),
    'donpapi_collect_target': CommandTemplate(
        'donpapi_collect_target',
        'donpapi',
        'DonPAPI target collect',
        'Bounded DPAPI/credential artifact collection for one target.',
        [
            'DonPAPI',
            'collect',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
            '--target',
            '{target}',
            '-o',
            '{output}',
        ],
        ['domain', 'username', 'password', 'target', 'output'],
        [],
        'donpapi',
        'high',
        'credential_artifact',
    ),
    'donpapi_collect_target_hash': CommandTemplate(
        'donpapi_collect_target_hash',
        'donpapi',
        'DonPAPI target collect hash',
        'Bounded DPAPI/credential artifact collection for one target using a hash.',
        [
            'DonPAPI',
            'collect',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-H',
            '{ntlm_hash}',
            '--target',
            '{target}',
            '-o',
            '{output}',
        ],
        ['domain', 'username', 'ntlm_hash', 'target', 'output'],
        [],
        'donpapi',
        'high',
        'credential_artifact',
    ),
    'coercer_check_single_target': CommandTemplate(
        'coercer_check_single_target',
        'coercer',
        'Coercer single target',
        'Check coercion methods against one target and explicit listener.',
        [
            'coercer',
            'coerce',
            '-t',
            '{target}',
            '-l',
            '{listener}',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
        ],
        ['target', 'listener', 'domain', 'username', 'password'],
        [],
        'coercer',
        'high',
        'coercion',
    ),
    'coercer_list_methods': CommandTemplate(
        'coercer_list_methods',
        'coercer',
        'Coercer list methods',
        'List supported coercion methods without targeting hosts.',
        ['coercer', 'list'],
        [],
        [],
        'coercer',
        'high',
        'coercion',
    ),
    'bloodyad_get_object': CommandTemplate(
        'bloodyad_get_object',
        'bloodyad',
        'BloodyAD get object',
        'Read an AD object.',
        [
            'bloodyAD',
            '--host',
            '{dc_ip}',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
            'get',
            'object',
            '{object}',
        ],
        ['dc_ip', 'domain', 'username', 'password', 'object'],
        [],
        'bloodyad',
        'high',
        'ad_object',
    ),
    'bloodyad_get_membership': CommandTemplate(
        'bloodyad_get_membership',
        'bloodyad',
        'BloodyAD get membership',
        'Read AD memberships.',
        [
            'bloodyAD',
            '--host',
            '{dc_ip}',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
            'get',
            'membership',
            '{object}',
        ],
        ['dc_ip', 'domain', 'username', 'password', 'object'],
        [],
        'bloodyad',
        'high',
        'membership',
    ),
    'bloodyad_get_children': CommandTemplate(
        'bloodyad_get_children',
        'bloodyad',
        'BloodyAD get children',
        'Read AD child objects.',
        [
            'bloodyAD',
            '--host',
            '{dc_ip}',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
            'get',
            'children',
            '{object}',
        ],
        ['dc_ip', 'domain', 'username', 'password', 'object'],
        [],
        'bloodyad',
        'high',
        'ad_object',
    ),
    'bloodyad_get_acl': CommandTemplate(
        'bloodyad_get_acl',
        'bloodyad',
        'BloodyAD get ACL',
        'Read AD ACLs only; no write templates are provided.',
        [
            'bloodyAD',
            '--host',
            '{dc_ip}',
            '-d',
            '{domain}',
            '-u',
            '{username}',
            '-p',
            '{password}',
            'get',
            'acl',
            '{object}',
        ],
        ['dc_ip', 'domain', 'username', 'password', 'object'],
        [],
        'bloodyad',
        'high',
        'acl',
    ),
    'impacket_getnpusers': CommandTemplate(
        'impacket_getnpusers',
        'impacket_sensitive',
        'GetNPUsers unauth',
        'Collect AS-REP roastable users from a users file.',
        ['GetNPUsers.py', '{domain}/', '-usersfile', '{userlist}', '-dc-ip', '{dc_ip}', '-outputfile', '{output}'],
        ['domain', 'userlist', 'dc_ip', 'output'],
        [],
        'impacket_getnpusers',
        'high',
        'asrep',
    ),
    'impacket_getnpusers_auth': CommandTemplate(
        'impacket_getnpusers_auth',
        'impacket_sensitive',
        'GetNPUsers auth',
        'Request AS-REP material with valid credentials.',
        ['GetNPUsers.py', '{domain}/{username}:{password}', '-dc-ip', '{dc_ip}', '-request', '-outputfile', '{output}'],
        ['domain', 'username', 'password', 'dc_ip', 'output'],
        [],
        'impacket_getnpusers',
        'high',
        'asrep',
    ),
    'impacket_getuserspns': CommandTemplate(
        'impacket_getuserspns',
        'impacket_sensitive',
        'GetUserSPNs',
        'Collect Kerberoastable SPN material.',
        ['GetUserSPNs.py', '{domain}/{username}:{password}', '-dc-ip', '{dc_ip}', '-outputfile', '{output}'],
        ['domain', 'username', 'password', 'dc_ip', 'output'],
        [],
        'impacket_getuserspns',
        'high',
        'spn',
    ),
    'impacket_lookupsid': CommandTemplate(
        'impacket_lookupsid',
        'impacket_sensitive',
        'LookupSID',
        'Enumerate domain SID information.',
        ['lookupsid.py', '{domain}/{username}:{password}@{target}'],
        ['domain', 'username', 'password', 'target'],
        [],
        'impacket_lookupsid',
        'high',
        'sid',
    ),
    'impacket_smbclient_list': CommandTemplate(
        'impacket_smbclient_list',
        'impacket_sensitive',
        'smbclient list',
        'List SMB shares.',
        ['smbclient.py', '{domain}/{username}:{password}@{target}', '-list'],
        ['domain', 'username', 'password', 'target'],
        [],
        'impacket_smbclient',
        'high',
        'share',
    ),
    'impacket_rpcdump': CommandTemplate(
        'impacket_rpcdump',
        'impacket_sensitive',
        'rpcdump',
        'List RPC endpoints.',
        ['rpcdump.py', '{domain}/{username}:{password}@{target}'],
        ['domain', 'username', 'password', 'target'],
        [],
        'impacket_rpcdump',
        'high',
        'service',
    ),
    'impacket_samrdump': CommandTemplate(
        'impacket_samrdump',
        'impacket_sensitive',
        'samrdump',
        'Enumerate SAMR users/groups when visible.',
        ['samrdump.py', '{domain}/{username}:{password}@{target}'],
        ['domain', 'username', 'password', 'target'],
        [],
        'impacket_samrdump',
        'high',
        'user',
    ),
    'responder_analyze': CommandTemplate(
        'responder_analyze',
        'responder',
        'Responder analyze',
        'Analyze traffic without poisoning.',
        ['responder', '-I', '{interface}', '-A'],
        ['interface'],
        [],
        'responder',
        'high',
        'captured_hash',
    ),
    'responder_lab_capture': CommandTemplate(
        'responder_lab_capture',
        'responder',
        'Responder lab capture',
        'Capture traffic in an authorized LAB on an explicitly selected interface.',
        ['responder', '-I', '{interface}', '-wrf'],
        ['interface'],
        [],
        'responder',
        'high',
        'captured_hash',
    ),
    'metasploit_db_status': CommandTemplate(
        'metasploit_db_status',
        'metasploit',
        'Metasploit DB status',
        'Show Metasploit database status.',
        ['msfconsole', '-q', '-x', 'db_status; exit'],
        [],
        [],
        'metasploit',
        'high',
        'metasploit',
    ),
    'metasploit_search_by_cve': CommandTemplate(
        'metasploit_search_by_cve',
        'metasploit',
        'Search by CVE',
        'Search Metasploit modules by CVE.',
        ['msfconsole', '-q', '-x', 'search cve:{cve}; exit'],
        ['cve'],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_search_by_service': CommandTemplate(
        'metasploit_search_by_service',
        'metasploit',
        'Search by service',
        'Search Metasploit modules by service name.',
        ['msfconsole', '-q', '-x', 'search name:{service}; exit'],
        ['service'],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_search_by_platform_windows': CommandTemplate(
        'metasploit_search_by_platform_windows',
        'metasploit',
        'Search Windows keyword',
        'Search Windows modules by keyword.',
        ['msfconsole', '-q', '-x', 'search platform:windows name:{keyword}; exit'],
        ['keyword'],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_search_smb': CommandTemplate(
        'metasploit_search_smb',
        'metasploit',
        'Search SMB',
        'Search Windows SMB modules.',
        ['msfconsole', '-q', '-x', 'search type:auxiliary type:exploit platform:windows smb; exit'],
        [],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_search_ldap': CommandTemplate(
        'metasploit_search_ldap',
        'metasploit',
        'Search LDAP',
        'Search Windows LDAP modules.',
        ['msfconsole', '-q', '-x', 'search ldap platform:windows; exit'],
        [],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_search_kerberos': CommandTemplate(
        'metasploit_search_kerberos',
        'metasploit',
        'Search Kerberos',
        'Search Windows Kerberos modules.',
        ['msfconsole', '-q', '-x', 'search kerberos platform:windows; exit'],
        [],
        [],
        'metasploit',
        'high',
        'metasploit_module',
    ),
    'metasploit_info_module': CommandTemplate(
        'metasploit_info_module',
        'metasploit',
        'Module info',
        'Show module information only.',
        ['msfconsole', '-q', '-x', 'info {module}; exit'],
        ['module'],
        [],
        'metasploit_info',
        'high',
        'metasploit_module',
    ),
    'metasploit_check_ms17_010': CommandTemplate(
        'metasploit_check_ms17_010',
        'metasploit',
        'Check MS17-010',
        'Run the explicitly allowed non-destructive MS17-010 check.',
        ['msfconsole', '-q', '-x', 'use auxiliary/scanner/smb/smb_ms17_010; set RHOSTS {target}; check; exit'],
        ['target'],
        [],
        'metasploit_check',
        'high',
        'vulnerability',
    ),
    'metasploit_smb_version': CommandTemplate(
        'metasploit_smb_version',
        'metasploit',
        'SMB version scanner',
        'Run the auxiliary SMB version scanner only.',
        ['msfconsole', '-q', '-x', 'use auxiliary/scanner/smb/smb_version; set RHOSTS {target}; run; exit'],
        ['target'],
        [],
        'metasploit_check',
        'high',
        'service',
    ),
}

COMMAND_TEMPLATES: dict[str, list[str]] = {k: v.argv for k, v in COMMAND_TEMPLATE_DEFINITIONS.items()}

# Controlled Metasploit templates are constructed by backend-only allowlist logic.
COMMAND_TEMPLATE_DEFINITIONS.update(
    {
        'metasploit_controlled_check': CommandTemplate(
            'metasploit_controlled_check',
            'metasploit',
            'Controlled allowlisted check',
            'Run only an allowlisted Metasploit check module against one validated target.',
            ['msfconsole', '-q', '-x', 'use {module}; set RHOSTS {target}; setg VERBOSE true; check; exit'],
            ['module', 'target'],
            [],
            'metasploit_check',
            'high',
            'metasploit_check',
        ),
        'metasploit_controlled_exploit': CommandTemplate(
            'metasploit_controlled_exploit',
            'metasploit',
            'Controlled allowlisted exploit',
            'Disabled-by-default controlled exploit path; requires strict allowlist, successful check, and final confirmation.',
            [
                'msfconsole',
                '-q',
                '-x',
                'use {module}; set RHOSTS {target}; setg VERBOSE true; {validated_options}; {validated_payload}; run; exit',
            ],
            ['module', 'target', 'validated_options', 'validated_payload'],
            [],
            'metasploit_controlled_exploit',
            'high',
            'metasploit_controlled_exploit',
        ),
    }
)
COMMAND_TEMPLATES.update(
    {k: v.argv for k, v in COMMAND_TEMPLATE_DEFINITIONS.items() if k.startswith('metasploit_controlled_')}
)


def _infer_metadata() -> None:
    network = {
        'target',
        'targets',
        'dc_ip',
        'dc_host',
        'domain_controller',
        'listener',
        'source',
        'source_ip',
        'rhost',
        'rhosts',
        'lhost',
        'url',
        'host',
        'hostname',
        'fqdn',
    }
    file_in = {'artifact', 'userlist', 'wordlist', 'input', 'input_file', 'targets_file'}
    file_out = {'output', 'output_file', 'report_path', 'artifact_path'}
    creds = {'password', 'ntlm_hash', 'hash', 'token', 'secret', 'api_key'}
    enums = {'protocol', 'scheme', 'execution_mode', 'risk_level', 'direction'}
    for template in COMMAND_TEMPLATE_DEFINITIONS.values():
        params = list(dict.fromkeys(template.required_params + template.optional_params))
        object.__setattr__(template, 'scope_sensitive_params', [p for p in params if p in network])
        object.__setattr__(template, 'file_input_params', [p for p in params if p in file_in])
        object.__setattr__(template, 'file_output_params', [p for p in params if p in file_out])
        object.__setattr__(template, 'credential_params', [p for p in params if p in creds])
        object.__setattr__(
            template, 'free_text_params', [p for p in params if p not in network | file_in | file_out | creds | enums]
        )
        object.__setattr__(template, 'enum_params', {p: [] for p in params if p in enums})
        object.__setattr__(template, 'allow_urls', 'url' in params or template.id == 'nuclei_safe_templates')
        object.__setattr__(
            template,
            'allow_hostnames',
            any(p in params for p in {'host', 'hostname', 'fqdn', 'dc_host', 'domain_controller'}),
        )
        object.__setattr__(template, 'parser_id', template.parser)
        object.__setattr__(template, 'artifact_type', template.output_artifact_type)

    family_map = {
        'nmap_safe_discovery': 'network_discovery',
        'nmap_service_fingerprint_limited': 'service_fingerprinting',
        'nuclei_safe_templates': 'web_surface_review',
        'nuclei_web_exposure_scan': 'web_surface_review',
        'nuclei_cves_safe_review': 'vulnerability_analysis',
        'nuclei_misconfig_review': 'web_surface_review',
        'nuclei_default_credentials_check_preview': 'web_surface_review',
        'enum4linux_ng_basic': 'smb_enumeration',
        'bloodhound_sharphound_upload': 'bloodhound_analysis',
        'bloodhound_import_existing_zip': 'bloodhound_analysis',
        'bloodhound_explorer': 'bloodhound_analysis',
        'bloodhound_pathfinding': 'bloodhound_analysis',
    }
    for tid, template in COMMAND_TEMPLATE_DEFINITIONS.items():
        family = family_map.get(tid)
        if family is None:
            if tid.startswith('netexec_smb'):
                family = 'smb_enumeration'
            elif tid.startswith(('ldap_', 'bloodyad_')):
                family = 'ldap_ad_enumeration'
            elif tid.startswith(('kerberos_', 'kerbrute_', 'impacket_getnpusers', 'impacket_getuserspns')):
                family = 'kerberos_review'
            elif tid.startswith(('adcs_',)):
                family = 'adcs_review'
            elif tid.startswith(('bloodhound_',)):
                family = 'bloodhound_analysis'
            elif tid.startswith(('winrm_', 'wmi_')):
                family = 'remote_management_review'
            elif tid.startswith('rdp_'):
                family = 'rdp_review'
            elif tid.startswith('mssql_'):
                family = 'mssql_review'
            elif tid.startswith(
                ('credential_', 'password_policy', 'secrets_', 'gmsa_', 'smb_anonymous', 'kerberos_roastability')
            ):
                family = 'credential_exposure_review'
            elif tid.startswith(('coercer_', 'responder_')):
                family = 'coercion_capture_review'
            elif tid.startswith('impacket_'):
                family = 'smb_enumeration'
            elif tid.startswith(('generate_', 'prepare_', 'consolidate_')):
                family = 'evidence_reporting'
            elif tid.startswith('metasploit_'):
                family = 'vulnerability_analysis'
            else:
                family = 'manual_only_sensitive'
        supported = tid in {
            'nmap_safe_discovery',
            'netexec_smb_fingerprint',
            'netexec_smb_signing_check',
            'netexec_smb_null_session_check',
            'netexec_smb_null_session_shares',
            'nuclei_safe_templates',
            'nuclei_web_exposure_scan',
        }
        mode = (
            'approval_required'
            if supported
            else ('reinforced_approval_required' if template.risk_level == 'high' else 'approval_required')
        )
        if family == 'evidence_reporting' and template.risk_level == 'low':
            mode = 'safe_auto'
        if tid.startswith('metasploit_'):
            mode = 'preview_only'
        if tid in {'metasploit_smb_version', 'metasploit_controlled_exploit'}:
            mode = 'blocked'
        if family == 'manual_only_sensitive' or tid in {
            'kerbrute_passwordspray_safe_preview',
            'responder_lab_capture',
        }:
            mode = 'manual_only'
        object.__setattr__(template, 'family', family)
        object.__setattr__(template, 'execution_mode', mode)
        object.__setattr__(template, 'supported_for_run', supported)
        object.__setattr__(
            template, 'safety_notes', ['Backend allowlisted argv only; no raw frontend command material.']
        )
        object.__setattr__(
            template,
            'blocked_reason',
            None if supported else 'Cataloged for preview/planning only; not supported by controlled runner.',
        )

    for tid in [
        'donpapi_collect_target',
        'donpapi_collect_target_hash',
        'gmsadumper_assessment_password',
        'gmsadumper_assessment_hash',
        'kerbrute_passwordspray_safe_preview',
        'coercer_check_single_target',
        'responder_lab_capture',
    ]:
        if tid in COMMAND_TEMPLATE_DEFINITIONS:
            object.__setattr__(COMMAND_TEMPLATE_DEFINITIONS[tid], 'execution_mode', 'manual_only')
            object.__setattr__(COMMAND_TEMPLATE_DEFINITIONS[tid], 'supported_for_run', False)
            object.__setattr__(
                COMMAND_TEMPLATE_DEFINITIONS[tid],
                'blocked_reason',
                'Manual-only high-risk capability is not executable by OpenAD-Zero.',
            )


def _add_catalog_only_templates() -> None:
    def add(
        tid,
        tool,
        family,
        name,
        desc,
        risk='medium',
        mode='approval_required',
        parser='catalog_review',
        artifact='review',
        argv=None,
        req=None,
    ):
        if tid in COMMAND_TEMPLATE_DEFINITIONS:
            return
        tmpl = CommandTemplate(
            tid, tool, name, desc, argv or ['catalog-preview', tid], req or [], [], parser, risk, artifact
        )
        object.__setattr__(tmpl, 'family', family)
        object.__setattr__(tmpl, 'execution_mode', mode)
        object.__setattr__(tmpl, 'supported_for_run', False)
        object.__setattr__(tmpl, 'parser_id', parser)
        object.__setattr__(tmpl, 'artifact_type', artifact)
        object.__setattr__(tmpl, 'safety_notes', ['Catalog metadata only; not executable in Prompt 11.'])
        object.__setattr__(
            tmpl, 'blocked_reason', 'Preview/manual/planned template is not executable by the controlled runner.'
        )
        COMMAND_TEMPLATE_DEFINITIONS[tid] = tmpl

    entries = [
        (
            'metasploit_search_preview',
            'metasploit',
            'vulnerability_analysis',
            'Metasploit search preview',
            'Preview Metasploit search guidance only; no msfconsole execution.',
            'high',
            'preview_only',
            'metasploit',
            'metasploit',
        ),
        (
            'metasploit_info_preview',
            'metasploit',
            'vulnerability_analysis',
            'Metasploit info preview',
            'Preview Metasploit module info guidance only; no msfconsole execution.',
            'high',
            'preview_only',
            'metasploit_info',
            'metasploit_module',
        ),
        (
            'metasploit_module_metadata_preview',
            'metasploit',
            'vulnerability_analysis',
            'Metasploit module metadata preview',
            'Preview allowlisted module metadata only; no execution.',
            'high',
            'preview_only',
            'metasploit_info',
            'metasploit_module',
        ),
        (
            'metasploit_check_preview',
            'metasploit',
            'vulnerability_analysis',
            'Metasploit check preview',
            'Preview allowlisted non-destructive check intent; no execution.',
            'high',
            'preview_only',
            'metasploit_check',
            'vulnerability',
        ),
        (
            'nmap_service_fingerprint_limited',
            'nmap',
            'service_fingerprinting',
            'Nmap limited service fingerprint',
            'Limited service fingerprinting; no -A or arbitrary NSE.',
            'medium',
            'approval_required',
        ),
        (
            'ldap_basic_domain_info',
            'ldapsearch',
            'ldap_ad_enumeration',
            'LDAP basic domain info',
            'Read-only domain naming/context review.',
        ),
        (
            'ldap_domain_users_preview',
            'ldapsearch',
            'ldap_ad_enumeration',
            'LDAP users preview',
            'Preview bounded user enumeration.',
        ),
        (
            'ldap_domain_groups_preview',
            'ldapsearch',
            'ldap_ad_enumeration',
            'LDAP groups preview',
            'Preview bounded group enumeration.',
        ),
        (
            'ldap_domain_computers_preview',
            'ldapsearch',
            'ldap_ad_enumeration',
            'LDAP computers preview',
            'Preview bounded computer enumeration.',
        ),
        (
            'ldap_signing_review',
            'ldapsearch',
            'ldap_ad_enumeration',
            'LDAP signing review',
            'Review LDAP signing/channel binding posture.',
        ),
        (
            'ldap_machine_account_quota_review',
            'ldapsearch',
            'ldap_ad_enumeration',
            'Machine account quota review',
            'Review MachineAccountQuota from imported/read-only data.',
        ),
        ('ldap_trusts_review', 'ldapsearch', 'ldap_ad_enumeration', 'LDAP trusts review', 'Review trusts read-only.'),
        (
            'kerberos_realm_discovery',
            'kerbrute',
            'kerberos_review',
            'Kerberos realm discovery',
            'Realm/DC discovery review.',
            'medium',
            'approval_required',
        ),
        (
            'kerbrute_userenum_preview',
            'kerbrute',
            'kerberos_review',
            'Kerbrute userenum preview',
            'Preview-only controlled Kerberos user enumeration.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'kerberos_asrep_exposure_review',
            'reporting',
            'kerberos_review',
            'ASREP exposure review',
            'Review imported ASREP exposure data.',
            'medium',
            'approval_required',
        ),
        (
            'kerberos_spn_exposure_review',
            'reporting',
            'kerberos_review',
            'SPN exposure review',
            'Review imported SPN exposure data.',
            'medium',
            'approval_required',
        ),
        (
            'adcs_http_endpoint_review',
            'certipy',
            'adcs_review',
            'ADCS HTTP endpoint review',
            'Review ADCS HTTP endpoints.',
        ),
        (
            'adcs_template_inventory_review',
            'certipy',
            'adcs_review',
            'ADCS template inventory',
            'Read-only template inventory review.',
        ),
        (
            'adcs_esc_path_review_preview',
            'certipy',
            'adcs_review',
            'ADCS ESC path preview',
            'Preview ESC-path review without exploitation.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'bloodhound_import_existing_zip',
            'bloodhound',
            'bloodhound_analysis',
            'BloodHound import existing ZIP',
            'Import existing SharpHound archive metadata only.',
            'medium',
            'approval_required',
        ),
        (
            'bloodhound_pathfinding_review',
            'bloodhound',
            'bloodhound_analysis',
            'BloodHound pathfinding review',
            'Analyze existing graph paths.',
        ),
        (
            'bloodhound_high_value_targets_review',
            'bloodhound',
            'bloodhound_analysis',
            'BloodHound high value targets',
            'Analyze high-value targets from imported data.',
        ),
        (
            'bloodhound_dangerous_acl_review',
            'bloodhound',
            'bloodhound_analysis',
            'BloodHound dangerous ACL review',
            'Analyze dangerous ACLs from imported data.',
        ),
        (
            'bloodhound_kerberoastable_from_imported_data',
            'bloodhound',
            'bloodhound_analysis',
            'Kerberoastable from imported data',
            'Analyze imported Kerberoastable flags.',
        ),
        (
            'bloodhound_asreproastable_from_imported_data',
            'bloodhound',
            'bloodhound_analysis',
            'ASREPRoastable from imported data',
            'Analyze imported ASREPRoastable flags.',
        ),
        (
            'nuclei_cves_safe_review',
            'nuclei',
            'vulnerability_analysis',
            'Nuclei CVEs safe review',
            'Curated non-aggressive CVE review.',
            'medium',
            'approval_required',
        ),
        (
            'nuclei_misconfig_review',
            'nuclei',
            'web_surface_review',
            'Nuclei misconfiguration review',
            'Curated misconfiguration review.',
            'medium',
            'approval_required',
        ),
        (
            'nuclei_default_credentials_check_preview',
            'nuclei',
            'web_surface_review',
            'Default credentials check preview',
            'Preview only; active default-credential checks are reinforced/blocked.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'winrm_exposure_review',
            'netexec_winrm',
            'remote_management_review',
            'WinRM exposure review',
            'Review WinRM exposure.',
        ),
        (
            'winrm_auth_surface_review',
            'netexec_winrm',
            'remote_management_review',
            'WinRM auth surface',
            'Review WinRM auth surface.',
            'high',
            'reinforced_approval_required',
        ),
        ('rdp_exposure_review', 'nmap', 'rdp_review', 'RDP exposure review', 'Review RDP exposure.'),
        ('rdp_nla_tls_review', 'nmap', 'rdp_review', 'RDP NLA/TLS review', 'Review RDP NLA/TLS posture.'),
        (
            'wmi_exposure_review',
            'netexec_wmi',
            'remote_management_review',
            'WMI exposure review',
            'Review WMI exposure.',
        ),
        ('mssql_exposure_review', 'netexec_mssql', 'mssql_review', 'MSSQL exposure review', 'Review MSSQL exposure.'),
        (
            'mssql_auth_surface_review',
            'netexec_mssql',
            'mssql_review',
            'MSSQL auth surface',
            'Review MSSQL auth surface.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'mssql_linked_server_review_preview',
            'netexec_mssql',
            'mssql_review',
            'MSSQL linked server preview',
            'Preview linked server review.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'credential_exposure_summary',
            'reporting',
            'credential_exposure_review',
            'Credential exposure summary',
            'Summarize credential exposure evidence.',
            'low',
            'safe_auto',
        ),
        (
            'smb_anonymous_exposure_review',
            'reporting',
            'credential_exposure_review',
            'SMB anonymous exposure review',
            'Summarize SMB anonymous exposure.',
        ),
        (
            'kerberos_roastability_summary',
            'reporting',
            'credential_exposure_review',
            'Kerberos roastability summary',
            'Summarize roastability from imported data.',
        ),
        (
            'gmsa_exposure_review_from_imported_data',
            'reporting',
            'credential_exposure_review',
            'gMSA exposure review',
            'Summarize imported gMSA exposure data.',
        ),
        (
            'password_policy_review',
            'reporting',
            'credential_exposure_review',
            'Password policy review',
            'Summarize password policy evidence.',
        ),
        (
            'secrets_evidence_review',
            'reporting',
            'credential_exposure_review',
            'Secrets evidence review',
            'Review already collected evidence; no dumping.',
            'high',
            'manual_only',
        ),
        (
            'coercer_methods_preview',
            'coercer',
            'coercion_capture_review',
            'Coercer methods preview',
            'Preview coercion methods.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'coercer_single_target_check_preview',
            'coercer',
            'coercion_capture_review',
            'Coercer single target preview',
            'Preview a single-target coercion check only.',
            'high',
            'reinforced_approval_required',
        ),
        (
            'responder_analyze_mode_preview',
            'responder',
            'coercion_capture_review',
            'Responder analyze mode preview',
            'Preview analyze-only mode.',
            'high',
            'reinforced_approval_required',
        ),
    ]
    for e in entries:
        add(*e)
    for tid in [
        'impacket_lookupsid_preview',
        'impacket_rpcdump_preview',
        'impacket_samrdump_preview',
        'impacket_smbclient_list_preview',
        'impacket_getnpusers_preview',
        'impacket_getuserspns_preview',
    ]:
        add(
            tid,
            'impacket',
            'smb_enumeration',
            tid.replace('_', ' ').title(),
            'Sensitive Impacket read-oriented preview only.',
            'high',
            'reinforced_approval_required',
        )
    for tid in [
        'mimikatz',
        'lsass_dump',
        'secretsdump',
        'pass_the_hash',
        'password_spray',
        'bruteforce',
        'lateral_movement_execution',
        'persistence',
        'trace_cleanup',
    ]:
        add(
            tid,
            tid,
            'manual_only_sensitive',
            tid.replace('_', ' ').title(),
            'Explicitly non-executable sensitive workflow.',
            'critical',
            'manual_only',
            'manual_only',
            None,
        )


_infer_metadata()
_add_catalog_only_templates()
