from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.parameter_validation import ParameterValidationError
from app.db.models import Mission, ScanEvent
from app.db.session import get_db
from app.events.scan_websocket_manager import scan_ws_manager, serialize_scan_event
from app.queue.connection import get_scan_queue
from app.scanning.initial_discovery import (
    SAFE_INITIAL_DISCOVERY_PROFILE,
    validate_initial_discovery_profile,
    validate_initial_discovery_targets,
)
from app.services import scan_orchestrator, scan_service
from app.services.scan_schemas import (
    ScanArtifactRead,
    ScanCreate,
    ScanEventRead,
    ScanListItem,
    ScanRead,
    ScanRename,
)
from app.workers.initial_discovery_jobs import run_initial_discovery_scan

router = APIRouter(prefix='/v2/scans', tags=['v2-scans'])


class InitialDiscoveryStart(BaseModel):
    model_config = ConfigDict(extra='forbid')

    profile: str = SAFE_INITIAL_DISCOVERY_PROFILE


def _validated_scan_scope(db: Session, scan) -> list[str]:
    if not scan.mission_id:
        raise HTTPException(status_code=409, detail='Scan is not attached to a validated mission scope')
    mission = db.get(Mission, scan.mission_id)
    if mission is None or not mission.validated_targets:
        raise HTTPException(status_code=409, detail='No validated scope is available for this scan')
    try:
        return validate_initial_discovery_targets(list(mission.validated_targets))
    except ParameterValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _broadcast_latest_scan_event(db: Session, scan) -> None:
    event = db.query(ScanEvent).filter_by(scan_id=scan.id).order_by(ScanEvent.created_at.desc()).first()
    if event is None:
        return
    try:
        await scan_ws_manager.broadcast(scan.id, serialize_scan_event(event, scan))
    except Exception:
        return


def _scan_or_404(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.post('', response_model=ScanRead, status_code=201)
async def create_scan(payload: ScanCreate, db: Session = Depends(get_db)):
    # V2 creates scans as draft: no tool is executed until a future explicit, human-approved workflow promotes it.
    scan = scan_orchestrator.create_manual_scan(db, payload)
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.get('', response_model=list[ScanListItem])
def list_scans(include_deleted: bool = Query(False), db: Session = Depends(get_db)):
    return scan_service.list_scans(db, include_deleted=include_deleted)


@router.get('/{scan_id}', response_model=ScanRead)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    return _scan_or_404(db, scan_id)


@router.patch('/{scan_id}/rename', response_model=ScanRead)
async def rename_scan(scan_id: str, payload: ScanRename, db: Session = Depends(get_db)):
    scan = scan_service.rename_scan(db, scan_id, payload.name)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.post('/{scan_id}/start-initial-discovery', response_model=ScanRead)
async def start_initial_discovery(scan_id: str, payload: InitialDiscoveryStart, db: Session = Depends(get_db)):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    if scan.status == 'deleted' or scan.deleted_at is not None:
        raise HTTPException(status_code=409, detail='deleted scans cannot be queued')
    if scan.status in scan_orchestrator.ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail='scan is already active')
    try:
        validate_initial_discovery_profile(payload.profile)
        _validated_scan_scope(db, scan)
    except ParameterValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        queue = get_scan_queue()
        job = queue.enqueue(run_initial_discovery_scan, scan_id, job_timeout=3600, result_ttl=86400, failure_ttl=86400)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    scan.status = 'queued'
    scan.rq_job_id = job.id
    scan.progress_percent = 0
    scan.current_step = 'Initial discovery queued'
    scan_service.add_scan_event(
        db,
        scan.id,
        'scan.initial_discovery_queued',
        'Initial discovery queued',
        {'scan_id': scan.id, 'progress_percent': 0, 'current_step': scan.current_step, 'rq_job_id': job.id},
    )
    db.commit()
    db.refresh(scan)
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.post('/{scan_id}/enqueue-demo', response_model=ScanRead)
async def enqueue_demo_scan(scan_id: str, db: Session = Depends(get_db)):
    try:
        scan = scan_orchestrator.enqueue_demo_scan(db, scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.post('/{scan_id}/stop', response_model=ScanRead)
async def stop_scan(scan_id: str, db: Session = Depends(get_db)):
    try:
        scan = scan_orchestrator.request_scan_stop(db, scan_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.delete('/{scan_id}', response_model=ScanRead)
async def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = scan_service.soft_delete_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    await _broadcast_latest_scan_event(db, scan)
    return scan


@router.get('/{scan_id}/events', response_model=list[ScanEventRead])
def list_scan_events(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return (
        db.query(scan_service.ScanEvent)
        .filter_by(scan_id=scan_id)
        .order_by(scan_service.ScanEvent.created_at.asc())
        .all()
    )


@router.get('/{scan_id}/artifacts', response_model=list[ScanArtifactRead])
def list_scan_artifacts(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return (
        db.query(scan_service.ScanArtifact)
        .filter_by(scan_id=scan_id)
        .order_by(scan_service.ScanArtifact.created_at.asc())
        .all()
    )
