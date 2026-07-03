from app.db.models import ParsedSignal, Scan, ScanEvent
from app.recommendations.engine import build_recommendations

def test_parsed_signal_smb_recommends_smb_review(db_session):
    scan=Scan(name='s',scan_type='manual',tool_name='manual'); db_session.add(scan); db_session.flush(); db_session.add(ParsedSignal(scan_id=scan.id,source_type='test',signal='smb_open',value='true',confidence=1.0)); db_session.commit()
    recs=build_recommendations(scan, [], [], db=db_session)
    assert any('smb' in r.template_id.lower() or 'smb' in r.name.lower() for r in recs)

def test_recommendations_fallback_events_still_work(db_session):
    scan=Scan(name='s',scan_type='manual',tool_name='manual'); db_session.add(scan); db_session.flush(); ev=ScanEvent(scan_id=scan.id,event_type='service',message='port 445 smb',payload_json={}); db_session.add(ev); db_session.commit()
    recs=build_recommendations(scan, [ev], [], db=db_session)
    assert recs
