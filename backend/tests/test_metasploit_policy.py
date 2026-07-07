import pytest

from app.tool_catalog.high_risk_policy import HighRiskPolicyViolation, validate_template_high_risk_policy
from app.tool_catalog.registry import get_template, list_template_metadata


def test_metasploit_exploit_template_absent_or_blocked():
    blocked = get_template('metasploit_controlled_exploit')
    assert blocked is not None
    assert blocked.execution_mode == 'blocked'
    assert not blocked.supported_for_run


def test_metasploit_preview_search_info_check_are_preview_only():
    for tid in [
        'metasploit_search_preview',
        'metasploit_info_preview',
        'metasploit_module_metadata_preview',
        'metasploit_check_preview',
    ]:
        template = get_template(tid)
        assert template is not None
        assert template.execution_mode == 'preview_only'
        assert not template.supported_for_run


def test_metasploit_payload_run_exploit_sessions_refused():
    base = get_template('metasploit_search_preview').to_dict()
    for token in ['set payload windows/meterpreter/reverse_tcp', 'run', 'exploit', 'sessions -i 1']:
        bad = {**base, 'argv': ['msfconsole', '-q', '-x', f'{token}; exit']}
        with pytest.raises(HighRiskPolicyViolation):
            validate_template_high_risk_policy(bad)


def test_metasploit_module_non_allowlisted_refused():
    base = get_template('metasploit_check_preview').to_dict()
    bad = {
        **base,
        'template_id': 'metasploit_free_module',
        'argv': ['msfconsole', '-q', '-x', 'use exploit/windows/smb/psexec; check; exit'],
    }
    with pytest.raises(HighRiskPolicyViolation):
        validate_template_high_risk_policy(bad)


def test_no_metasploit_template_supported_for_run():
    assert all(not t.supported_for_run for t in list_template_metadata() if t.tool_id == 'metasploit')
