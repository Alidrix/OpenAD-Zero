from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.core.paths import get_evidence_root
from app.db.models import Scan, ScanArtifact, ScanEvent
from app.services.scan_schemas import ScanCreate

SCAN_STATUSES = {'draft', 'queued', 'running', 'stopping', 'stopped', 'completed', 'failed', 'deleted'}
SCAN_STEP_STATUSES = {'pending', 'running', 'completed', 'failed', 'skipped'}


def _now() -> datetime:
    return datetime.utcnow()


def _validate_progress(progress_percent: int) -> None:
    if progress_percent < 0 or progress_percent > 100:
        raise ValueError('progress_percent must be between 0 and 100')


def _validate_scan_status(status: str | None) -> None:
    if status is not None and status not in SCAN_STATUSES:
        raise ValueError(f'invalid scan status: {status}')


def create_scan(db: Session, payload: ScanCreate) -> Scan:
    scan = Scan(
        name=payload.name,
        mission_id=payload.mission_id,
        scan_type=payload.scan_type,
        tool_name=payload.tool_name,
        status='draft',
        progress_percent=0,
    )
    db.add(scan)
    db.flush()
    add_scan_event(db, scan.id, 'scan.created', 'Scan created in draft state')
    db.commit()
    db.refresh(scan)
    return scan


def list_scans(db: Session, include_deleted: bool = False) -> list[Scan]:
    query = db.query(Scan)
    if not include_deleted:
        query = query.filter(Scan.deleted_at.is_(None), Scan.status != 'deleted')
    return query.order_by(Scan.created_at.desc()).all()


def get_scan(db: Session, scan_id: str) -> Scan | None:
    return (
        db.query(Scan)
        .options(selectinload(Scan.steps), selectinload(Scan.events), selectinload(Scan.artifacts))
        .filter(Scan.id == scan_id)
        .first()
    )


def rename_scan(db: Session, scan_id: str, new_name: str) -> Scan | None:
    scan = get_scan(db, scan_id)
    if scan is None:
        return None
    old_name = scan.name
    scan.name = new_name
    scan.renamed_at = _now()
    add_scan_event(db, scan.id, 'scan.renamed', 'Scan renamed', {'old_name': old_name, 'new_name': new_name})
    db.commit()
    db.refresh(scan)
    return scan


def soft_delete_scan(db: Session, scan_id: str) -> Scan | None:
    scan = get_scan(db, scan_id)
    if scan is None:
        return None
    scan.status = 'deleted'
    scan.deleted_at = _now()
    add_scan_event(db, scan.id, 'scan.deleted', 'Scan soft deleted')
    db.commit()
    db.refresh(scan)
    return scan


def add_scan_event(
    db: Session, scan_id: str, event_type: str, message: str, payload_json: dict[str, Any] | None = None
) -> ScanEvent:
    event = ScanEvent(scan_id=scan_id, event_type=event_type, message=message, payload_json=payload_json)
    db.add(event)
    db.flush()
    return event


def update_scan_progress(
    db: Session, scan_id: str, progress_percent: int, current_step: str | None = None, status: str | None = None
) -> Scan | None:
    _validate_progress(progress_percent)
    _validate_scan_status(status)
    scan = get_scan(db, scan_id)
    if scan is None:
        return None
    scan.progress_percent = progress_percent
    if current_step is not None:
        scan.current_step = current_step
    if status is not None:
        scan.status = status
    add_scan_event(
        db,
        scan.id,
        'scan.progress_updated',
        'Scan progress updated',
        {'progress_percent': progress_percent, 'current_step': current_step, 'status': status},
    )
    db.commit()
    db.refresh(scan)
    return scan


def add_scan_artifact(
    db: Session, scan_id: str, artifact_type: str, path: str, sha256: str | None = None, size_bytes: int | None = None
) -> ScanArtifact:
    evidence_root = get_evidence_root(create=True)
    artifact_path = Path(path)
    resolved = artifact_path if artifact_path.is_absolute() else (evidence_root / artifact_path)
    try:
        resolved.resolve().relative_to(evidence_root.resolve())
    except ValueError as exc:
        raise ValueError('scan artifacts must stay under EVIDENCE_DIR') from exc
    artifact = ScanArtifact(
        scan_id=scan_id, artifact_type=artifact_type, path=str(resolved), sha256=sha256, size_bytes=size_bytes
    )
    db.add(artifact)
    add_scan_event(
        db,
        scan_id,
        'scan.artifact_added',
        'Scan artifact registered',
        {'artifact_type': artifact_type, 'path': str(resolved)},
    )
    db.commit()
    db.refresh(artifact)
    return artifact
