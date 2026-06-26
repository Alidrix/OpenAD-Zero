import ipaddress
import re
from dataclasses import dataclass


class ScopeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ScopeValidationResult:
    targets: list[str]


def _split(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r'[\s,]+', raw or '') if p.strip()]


def validate_scope(raw_scope: str, allow_public: bool = False, max_prefix: int = 24) -> ScopeValidationResult:
    seen = set()
    out = []
    for token in _split(raw_scope):
        try:
            if '/' in token:
                net = ipaddress.ip_network(token, strict=False)
                if str(net) == '0.0.0.0/0' or str(net) == '::/0':
                    raise ScopeValidationError('0.0.0.0/0 is not allowed')
                if net.version != 4:
                    raise ScopeValidationError('Only IPv4 targets are supported in V1')
                if net.prefixlen < max_prefix:
                    raise ScopeValidationError(f'CIDR ranges larger than /{max_prefix} are refused in V1')
                if not allow_public and not net.is_private:
                    raise ScopeValidationError('Public ranges are refused by default')
                value = str(net)
            else:
                ip = ipaddress.ip_address(token)
                if ip.version != 4:
                    raise ScopeValidationError('Only IPv4 targets are supported in V1')
                if not allow_public and not ip.is_private:
                    raise ScopeValidationError('Public IPs are refused by default')
                value = str(ip)
        except ValueError as e:
            if isinstance(e, ScopeValidationError):
                raise
            raise ScopeValidationError(f'Invalid target: {token}') from e
        if value not in seen:
            seen.add(value)
            out.append(value)
    if not out:
        raise ScopeValidationError('Scope must contain at least one IP or CIDR')
    return ScopeValidationResult(out)
