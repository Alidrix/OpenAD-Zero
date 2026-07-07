from types import SimpleNamespace

from app.pentest.rules import PentestFacts, evaluate_rules


def test_rules_normalize_supported_catalog_template():
    ctx = PentestFacts(
        scan=SimpleNamespace(id='s1', mission_id=None),
        parsed_services=[SimpleNamespace(protocol='tcp', port=445, ip_address='10.0.0.5')],
    )
    _phases, actions = evaluate_rules(ctx)
    assert any(a.template_id == 'smb_fingerprint' for a in actions)


def test_rules_catalog_block_absent_template_via_remote_management():
    ctx = PentestFacts(
        scan=SimpleNamespace(id='s1', mission_id=None),
        parsed_services=[SimpleNamespace(protocol='tcp', port=5985, ip_address='10.0.0.5')],
    )
    _phases, actions = evaluate_rules(ctx)
    assert actions
    assert any(a.blocked_reason and 'not declared' in a.blocked_reason for a in actions)


def test_rules_manual_only_template_is_blocked():
    ctx = PentestFacts(
        scan=SimpleNamespace(id='s1', mission_id=None),
        parsed_findings=[SimpleNamespace(severity='high', title='secret', description='exposed_secret')],
        parsed_signals=[SimpleNamespace(signal='exposed_secret', value='yes')],
    )
    _phases, actions = evaluate_rules(ctx)
    manual = [a for a in actions if a.execution_mode == 'manual_only']
    assert manual
    assert all(a.status == 'blocked' for a in manual)
