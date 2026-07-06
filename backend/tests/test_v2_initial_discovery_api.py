from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Mission, Scan, ScanEvent
from app.db.session import Base, get_db
from app.main import app


class DummyJob:
    id = 'rq-safe-1'


class DummyQueue:
    calls = []

    def enqueue(self, func, *args, **kwargs):
        self.calls.append((func, args, kwargs))
        return DummyJob()


def _setup(monkeypatch):
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
    q = DummyQueue()
    q.calls.clear()
    monkeypatch.setattr('app.api.routes_v2_scans.get_scan_queue', lambda: q)
    return engine, Session, q


def _scan(Session, status='draft', scoped=True):
    db = Session()
    try:
        mission = Mission(
            name='m',
            scenario='s',
            mode='safe',
            raw_scope='10.0.0.0/24',
            validated_targets=['10.0.0.0/24'] if scoped else [],
        )
        db.add(mission)
        db.commit()
        db.refresh(mission)
        scan = Scan(name='s', scan_type='initial_discovery', status=status, mission_id=mission.id)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan.id
    finally:
        db.close()


def test_start_initial_discovery_api_guards_and_enqueue(client, monkeypatch):
    engine, Session, q = _setup(monkeypatch)
    try:
        assert (
            client.post('/api/v2/scans/missing/start-initial-discovery', json={'profile': 'safe_default'}).status_code
            == 404
        )
        deleted_id = _scan(Session, 'deleted')
        assert (
            client.post(
                f'/api/v2/scans/{deleted_id}/start-initial-discovery', json={'profile': 'safe_default'}
            ).status_code
            == 409
        )
        running_id = _scan(Session, 'running')
        assert (
            client.post(
                f'/api/v2/scans/{running_id}/start-initial-discovery', json={'profile': 'safe_default'}
            ).status_code
            == 409
        )
        no_scope_id = _scan(Session, 'draft', scoped=False)
        assert (
            client.post(
                f'/api/v2/scans/{no_scope_id}/start-initial-discovery', json={'profile': 'safe_default'}
            ).status_code
            == 409
        )
        ok_id = _scan(Session)
        assert (
            client.post(
                f'/api/v2/scans/{ok_id}/start-initial-discovery', json={'profile': 'safe_default', 'command': 'nmap'}
            ).status_code
            == 422
        )
        assert (
            client.post(
                f'/api/v2/scans/{ok_id}/start-initial-discovery', json={'profile': 'safe_default', 'argv': ['nmap']}
            ).status_code
            == 422
        )
        data = client.post(f'/api/v2/scans/{ok_id}/start-initial-discovery', json={'profile': 'safe_default'}).json()
        assert data['status'] == 'queued'
        assert data['rq_job_id'] == 'rq-safe-1'
        assert q.calls and q.calls[0][0].__name__ == 'run_initial_discovery_scan'
        db = Session()
        assert db.query(ScanEvent).filter_by(scan_id=ok_id, event_type='scan.initial_discovery_queued').first()
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
