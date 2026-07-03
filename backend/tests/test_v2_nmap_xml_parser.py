from app.db.models import ParseDiagnostic, ParsedService, ParsedSignal, Scan, ScanArtifact
from app.parsing.service import parse_persisted_scan

def test_nmap_xml_artifact_parses_services_and_signals(db_session, isolated_evidence_dir):
    isolated_evidence_dir.mkdir(parents=True, exist_ok=True); xml=isolated_evidence_dir/'nmap.xml'; xml.write_text('<nmaprun><host><status state="up"/><address addr="10.0.0.7" addrtype="ipv4"/><ports><port protocol="tcp" portid="445"><state state="open"/><service name="microsoft-ds"/></port><port protocol="tcp" portid="80"><state state="open"/><service name="http"/></port></ports></host></nmaprun>')
    scan=Scan(name='s', scan_type='manual', tool_name='manual'); db_session.add(scan); db_session.flush(); db_session.add(ScanArtifact(scan_id=scan.id, artifact_type='nmap_xml', path=str(xml), sha256=None, size_bytes=1)); db_session.commit()
    parse_persisted_scan(db_session, scan.id)
    assert db_session.query(ParsedService).filter_by(scan_id=scan.id).count()==2
    assert {'smb_open','http_open'} <= {r.signal for r in db_session.query(ParsedSignal).filter_by(scan_id=scan.id)}

def test_nmap_xml_invalid_and_missing_are_diagnostics(db_session, isolated_evidence_dir):
    isolated_evidence_dir.mkdir(parents=True, exist_ok=True); bad=isolated_evidence_dir/'bad.xml'; bad.write_text('<no')
    scan=Scan(name='s', scan_type='manual', tool_name='manual'); db_session.add(scan); db_session.flush(); db_session.add_all([ScanArtifact(scan_id=scan.id, artifact_type='nmap', path=str(bad), sha256=None, size_bytes=1), ScanArtifact(scan_id=scan.id, artifact_type='nmap', path=str(isolated_evidence_dir/'missing.xml'), sha256=None, size_bytes=None)]); db_session.commit()
    parse_persisted_scan(db_session, scan.id)
    messages=[d.message for d in db_session.query(ParseDiagnostic).filter_by(scan_id=scan.id)]
    assert any('Invalid Nmap XML' in m for m in messages)
    assert any('does not exist' in m for m in messages)

def test_nmap_parser_does_not_import_subprocess():
    import app.parsing.nmap_xml_parser as parser
    assert 'subprocess' not in parser.__dict__
