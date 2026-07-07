from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_v2_scan_events
from app.db.session import Base, get_db
from app.main import app


def test_v2_scan_websocket_replays_scan_events_in_order(client):
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
    original_session_local = routes_v2_scan_events.SessionLocal
    routes_v2_scan_events.SessionLocal = Session
    try:
        created = client.post(
            '/api/v2/scans', json={'name': 'WS scan', 'scan_type': 'manual', 'tool_name': 'manual'}
        ).json()
        scan_id = created['id']
        renamed = client.patch(f'/api/v2/scans/{scan_id}/rename', json={'name': 'WS scan renamed'}).json()
        assert renamed['name'] == 'WS scan renamed'

        persisted_events = client.get(f'/api/v2/scans/{scan_id}/events').json()
        assert [event['event_type'] for event in persisted_events] == ['scan.created', 'scan.renamed']

        with client.websocket_connect(f'/ws/v2/scans/{scan_id}?replay=true') as websocket:
            first = websocket.receive_json()
            second = websocket.receive_json()
            assert first['type'] == 'scan.created'
            assert first['event_type'] == 'scan.created'
            assert first['scan_id'] == scan_id
            assert first['status'] == 'draft'
            assert first['progress_percent'] == 0
            assert first['message'] == 'Scan created in draft state'
            assert 'created_at' in first
            assert second['type'] == 'scan.renamed'
            assert second['event_type'] == 'scan.renamed'
            assert second['payload'] == {'old_name': 'WS scan', 'new_name': 'WS scan renamed'}
    finally:
        routes_v2_scan_events.SessionLocal = original_session_local
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
