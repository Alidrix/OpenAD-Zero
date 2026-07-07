from pathlib import Path

from app.db.models import ParsedCredentialRisk, ParsedFinding, Scan
from app.normalization.service import normalize_netexec_smb, normalize_nuclei_jsonl

FIX = Path(__file__).parent / 'fixtures/normalization'


def test_cross_normalizers_idempotent(db_session):
    s = Scan(name='idem', scan_type='manual', tool_name='x')
    db_session.add(s)
    db_session.commit()
    for _ in range(2):
        normalize_nuclei_jsonl(db_session, s.id, FIX / 'nuclei/sample.jsonl')
        normalize_netexec_smb(db_session, s.id, FIX / 'netexec/smb.log')
    assert db_session.query(ParsedFinding).filter_by(scan_id=s.id, title='Demo CVE').count() == 1
    assert db_session.query(ParsedCredentialRisk).filter_by(scan_id=s.id, risk_type='null_session').count() == 1
