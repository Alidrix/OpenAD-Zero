from app.db.models import Scan, ScanEvent, ParsedSignal, ParsedService, ParsedAsset
from app.parsing.service import parse_persisted_scan

def test_generic_event_payload_signals_and_ports_are_idempotent(db_session):
    scan=Scan(name='s', scan_type='manual', tool_name='manual'); db_session.add(scan); db_session.flush()
    db_session.add_all([
        ScanEvent(scan_id=scan.id,event_type='service',message='structured',payload_json={'ip':'10.0.0.5','hostname':'host1','port':445,'protocol':'tcp','service':'smb','signals':['smb_open']}),
        ScanEvent(scan_id=scan.id,event_type='service',message='structured',payload_json={'ip':'10.0.0.6','port':389,'protocol':'tcp','service':'ldap'}),
    ]); db_session.commit()
    parse_persisted_scan(db_session, scan.id); parse_persisted_scan(db_session, scan.id)
    assert db_session.query(ParsedAsset).filter_by(scan_id=scan.id).count()==2
    assert db_session.query(ParsedService).filter_by(scan_id=scan.id).count()==2
    signals={r.signal for r in db_session.query(ParsedSignal).filter_by(scan_id=scan.id)}
    assert {'smb_open','ldap_open','host_discovered'} <= signals
