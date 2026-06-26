from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Evidence, Finding, Host, Mission, MissionPhase, Report, Service
from app.db.session import get_db
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.operations.objective import get_objective, update_objective
from app.operations.phases import ensure_default_phases, get_phases, update_phase_status
from app.operations.progress import calculate_progress_score
from app.operations.schemas import (
    MissionObjectiveResponse,
    MissionObjectiveUpdate,
    MissionPhaseResponse,
    MissionPhaseUpdate,
    ProgressScoreResponse,
    TimelineEventCreate,
    TimelineEventResponse,
)
from app.operations.service import initialize_operations_for_mission, sync_operations_from_current_data
from app.operations.timeline import create_timeline_event, list_timeline_events

router = APIRouter(prefix='/missions')


def _mission(db, mission_id):
    if not db.get(Mission, mission_id):
        raise HTTPException(404, 'Mission not found')


@router.get('/{mission_id}/objective', response_model=MissionObjectiveResponse)
def objective(mission_id: str, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    return get_objective(db, mission_id)


@router.patch('/{mission_id}/objective', response_model=MissionObjectiveResponse)
def patch_objective(mission_id: str, payload: MissionObjectiveUpdate, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    try:
        return update_objective(db, mission_id, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get('/{mission_id}/phases', response_model=list[MissionPhaseResponse])
def phases(mission_id: str, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    return ensure_default_phases(db, mission_id)


@router.patch('/{mission_id}/phases/{phase_id}', response_model=MissionPhaseResponse)
async def patch_phase(mission_id: str, phase_id: str, payload: MissionPhaseUpdate, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    p = db.get(MissionPhase, phase_id)
    if not p or p.mission_id != mission_id:
        raise HTTPException(404, 'Phase not found')
    try:
        p = update_phase_status(db, mission_id, p.phase_key, payload.status or p.status, payload.summary)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await publish(
        MissionEvent(
            type='phase.updated', mission_id=mission_id, payload={'phase_key': p.phase_key, 'status': p.status}
        )
    )
    return p


@router.get('/{mission_id}/timeline', response_model=list[TimelineEventResponse])
def timeline(
    mission_id: str,
    source: str | None = None,
    severity: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _mission(db, mission_id)
    try:
        return list_timeline_events(db, mission_id, source, severity, limit)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post('/{mission_id}/timeline', response_model=TimelineEventResponse)
async def post_timeline(mission_id: str, payload: TimelineEventCreate, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    try:
        ev = create_timeline_event(db, mission_id, payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    await publish(
        MissionEvent(
            type='timeline.event.created',
            mission_id=mission_id,
            payload={'event_type': ev.event_type, 'title': ev.title},
        )
    )
    return ev


@router.get('/{mission_id}/progress', response_model=ProgressScoreResponse)
def progress(mission_id: str, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    return calculate_progress_score(db, mission_id)


@router.get('/{mission_id}/operations/summary')
def summary(mission_id: str, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    initialize_operations_for_mission(db, mission_id)
    return {
        'objective': get_objective(db, mission_id),
        'phases': get_phases(db, mission_id),
        'progress': calculate_progress_score(db, mission_id),
        'recent_timeline': list_timeline_events(db, mission_id, limit=10),
        'counts': {
            'hosts': db.query(Host).filter_by(mission_id=mission_id).count(),
            'services': db.query(Service).filter_by(mission_id=mission_id).count(),
            'findings': db.query(Finding).filter_by(mission_id=mission_id).count(),
            'evidence': db.query(Evidence).filter_by(mission_id=mission_id).count(),
            'reports': db.query(Report).filter_by(mission_id=mission_id).count(),
        },
    }


@router.post('/{mission_id}/operations/sync', response_model=ProgressScoreResponse)
async def sync(mission_id: str, db: Session = Depends(get_db)):
    _mission(db, mission_id)
    score = sync_operations_from_current_data(db, mission_id)
    await publish(
        MissionEvent(
            type='operations.updated', mission_id=mission_id, payload={'score': score['score'], 'level': score['level']}
        )
    )
    return score
