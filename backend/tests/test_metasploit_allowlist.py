from app.tool_automation.metasploit_allowlist import validate_metasploit_module
from app.tool_automation.command_templates import COMMAND_TEMPLATES


def test_module_absent_refused():
    ok, reason = validate_metasploit_module('missing')
    assert not ok and 'allowlisted' in reason


def test_module_disabled_refused():
    ok, reason = validate_metasploit_module('msf_controlled_exploit_example', final_confirmation=True, check_status='success')
    assert not ok and 'disabled' in reason


def test_option_non_allowlisted_refused():
    ok, reason = validate_metasploit_module('msf_smb_ms17_010_check', options={'BAD': 'x'})
    assert not ok and 'option' in reason


def test_payload_non_allowlisted_refused_for_disabled_example_precedence_is_disabled():
    ok, reason = validate_metasploit_module('msf_controlled_exploit_example', payload='bad')
    assert not ok


def test_check_module_accepted_when_conditions_met():
    ok, reason = validate_metasploit_module('msf_smb_ms17_010_check', options={'RHOSTS': '10.0.0.5'})
    assert ok, reason


def test_no_exploit_all_template():
    assert all('exploit all' not in ' '.join(argv).lower() for argv in COMMAND_TEMPLATES.values())
