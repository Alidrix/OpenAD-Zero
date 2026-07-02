from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import scan_orchestrator, scan_service
from app.services.scan_schemas import (
    ScanArtifactRead,
    ScanCreate,
    ScanEventRead,
    ScanListItem,
    ScanRead,
    ScanRename,
)

router = APIRouter(prefix='/v2/scans', tags=['v2-scans'])


def _scan_or_404(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.post('', response_model=ScanRead, status_code=201)
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)):
    # V2 creates scans as draft: no tool is executed until a future explicit, human-approved workflow promotes it.
    return scan_orchestrator.create_manual_scan(db, payload)


@router.get('', response_model=list[ScanListItem])
def list_scans(include_deleted: bool = Query(False), db: Session = Depends(get_db)):
    return scan_service.list_scans(db, include_deleted=include_deleted)


@router.get('/{scan_id}', response_model=ScanRead)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    return _scan_or_404(db, scan_id)


@router.patch('/{scan_id}/rename', response_model=ScanRead)
def rename_scan(scan_id: str, payload: ScanRename, db: Session = Depends(get_db)):
    scan = scan_service.rename_scan(db, scan_id, payload.name)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.post('/{scan_id}/stop', response_model=ScanRead)
def stop_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = scan_orchestrator.request_scan_stop(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.delete('/{scan_id}', response_model=ScanRead)
def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = scan_service.soft_delete_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.get('/{scan_id}/events', response_model=list[ScanEventRead])
def list_scan_events(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(scan_service.ScanEvent).filter_by(scan_id=scan_id).order_by(scan_service.ScanEvent.created_at.asc()).all()


@router.get('/{scan_id}/artifacts', response_model=list[ScanArtifactRead])
def list_scan_artifacts(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(scan_service.ScanArtifact).filter_by(scan_id=scan_id).order_by(scan_service.ScanArtifact.created_at.asc()).all()
