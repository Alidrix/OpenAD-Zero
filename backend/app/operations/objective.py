from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import MissionObjective
from app.operations.defaults import OBJECTIVE_STATUSES, OBJECTIVE_TYPES
from app.operations.schemas import MissionObjectiveUpdate


def ensure_default_objective(db: Session, mission_id: str) -> MissionObjective:
    obj = db.query(MissionObjective).filter_by(mission_id=mission_id).first()
    if obj:
        return obj
    obj = MissionObjective(
        mission_id=mission_id,
        objective_name='Identify and document paths to privileged access',
        objective_description=None,
        objective_type='domain_admin_path',
        objective_target='Domain Admins',
        objective_status='not_started',
        operator_note=None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_objective(db: Session, mission_id: str) -> MissionObjective:
    return ensure_default_objective(db, mission_id)


def update_objective(db: Session, mission_id: str, payload: MissionObjectiveUpdate) -> MissionObjective:
    obj = ensure_default_objective(db, mission_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get('objective_type') and data['objective_type'] not in OBJECTIVE_TYPES:
        raise ValueError('Invalid objective type')
    if data.get('objective_status') and data['objective_status'] not in OBJECTIVE_STATUSES:
        raise ValueError('Invalid objective status')
    for k, v in data.items():
        setattr(obj, k, v)
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
