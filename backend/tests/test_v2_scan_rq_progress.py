from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ScanEvent, ScanStep
from app.db.session import Base, get_db
from app.main import app
from app.services import scan_service
from app.services.scan_schemas import ScanCreate


class FakeRQJob:
    id = 'rq-demo-123'

    def __init__(self, status='queued'):
        self._status = status
        self.cancel_called = False

    def get_status(self, refresh=True):
        return self._status

    def cancel(self):
        self.cancel_called = True


class FakeQueue:
    def enqueue(self, func, *args, **kwargs):
        assert func.__name__ == 'run_demo_scan'
        assert args
        return FakeRQJob()


def make_session():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def test_enqueue_demo_scan_creates_rq_job_and_queued_status(client, monkeypatch):
    engine, Session = make_session()

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr('app.services.scan_orchestrator.get_scan_queue', lambda: FakeQueue())
    try:
        created = client.post('/api/v2/scans', json={'name': 'Demo enqueue', 'scan_type': 'demo', 'tool_name': 'demo-worker'}).json()
        queued = client.post(f"/api/v2/scans/{created['id']}/enqueue-demo").json()
        assert queued['status'] == 'queued'
        assert queued['rq_job_id'] == 'rq-demo-123'
        events = client.get(f"/api/v2/scans/{created['id']}/events").json()
        assert any(event['event_type'] == 'scan.queued' for event in events)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_run_demo_scan_persists_progress_to_completion(monkeypatch):
    engine, Session = make_session()
    monkeypatch.setattr('app.workers.v2_scan_jobs.SessionLocal', Session)
    db = Session()
    try:
        scan = scan_service.create_scan(db, ScanCreate(name='Demo worker', scan_type='demo', tool_name='demo-worker'))
        result = __import__('app.workers.v2_scan_jobs', fromlist=['run_demo_scan']).run_demo_scan(scan.id)
        db.expire_all()
        completed = scan_service.get_scan(db, scan.id)
        events = db.query(ScanEvent).filter_by(scan_id=scan.id).order_by(ScanEvent.created_at.asc()).all()
        steps = db.query(ScanStep).filter_by(scan_id=scan.id).order_by(ScanStep.order.asc()).all()
        assert result['status'] == 'completed'
        assert any(event.event_type == 'scan.running' for event in events)
        assert completed.status == 'completed'
        assert completed.progress_percent == 100
        assert completed.current_step == 'Demo worker completed'
        assert len(steps) == 6
        assert [step.progress_percent for step in steps] == [0, 20, 40, 60, 80, 100]
        assert any(event.event_type == 'scan.completed' for event in events)
        assert sum(1 for event in events if event.event_type == 'scan.progress_updated') >= 6
    finally:
        db.close()
        Base.metadata.drop_all(engine)


def test_stop_without_rq_job_keeps_logical_stop(db_session):
    from app.services.scan_orchestrator import request_scan_stop

    scan = scan_service.create_scan(db_session, ScanCreate(name='Stop logical', scan_type='manual'))
    stopped = request_scan_stop(db_session, scan.id)
    assert stopped.status == 'stopped'
    assert stopped.stopped_at is not None


def test_stop_queued_rq_job_uses_cancel(db_session, monkeypatch):
    from app.services.scan_orchestrator import request_scan_stop

    fake_job = FakeRQJob('queued')
    scan = scan_service.create_scan(db_session, ScanCreate(name='Stop queued', scan_type='demo'))
    scan.status = 'queued'
    scan.rq_job_id = 'rq-queued'
    db_session.commit()

    monkeypatch.setattr('app.services.scan_orchestrator.get_redis_connection', lambda: object())
    monkeypatch.setattr('app.services.scan_orchestrator.Job.fetch', lambda job_id, connection: fake_job)

    stopped = request_scan_stop(db_session, scan.id)
    assert fake_job.cancel_called is True
    assert stopped.status == 'stopped'


def test_stop_started_rq_job_sends_stop_command(db_session, monkeypatch):
    from app.services.scan_orchestrator import request_scan_stop

    sent = []
    fake_job = FakeRQJob('started')
    scan = scan_service.create_scan(db_session, ScanCreate(name='Stop started', scan_type='demo'))
    scan.status = 'running'
    scan.rq_job_id = 'rq-started'
    db_session.commit()

    monkeypatch.setattr('app.services.scan_orchestrator.get_redis_connection', lambda: object())
    monkeypatch.setattr('app.services.scan_orchestrator.Job.fetch', lambda job_id, connection: fake_job)
    monkeypatch.setattr('app.services.scan_orchestrator.send_stop_job_command', lambda connection, job_id: sent.append(job_id))

    stopping = request_scan_stop(db_session, scan.id)
    assert sent == ['rq-started']
    assert stopping.status == 'stopping'
    events = db_session.query(ScanEvent).filter_by(scan_id=scan.id).all()
    assert any(event.event_type == 'scan.stop_requested' for event in events)


def test_stop_rq_unavailable_preserves_state_and_records_failure(db_session, monkeypatch):
    from app.services.scan_orchestrator import request_scan_stop

    scan = scan_service.create_scan(db_session, ScanCreate(name='Stop unavailable', scan_type='demo'))
    scan.status = 'running'
    scan.rq_job_id = 'rq-unavailable'
    db_session.commit()

    monkeypatch.setattr('app.services.scan_orchestrator.get_redis_connection', lambda: (_ for _ in ()).throw(ConnectionError('redis down')))

    try:
        request_scan_stop(db_session, scan.id)
    except RuntimeError:
        pass
    else:
        raise AssertionError('request_scan_stop should raise RuntimeError when RQ is unavailable')

    db_session.refresh(scan)
    assert scan.status == 'running'
    events = db_session.query(ScanEvent).filter_by(scan_id=scan.id).all()
    assert any(event.event_type == 'scan.stop_failed' for event in events)


def test_demo_worker_does_not_import_or_call_external_tools():
    import inspect
    import app.workers.v2_scan_jobs as jobs

    source = inspect.getsource(jobs)
    forbidden = ['subprocess', 'os.system', 'netexec', 'nmap', 'impacket', 'kerbrute']
    assert not any(token in source.lower() for token in forbidden)
