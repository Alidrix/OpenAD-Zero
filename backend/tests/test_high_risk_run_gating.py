from datetime import datetime, timedelta

import pytest

from app.approvals.errors import ApprovalError
from app.approvals.run_service import build_run_context
from app.db.models import OperatorApproval, PentestAction, Scan


def _approved(db, template_id, mode):
    scan = Scan(id=f'scan-run-{template_id}', name='s', scan_type='v2', status='completed')
    action = PentestAction(
        id=f'action-{template_id}',
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
        status='approved',
    )
    approval = OperatorApproval(
        scan_id=scan.id,
        action_id=f'action-{template_id}',
        phase_id='p',
        tool_id=template_id,
        template_id=template_id,
        command_hash='0' * 64,
        masked_preview_json={},
        resolved_inputs_json={},
        missing_inputs_json=[],
        scope_snapshot_json={},
        risk_level='critical',
        approval_level='standard',
        status='approved',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        metadata_json={},
    )
    db.add_all([scan, action, approval])
    db.commit()
    return approval


@pytest.mark.parametrize(
    'template_id,mode',
    [
        ('metasploit_search_preview', 'preview_only'),
        ('mimikatz', 'manual_only'),
        ('metasploit_controlled_exploit', 'blocked'),
    ],
)
def test_run_refuses_high_risk_without_consuming_approval(db_session, template_id, mode):
    approval = _approved(db_session, template_id, mode)
    with pytest.raises(ApprovalError):
        build_run_context(db_session, approval.id)
    db_session.refresh(approval)
    assert approval.status == 'approved'
    assert approval.consumed_at is None
