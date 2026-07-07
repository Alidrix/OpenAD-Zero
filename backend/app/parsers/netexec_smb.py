from __future__ import annotations

import json
import re
from pathlib import Path


def parse_netexec_smb(path: str | Path) -> dict:
    text = Path(path).read_text(errors='replace') if Path(path).exists() else ''
    if Path(path).suffix == '.json':
        try:
            return json.loads(text)
        except Exception:
            pass
    low = text.lower()
    hosts = sorted(set(re.findall(r'(?:\d{1,3}\.){3}\d{1,3}', text)))
    return {
        'raw_empty': not text.strip(),
        'hosts': hosts,
        'signals': {
            'smb_signing_disabled': any(
                x in low for x in ['signing:false', 'signing: false', 'signing disabled', 'signing is disabled']
            ),
            'smb_signing_required': any(x in low for x in ['signing:true', 'signing: true', 'signing required']),
            'anonymous_smb_possible': 'anonymous' in low,
            'null_session_possible': 'null session' in low,
            'smb_share_listed': ' share' in low or '\tshare' in low,
            'smb_admin_access_detected': any(x in low for x in ['pwn3d', 'admin access', 'administrator']),
            'smb_guest_access_detected': 'guest' in low,
            'domain_joined_host': 'domain:' in low,
        },
        'text': text[:4000],
    }


def _bool_after(text: str, key: str):
    m = re.search(rf'{re.escape(key)}\s*:\s*(true|false)', text, re.I)
    return None if not m else m.group(1).lower() == 'true'


def parse_netexec_smb_output(output: str) -> dict:
    facts = []
    shares = []
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        m = re.match(r'^SMB\s+((?:\d{1,3}\.){3}\d{1,3})\s+\d+\s+(\S+)\s+(.*)$', line)
        if not m:
            continue
        ip, host, rest = m.groups()
        fact = {'ip': ip, 'hostname': host}
        dm = re.search(r'domain:([^\)\s]+)', rest, re.I)
        if dm:
            fact['domain'] = dm.group(1)
        signing = _bool_after(rest, 'signing')
        if signing is not None:
            fact['smb_signing_required'] = signing
        smbv1 = _bool_after(rest, 'SMBv1')
        if smbv1 is not None:
            fact['smbv1_enabled'] = smbv1
        if '[+]' in rest and ('\\:' in rest or 'null' in rest.lower() or rest.strip().endswith(':')):
            fact['null_session_possible'] = True
        if 'guest' in rest.lower():
            fact['guest_access_possible'] = True
        if len(fact) > 2 or '[*]' in rest or '[+]' in rest:
            facts.append(fact)
        if i + 2 < len(lines) and 'Share' in lines[i + 1] and 'Permissions' in lines[i + 1]:
            sm = lines[i + 2].split()
            if len(sm) >= 2:
                shares.append({'ip': ip, 'name': sm[0], 'access': sm[1], 'remark': ' '.join(sm[2:])})
    return {'facts': facts, 'shares': shares}
