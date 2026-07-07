from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

MASK = '********'

SENSITIVE_FIELD_NAMES = {
    'password',
    'pass',
    'pwd',
    'hash',
    'ntlm',
    'ntlm_hash',
    'token',
    'secret',
    'key',
    'api_key',
    'apikey',
    'authorization',
    'cookie',
    'session',
    'smbpass',
    'smbuser',
}

_SENSITIVE_NAME_RE = re.compile(
    r'(?:password|pass|pwd|hash|ntlm|token|secret|key|api[_-]?key|authorization|cookie|session|SMBPass|SMBUser)', re.I
)
_ASSIGNMENT_RE = re.compile(
    r'(?P<name>\b(?:password|pass|pwd|hash|ntlm(?:_hash)?|token|secret|key|api[_-]?key|authorization|cookie|session|SMBPass|SMBUser)\b)(?P<sep>\s*[:=]\s*)(?P<value>[^\s,;]+)',
    re.I,
)
_SET_RE = re.compile(
    r'(?P<prefix>\bset\s+(?:password|pass|pwd|hash|ntlm(?:_hash)?|token|secret|key|api[_-]?key|authorization|cookie|session|SMBPass|SMBUser)\s+)(?P<value>[^\s,;]+)',
    re.I,
)
_BEARER_RE = re.compile(r'\b(Bearer|Basic)\s+[^\s,;]+', re.I)
_NTLM_RE = re.compile(r'\b[a-f0-9]{32}(?::[a-f0-9]{32})?\b', re.I)
_DOLLAR_HASH_RE = re.compile(r'\$krb5(?:asrep|tgs)\$[^\s]+', re.I)
_COMMAND_SECRET_FLAGS = {
    '-p',
    '--password',
    '-H',
    '--hash',
    '--hashes',
    '--ntlm',
    '--token',
    '--secret',
    '--key',
    '--api-key',
    'apikey',
    'SMBPass',
    'SMBUser',
}


def is_sensitive_field_name(name: str) -> bool:
    normalized = name.replace('-', '_').casefold()
    return normalized in SENSITIVE_FIELD_NAMES or bool(_SENSITIVE_NAME_RE.search(name))


def redact_sensitive_value(value: object) -> object:
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_value(item) for item in value)
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        redacted[str(key)] = MASK if is_sensitive_field_name(str(key)) else redact_sensitive_value(value)
    return redacted


def redact_text(text: str) -> str:
    redacted = text
    # Specific HTTP auth/cookie patterns first so generic assignments do not partially mask them.
    redacted = re.sub(r'(?i)\b(Authorization\s*:\s*Bearer)\s+[^\s,;]+', rf'\1 {MASK}', redacted)
    redacted = re.sub(r'(?i)\b(authorization\s*=\s*Bearer)\s+[^\s,;]+', rf'\1 {MASK}', redacted)
    redacted = re.sub(r'(?i)\b(Authorization\s*:\s*Basic)\s+[^\s,;]+', rf'\1 {MASK}', redacted)
    redacted = re.sub(r'(?i)\b(authorization\s*=\s*Basic)\s+[^\s,;]+', rf'\1 {MASK}', redacted)
    redacted = re.sub(r'(?i)\bCookie\s*:\s*[^\r\n]+', f'Cookie: {MASK}', redacted)
    redacted = _DOLLAR_HASH_RE.sub(MASK, redacted)
    redacted = _NTLM_RE.sub(MASK, redacted)
    redacted = _ASSIGNMENT_RE.sub(lambda m: f'{m.group("name")}{m.group("sep")}{MASK}', redacted)
    redacted = _SET_RE.sub(lambda m: f'{m.group("prefix")}{MASK}', redacted)
    redacted = re.sub(
        r'(?i)(^|\s)(-p|--password|-H|--hash(?:es)?|--token)\s+[^\s,;]+',
        lambda m: f'{m.group(1)}{m.group(2)} {MASK}',
        redacted,
    )
    return redacted


def mask_command(command: Sequence[str], params: Mapping[str, Any] | None = None) -> list[str]:
    sensitive_values = {str(v) for k, v in (params or {}).items() if v and is_sensitive_field_name(str(k))}
    masked: list[str] = []
    mask_next = False
    for arg in command:
        item = str(arg)
        for secret in sensitive_values:
            item = item.replace(secret, MASK)
        if item != str(arg):
            masked.append(redact_text(item))
            mask_next = False
            continue
        if mask_next:
            masked.append(MASK)
            mask_next = False
            continue
        if arg in _COMMAND_SECRET_FLAGS or is_sensitive_field_name(arg):
            masked.append(arg)
            mask_next = True
            continue
        masked.append(redact_text(item))
    return masked
