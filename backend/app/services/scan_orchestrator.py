from datetime import datetime

from rq.command import send_stop_job_command
from rq.job import Job
from sqlalchemy.orm import Session

from app.queue.connection import get_redis_connection, get_scan_queue
from app.services import scan_service
from app.services.scan_schemas import ScanCreate
from app.workers.v2_scan_jobs import run_demo_scan

ACTIVE_STATUSES = {'queued', 'running', 'stopping'}


def create_manual_scan(db: Session, payload: ScanCreate):
    return scan_service.create_scan(db, payload)


def mark_scan_queued(db: Session, scan_id: str, rq_job_id: str | None = None):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    scan.status = 'queued'
    scan.rq_job_id = rq_job_id
    scan_service.add_scan_event(
        db, scan_id, 'scan.queued', 'Scan marked queued', {'rq_job_id': rq_job_id, 'status': 'queued'}
    )
    db.commit()
    db.refresh(scan)
    return scan


def enqueue_demo_scan(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    if scan.status == 'deleted' or scan.deleted_at is not None:
        raise ValueError('deleted scans cannot be queued')
    if scan.status in ACTIVE_STATUSES:
        raise ValueError('scan is already active')

    queue = get_scan_queue()
    job = queue.enqueue(run_demo_scan, scan_id, job_timeout=300)
    scan.status = 'queued'
    scan.rq_job_id = job.id
    scan.current_step = 'Demo worker queued'
    scan_service.add_scan_event(
        db,
        scan_id,
        'scan.queued',
        'Demo scan worker queued',
        {
            'rq_job_id': job.id,
            'status': 'queued',
            'progress_percent': scan.progress_percent,
            'current_step': scan.current_step,
        },
    )
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


def _logical_stop(
    db: Session, scan, event_type: str = 'scan.stopped', message: str = 'Scan stopped logically without RQ job'
):
    scan.status = 'stopped'
    scan.stopped_at = datetime.utcnow()
    scan.finished_at = scan.finished_at or scan.stopped_at
    scan_service.add_scan_event(db, scan.id, event_type, message, {'status': scan.status, 'rq_job_id': scan.rq_job_id})
    db.commit()
    db.refresh(scan)
    return scan


def request_scan_stop(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        return None
    if not scan.rq_job_id:
        return _logical_stop(db, scan)

    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(scan.rq_job_id, connection=redis_conn)
        raw_status = job.get_status(refresh=True)
        status = getattr(raw_status, 'value', str(raw_status)).lower()
    except Exception as exc:
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.stop_failed',
            'Unable to contact RQ while requesting stop',
            {'rq_job_id': scan.rq_job_id, 'error': str(exc)},
        )
        db.commit()
        db.refresh(scan)
        raise RuntimeError('Unable to contact RQ while requesting stop') from exc

    if status in {'queued', 'deferred', 'scheduled'}:
        job.cancel()
        return _logical_stop(db, scan, 'scan.stopped', 'Queued RQ demo scan canceled before execution')
    if status in {'started', 'running'}:
        send_stop_job_command(redis_conn, scan.rq_job_id)
        scan.status = 'stopping'
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.stop_requested',
            'Stop requested for running RQ demo scan',
            {'rq_job_id': scan.rq_job_id, 'rq_status': status, 'status': 'stopping'},
        )
    elif status == 'finished':
        scan.status = 'completed'
        scan.progress_percent = 100
        scan.finished_at = scan.finished_at or datetime.utcnow()
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.rq_synchronized',
            'RQ job already finished; scan synchronized',
            {'rq_job_id': scan.rq_job_id, 'rq_status': status, 'status': 'completed'},
        )
    elif status in {'failed'}:
        scan.status = 'failed'
        scan.finished_at = scan.finished_at or datetime.utcnow()
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.rq_synchronized',
            'RQ job failed; scan synchronized',
            {'rq_job_id': scan.rq_job_id, 'rq_status': status, 'status': 'failed'},
        )
    elif status in {'stopped', 'canceled', 'cancelled'}:
        scan.status = 'stopped'
        scan.stopped_at = scan.stopped_at or datetime.utcnow()
        scan.finished_at = scan.finished_at or scan.stopped_at
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.stopped',
            'RQ job stopped/canceled; scan synchronized',
            {'rq_job_id': scan.rq_job_id, 'rq_status': status, 'status': 'stopped'},
        )
    else:
        scan.status = 'stopping'
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.stop_requested',
            'Stop requested for RQ demo scan with unknown status',
            {'rq_job_id': scan.rq_job_id, 'rq_status': status, 'status': 'stopping'},
        )
    db.commit()
    db.refresh(scan)
    return scan
