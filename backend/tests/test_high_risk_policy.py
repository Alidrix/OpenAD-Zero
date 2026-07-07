import pytest

from app.tool_catalog.high_risk_policy import (
    HighRiskPolicyViolation,
    assert_template_allowed_for_approval,
    assert_template_allowed_for_run,
    classify_high_risk_capability,
)
from app.tool_catalog.registry import get_template


def test_classifies_strict_high_risk_families():
    assert classify_high_risk_capability('secretsdump ntds') == 'credential_access'
    assert classify_high_risk_capability('password_spray bruteforce') == 'authentication_attack'
    assert classify_high_risk_capability('psexec remote shell') == 'lateral_movement'
    assert classify_high_risk_capability('ntlmrelayx responder capture') == 'coercion_capture'
    assert classify_high_risk_capability('bloodyad_write DACL modification') == 'ad_write_operations'
    assert classify_high_risk_capability('meterpreter payload reverse_tcp') == 'metasploit'
    assert classify_high_risk_capability('persistence cleanup traces') == 'impact_or_persistence'


def test_preview_manual_blocked_never_allowed_for_run():
    for tid in ['metasploit_search_preview', 'secrets_evidence_review', 'persistence']:
        template = get_template(tid)
        assert template is not None
        with pytest.raises(HighRiskPolicyViolation):
            assert_template_allowed_for_run(template)


def test_blocked_and_manual_only_not_allowed_for_approval():
    for tid in ['metasploit_controlled_exploit', 'mimikatz', 'secrets_evidence_review']:
        template = get_template(tid)
        assert template is not None
        with pytest.raises(HighRiskPolicyViolation):
            assert_template_allowed_for_approval(template)
