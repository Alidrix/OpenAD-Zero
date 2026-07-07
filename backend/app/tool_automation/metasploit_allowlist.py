from __future__ import annotations

from pathlib import Path

import yaml

PATH = Path(__file__).with_name('metasploit_allowlist.yml')


def load_metasploit_allowlist(path: Path = PATH) -> dict[str, dict]:
    raw = yaml.safe_load(path.read_text()) or {}
    return {m['id']: m for m in raw.get('modules', [])}


def validate_metasploit_module(
    module_id: str,
    *,
    options: dict[str, object] | None = None,
    payload: str | None = None,
    final_confirmation: bool = False,
    check_status: str | None = None,
) -> tuple[bool, str]:
    item = load_metasploit_allowlist().get(module_id)
    if not item:
        return False, 'Metasploit module is not allowlisted.'
    if not item.get('allowed'):
        return False, 'Metasploit module is disabled by allowlist.'
    allowed_options = set(item.get('allowed_options') or [])
    invalid = set((options or {}).keys()) - allowed_options
    if invalid:
        return False, f'Metasploit option is not allowlisted: {sorted(invalid)[0]}'
    if item.get('requires_payload') and payload not in set(item.get('allowed_payloads') or []):
        return False, 'Metasploit payload is not allowlisted.'
    if item.get('type') == 'exploit' and not final_confirmation:
        return False, 'Metasploit controlled exploit requires final confirmation.'
    if item.get('requires_check_first') and check_status != 'success':
        return False, 'Metasploit controlled exploit requires a successful check first.'
    return True, 'Metasploit module is allowlisted.'
