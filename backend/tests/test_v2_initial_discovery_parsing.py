from pathlib import Path

from app.db.models import ParsedAsset, ParsedService, ParsedSignal, Scan, ScanArtifact
from app.parsing.service import parse_persisted_scan

FIX = Path(__file__).parent / 'fixtures' / 'nmap'


def _scan_with_artifact(db, evidence_root, fixture):
    scan = Scan(name='parse', scan_type='initial_discovery', status='draft')
    db.add(scan)
    db.commit()
    db.refresh(scan)
    evidence_root.mkdir(parents=True, exist_ok=True)
    dst = evidence_root / fixture
    dst.write_text((FIX / fixture).read_text(), encoding='utf-8')
    art = ScanArtifact(scan_id=scan.id, artifact_type='nmap_xml', path=str(dst))
    db.add(art)
    db.commit()
    return scan


def test_parse_nmap_fixture_creates_assets_services_and_signals(db_session, isolated_evidence_dir):
    scan = _scan_with_artifact(db_session, isolated_evidence_dir, 'mixed_windows_internal.xml')
    result = parse_persisted_scan(db_session, scan.id)
    assert result.assets_created == 1
    assert db_session.query(ParsedAsset).filter_by(scan_id=scan.id, ip_address='10.0.0.40').first()
    assert db_session.query(ParsedService).filter_by(scan_id=scan.id, port=445).first()
    signals = {s.signal for s in db_session.query(ParsedSignal).filter_by(scan_id=scan.id).all()}
    assert {'smb_detected', 'ldap_detected', 'kerberos_detected', 'http_detected'} <= signals


def test_parse_malformed_xml_creates_diagnostic(db_session, isolated_evidence_dir):
    scan = _scan_with_artifact(db_session, isolated_evidence_dir, 'malformed.xml')
    result = parse_persisted_scan(db_session, scan.id)
    assert result.diagnostics_created == 1
