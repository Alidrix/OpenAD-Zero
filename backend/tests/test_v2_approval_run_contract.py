from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import ApprovedActionRun, OperatorApproval, PentestAction, Scan
from app.db.session import Base, get_db
from app.main import app


class _FakeJob:
    id = 'rq'


class _FakeQueue:
    def enqueue(self, *args, **kwargs):
        job = _FakeJob()
        job.id = kwargs.get('job_id', 'rq')
        return job


def _install(monkeypatch):
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


def _seed(Session):
    db = Session()
    scan = Scan(id='scan-run', name='scan-run', scan_type='manual', status='draft')
    action = PentestAction(
        scan_id='scan-run',
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
    return action.id


def test_run_contract_queues_without_raw_frontend_command(client, monkeypatch):
    engine, Session = _install(monkeypatch)
    monkeypatch.setattr('app.approvals.run_service.get_action_queue', lambda: _FakeQueue())
    try:
        action_id = _seed(Session)
        prep = client.post(f'/api/v2/scans/scan-run/pentest/actions/{action_id}/approval/prepare', json={}).json()
        client.post(f'/api/v2/scans/scan-run/pentest/actions/{action_id}/approval/approve', json={'operator': 'op'})
        response = client.post(f'/api/v2/approvals/{prep["id"]}/run', json={'operator': 'op'})
        assert response.status_code == 200
        assert response.json()['rq_job_id'] == f'approval-run:{prep["id"]}'
        db = Session()
        approval = db.get(OperatorApproval, prep['id'])
        action = db.get(PentestAction, action_id)
        run = db.query(ApprovedActionRun).filter_by(approval_id=prep['id']).first()
        assert run is not None
        assert approval.status == 'consumed'
        assert approval.consumed_at is not None
        assert action.status == 'queued'
        db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
