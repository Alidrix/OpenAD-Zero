from pathlib import Path

from app.db.models import ParsedFinding, ParseDiagnostic, Scan
from app.normalization.service import normalize_nuclei_jsonl

FIX = Path(__file__).parent / 'fixtures/normalization/nuclei'


def test_nuclei_valid_malformed_and_idempotence(db_session):
    s = Scan(name='nuc', scan_type='manual', tool_name='nuclei')
    db_session.add(s)
    db_session.commit()
    normalize_nuclei_jsonl(db_session, s.id, FIX / 'sample.jsonl')
    f = db_session.query(ParsedFinding).filter_by(scan_id=s.id).one()
    assert f.severity == 'critical' and 'references' in f.tags_json
    normalize_nuclei_jsonl(db_session, s.id, FIX / 'sample.jsonl')
    assert db_session.query(ParsedFinding).filter_by(scan_id=s.id).count() == 1
    normalize_nuclei_jsonl(db_session, s.id, FIX / 'malformed.jsonl')
    assert db_session.query(ParseDiagnostic).filter_by(message='malformed_nuclei_jsonl_line').count() == 1
