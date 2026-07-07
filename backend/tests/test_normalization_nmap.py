from pathlib import Path

from app.db.models import ParsedAsset, ParseDiagnostic, ParsedService, ParsedSignal, Scan
from app.normalization.service import normalize_nmap_xml

FIX = Path(__file__).parent / 'fixtures/normalization/nmap'


def test_nmap_normalization_and_idempotence(db_session):
    s = Scan(name='n', scan_type='manual', tool_name='nmap')
    db_session.add(s)
    db_session.commit()
    r = normalize_nmap_xml(db_session, s.id, FIX / 'sample.xml')
    assert r.assets_created == 1 and db_session.query(ParsedService).filter_by(scan_id=s.id).count() == 3
    assert db_session.query(ParsedSignal).filter_by(scan_id=s.id, signal='smb_detected').count() == 1
    assert db_session.query(ParsedSignal).filter_by(scan_id=s.id, signal='ad_candidate_dc').count() == 1
    normalize_nmap_xml(db_session, s.id, FIX / 'sample.xml')
    assert db_session.query(ParsedAsset).filter_by(scan_id=s.id).count() == 1


def test_nmap_malformed_diagnostic(db_session):
    s = Scan(name='n', scan_type='manual', tool_name='nmap')
    db_session.add(s)
    db_session.commit()
    normalize_nmap_xml(db_session, s.id, FIX / 'malformed.xml')
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='malformed_nmap_xml').count() == 1
