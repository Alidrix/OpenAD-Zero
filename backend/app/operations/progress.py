from sqlalchemy.orm import Session

from app.db.models import (
    BloodHoundCollection,
    Evidence,
    Finding,
    Host,
    MissionPhase,
    Report,
    Service,
    SMBFact,
    SMBShare,
    WebTarget,
)

PHASE_KEYS = [
    'scope_validation',
    'network_discovery',
    'service_enumeration',
    'smb_enrichment',
    'web_exposure_scan',
    'active_directory_collection',
    'bloodhound_analysis',
    'pathfinding',
    'evidence_consolidation',
    'reporting',
]


def _level(score: int) -> str:
    if score == 100:
        return 'complete'
    if score >= 81:
        return 'nearly_complete'
    if score >= 51:
        return 'advanced'
    if score >= 21:
        return 'in_progress'
    return 'initialized'


def calculate_progress_score(db: Session, mission_id: str) -> dict:
    counts = {
        'hosts': db.query(Host).filter_by(mission_id=mission_id).count(),
        'services': db.query(Service).filter_by(mission_id=mission_id).count(),
        'smb_facts': db.query(SMBFact).filter_by(mission_id=mission_id).count(),
        'smb_shares': db.query(SMBShare).filter_by(mission_id=mission_id).count(),
        'web_targets': db.query(WebTarget).filter_by(mission_id=mission_id).count(),
        'evidence': db.query(Evidence).filter_by(mission_id=mission_id).count(),
        'reports': db.query(Report).filter_by(mission_id=mission_id).count(),
        'findings': db.query(Finding).filter_by(mission_id=mission_id).count(),
        'valid_bh': db.query(BloodHoundCollection).filter_by(mission_id=mission_id, zip_valid=True).count(),
    }
    phases = {p.phase_key: p for p in db.query(MissionPhase).filter_by(mission_id=mission_id).all()}
    completed = set(k for k, p in phases.items() if p.status == 'completed')
    if counts['hosts'] > 0:
        completed.add('network_discovery')
    if counts['services'] > 0:
        completed.add('service_enumeration')
    if counts['smb_facts'] > 0 or counts['smb_shares'] > 0:
        completed.add('smb_enrichment')
    if counts['web_targets'] > 0 and db.query(Finding).filter_by(mission_id=mission_id, source='nuclei').count() > 0:
        completed.add('web_exposure_scan')
    if counts['valid_bh'] > 0:
        completed.add('active_directory_collection')
    if db.query(Finding).filter_by(mission_id=mission_id, source='bloodhound').count() > 0:
        completed.add('bloodhound_analysis')
    if (
        db.query(Finding)
        .filter(Finding.mission_id == mission_id, Finding.source == 'bloodhound', Finding.title.ilike('%path%'))
        .count()
        > 0
    ):
        completed.add('pathfinding')
    if counts['evidence'] > 0:
        completed.add('evidence_consolidation')
    if counts['reports'] > 0:
        completed.add('reporting')
    ordered = [k for k in PHASE_KEYS if k in completed]
    missing = [k for k in PHASE_KEYS if k not in completed]
    score = len(ordered) * 10
    return {
        'score': score,
        'level': _level(score),
        'completed_items': ordered,
        'missing_items': missing,
        'details': {'counts': counts, 'phase_statuses': {k: p.status for k, p in phases.items()}},
    }
