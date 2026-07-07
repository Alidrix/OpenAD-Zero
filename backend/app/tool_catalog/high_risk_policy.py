from __future__ import annotations

from typing import Any

from app.tool_catalog.models import EXECUTION_MODES


class HighRiskPolicyViolation(ValueError):
    """Raised when a catalog template violates OpenAD-Zero high-risk policy."""


NON_RUNNABLE_MODES = {'manual_only', 'blocked', 'preview_only', 'planned'}
METASPLOIT_PREVIEW_TEMPLATE_IDS = {
    'metasploit_search_preview',
    'metasploit_info_preview',
    'metasploit_module_metadata_preview',
    'metasploit_check_preview',
    'metasploit_db_status',
    'metasploit_search_by_cve',
    'metasploit_search_by_service',
    'metasploit_search_by_platform_windows',
    'metasploit_info_module',
    'metasploit_check_ms17_010',
}
METASPLOIT_ALLOWED_MODULES = {
    'auxiliary/scanner/smb/smb_ms17_010',
}
METASPLOIT_FORBIDDEN_TOKENS = {
    ' run',
    ';run',
    ' exploit',
    ';exploit',
    'type:exploit',
    'payload',
    'sessions',
    'meterpreter',
    ' shell ',
    'reverse_tcp',
    'bind_tcp',
    'multi/handler',
    'autoroute',
    'route add',
    'post/',
    'privilege escalation',
    'persistence',
    'upload',
    'download',
    'execute',
}
RUN_FORBIDDEN_TOKENS = {
    'metasploit',
    'msfconsole',
    'payload',
    'meterpreter',
    'reverse_tcp',
    'bind_tcp',
    'multi/handler',
    'mimikatz',
    'lsass',
    'secretsdump',
    'psexec',
    'wmiexec',
    'smbexec',
    'atexec',
    'evil-winrm',
    'xp_cmdshell',
    'password_spray',
    'passwordspray',
    'bruteforce',
    'pass-the-hash',
    'pass_the_hash',
    'ntlmrelayx',
    'responder capture',
    'coercer active',
}
CAPABILITY_KEYWORDS: dict[str, set[str]] = {
    'credential_access': {
        'secretsdump',
        'mimikatz',
        'lsass',
        'samdump',
        'lsa dump',
        'ntds',
        'dpapi',
        'hash dump',
        'donpapi',
    },
    'authentication_attack': {
        'password_spray',
        'passwordspray',
        'bruteforce',
        'brute force',
        'credential stuffing',
        'hash cracking',
    },
    'lateral_movement': {'psexec', 'wmiexec', 'smbexec', 'atexec', 'evil-winrm', 'remote shell', 'wmi command'},
    'coercion_capture': {'ntlmrelayx', 'responder', 'coercer', 'relay', 'poisoning', 'coercion active'},
    'ad_write_operations': {
        'bloodyad_write',
        'dacl',
        'owner modification',
        'group membership write',
        'password reset',
        'shadow credentials',
        'rbcd',
        'gpo modification',
    },
    'exploitation': {
        'exploit',
        'payload',
        'reverse shell',
        'bind shell',
        'meterpreter',
        ' rce ',
        'upload',
        'download',
        'interactive session',
    },
    'impact_or_persistence': {
        'persistence',
        'defense evasion',
        'cleanup',
        'trace_cleanup',
        'disable security',
        'ransomware',
        'destruction',
        'exfiltration',
    },
}
BLOCKED_CAPABILITIES = {'impact_or_persistence'}
MANUAL_ONLY_CAPABILITIES = set(CAPABILITY_KEYWORDS) - BLOCKED_CAPABILITIES


def _field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _text(obj: Any) -> str:
    parts: list[str] = []
    for name in (
        'template_id',
        'id',
        'tool_id',
        'family',
        'name',
        'description',
        'execution_mode',
        'parser_id',
        'parser',
    ):
        value = _field(obj, name)
        if value:
            parts.append(str(value))
    argv = _field(obj, 'argv', []) or []
    parts.extend(map(str, argv))
    return f' {" ".join(parts).casefold().replace("--no-bruteforce", "")} '


def classify_high_risk_capability(template_or_text: Any) -> str | None:
    text = template_or_text.casefold() if isinstance(template_or_text, str) else _text(template_or_text)
    if is_metasploit_capability(template_or_text):
        return 'metasploit'
    for capability, keywords in CAPABILITY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return capability
    return None


def is_metasploit_capability(template_or_text: Any) -> bool:
    text = template_or_text.casefold() if isinstance(template_or_text, str) else _text(template_or_text)
    return 'metasploit' in text or 'msfconsole' in text or 'meterpreter' in text


def is_manual_only_capability(capability: str | None) -> bool:
    return capability in MANUAL_ONLY_CAPABILITIES or capability == 'metasploit'


def is_blocked_capability(capability: str | None) -> bool:
    return capability in BLOCKED_CAPABILITIES


def _metasploit_preview_is_safe(template: Any) -> bool:
    tid = _field(template, 'template_id') or _field(template, 'id')
    text = _text(template)
    if tid not in METASPLOIT_PREVIEW_TEMPLATE_IDS:
        return False
    if any(token in text for token in METASPLOIT_FORBIDDEN_TOKENS):
        return False
    return not ('use {' in text or 'set {' in text or 'setg {' in text or 'validated_options' in text)


def validate_template_high_risk_policy(template: Any) -> None:
    tid = _field(template, 'template_id') or _field(template, 'id') or '<unknown>'
    mode = _field(template, 'execution_mode', 'manual_only')
    supported = bool(_field(template, 'supported_for_run', False))
    risk = _field(template, 'risk_level', 'info')
    if mode not in EXECUTION_MODES:
        raise HighRiskPolicyViolation(f'{tid}: invalid execution_mode {mode}')
    if mode in NON_RUNNABLE_MODES and supported:
        raise HighRiskPolicyViolation(f'{tid}: {mode} templates cannot be supported_for_run=true')
    if risk in {'high', 'critical'} and mode == 'safe_auto':
        raise HighRiskPolicyViolation(f'{tid}: high-risk templates cannot be safe_auto')
    if supported and any(token in _text(template) for token in RUN_FORBIDDEN_TOKENS):
        raise HighRiskPolicyViolation(f'{tid}: runnable template contains forbidden high-risk token')
    capability = classify_high_risk_capability(template)
    if capability == 'metasploit':
        if mode == 'blocked' and not supported:
            return
        if mode != 'preview_only' or supported or not _metasploit_preview_is_safe(template):
            raise HighRiskPolicyViolation(f'{tid}: Metasploit is limited to allowlisted preview-only templates')
    elif is_blocked_capability(capability) and mode != 'blocked':
        raise HighRiskPolicyViolation(f'{tid}: {capability} must be blocked')
    elif is_manual_only_capability(capability) and mode not in {'manual_only', 'blocked', 'preview_only'}:
        raise HighRiskPolicyViolation(f'{tid}: {capability} must be manual_only, blocked, or preview_only')


def assert_template_allowed_for_preview(template: Any) -> None:
    validate_template_high_risk_policy(template)


def assert_template_allowed_for_approval(template: Any) -> None:
    validate_template_high_risk_policy(template)
    mode = _field(template, 'execution_mode', 'manual_only')
    if mode in {'blocked', 'manual_only', 'preview_only', 'planned'}:
        raise HighRiskPolicyViolation(f'Template is {mode} and cannot be approved for execution')


def assert_template_allowed_for_run(template: Any) -> None:
    validate_template_high_risk_policy(template)
    mode = _field(template, 'execution_mode', 'manual_only')
    if mode in NON_RUNNABLE_MODES:
        raise HighRiskPolicyViolation(f'Template is {mode} and cannot be executed')
    if not _field(template, 'supported_for_run', False):
        raise HighRiskPolicyViolation('Template is not supported_for_run')
