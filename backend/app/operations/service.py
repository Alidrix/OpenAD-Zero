import logging

from sqlalchemy.orm import Session

from app.db.models import MissionTimelineEvent
from app.operations.objective import ensure_default_objective
from app.operations.phases import ensure_default_phases, mark_phase_completed
from app.operations.progress import calculate_progress_score
from app.operations.schemas import TimelineEventCreate
from app.operations.timeline import create_timeline_event

log = logging.getLogger(__name__)


def _event_once(
    db: Session, mission_id: str, event_type: str, title: str, source: str = 'system', severity: str = 'info', **rels
):
    q = db.query(MissionTimelineEvent).filter_by(mission_id=mission_id, event_type=event_type)
    for k, v in rels.items():
        if v is not None and hasattr(MissionTimelineEvent, k):
            q = q.filter(getattr(MissionTimelineEvent, k) == v)
    if q.first():
        return None
    return create_timeline_event(
        db,
        mission_id,
        TimelineEventCreate(event_type=event_type, title=title, source=source, severity=severity, **rels),
    )


def initialize_operations_for_mission(db: Session, mission_id: str) -> None:
    ensure_default_objective(db, mission_id)
    ensure_default_phases(db, mission_id)
    _event_once(db, mission_id, 'mission.created', 'Mission created')


def sync_operations_from_current_data(db: Session, mission_id: str) -> dict:
    ensure_default_phases(db, mission_id)
    score = calculate_progress_score(db, mission_id)
    labels = {
        'network_discovery': 'Nmap discovery completed',
        'service_enumeration': 'Service enumeration completed',
        'smb_enrichment': 'NetExec SMB enrichment completed',
        'web_exposure_scan': 'Nuclei web exposure scan completed',
        'active_directory_collection': 'BloodHound collection uploaded and validated',
        'bloodhound_analysis': 'BloodHound analysis completed',
        'pathfinding': 'BloodHound pathfinding detected a path',
        'evidence_consolidation': 'Evidence imported',
        'reporting': 'Report generated',
    }
    sources = {
        'network_discovery': 'nmap',
        'service_enumeration': 'nmap',
        'smb_enrichment': 'netexec',
        'web_exposure_scan': 'nuclei',
        'active_directory_collection': 'bloodhound',
        'bloodhound_analysis': 'bloodhound',
        'pathfinding': 'bloodhound',
        'evidence_consolidation': 'evidence',
        'reporting': 'report',
    }
    for key in score['completed_items']:
        if key != 'scope_validation':
            mark_phase_completed(db, mission_id, key, 'Completed from current mission data.')
        if key in labels:
            _event_once(db, mission_id, key + '.completed', labels[key], sources[key], 'success')
    return calculate_progress_score(db, mission_id)


def safe_sync(db: Session, mission_id: str):
    try:
        return sync_operations_from_current_data(db, mission_id)
    except Exception:
        log.exception('operations sync failed for %s', mission_id)
        return None
