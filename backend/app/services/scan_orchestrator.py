from datetime import datetime

from sqlalchemy.orm import Session

from app.services import scan_service
from app.services.scan_schemas import ScanCreate


def create_manual_scan(db: Session, payload: ScanCreate):
    return scan_service.create_scan(db, payload)


def mark_scan_queued(db: Session, scan_id: str, rq_job_id: str | None = None):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    scan.status = 'queued'
    scan.rq_job_id = rq_job_id
    scan_service.add_scan_event(db, scan_id, 'scan.queued', 'Scan marked queued', {'rq_job_id': rq_job_id})
    db.commit()
    db.refresh(scan)
    return scan


def mark_scan_running(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    scan.status = 'running'
    scan.started_at = scan.started_at or datetime.utcnow()
    scan_service.add_scan_event(db, scan_id, 'scan.running', 'Scan marked running')
    db.commit()
    db.refresh(scan)
    return scan


def mark_scan_completed(db: Session, scan_id: str):
    return scan_service.update_scan_progress(db, scan_id, 100, status='completed')


def mark_scan_failed(db: Session, scan_id: str, message: str = 'Scan failed'):
    scan = scan_service.update_scan_progress(db, scan_id, 0, status='failed')
    if scan is not None:
        scan.finished_at = datetime.utcnow()
        scan_service.add_scan_event(db, scan_id, 'scan.failed', message)
        db.commit()
        db.refresh(scan)
    return scan


def request_scan_stop(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    if scan.rq_job_id:
        # TODO: wire this to the future RQ stop/cancel control path without exposing raw commands to the frontend.
        scan.status = 'stopping'
        scan_service.add_scan_event(db, scan_id, 'scan.stop_requested', 'Stop requested for scan with RQ job', {'rq_job_id': scan.rq_job_id})
    else:
        scan.status = 'stopped'
        scan.stopped_at = datetime.utcnow()
        scan.finished_at = scan.finished_at or scan.stopped_at
        scan_service.add_scan_event(db, scan_id, 'scan.stopped', 'Scan stopped logically without RQ job')
    db.commit()
    db.refresh(scan)
    return scan
