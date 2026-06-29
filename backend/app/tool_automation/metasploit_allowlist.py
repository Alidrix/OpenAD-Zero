from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWLIST_PATH = Path(__file__).with_name('metasploit_allowlist.yml')
SECRET_RE = re.compile(r'(password|pass|hash|token|key|secret)', re.I)
SAFE_VALUE_RE = re.compile(r'^[A-Za-z0-9_.:/@+\-\\]+$')


@dataclass(frozen=True)
class MetasploitModule:
    id: str
    module: str
    type: str
    allowed: bool
    requires_payload: bool
    allowed_options: list[str]
    allowed_payloads: list[str]
    notes: str | None = None


def load_metasploit_allowlist(path: Path = ALLOWLIST_PATH) -> dict[str, MetasploitModule]:
    raw = yaml.safe_load(path.read_text()) or {}
    modules: dict[str, MetasploitModule] = {}
    for item in raw.get('modules', []):
        module = MetasploitModule(
            id=str(item['id']),
            module=str(item['module']),
            type=str(item.get('type', 'check')),
            allowed=bool(item.get('allowed', False)),
            requires_payload=bool(item.get('requires_payload', False)),
            allowed_options=list(item.get('allowed_options') or []),
            allowed_payloads=list(item.get('allowed_payloads') or []),
            notes=item.get('notes'),
        )
        modules[module.id] = module
    return modules


def mask_secret_value(key: str, value: str) -> str:
    return '********' if SECRET_RE.search(key) and value else value


def mask_metasploit_secrets(text: str) -> str:
    masked = text
    for pattern in [r'(SMBPass\s+)(\S+)', r'(PASSWORD\s+)(\S+)', r'(PASS\s+)(\S+)', r'(TOKEN\s+)(\S+)', r'(KEY\s+)(\S+)', r'(HASH\s+)(\S+)']:
        masked = re.sub(pattern, r'\1********', masked, flags=re.I)
    return masked


def _validate_value(value: str) -> None:
    if ';' in value or '\n' in value or '\r' in value or not SAFE_VALUE_RE.match(value):
        raise ValueError('Metasploit option value contains unsafe characters.')


def get_allowlisted_module(module_id: str | None, module_path: str | None = None) -> MetasploitModule:
    modules = load_metasploit_allowlist()
    if module_id and module_id in modules:
        return modules[module_id]
    for item in modules.values():
        if module_path and item.module == module_path:
            return item
    raise ValueError('Metasploit module is not allowlisted.')


def validate_metasploit_selection(*, module_id: str | None, module_path: str | None, options: dict[str, str] | None = None, payload: str | None = None, require_allowed: bool = True) -> MetasploitModule:
    module = get_allowlisted_module(module_id, module_path)
    if require_allowed and not module.allowed:
        raise ValueError('Metasploit module is disabled in the allowlist.')
    requested = set((options or {}).keys()) - {'module_id', 'module', 'payload'}
    if not requested <= set(module.allowed_options):
        raise ValueError('One or more options are not allowed for this module.')
    for value in (options or {}).values():
        if value:
            _validate_value(str(value))
    if payload:
        if payload not in module.allowed_payloads:
            raise ValueError('Selected payload is not allowlisted.')
        _validate_value(payload)
    elif module.requires_payload and require_allowed:
        raise ValueError('Selected payload is not allowlisted.')
    return module


def build_metasploit_command(*, template_id: str, target: str, module_id: str | None, module_path: str | None = None, options: dict[str, str] | None = None, payload: str | None = None, masked: bool = False) -> list[str]:
    module = validate_metasploit_selection(module_id=module_id, module_path=module_path, options=options, payload=payload, require_allowed=template_id != 'metasploit_controlled_check')
    safe_options = []
    for key in module.allowed_options:
        if key in (options or {}) and key != 'RHOSTS':
            val = str((options or {})[key])
            safe_options.append(f'set {key} {mask_secret_value(key, val) if masked else val}')
    validated_options = '; '.join(safe_options)
    validated_payload = f'set PAYLOAD {payload}' if payload else ''
    if template_id == 'metasploit_controlled_check':
        script = f'use {module.module}; set RHOSTS {target}; setg VERBOSE true; check; exit'
    else:
        pieces = [f'use {module.module}', f'set RHOSTS {target}', 'setg VERBOSE true', validated_options, validated_payload, 'run', 'exit']
        script = '; '.join(piece for piece in pieces if piece)
    return ['msfconsole', '-q', '-x', script]


def public_allowlist() -> list[dict[str, Any]]:
    return [m.__dict__ for m in load_metasploit_allowlist().values()]
