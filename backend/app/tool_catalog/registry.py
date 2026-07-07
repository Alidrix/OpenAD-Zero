from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS, CommandTemplate
from app.tool_catalog.families import FAMILIES
from app.tool_catalog.models import TemplateMetadata, ToolMetadata

SUPPORTED_RUN_TEMPLATE_IDS = {
    'nmap_safe_discovery',
    'netexec_smb_fingerprint',
    'netexec_smb_signing_check',
    'netexec_smb_null_session_check',
    'netexec_smb_null_session_shares',
    'nuclei_safe_templates',
    'nuclei_web_exposure_scan',
}

TOOL_OVERRIDES: dict[str, dict[str, Any]] = {
    'nmap': {'name': 'Nmap', 'binary': 'nmap', 'aliases': []},
    'netexec_smb': {'name': 'NetExec SMB', 'binary': 'nxc', 'aliases': ['netexec']},
    'nuclei': {'name': 'Nuclei', 'binary': 'nuclei', 'aliases': []},
    'enum4linux_ng': {'name': 'enum4linux-ng', 'binary': 'enum4linux-ng', 'aliases': []},
    'ldapsearch': {'name': 'ldapsearch', 'binary': 'ldapsearch', 'aliases': []},
    'kerbrute': {'name': 'Kerbrute', 'binary': 'kerbrute', 'aliases': []},
    'certipy': {'name': 'Certipy', 'binary': 'certipy', 'aliases': ['certipy-ad']},
    'bloodhound': {'name': 'BloodHound', 'binary': 'bloodhound-import', 'aliases': ['bloodhound-query']},
    'reporting': {'name': 'Reporting parsers', 'binary': None, 'aliases': []},
    'coercer': {'name': 'Coercer', 'binary': 'coercer', 'aliases': []},
    'responder': {'name': 'Responder', 'binary': 'responder', 'aliases': []},
    'impacket': {'name': 'Impacket', 'binary': 'impacket-lookupSID', 'aliases': ['lookupsid.py']},
    'impacket_sensitive': {'name': 'Impacket sensitive', 'binary': 'impacket-lookupSID', 'aliases': ['lookupsid.py']},
    'metasploit': {'name': 'Metasploit', 'binary': 'msfconsole', 'aliases': []},
}

TOOL_ID_ALIASES = {
    'nmap_safe_discovery': 'nmap',
    'nuclei_safe_templates': 'nuclei',
    'nuclei_web_exposure_scan': 'nuclei',
    'enum4linux_ng_basic': 'enum4linux_ng',
    'netexec_smb_fingerprint': 'netexec_smb',
    'netexec_smb_signing_check': 'netexec_smb',
    'netexec_smb_null_session_check': 'netexec_smb',
    'netexec_smb_null_session_shares': 'netexec_smb',
    'bloodhound_sharphound_upload': 'bloodhound',
    'bloodhound_explorer': 'bloodhound',
    'bloodhound_pathfinding': 'bloodhound',
}

TEMPLATE_ALIASES = {
    ('network_discovery', 'initial_discovery'): 'nmap_safe_discovery',
    ('netexec', 'smb_fingerprint'): 'netexec_smb_fingerprint',
    ('netexec', 'smb_signing_check'): 'netexec_smb_signing_check',
    ('netexec', 'smb_null_session_check'): 'netexec_smb_null_session_check',
    ('netexec', 'smb_null_session_shares'): 'netexec_smb_null_session_shares',
    ('nuclei', 'safe_templates'): 'nuclei_safe_templates',
    ('nuclei', 'web_exposure_scan'): 'nuclei_web_exposure_scan',
    ('kerberos', 'kerberos_user_enumeration'): 'kerbrute_userenum_preview',
    ('bloodhound', 'path_analysis'): 'bloodhound_pathfinding_review',
    ('ad_enumerator', 'ldap_kerberos_enumeration'): 'ldap_basic_domain_info',
    ('ad_enumerator', 'ldap_basic_domain_enumeration'): 'ldap_basic_domain_info',
    ('ad_enumerator', 'ad_users_groups_enumeration'): 'ldap_domain_users_preview',
    ('ad_enumerator', 'ad_computer_enumeration'): 'ldap_domain_computers_preview',
    ('ad_enumerator', 'ad_trust_enumeration'): 'ldap_trusts_review',
    ('winrm_review', 'winrm_exposure_review'): 'winrm_exposure_review',
    ('winrm_review', 'winrm_authentication_surface_review'): 'winrm_auth_surface_review',
    ('rdp_review', 'rdp_exposure_review'): 'rdp_exposure_review',
    ('rdp_review', 'nlatls_configuration_review'): 'rdp_nla_tls_review',
    ('mssql_review', 'mssql_exposure_review'): 'mssql_exposure_review',
    ('mssql_review', 'mssql_authentication_surface_review'): 'mssql_auth_surface_review',
    ('mssql_review', 'mssql_linked_server_review'): 'mssql_linked_server_review_preview',
    ('credential_review', 'credential_exposure_review'): 'credential_exposure_summary',
    ('credential_review', 'password_policy_review'): 'password_policy_review',
    ('credential_review', 'kerberos_roastability_review'): 'kerberos_roastability_summary',
    ('credential_review', 'gmsa_exposure_review'): 'gmsa_exposure_review_from_imported_data',
    ('credential_review', 'secrets_evidence_consolidation'): 'secrets_evidence_review',
    ('credential_review', 'secrets_extraction_manual_only'): 'secrets_evidence_review',
    ('reporting', 'generate_interim_report'): 'generate_interim_report',
    ('reporting', 'generate_executive_summary'): 'generate_executive_summary',
    ('reporting', 'prepare_remediation_plan'): 'prepare_remediation_plan',
    ('evidence', 'consolidate_high_risk_evidence'): 'consolidate_high_risk_evidence',
}


def normalize_tool_id(template: CommandTemplate) -> str:
    return TOOL_ID_ALIASES.get(template.id, template.tool_id)


def normalize_template_id(tool_id: str, template_id: str) -> str:
    return TEMPLATE_ALIASES.get((tool_id, template_id), template_id)


def list_template_metadata() -> list[TemplateMetadata]:
    out = []
    for tid, t in sorted(COMMAND_TEMPLATE_DEFINITIONS.items()):
        supported = bool(getattr(t, 'supported_for_run', False)) and tid in SUPPORTED_RUN_TEMPLATE_IDS
        mode = getattr(t, 'execution_mode', 'manual_only')
        status = (
            'supported'
            if supported
            else ('manual_only' if mode == 'manual_only' else 'blocked' if mode == 'blocked' else 'preview_only')
        )
        out.append(
            TemplateMetadata(
                template_id=tid,
                tool_id=normalize_tool_id(t),
                family=getattr(t, 'family', 'manual_only_sensitive'),
                name=t.name,
                description=t.description,
                argv=t.argv,
                required_params=t.required_params,
                optional_params=t.optional_params,
                scope_sensitive_params=t.scope_sensitive_params,
                file_input_params=t.file_input_params,
                file_output_params=t.file_output_params,
                credential_params=t.credential_params,
                free_text_params=t.free_text_params,
                enum_params=t.enum_params,
                risk_level=t.risk_level,
                execution_mode=mode,
                supported_for_run=supported,
                parser_id=getattr(t, 'parser_id', None) or t.parser,
                artifact_type=getattr(t, 'artifact_type', None) or t.output_artifact_type,
                integration_status=status,
                safety_notes=getattr(t, 'safety_notes', []),
                blocked_reason=getattr(t, 'blocked_reason', None),
            )
        )
    return out


def get_template(template_id: str) -> TemplateMetadata | None:
    return next((t for t in list_template_metadata() if t.template_id == template_id), None)


def list_tools() -> list[ToolMetadata]:
    by_tool: dict[str, list[TemplateMetadata]] = defaultdict(list)
    for template in list_template_metadata():
        by_tool[template.tool_id].append(template)
    tools: list[ToolMetadata] = []
    for tool_id, templates in sorted(by_tool.items()):
        family = Counter(t.family for t in templates).most_common(1)[0][0]
        default_mode = FAMILIES.get(family).default_execution_mode if family in FAMILIES else 'manual_only'
        risk = FAMILIES.get(family).default_risk_level if family in FAMILIES else 'critical'
        if any(t.supported_for_run for t in templates):
            status = 'supported'
        elif all(t.execution_mode == 'manual_only' for t in templates):
            status = 'manual_only'
        else:
            status = 'preview_only'
        override = TOOL_OVERRIDES.get(tool_id, {})
        tools.append(
            ToolMetadata(
                tool_id=tool_id,
                name=override.get('name', tool_id.replace('_', ' ').title()),
                family=family,
                description=f'{tool_id} catalog entry with controlled Windows/AD templates.',
                binary=override.get('binary', tool_id),
                binary_aliases=override.get('aliases', []),
                integration_status=status,
                default_risk_level=risk,
                default_execution_mode=default_mode,
                requires_approval=default_mode != 'safe_auto',
                requires_reinforced_approval=default_mode == 'reinforced_approval_required',
                requires_terms_acceptance=any(t.risk_level in {'high', 'critical'} for t in templates),
                supports_dry_run=True,
                supports_json_output=any((t.artifact_type or '').lower() == 'json' for t in templates),
                supports_parser=any(bool(t.parser_id) for t in templates),
                parser_id=None,
                allowed_templates=[t.template_id for t in templates],
                blocked_capabilities=['raw shell commands', 'credential dumping', 'lateral movement', 'persistence'],
                health_check='shutil.which only; no process execution',
                install_notes='Install binary separately if readiness reports missing.',
                safety_notes=[
                    'Catalog metadata does not grant execution. Runner still requires approval, scope, and hash validation.'
                ],
            )
        )
    return tools


def get_tool_catalog() -> dict[str, Any]:
    return {
        'families': [f.to_dict() for f in FAMILIES.values()],
        'tools': [t.to_dict() for t in list_tools()],
        'templates': [t.to_dict(include_argv=False) for t in list_template_metadata()],
    }
