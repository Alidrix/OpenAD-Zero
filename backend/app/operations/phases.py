from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import MissionPhase
from app.operations.defaults import DEFAULT_PHASES, PHASE_STATUSES


def ensure_default_phases(db: Session, mission_id: str) -> list[MissionPhase]:
    existing = db.query(MissionPhase).filter_by(mission_id=mission_id).all()
    keys = {p.phase_key for p in existing}
    for item in DEFAULT_PHASES:
        if item['phase_key'] not in keys:
            db.add(MissionPhase(mission_id=mission_id, status='pending', **item))
    db.commit()
    return get_phases(db, mission_id)


def get_phases(db: Session, mission_id: str) -> list[MissionPhase]:
    return db.query(MissionPhase).filter_by(mission_id=mission_id).order_by(MissionPhase.order_index.asc()).all()


def update_phase_status(
    db: Session, mission_id: str, phase_key: str, status: str, summary: str | None = None
) -> MissionPhase | None:
    if status not in PHASE_STATUSES:
        raise ValueError('Invalid phase status')
    phase = db.query(MissionPhase).filter_by(mission_id=mission_id, phase_key=phase_key).first()
    if not phase:
        return None
    now = datetime.utcnow()
    phase.status = status
    phase.updated_at = now
    if summary is not None:
        phase.summary = summary
    if status == 'running' and not phase.started_at:
        phase.started_at = now
    if status == 'completed':
        if not phase.started_at:
            phase.started_at = now
        phase.completed_at = now
    db.commit()
    db.refresh(phase)
    return phase


def mark_phase_completed(
    db: Session, mission_id: str, phase_key: str, summary: str | None = None
) -> MissionPhase | None:
    return update_phase_status(db, mission_id, phase_key, 'completed', summary)
