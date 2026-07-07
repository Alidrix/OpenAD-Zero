from app.tool_catalog.risk_policy import can_support_run, classify_execution_allowed, contains_dangerous_keyword


def test_manual_and_blocked_cannot_support_run():
    assert can_support_run('manual_only', True, 'critical')[0] is False
    assert can_support_run('blocked', True, 'critical')[0] is False
    assert can_support_run('safe_auto', True, 'high')[0] is False


def test_execution_classification():
    assert classify_execution_allowed('manual_only', False)[1] == 403
    assert classify_execution_allowed('approval_required', False)[1] == 501
    assert classify_execution_allowed('approval_required', True)[0] is True
    assert contains_dangerous_keyword(['tool', 'secretsdump']) is True
