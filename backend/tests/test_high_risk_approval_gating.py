import pytest

from app.approvals.errors import ApprovalError
from app.approvals.service import prepare_approval
from app.db.models import PentestAction, Scan


def _action(db, template_id, mode):
    scan = Scan(id=f'scan-{template_id}', name='s', scan_type='v2', status='completed')
    action = PentestAction(
        scan_id=scan.id,
        phase_id='p',
        title='t',
        description='d',
        reason='r',
        risk_level='critical',
        execution_mode=mode,
        tool_id=template_id,
        template_id=template_id,
        required_inputs_json=[],
        resolved_inputs_json={},
        missing_inputs_json=[],
        scope_sensitive_params_json={},
        priority=1,
        status='proposed',
    )
    db.add_all([scan, action])
    db.commit()
    return scan, action


@pytest.mark.parametrize(
    'template_id,mode',
    [
        ('metasploit_controlled_exploit', 'blocked'),
        ('mimikatz', 'manual_only'),
        ('metasploit_search_preview', 'preview_only'),
    ],
)
def test_prepare_approval_refuses_high_risk_modes(db_session, template_id, mode):
    scan, action = _action(db_session, template_id, mode)
    with pytest.raises(ApprovalError):
        prepare_approval(db_session, scan.id, action.id)
