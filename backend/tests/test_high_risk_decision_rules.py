from app.pentest.rules import evaluate_rules
from app.pentest.rules.base import RuleContext


def test_rules_do_not_propose_sensitive_execution_keywords():
    _signals, actions = evaluate_rules(
        RuleContext(
            scan=type('Scan', (), {'id': 's', 'mission_id': None})(),
            parsed_signals=[
                type('Signal', (), {'signal': 'kerberoastable', 'value': 'true'})(),
                type('Signal', (), {'signal': 'smb_admin_access_detected', 'value': 'true'})(),
                type('Signal', (), {'signal': 'dangerous_acl_detected', 'value': 'true'})(),
            ],
        )
    )
    text = ' '.join(f'{a.tool_id} {a.template_id} {a.title}' for a in actions).casefold()
    for word in ['psexec', 'wmiexec', 'secretsdump', 'mimikatz', 'password_spray', 'password spray']:
        assert word not in text


def test_rules_propose_review_reporting_for_high_risk_signals():
    _signals, actions = evaluate_rules(
        RuleContext(
            scan=type('Scan', (), {'id': 's', 'mission_id': None})(),
            parsed_signals=[type('Signal', (), {'signal': 'kerberoastable', 'value': 'true'})()],
        )
    )
    assert any('review' in (a.title + a.template_id).casefold() or 'summary' in a.template_id for a in actions)
