from pathlib import Path

from app.db.models import ParsedADObject, ParsedCredentialRisk, ParseDiagnostic, Scan
from app.normalization.service import normalize_adcs_output, normalize_kerberos_output, normalize_ldap_output

FIX = Path(__file__).parent / 'fixtures/normalization'


def test_ldap_parsed_json_and_text_diagnostic(db_session, tmp_path):
    s = Scan(name='ldap', scan_type='manual', tool_name='ldap')
    db_session.add(s)
    db_session.commit()
    normalize_ldap_output(db_session, s.id, FIX / 'ldap/sample.json')
    assert db_session.query(ParsedADObject).filter_by(scan_id=s.id).count() == 1
    assert db_session.query(ParsedCredentialRisk).filter_by(scan_id=s.id, risk_type='weak_password_policy').count() == 1
    t = tmp_path / 'x.txt'
    t.write_text('unsupported')
    normalize_kerberos_output(db_session, s.id, t)
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='parser_not_implemented').count() == 1


def test_adcs_json_supported(db_session):
    s = Scan(name='adcs', scan_type='manual', tool_name='adcs')
    db_session.add(s)
    db_session.commit()
    normalize_adcs_output(db_session, s.id, FIX / 'adcs/sample.json')
    assert db_session.query(ParsedADObject).filter_by(scan_id=s.id).count() == 1
