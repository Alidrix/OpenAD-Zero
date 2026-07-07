from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import PentestAction, Scan, ScanEvent
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


def _seed(Session, scan_id='scan-events'):
    db = Session()
    scan = Scan(id=scan_id, name=scan_id, scan_type='manual', status='draft')
    action = PentestAction(
        scan_id=scan_id,
        phase_id='smb_enumeration',
        title='SMB',
        description='d',
        reason='r',
        risk_level='medium',
        execution_mode='approval_required',
        tool_id='netexec',
        template_id='smb_fingerprint',
        required_inputs_json=['target'],
        resolved_inputs_json={'target': '10.0.0.5'},
        missing_inputs_json=[],
        scope_sensitive_params_json={'target': '10.0.0.5'},
        status='proposed',
    )
    db.add_all([scan, action])
    db.commit()
    db.refresh(action)
    db.close()
    return scan_id, action.id


def test_approval_events_are_persisted_and_ui_safe(client):
    engine, Session = _install()
    try:
        scan_id, action_id = _seed(Session)
        client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', json={})
        client.post(f'/api/v2/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', json={'operator': 'op'})
        scan2, action2 = _seed(Session, 'scan-events-reject')
        client.post(f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/prepare', json={})
        client.post(
            f'/api/v2/scans/{scan2}/pentest/actions/{action2}/approval/reject', json={'operator': 'op', 'reason': 'no'}
        )
        db = Session()
        events = (
            db.query(ScanEvent)
            .filter(ScanEvent.event_type.in_(['approval.prepared', 'approval.approved', 'approval.rejected']))
            .all()
        )
        event_types = {e.event_type for e in events}
        assert {'approval.prepared', 'approval.approved', 'approval.rejected'} <= event_types
        forbidden = ['secret', 'raw_command', 'argv', 'token', 'credential']
        for event in events:
            text = str(event.payload_json).lower()
            assert all(word not in text for word in forbidden)
            assert set(event.payload_json) == {
                'approval_id',
                'scan_id',
                'action_id',
                'phase_id',
                'tool_id',
                'template_id',
                'risk_level',
                'approval_level',
                'status',
            }
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
