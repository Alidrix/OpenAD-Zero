from app.db.models import ScanEvent
from app.recommendations.engine import build_recommendations
from app.services import scan_service
from app.services.scan_schemas import ScanCreate


def _scan(db_session, event_type: str, message: str):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Signals', scan_type='manual'))
    event = ScanEvent(scan_id=scan.id, event_type=event_type, message=message, payload_json={})
    db_session.add(event)
    db_session.commit()
    return scan, [event]


def test_smb_open_recommends_smb_review(db_session):
    scan, events = _scan(db_session, 'service.detected', 'SMB port 445 open on Windows host')
    recs = build_recommendations(scan, events, [])
    assert any(rec.template_id == 'v2_netexec_smb_fingerprint_preview' for rec in recs)
    assert all(rec.reason and rec.risk_level for rec in recs)


def test_ldap_open_recommends_ldap_review(db_session):
    scan, events = _scan(db_session, 'service.detected', 'LDAP port 389 open')
    recs = build_recommendations(scan, events, [])
    assert any(rec.template_id == 'v2_ldap_review_preview' for rec in recs)


def test_scan_without_signal_has_no_recommendations(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='No signal', scan_type='manual'))
    assert build_recommendations(scan, [], []) == []
