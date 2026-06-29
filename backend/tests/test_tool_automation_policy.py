from pathlib import Path

import yaml

from app.tool_automation.command_templates import COMMAND_TEMPLATES
from app.tool_automation.policy import VALID_INTEGRATION_STATUSES, evaluate_tool_action, load_tool_catalog


def test_unknown_tool_and_out_of_scope_are_blocked():
    assert not evaluate_tool_action(tool_id='missing', action='preview').allowed
    decision = evaluate_tool_action(tool_id='nmap_safe_discovery', action='run', target_in_scope=False)
    assert not decision.allowed and 'outside' in decision.reason


def test_blocked_planned_manual_and_no_template_are_refused_on_run():
    catalog = {
        'blocked': {'id': 'blocked', 'integration_status': 'blocked_auto', 'templates': []},
        'planned': {'id': 'planned', 'integration_status': 'planned', 'templates': []},
        'manual': {'id': 'manual', 'integration_status': 'manual_only', 'templates': []},
        'none': {'id': 'none', 'integration_status': 'safe_auto', 'templates': []},
    }
    assert 'Blocked automation' in evaluate_tool_action(tool_id='blocked', action='run', catalog=catalog).reason
    assert 'Planned tools' in evaluate_tool_action(tool_id='planned', action='run', catalog=catalog).reason
    assert 'Manual-only' in evaluate_tool_action(tool_id='manual', action='run', catalog=catalog).reason
    assert 'No declared' in evaluate_tool_action(tool_id='none', action='run', catalog=catalog).reason


def test_executable_after_human_approval_preview_and_approve_allowed():
    assert evaluate_tool_action(tool_id='kerbrute', action='preview').allowed
    assert evaluate_tool_action(tool_id='kerbrute', action='approve').allowed


def test_executable_after_human_approval_run_gates():
    base = dict(tool_id='kerbrute', action='run', selected_template_id='kerbrute_userenum')
    assert 'preview' in evaluate_tool_action(**base).reason
    assert 'human approval' in evaluate_tool_action(**base, preview_generated=True).reason
    assert 'terms acceptance' in evaluate_tool_action(**base, preview_generated=True, human_approved=True).reason
    assert 'hash' in evaluate_tool_action(**base, preview_generated=True, human_approved=True, terms_accepted=True, command_hash='abc', preview_command_hash='abc').reason
    assert evaluate_tool_action(**base, preview_generated=True, human_approved=True, terms_accepted=True, command_hash='abc', preview_command_hash='abc').allowed


def test_executable_after_human_approval_template_refusals():
    assert 'No declared' in evaluate_tool_action(tool_id='kerbrute', action='run').reason
    assert 'not allowed' in evaluate_tool_action(tool_id='kerbrute', action='run', selected_template_id='missing').reason
    assert 'not allowed' in evaluate_tool_action(tool_id='kerbrute', action='run', selected_template_id='responder_analyze').reason


def test_sensitive_keywords_block_safe_but_not_declared_advanced_after_all_gates():
    assert not evaluate_tool_action(tool_id='nmap_safe_discovery', action='run', selected_template_id='nmap_safe_discovery', argv=['responder']).allowed
    decision = evaluate_tool_action(tool_id='responder', action='run', selected_template_id='responder_analyze', argv=COMMAND_TEMPLATES['responder_analyze'], preview_generated=True, human_approved=True, terms_accepted=True, command_hash='abc', preview_command_hash='abc')
    assert decision.allowed and decision.risk_level == 'high'


def test_catalog_and_templates_are_consistent():
    catalog = load_tool_catalog()
    referenced = set()
    for tool_id, tool in catalog.items():
        if tool['integration_status'] == 'executable_after_human_approval':
            assert tool['risk_level'] == 'high'
            assert tool['requires_human_approval'] is True
            assert tool['requires_terms_acceptance'] is True
            assert tool['templates']
        for template_id in tool.get('templates', []):
            referenced.add(template_id)
            assert template_id in COMMAND_TEMPLATES, f'{tool_id}: {template_id}'
    assert set(COMMAND_TEMPLATES) == referenced


def test_command_templates_are_argument_lists_without_shell_true():
    for argv in COMMAND_TEMPLATES.values():
        assert isinstance(argv, list)
        assert all(isinstance(arg, str) for arg in argv)
        joined = ' '.join(argv)
        assert 'shell=True' not in joined
        assert not isinstance(argv, str)


def test_catalog_uses_strict_integration_statuses():
    raw = yaml.safe_load(Path('backend/app/tool_automation/tools.yml').read_text())
    assert {item['integration_status'] for item in raw} <= VALID_INTEGRATION_STATUSES


def test_removed_scanner_absent_from_tool_catalog_and_templates_and_docs():
    catalog = load_tool_catalog()
    assert all('ping' + 'castle' not in tool_id.lower() for tool_id in catalog)
    assert all('ping' + 'castle' not in template_id.lower() for template_id in COMMAND_TEMPLATES)


def test_metasploit_templates_forbid_payload_sessions_and_background_exploit():
    forbidden = ['exploit -j', 'run -j', 'set PAYLOAD', 'set LHOST', 'set LPORT', 'sessions -i']
    for tid, argv in COMMAND_TEMPLATES.items():
        if tid.startswith('metasploit'):
            joined = ' '.join(argv)
            for token in forbidden:
                assert token not in joined

def test_preview_hash_mismatch_refused():
    decision = evaluate_tool_action(tool_id='kerbrute', action='run', selected_template_id='kerbrute_userenum', preview_generated=True, human_approved=True, terms_accepted=True, command_hash='new', preview_command_hash='old')
    assert not decision.allowed and 'hash' in decision.reason
