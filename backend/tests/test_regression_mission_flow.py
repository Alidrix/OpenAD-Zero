from app.db.models import Host, Finding, Evidence, EvidenceLink, Report
from app.operations.progress import calculate_progress_score
from app.operations.timeline import list_timeline_events


def test_complete_demo_mission_flow(client, db_session, demo_mission, demo_finding, demo_evidence):
    assert demo_mission.id
    assert db_session.query(Host).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(Finding).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(Evidence).filter_by(mission_id=demo_mission.id).count() > 0
    link=EvidenceLink(mission_id=demo_mission.id,evidence_id=demo_evidence.id,target_type='finding',target_id=demo_finding.id)
    db_session.add(link); db_session.commit()
    report=client.post(f'/api/missions/{demo_mission.id}/report/generate').json()
    assert report['status'] == 'generated'
    assert db_session.query(Report).filter_by(mission_id=demo_mission.id).count() > 0
    assert calculate_progress_score(db_session, demo_mission.id)['score'] >= 0
    assert list_timeline_events(db_session, demo_mission.id)
    caps=client.get('/api/capabilities').json()
    blob=str(caps).lower()
    for name in ['nmap','netexec','nuclei','bloodhound','evidence','report','lab']:
        assert name in blob
