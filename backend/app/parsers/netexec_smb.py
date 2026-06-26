from __future__ import annotations

import re
from typing import Any

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
SMB_RE = re.compile(r'^SMB\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+(?P<port>\d+)\s+(?P<rest>.*)$', re.I)


def _bool_after(rest: str, labels: list[str]) -> bool | None:
    for label in labels:
        m = re.search(label + r'\s*[:=]\s*(True|False|Yes|No|Enabled|Disabled|Required|Not\s+Required)', rest, re.I)
        if m:
            val = m.group(1).lower().replace(' ', '')
            return val in {'true', 'yes', 'enabled', 'required'}
    return None


def parse_netexec_smb_output(text: str) -> dict[str, list[dict[str, Any]]]:
    facts_by_ip: dict[str, dict[str, Any]] = {}
    shares: list[dict[str, Any]] = []
    current_ip: str | None = None
    for raw in text.splitlines():
        line = ANSI_RE.sub('', raw).strip()
        if not line or line.lower().startswith(('warning', 'error:', '[*]')):
            continue
        m = SMB_RE.match(line)
        if not m:
            # tolerate table share rows following an SMB host line
            if current_ip:
                cols = re.split(r'\s{2,}|\t+', line)
                if cols and cols[0] and cols[0].upper() not in {'SHARE', 'NAME'} and len(cols) >= 2:
                    name, access = cols[0].strip(), cols[1].strip()
                    if name and access and re.match(r'^[A-Za-z0-9_$.-]+$', name):
                        shares.append(
                            {
                                'ip': current_ip,
                                'name': name,
                                'access': access,
                                'remark': cols[2].strip() if len(cols) > 2 else '',
                                'anonymous': True,
                            }
                        )
            continue
        ip, rest = m.group('ip'), m.group('rest')
        current_ip = ip
        fact = facts_by_ip.setdefault(
            ip,
            {
                'ip': ip,
                'hostname': None,
                'domain': None,
                'os': None,
                'smb_signing_required': None,
                'smbv1_enabled': None,
                'null_session_possible': None,
                'raw_line': line,
            },
        )
        # Common NXC: SMB ip 445 HOST [*] Windows ... (domain:LAB) (signing:True) (SMBv1:False)
        host_match = re.match(r'(?P<host>\S+)\s+(?P<tail>.*)', rest)
        tail = rest
        if host_match:
            host = host_match.group('host')
            if host not in {'[*]', '[+]', '[-]'}:
                fact['hostname'] = host
            tail = host_match.group('tail')
        dom = re.search(r'(?:domain|domain name)\s*[:=]\s*([^\s)]+)', rest, re.I)
        if dom:
            fact['domain'] = dom.group(1)
        signing = _bool_after(rest, [r'signing', r'smb signing'])
        if signing is not None:
            fact['smb_signing_required'] = signing
        smbv1 = _bool_after(rest, [r'smbv1'])
        if smbv1 is not None:
            fact['smbv1_enabled'] = smbv1
        if '[+]' in rest and ("'':" in rest or 'null' in rest.lower() or '-u' not in rest):
            fact['null_session_possible'] = True
        if 'STATUS_LOGON_FAILURE' in rest or 'STATUS_ACCESS_DENIED' in rest or '[-]' in rest:
            fact['null_session_possible'] = (
                False if fact.get('null_session_possible') is None else fact['null_session_possible']
            )
        os_part = re.sub(r'\([^)]*\)', '', tail)
        os_part = re.sub(r'\[[^]]*\]', '', os_part).strip(' -')
        if os_part and any(w.lower() in os_part.lower() for w in ['windows', 'server', 'samba']):
            fact['os'] = os_part
        # inline share row sometimes: SMB ip 445 HOST Share Permissions Remark
        if re.search(r'\b(READ|WRITE|NO ACCESS|Read|Write)\b', rest) and 'signing' not in rest.lower():
            cols = re.split(r'\s{2,}|\t+', rest)
            if len(cols) >= 3:
                name = cols[-3].strip()
                access = cols[-2].strip()
                remark = cols[-1].strip()
                if re.match(r'^[A-Za-z0-9_$.-]+$', name):
                    shares.append({'ip': ip, 'name': name, 'access': access, 'remark': remark, 'anonymous': True})
    return {'facts': list(facts_by_ip.values()), 'shares': shares}
