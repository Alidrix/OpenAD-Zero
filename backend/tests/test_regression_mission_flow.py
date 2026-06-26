from app.db import models
from app.operations.progress import calculate_progress_score
from app.capabilities.catalog import load_capabilities

def test_demo_mission_flow_regression(db_session, demo_mission):
    assert demo_mission.id
    assert db_session.query(models.MissionObjective).filter_by(mission_id=demo_mission.id).first()
    assert db_session.query(models.MissionPhase).filter_by(mission_id=demo_mission.id).count() >= 10
    assert db_session.query(models.Host).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(models.Service).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(models.Finding).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(models.Evidence).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(models.EvidenceLink).filter_by(mission_id=demo_mission.id).count() > 0
    assert db_session.query(models.Report).filter_by(mission_id=demo_mission.id).first()
    assert calculate_progress_score(db_session, demo_mission.id)['score'] >= 0
    assert db_session.query(models.MissionTimelineEvent).filter_by(mission_id=demo_mission.id).count() > 0
    ids={c.id for c in load_capabilities()}
    for expected in ['nmap_discovery','netexec_smb_safe_enum','nuclei_web_exposure_scan','bloodhound_sharphound_upload','evidence_manager','report_markdown_html','lab_operations_center']:
        assert expected in ids
