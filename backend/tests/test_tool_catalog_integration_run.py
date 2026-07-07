from datetime import datetime, timedelta

import pytest

from app.approvals.errors import ApprovalError
from app.approvals.run_service import build_run_context
from app.db.models import OperatorApproval, PentestAction, Scan


def _rows(template_id='secrets_evidence_review'):
    scan = Scan(id='scan1', name='scan1', mission_id=None, scan_type='v2')
    action = PentestAction(
        id='act1',
        scan_id='scan1',
        phase_id='credential_exposure_review',
        title='t',
        description='d',
        reason='r',
        risk_level='high',
        execution_mode='manual_only',
        tool_id='reporting',
        template_id=template_id,
        resolved_inputs_json={},
        missing_inputs_json=[],
        scope_sensitive_params_json={},
    )
    approval = OperatorApproval(
        id='ap1',
        scan_id='scan1',
        action_id='act1',
        phase_id='credential_exposure_review',
        tool_id='reporting',
        template_id=template_id,
        command_hash='x',
        masked_preview_json={},
        resolved_inputs_json={},
        missing_inputs_json=[],
        scope_snapshot_json={},
        risk_level='high',
        approval_level='standard',
        status='approved',
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return scan, action, approval


def test_run_refuses_unsupported_without_consuming_approval(db_session):
    scan, action, approval = _rows()
    db_session.add_all([scan, action, approval])
    db_session.commit()
    with pytest.raises(ApprovalError) as exc:
        build_run_context(db_session, 'ap1')
    assert exc.value.status_code in {403, 501}
    db_session.refresh(approval)
    assert approval.status == 'approved'


def test_run_accepts_only_prompt10_supported_template_metadata(db_session):
    scan, action, approval = _rows('nmap_safe_discovery')
    action.phase_id = 'network_discovery'
    action.risk_level = 'low'
    action.execution_mode = 'safe_auto'
    action.tool_id = 'network_discovery'
    action.resolved_inputs_json = {'target': '10.0.0.5'}
    action.scope_sensitive_params_json = {'validated_scope': ['10.0.0.5']}
    approval.tool_id = 'network_discovery'
    approval.template_id = 'nmap_safe_discovery'
    approval.risk_level = 'low'
    db_session.add_all([scan, action, approval])
    db_session.commit()
    ctx = build_run_context(db_session, 'ap1')
    assert ctx.template_id == 'nmap_safe_discovery'
