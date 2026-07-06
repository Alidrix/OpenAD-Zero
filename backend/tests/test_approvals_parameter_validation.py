from datetime import datetime

import pytest

from app.approvals.errors import ApprovalError
from app.approvals.service import prepare_approval
from app.db.models import PentestAction, Scan


def _scan(db):
    scan = Scan(id='scan-params', name='s', scan_type='nmap', status='completed')
    db.add(scan)
    db.commit()
    return scan


def _action(db, scan, inputs):
    action = PentestAction(
        scan_id=scan.id,
        phase_id='p',
        title='t',
        description='d',
        reason='r',
        risk_level='low',
        execution_mode='approval_required',
        tool_id='nmap_safe_discovery',
        template_id='nmap_safe_discovery',
        required_inputs_json=['target'],
        resolved_inputs_json=inputs,
        missing_inputs_json=[],
        scope_sensitive_params_json={'validated_scope': ['10.0.0.0/24']},
        status='proposed',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def test_approval_prepare_refuses_out_of_scope(db_session):
    scan = _scan(db_session)
    action = _action(db_session, scan, {'target': '10.0.1.5'})
    with pytest.raises(ApprovalError):
        prepare_approval(db_session, scan.id, action.id)


def test_approval_prepare_refuses_bad_file(db_session):
    scan = _scan(db_session)
    action = PentestAction(
        scan_id=scan.id,
        phase_id='p',
        title='t',
        description='d',
        reason='r',
        risk_level='high',
        execution_mode='reinforced_approval_required',
        tool_id='kerbrute',
        template_id='kerberos_user_enumeration',
        required_inputs_json=['dc_ip', 'domain', 'userlist'],
        resolved_inputs_json={'dc_ip': '10.0.0.10', 'domain': 'LAB', 'userlist': '/etc/passwd'},
        missing_inputs_json=[],
        scope_sensitive_params_json={'validated_scope': ['10.0.0.0/24']},
        status='waiting_approval',
    )
    db_session.add(action)
    db_session.commit()
    db_session.refresh(action)
    with pytest.raises(ApprovalError):
        prepare_approval(db_session, scan.id, action.id)
