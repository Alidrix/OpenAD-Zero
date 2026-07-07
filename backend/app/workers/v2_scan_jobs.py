from __future__ import annotations

from datetime import datetime
from time import sleep

from app.db.models import ScanStep
from app.db.session import SessionLocal
from app.services import scan_service

DEMO_PROGRESS_STEPS = [0, 20, 40, 60, 80, 100]


def _ensure_step(db, scan_id: str, order: int, name: str, progress_percent: int) -> None:
    step = db.query(ScanStep).filter_by(scan_id=scan_id, order=order).first()
    now = datetime.utcnow()
    if step is None:
        step = ScanStep(
            scan_id=scan_id, order=order, name=name, status='running', progress_percent=progress_percent, started_at=now
        )
        db.add(step)
    step.status = 'completed' if progress_percent == 100 else 'running'
    step.progress_percent = progress_percent
    step.started_at = step.started_at or now
    if progress_percent == 100:
        step.finished_at = now


def run_demo_scan(scan_id: str) -> dict:
    """Run a safe demo scan that only persists progress; no external tools are executed."""
    db = SessionLocal()
    try:
        scan = scan_service.get_scan(db, scan_id)
        if scan is None or scan.status == 'deleted':
            return {'scan_id': scan_id, 'status': 'missing'}

        scan.status = 'running'
        scan.started_at = scan.started_at or datetime.utcnow()
        scan.current_step = 'Demo worker starting'
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.running',
            'Demo scan worker started',
            {'status': 'running', 'progress_percent': scan.progress_percent, 'current_step': scan.current_step},
        )
        db.commit()

        # TODO: a future worker-control brick should check the RQ stop signal inside this loop.
        for index, progress in enumerate(DEMO_PROGRESS_STEPS, start=1):
            current_step = f'Demo worker step {index}/{len(DEMO_PROGRESS_STEPS)}'
            status = 'completed' if progress == 100 else 'running'
            _ensure_step(db, scan_id, index, current_step, progress)
            scan = scan_service.update_scan_progress(db, scan_id, progress, current_step=current_step, status=status)
            if scan is None:
                return {'scan_id': scan_id, 'status': 'missing'}
            if progress < 100:
                sleep(0.01)

        scan.finished_at = datetime.utcnow()
        scan.current_step = 'Demo worker completed'
        scan_service.add_scan_event(
            db,
            scan_id,
            'scan.completed',
            'Demo scan worker completed',
            {
                'status': 'completed',
                'progress_percent': 100,
                'current_step': scan.current_step,
                'metadata': {'demo_worker': True},
            },
        )
        db.commit()
        return {'scan_id': scan_id, 'status': 'completed', 'progress_percent': 100}
    finally:
        db.close()
