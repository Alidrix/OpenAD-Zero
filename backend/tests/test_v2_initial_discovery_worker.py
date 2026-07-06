from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Mission, ParsedSignal, PentestAction, Scan, ScanArtifact, ScanEvent
from app.db.session import Base
from app.jobs.runner import CommandResult
from app.scanning.initial_discovery import build_safe_nmap_command

FIX = Path(__file__).parent / 'fixtures' / 'nmap' / 'mixed_windows_internal.xml'


def _engine_session():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _seed(Session):
    db = Session()
    mission = Mission(name='m', scenario='s', mode='safe', raw_scope='10.0.0.0/24', validated_targets=['10.0.0.0/24'])
    db.add(mission)
    db.commit()
    db.refresh(mission)
    scan = Scan(name='s', scan_type='initial_discovery', status='queued', mission_id=mission.id, rq_job_id='rq1')
    db.add(scan)
    db.commit()
    db.refresh(scan)
    sid = scan.id
    db.close()
    return sid


def test_worker_runs_nmap_parse_recompute_and_completes(monkeypatch, isolated_evidence_dir):
    from app.workers import initial_discovery_jobs as worker

    engine, Session = _engine_session()
    scan_id = _seed(Session)
    monkeypatch.setattr(worker, 'SessionLocal', Session)
    called = {}

    async def fake_run(tool, args, cwd, stdout_path, stderr_path, mission_id, job_id, timeout):
        assert tool == 'nmap'
        assert args[:4] == ['-Pn', '-sV', '--top-ports', '1000']
        assert '-A' not in args and '--script' not in args and '-sU' not in args
        Path(stdout_path).write_text('ok')
        Path(stderr_path).write_text('')
        Path(args[args.index('-oX') + 1]).write_text(FIX.read_text())
        called['run'] = True
        return CommandResult(0)

    monkeypatch.setattr(worker, 'run_command', fake_run)
    worker.run_initial_discovery_scan(scan_id)
    db = Session()
    scan = db.get(Scan, scan_id)
    assert scan.status == 'completed'
    assert scan.progress_percent == 100
    artifact = db.query(ScanArtifact).filter_by(scan_id=scan_id, artifact_type='nmap_xml').first()
    assert artifact and Path(artifact.path).resolve().is_relative_to(isolated_evidence_dir.resolve())
    assert (isolated_evidence_dir / 'initial-discovery' / scan_id / 'stdout.log').exists()
    signals = {s.signal for s in db.query(ParsedSignal).filter_by(scan_id=scan_id).all()}
    assert {'smb_detected', 'http_detected', 'ldap_detected', 'kerberos_detected'} <= signals
    titles = {a.title for a in db.query(PentestAction).filter_by(scan_id=scan_id).all()}
    assert {'NetExec SMB fingerprint', 'LDAP/Kerberos enumeration', 'Nuclei safe templates'} <= titles
    assert db.query(ScanEvent).filter_by(scan_id=scan_id, event_type='scan.initial_discovery_completed').first()
    db.close()
    Base.metadata.drop_all(engine)


def test_worker_nmap_failure_marks_failed(monkeypatch, isolated_evidence_dir):
    from app.workers import initial_discovery_jobs as worker

    engine, Session = _engine_session()
    scan_id = _seed(Session)
    monkeypatch.setattr(worker, 'SessionLocal', Session)

    async def fake_run(*args, **kwargs):
        return CommandResult(127)

    monkeypatch.setattr(worker, 'run_command', fake_run)
    worker.run_initial_discovery_scan(scan_id)
    db = Session()
    scan = db.get(Scan, scan_id)
    assert scan.status == 'failed'
    assert db.query(ScanEvent).filter_by(scan_id=scan_id, event_type='scan.initial_discovery_failed').first()
    db.close()
    Base.metadata.drop_all(engine)


def test_safe_builder_refuses_output_outside_evidence(isolated_evidence_dir):
    cmd = build_safe_nmap_command(targets=['10.0.0.0/24'], job_dir=isolated_evidence_dir / 'job')
    assert cmd.tool == 'nmap'
    assert '-oX' in cmd.args
    assert '--script' not in cmd.args and '-A' not in cmd.args
