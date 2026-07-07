from pathlib import Path

from app.db.models import ParsedCredentialRisk, ParsedFinding, ParseDiagnostic, ParsedSignal, Scan
from app.normalization.service import normalize_netexec_smb

FIX = Path(__file__).parent / 'fixtures/normalization/netexec'


def test_netexec_smb_risks(db_session):
    s = Scan(name='nxc', scan_type='manual', tool_name='netexec')
    db_session.add(s)
    db_session.commit()
    normalize_netexec_smb(db_session, s.id, FIX / 'smb.log')
    assert db_session.query(ParsedSignal).filter_by(scan_id=s.id, signal='smb_signing_disabled').count() >= 1
    assert db_session.query(ParsedFinding).filter_by(scan_id=s.id).count() >= 2
    assert db_session.query(ParsedCredentialRisk).filter_by(scan_id=s.id, risk_type='null_session').count() == 1


def test_netexec_empty(db_session):
    s = Scan(name='nxc', scan_type='manual', tool_name='netexec')
    db_session.add(s)
    db_session.commit()
    normalize_netexec_smb(db_session, s.id, FIX / 'empty.log')
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='empty_netexec_output').count() == 1
