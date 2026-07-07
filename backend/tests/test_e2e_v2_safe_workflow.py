from pathlib import Path
from types import SimpleNamespace

from app.approvals.run_service import enqueue_approved_action_run
from app.approvals.service import approve_approval, prepare_approval
from app.db.models import (
    ApprovedActionRun,
    Mission,
    OperatorApproval,
    ParsedAsset,
    ParsedService,
    ParsedSignal,
    PentestAction,
    Scan,
    ScanEvent,
)
from app.normalization.service import normalize_nmap_xml
from app.pentest.orchestrator import PentestOrchestrator
from app.workers import approved_action_jobs


class FakeRqJob:
    def __init__(self, job_id):
        self.id = job_id


class FakeQueue:
    def enqueue(self, *args, **kwargs):
        return FakeRqJob(kwargs['job_id'])


def test_v2_safe_workflow_fixture_to_approved_run(db_session, tmp_path, monkeypatch):
    mission = Mission(
        name='Private lab mission',
        scenario='local-ad-lab',
        mode='safe',
        raw_scope='10.0.0.0/24',
        validated_targets=['10.0.0.0/24'],
        scope={'cidrs': ['10.0.0.0/24']},
        client_name='local-lab',
    )
    scan = Scan(id='safe-e2e-scan', mission_id=mission.id, name='safe-e2e', scan_type='manual', tool_name='nmap')
    db_session.add_all([mission, scan])
    db_session.commit()

    fixture = tmp_path / 'nmap-safe-e2e.xml'
    fixture.write_text(
        '<nmaprun><host><status state="up"/><address addr="10.0.0.10" addrtype="ipv4"/>'
        '<hostnames><hostname name="dc1.example.local"/></hostnames><ports>'
        '<port protocol="tcp" portid="80"><state state="open"/><service name="http" product="IIS"/></port>'
        '<port protocol="tcp" portid="445"><state state="open"/><service name="microsoft-ds" product="Windows SMB"/></port>'
        '<port protocol="tcp" portid="88"><state state="open"/><service name="kerberos"/></port>'
        '<port protocol="tcp" portid="389"><state state="open"/><service name="ldap" '
        'product="Microsoft Windows Active Directory LDAP"/></port>'
        '</ports></host></nmaprun>'
    )

    result = normalize_nmap_xml(db_session, scan.id, fixture)
    assert result.assets_created == 1
    assert db_session.query(ParsedAsset).filter_by(scan_id=scan.id, ip_address='10.0.0.10').count() == 1
    assert db_session.query(ParsedService).filter_by(scan_id=scan.id).count() == 4
    signals = {row.signal for row in db_session.query(ParsedSignal).filter_by(scan_id=scan.id).all()}
    assert {'smb_detected', 'http_detected', 'ad_candidate_dc'} <= signals

    state = PentestOrchestrator(db_session).recompute(scan.id)
    titles = {action.title for action in state.recommended_actions}
    assert any('SMB' in title for title in titles)
    assert any('Nuclei' in title for title in titles)
    assert any('LDAP' in title or 'Kerberos' in title for title in titles)

    action = (
        db_session.query(PentestAction)
        .filter_by(scan_id=scan.id, tool_id='netexec', template_id='smb_fingerprint')
        .first()
    )
    assert action is not None
    action.resolved_inputs_json = {'target': '10.0.0.10'}
    action.required_inputs_json = ['target']
    action.scope_sensitive_params_json = {'target': '10.0.0.10', 'validated_scope': ['10.0.0.0/24']}
    db_session.commit()

    approval = prepare_approval(db_session, scan.id, action.id)
    approval = approve_approval(db_session, scan.id, action.id, operator='qa')
    assert approval.status == 'approved'

    monkeypatch.setattr('app.approvals.run_service.get_action_queue', lambda: FakeQueue())
    run = enqueue_approved_action_run(db_session, approval.id, operator='qa')
    assert run.status == 'queued'
    assert db_session.get(OperatorApproval, approval.id).status == 'consumed'
    assert db_session.get(PentestAction, action.id).status == 'queued'

    class NoCloseSession:
        def __getattr__(self, name):
            return getattr(db_session, name)

        def close(self):
            pass

    def fake_run_process(argv, cwd, env, timeout_seconds, stdout_path, stderr_path, **kwargs):
        assert isinstance(argv, list)
        assert 'shell=True' not in ' '.join(argv)
        Path(stdout_path).write_text('SMB 10.0.0.10 445 DC1 signing:True SMBv1:False\n')
        Path(stderr_path).write_text('token=***REDACTED***\n')
        return SimpleNamespace(
            status='completed',
            return_code=0,
            error_message=None,
            duration_seconds=0.01,
            stdout_tail='SMB 10.0.0.10 445 DC1 signing:True SMBv1:False',
            stderr_tail='token=***REDACTED***',
        )

    monkeypatch.setattr(approved_action_jobs, 'SessionLocal', lambda: NoCloseSession())
    monkeypatch.setattr(approved_action_jobs, 'run_process', fake_run_process)
    approved_action_jobs.run_approved_action(approval.id)

    completed = db_session.query(ApprovedActionRun).filter_by(approval_id=approval.id).one()
    assert completed.status == 'completed'
    assert db_session.get(PentestAction, action.id).status == 'completed'
    event_types = {event.event_type for event in db_session.query(ScanEvent).filter_by(scan_id=scan.id).all()}
    assert {'approval.run_queued', 'approved_action.completed', 'normalization.completed'} <= event_types
    assert (
        not db_session.query(PentestAction)
        .filter(PentestAction.risk_level.in_(['high', 'critical']))
        .filter_by(status='completed')
        .count()
    )
