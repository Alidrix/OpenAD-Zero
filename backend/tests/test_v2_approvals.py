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


def _seed(Session, *, mode='approval_required', status='proposed', scan_id='scan-a'):
    db = Session()
    try:
        scan = Scan(id=scan_id, name=scan_id, scan_type='manual', status='draft')
        action = PentestAction(
            scan_id=scan_id,
            phase_id='smb_enumeration',
            title='SMB',
            description='d',
            reason='r',
            risk_level='medium',
            execution_mode=mode,
            tool_id='netexec',
            template_id='smb_fingerprint',
            required_inputs_json=['target'],
            resolved_inputs_json={'target': '10.0.0.5', 'password': 'secret'},
            missing_inputs_json=[],
            scope_sensitive_params_json={'target': '10.0.0.5'},
            status=status,
        )
        db.add(scan)
        db.add(action)
        db.commit()
        db.refresh(action)
        return scan.id, action.id
    finally:
        db.close()


def test_prepare_creates_pending_and_reuses_existing(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        first = client.post(
            f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={'operator_note': 'ok'}
        )
        second = client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={})
        assert first.status_code == 200
        assert first.json()['status'] == 'pending'
        assert second.json()['id'] == first.json()['id']
        db = Session()
        action = db.get(PentestAction, action_id)
        assert action.status == 'waiting_approval'
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_prepare_refuses_missing_other_scan_and_manual_only(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        db = Session()
        db.add(Scan(id='other', name='other', scan_type='manual'))
        db.commit()
        db.close()
        assert (
            client.post(f'/api/v2/scans/{scan_id}/pentest/actions/missing/approval/prepare', json={}).status_code == 404
        )
        assert (
            client.post(f'/api/v2/scans/other/pentest/actions/{action_id}/approval/prepare', json={}).status_code == 404
        )
        scan2, action2 = _seed(Session, mode='manual_only', scan_id='scan-manual')
        assert (
            client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={}).status_code == 400
        )
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_approve_reject_and_action_statuses(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={})
        approved = client.post(
            f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', json={'operator': 'local-operator'}
        )
        assert approved.status_code == 200
        assert approved.json()['status'] == 'approved'
        db = Session()
        assert db.get(PentestAction, action_id).status == 'approved'
        db.close()

        scan2, action2 = _seed(Session, scan_id='scan-reject')
        client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={})
        rejected = client.post(
            f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/reject',
            json={'operator': 'local-operator', 'reason': 'no'},
        )
        assert rejected.status_code == 200
        assert rejected.json()['status'] == 'rejected'
        db = Session()
        assert db.get(PentestAction, action2).status == 'rejected'
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_approve_refuses_expired_rejected_consumed_and_reinforced_confirmation(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        prep = client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={}).json()
        db = Session()
        row = db.get(OperatorApproval, prep['id'])
        row.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
        db.close()
        assert (
            client.post(
                f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 409
        )

        scan2, action2 = _seed(Session, scan_id='scan-consumed')
        client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={})
        db = Session()
        row = db.query(OperatorApproval).filter_by(action_id=action2).one()
        row.status = 'consumed'
        db.commit()
        db.close()
        assert (
            client.post(
                f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 409
        )

        scan3, action3 = _seed(Session, mode='reinforced_approval_required', scan_id='scan-reinf')
        prep3 = client.post(f'/api/v2/scans/{scan3}/pentest/actions/{action3}/approval/prepare', json={})
        assert prep3.json()['approval_level'] == 'reinforced'
        assert (
            client.post(
                f'/api/v2/scans/{scan3}/pentest/actions/{action3}/approval/approve', json={'operator': 'op'}
            ).status_code
            == 400
        )
        assert (
            client.post(
                f'/api/v2/scans/{scan3}/pentest/actions/{action3}/approval/approve',
                json={'operator': 'op', 'reinforced_confirmation': 'I confirm'},
            ).status_code
            == 200
        )
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_get_approval_masks_secret_and_scan_list_is_scoped(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        approval = client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={}).json()
        scan2, action2 = _seed(Session, scan_id='scan-other')
        client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={})
        got = client.get(f'/api/v2/approvals/{approval["id"]}')
        assert got.status_code == 200
        assert 'secret' not in got.text
        listed = client.get(f'/api/v2/scans/{scan_id}/approvals')
        assert [item['scan_id'] for item in listed.json()] == [scan_id]
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
