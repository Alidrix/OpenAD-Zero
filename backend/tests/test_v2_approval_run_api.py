from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ApprovedActionRun, OperatorApproval, PentestAction, Scan
from app.db.session import Base, get_db
from app.main import app


class FakeRqJob:
    id = 'approval-run:ap'


class FakeQueue:
    def enqueue(self, *args, **kwargs):
        job = FakeRqJob()
        job.id = kwargs.get('job_id', 'rq')
        return job


def install(monkeypatch):
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
    monkeypatch.setattr('app.approvals.run_service.get_action_queue', lambda: FakeQueue())
    return engine, Session


def seed(Session, status='approved', action_status='approved', template='smb_fingerprint'):
    from app.approvals.service import approve_approval, prepare_approval

    db = Session()
    scan = Scan(id='scan-run', name='scan-run', scan_type='manual', status='draft')
    action = PentestAction(
        scan_id='scan-run',
        phase_id='smb',
        title='SMB',
        description='d',
        reason='r',
        risk_level='low',
        execution_mode='approval_required',
        tool_id='netexec',
        template_id=template,
        required_inputs_json=['target'],
        resolved_inputs_json={'target': '10.0.0.5'},
        missing_inputs_json=[],
        scope_sensitive_params_json={'target': '10.0.0.5'},
        status='proposed',
    )
    db.add_all([scan, action])
    db.commit()
    db.refresh(action)
    ap = prepare_approval(db, 'scan-run', action.id)
    if status in {'approved', 'consumed'}:
        ap = approve_approval(db, 'scan-run', action.id, 'op')
    ap.status = status
    action.status = action_status
    db.commit()
    aid = action.id
    apid = ap.id
    db.close()
    return aid, apid


def test_run_refuses_missing(client, monkeypatch):
    engine, Session = install(monkeypatch)
    try:
        r = client.post('/api/v2/approvals/nope/run', json={'operator': 'op'})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_run_refuses_pending_and_extra_payload(client, monkeypatch):
    engine, Session = install(monkeypatch)
    try:
        _, apid = seed(Session, status='pending', action_status='waiting_approval')
        assert client.post(f'/api/v2/approvals/{apid}/run', json={'operator': 'op'}).status_code == 409
        assert (
            client.post(f'/api/v2/approvals/{apid}/run', json={'operator': 'op', 'command': 'nmap'}).status_code == 422
        )
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_run_enqueues_consumes_and_marks_queued(client, monkeypatch):
    engine, Session = install(monkeypatch)
    try:
        aid, apid = seed(Session)
        r = client.post(f'/api/v2/approvals/{apid}/run', json={'operator': 'op'})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body['status'] == 'queued'
        assert body['rq_job_id'] == f'approval-run:{apid}'
        db = Session()
        assert db.get(OperatorApproval, apid).status == 'consumed'
        assert db.get(PentestAction, aid).status == 'queued'
        assert db.query(ApprovedActionRun).filter_by(approval_id=apid).first().rq_job_id == f'approval-run:{apid}'
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
