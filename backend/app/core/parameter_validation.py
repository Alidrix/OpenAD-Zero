from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.scope import validate_scope


class ParameterValidationError(ValueError):
    pass


NETWORK_PARAM_NAMES = {
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
FILE_INPUT_PARAM_NAMES = {'artifact', 'userlist', 'wordlist', 'input', 'input_file', 'targets_file'}
FILE_OUTPUT_PARAM_NAMES = {'output', 'output_file', 'report_path', 'artifact_path'}
CREDENTIAL_PARAM_NAMES = {'password', 'ntlm_hash', 'hash', 'token', 'secret', 'api_key'}
SHELL_META_RE = re.compile(r'[;&|`$<>\\\n\r\x00]')
HOST_RE = re.compile(r'^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$')
NTLM_RE = re.compile(r'^[A-Fa-f0-9]{32}$')
SAFE_TEXT_RE = re.compile(r'^[A-Za-z0-9_.:@/+=, -]{0,512}$')

DEFAULT_ENUM_VALUES = {
    'protocol': {'tcp', 'udp', 'smb', 'ldap', 'kerberos', 'http', 'https'},
    'scheme': {'http', 'https'},
    'execution_mode': {'safe_auto', 'approval_required', 'reinforced_approval_required', 'manual_only'},
    'risk_level': {'low', 'medium', 'high', 'critical'},
    'direction': {'inbound', 'outbound', 'bidirectional'},
}


@dataclass(frozen=True)
class ParameterPolicy:
    scope_sensitive_params: list[str] = field(default_factory=list)
    file_input_params: list[str] = field(default_factory=list)
    file_output_params: list[str] = field(default_factory=list)
    credential_params: list[str] = field(default_factory=list)
    free_text_params: list[str] = field(default_factory=list)
    enum_params: dict[str, list[str]] = field(default_factory=dict)
    required_params: list[str] = field(default_factory=list)
    optional_params: list[str] = field(default_factory=list)
    allow_hostnames: bool = False
    allow_urls: bool = False
    allow_public_scans: bool | None = None
    max_cidr_prefix: int = 16
    allowed_file_extensions: dict[str, list[str]] = field(default_factory=dict)


def _as_policy(policy: Any) -> ParameterPolicy:
    if isinstance(policy, ParameterPolicy):
        return policy
    return ParameterPolicy(
        scope_sensitive_params=list(getattr(policy, 'scope_sensitive_params', []) or []),
        file_input_params=list(getattr(policy, 'file_input_params', []) or []),
        file_output_params=list(getattr(policy, 'file_output_params', []) or []),
        credential_params=list(getattr(policy, 'credential_params', []) or []),
        free_text_params=list(getattr(policy, 'free_text_params', []) or []),
        enum_params=dict(getattr(policy, 'enum_params', {}) or {}),
        required_params=list(getattr(policy, 'required_params', []) or []),
        optional_params=list(getattr(policy, 'optional_params', []) or []),
        allow_hostnames=bool(getattr(policy, 'allow_hostnames', False)),
        allow_urls=bool(getattr(policy, 'allow_urls', False)),
        allow_public_scans=getattr(policy, 'allow_public_scans', None),
        max_cidr_prefix=int(getattr(policy, 'max_cidr_prefix', 16)),
        allowed_file_extensions=dict(getattr(policy, 'allowed_file_extensions', {}) or {}),
    )


def mask_sensitive_params(params: dict[str, Any], credential_params: list[str] | None = None) -> dict[str, Any]:
    creds = set(credential_params or []) | CREDENTIAL_PARAM_NAMES
    return {k: ('***REDACTED***' if k in creds and v not in (None, '') else v) for k, v in params.items()}


def _values(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [str(value)]


def _scope_contains_ip(ip: ipaddress.IPv4Address, scope: list[str], allow_public: bool, max_prefix: int) -> bool:
    validated = validate_scope(','.join(scope), allow_public=allow_public, max_prefix=max_prefix).targets
    for item in validated:
        if '/' in item and ip in ipaddress.ip_network(item, strict=False):
            return True
        if '/' not in item and ip == ipaddress.ip_address(item):
            return True
    return False


def validate_network_value(
    name: str,
    value: Any,
    scope: list[str],
    *,
    allow_hostnames: bool = False,
    allow_urls: bool = False,
    allow_public_scans: bool | None = None,
    max_cidr_prefix: int = 16,
) -> list[str]:
    if value in (None, ''):
        raise ParameterValidationError(f'{name} is required')
    allow_public = get_settings().allow_public_scans if allow_public_scans is None else allow_public_scans
    validated: list[str] = []
    for raw in _values(value):
        token = raw.strip()
        if not token:
            raise ParameterValidationError(f'{name} is required')
        if SHELL_META_RE.search(token):
            raise ParameterValidationError(f'{name} contains unsafe characters')
        parsed = urlparse(token)
        if parsed.scheme:
            if not allow_urls or parsed.scheme not in {'http', 'https'} or not parsed.hostname:
                raise ParameterValidationError(f'{name} URL scheme is not allowed')
            validate_network_value(
                name,
                parsed.hostname,
                scope,
                allow_hostnames=allow_hostnames,
                allow_urls=False,
                allow_public_scans=allow_public,
                max_cidr_prefix=max_cidr_prefix,
            )
            validated.append(token)
            continue
        if ':' in token and not re.match(r'^\d+\.\d+\.\d+\.\d+(:\d+)?$', token):
            raise ParameterValidationError('IPv6 targets are not supported')
        host = token.split(':', 1)[0]
        try:
            if '/' in host:
                net = ipaddress.ip_network(host, strict=False)
                if str(net) in {'0.0.0.0/0', '::/0'} or net.version != 4 or net.prefixlen < max_cidr_prefix:
                    raise ParameterValidationError(f'{name} CIDR is not allowed')
                if not allow_public and not net.is_private:
                    raise ParameterValidationError(f'{name} public range is not allowed')
                for scoped in validate_scope(
                    ','.join(scope), allow_public=allow_public, max_prefix=max_cidr_prefix
                ).targets:
                    if '/' in scoped and net.subnet_of(ipaddress.ip_network(scoped, strict=False)):
                        validated.append(str(net))
                        break
                    if (
                        '/' not in scoped
                        and net.prefixlen == 32
                        and net.network_address == ipaddress.ip_address(scoped)
                    ):
                        validated.append(str(net))
                        break
                else:
                    raise ParameterValidationError(f'{name} is outside the validated scope')
            else:
                ip = ipaddress.ip_address(host)
                if ip.version != 4:
                    raise ParameterValidationError('IPv6 targets are not supported')
                if not allow_public and not ip.is_private:
                    raise ParameterValidationError(f'{name} public IP is not allowed')
                if not _scope_contains_ip(ip, scope or [str(ip)], allow_public, max_cidr_prefix):
                    raise ParameterValidationError(f'{name} is outside the validated scope')
                validated.append(str(ip))
        except ValueError as exc:
            if not allow_hostnames or not HOST_RE.match(host):
                raise ParameterValidationError(f'{name} hostname is not allowed') from exc
            validated.append(host.rstrip('.'))
    return validated


def _allowed_roots() -> list[Path]:
    settings = get_settings()
    return [Path(settings.evidence_dir), Path('/app/runtime')]


def _under(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve(strict=False)
    return any(
        resolved == root.resolve(strict=False) or root.resolve(strict=False) in resolved.parents for root in roots
    )


def validate_file_param(
    name: str, value: Any, *, allowed_extensions: list[str] | None = None, require_exists: bool = True
) -> str:
    if value in (None, ''):
        raise ParameterValidationError(f'{name} is required')
    raw = str(value)
    if '\x00' in raw or '..' in Path(raw).parts:
        raise ParameterValidationError(f'{name} path traversal is not allowed')
    path = Path(raw)
    if not path.is_absolute():
        path = Path(get_settings().evidence_dir) / path
    if not _under(path, _allowed_roots()):
        raise ParameterValidationError(f'{name} must stay under evidence/runtime')
    if require_exists and not path.exists():
        raise ParameterValidationError(f'{name} input file does not exist')
    if path.is_symlink() and not _under(path.resolve(strict=True), _allowed_roots()):
        raise ParameterValidationError(f'{name} symlink escapes allowed roots')
    if allowed_extensions and path.suffix.lower() not in {e.lower() for e in allowed_extensions}:
        raise ParameterValidationError(f'{name} extension is not allowed')
    return str(path.resolve(strict=require_exists))


def validate_output_param(
    name: str, value: Any, *, job_dir: str | None = None, allowed_extensions: list[str] | None = None
) -> str:
    if value in (None, ''):
        raise ParameterValidationError(f'{name} is required')
    raw = str(value)
    if Path(raw).is_absolute():
        candidate = Path(raw)
        if not _under(candidate, [Path(get_settings().evidence_dir)] + ([Path(job_dir)] if job_dir else [])):
            raise ParameterValidationError(f'{name} output path is not allowed')
    safe = re.sub(r'[^A-Za-z0-9._/-]+', '_', raw).strip('/ ')
    if not safe or '..' in Path(safe).parts or '\x00' in safe:
        raise ParameterValidationError(f'{name} path traversal is not allowed')
    path = Path(safe)
    if not path.is_absolute():
        base = Path(job_dir) if job_dir else Path(get_settings().evidence_dir)
        path = base / path
    forbidden = [Path('/app/app'), Path('/usr'), Path('/etc'), Path('/root'), Path.cwd()]
    if _under(path, forbidden) or not _under(
        path, [Path(get_settings().evidence_dir)] + ([Path(job_dir)] if job_dir else [])
    ):
        raise ParameterValidationError(f'{name} output path is not allowed')
    if allowed_extensions and path.suffix.lower() not in {e.lower() for e in allowed_extensions}:
        raise ParameterValidationError(f'{name} extension is not allowed')
    return str(path.resolve(strict=False))


def _validate_text(name: str, value: Any) -> None:
    text = str(value)
    if (
        len(text) > 512
        or any(ord(ch) < 32 for ch in text)
        or SHELL_META_RE.search(text)
        or not SAFE_TEXT_RE.match(text)
    ):
        raise ParameterValidationError(f'{name} contains invalid free-text characters')


def validate_scope_sensitive_params(params: dict[str, Any], policy: Any, scope: list[str]) -> list[str]:
    p = _as_policy(policy)
    validated: list[str] = []
    for name in p.scope_sensitive_params:
        if name in params:
            validated.extend(
                validate_network_value(
                    name,
                    params[name],
                    scope,
                    allow_hostnames=p.allow_hostnames,
                    allow_urls=p.allow_urls,
                    allow_public_scans=p.allow_public_scans,
                    max_cidr_prefix=p.max_cidr_prefix,
                )
            )
    return validated


def validate_action_parameters(
    params: dict[str, Any],
    policy: Any,
    scope: list[str],
    *,
    reject_unexpected: bool = True,
    job_dir: str | None = None,
    require_input_exists: bool = True,
) -> dict[str, Any]:
    p = _as_policy(policy)
    allowed = set(p.required_params) | set(p.optional_params)
    categorized = (
        set(p.scope_sensitive_params)
        | set(p.file_input_params)
        | set(p.file_output_params)
        | set(p.credential_params)
        | set(p.free_text_params)
        | set(p.enum_params)
    )
    if reject_unexpected:
        extras = set(params) - (allowed | categorized)
        if extras:
            raise ParameterValidationError(f'Unexpected parameter: {sorted(extras)[0]}')
    for name in p.required_params:
        if params.get(name) in (None, ''):
            raise ParameterValidationError(f'Missing required parameter: {name}')
    normalized = dict(params)
    validate_scope_sensitive_params(params, p, scope)
    for name in p.file_input_params:
        if name in params:
            normalized[name] = validate_file_param(
                name,
                params[name],
                allowed_extensions=p.allowed_file_extensions.get(name),
                require_exists=require_input_exists,
            )
    for name in p.file_output_params:
        if name in params:
            normalized[name] = validate_output_param(
                name, params[name], job_dir=job_dir, allowed_extensions=p.allowed_file_extensions.get(name)
            )
    for name in p.credential_params:
        if name in params:
            text = str(params[name])
            if not text or len(text) > 4096:
                raise ParameterValidationError(f'{name} credential length is invalid')
            if name == 'ntlm_hash' and not NTLM_RE.match(text):
                raise ParameterValidationError('ntlm_hash format is invalid')
    for name, values in {**DEFAULT_ENUM_VALUES, **p.enum_params}.items():
        if name in params and str(params[name]) not in set(values):
            raise ParameterValidationError(f'{name} is not an allowed value')
    for name in p.free_text_params:
        if name in params:
            _validate_text(name, params[name])
    return normalized
