from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import OperatorApproval, PentestAction, Scan
from app.db.session import Base, get_db
from app.main import app


def _install():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return engine, Session


def _seed(Session, *, mode='approval_required', scan_id='scan-a'):
    db = Session()
    try:
        scan = Scan(id=scan_id, name=scan_id, scan_type='manual', status='draft')
        action = PentestAction(
            scan_id=scan_id,
            phase_id='smb_enumeration',
            title='SMB',
            description='d',
            reason='r',
            risk_level='high',
            execution_mode=mode,
            tool_id='netexec',
            template_id='smb_fingerprint',
            required_inputs_json=['target'],
            resolved_inputs_json={'target': '10.0.0.5', 'password': 'secret'},
            missing_inputs_json=[],
            scope_sensitive_params_json={'target': '10.0.0.5'},
            status='proposed',
        )
        db.add_all([scan, action])
        db.commit()
        db.refresh(action)
        return scan.id, action.id
    finally:
        db.close()


def test_prepare_reuses_pending_and_forbids_raw_payload_fields(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        url = f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare'
        first = client.post(url, json={'operator_note': 'ok'})
        second = client.post(url, json={})
        assert first.status_code == 200
        assert first.json()['approval_level'] == 'standard'
        assert first.json()['command_hash']
        assert second.json()['id'] == first.json()['id']
        for field in ['command', 'argv', 'shell', 'human_approved', 'raw_command', 'command_hash', 'command_preview']:
            assert client.post(url, json={field: True}).status_code == 422
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_approve_reject_statuses_and_conflicts(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={})
        approved = client.post(
            f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', json={'operator': 'op'}
        )
        assert approved.status_code == 200
        db = Session()
        assert db.get(PentestAction, action_id).status == 'approved'
        db.close()

        scan2, action2 = _seed(Session, scan_id='scan-rejected')
        client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={})
        rejected = client.post(
            f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/reject', json={'operator': 'op', 'reason': 'no'}
        )
        assert rejected.status_code == 200
        assert rejected.json()['status'] == 'rejected'
        assert (
            client.post(
                f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 409
        )
        db = Session()
        assert db.get(PentestAction, action2).status == 'rejected'
        db.close()

        scan3, action3 = _seed(Session, scan_id='scan-expired')
        prep = client.post(f'/api/v2/scans/{scan3}/pentest/actions/{action3}/approval/prepare', json={}).json()
        db = Session()
        row = db.get(OperatorApproval, prep['id'])
        row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
        db.close()
        assert (
            client.post(
                f'/api/v2/scans/{scan3}/pentest/actions/{action3}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 409
        )

        scan4, action4 = _seed(Session, scan_id='scan-consumed')
        prep = client.post(f'/api/v2/scans/{scan4}/pentest/actions/{action4}/approval/prepare', json={}).json()
        db = Session()
        row = db.get(OperatorApproval, prep['id'])
        row.status = 'consumed'
        db.commit()
        db.close()
        assert (
            client.post(
                f'/api/v2/scans/{scan4}/pentest/actions/{action4}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 409
        )
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_reinforced_and_summary(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session, mode='reinforced_approval_required')
        prep = client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={})
        assert prep.json()['approval_level'] == 'reinforced'
        assert (
            client.post(
                f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 400
        )
        summary = client.get(f'/api/v2/scans/{scan_id}/approvals/summary')
        assert summary.status_code == 200
        assert summary.json()['pending'] == 1
        assert summary.json()['reinforced_pending'] == 1
        ok = client.post(
            f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve',
            json={'operator': 'op', 'reinforced_confirmation': 'confirmed'},
        )
        assert ok.status_code == 200
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
