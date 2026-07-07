from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.core.parameter_validation import ParameterValidationError
from app.core.paths import get_evidence_root, safe_join_under_root
from app.db.models import Mission, ScanStep
from app.db.session import SessionLocal
from app.jobs.runner import run_command
from app.normalization.service import normalize_artifact
from app.pentest.orchestrator import PentestOrchestrator
from app.scanning.initial_discovery import SAFE_INITIAL_DISCOVERY_PROFILE, build_safe_nmap_command, masked_command
from app.services import scan_service


def _payload(scan, progress: int, step: str, **extra):
    payload = {'scan_id': scan.id, 'progress_percent': progress, 'current_step': step, 'rq_job_id': scan.rq_job_id}
    payload.update({k: v for k, v in extra.items() if v is not None})
    return payload


def _event(db, scan, event_type: str, message: str, progress: int, step: str, **extra):
    scan_service.add_scan_event(db, scan.id, event_type, message, _payload(scan, progress, step, **extra))


def _mission_scope(db, scan) -> list[str]:
    if not scan.mission_id:
        raise ParameterValidationError('scan is not attached to a validated mission scope')
    mission = db.get(Mission, scan.mission_id)
    if mission is None or not mission.validated_targets:
        raise ParameterValidationError('validated mission scope is required')
    return list(mission.validated_targets)


def _is_stopping(scan) -> bool:
    return scan.status in {'stopping', 'stopped'}


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')


def run_initial_discovery_scan(scan_id: str) -> None:
    db = SessionLocal()
    scan = None
    step = None
    try:
        scan = scan_service.get_scan(db, scan_id)
        if scan is None:
            return
        targets = _mission_scope(db, scan)
        evidence_root = get_evidence_root(create=True)
        job_dir = safe_join_under_root(evidence_root, 'initial-discovery', scan.id)
        job_dir.mkdir(parents=True, exist_ok=True)
        command = build_safe_nmap_command(targets=targets, job_dir=job_dir, profile=SAFE_INITIAL_DISCOVERY_PROFILE)

        scan.status = 'running'
        scan.started_at = scan.started_at or datetime.utcnow()
        scan.progress_percent = 10
        scan.current_step = 'Initial discovery running'
        step = ScanStep(
            scan_id=scan.id,
            order=len(scan.steps or []) + 1,
            name='Initial network discovery',
            status='running',
            progress_percent=0,
            started_at=datetime.utcnow(),
        )
        db.add(step)
        _event(db, scan, 'scan.initial_discovery_started', 'Initial discovery started', 10, scan.current_step)
        _event(db, scan, 'scan.initial_discovery_progress', 'Initial discovery progress', 10, scan.current_step)
        db.commit()

        if _is_stopping(scan):
            raise RuntimeError('scan stop requested before nmap execution')

        stdout_path = safe_join_under_root(job_dir, 'stdout.log')
        stderr_path = safe_join_under_root(job_dir, 'stderr.log')
        _write_text(safe_join_under_root(job_dir, 'command.masked.txt'), masked_command(command) + '\n')
        result = asyncio.run(
            run_command(
                'nmap',
                command.args,
                job_dir,
                stdout_path,
                stderr_path,
                scan.mission_id or scan.id,
                scan.id,
                get_settings().nmap_timeout_seconds,
            )
        )
        if result.return_code != 0:
            raise RuntimeError(f'nmap failed with return code {result.return_code}')

        scan.progress_percent = 40
        scan.current_step = 'Nmap discovery completed'
        artifact = scan_service.add_scan_artifact(
            db,
            scan.id,
            'nmap_xml',
            str(command.output_xml),
            hashlib.sha256(command.output_xml.read_bytes()).hexdigest() if command.output_xml.exists() else None,
            command.output_xml.stat().st_size if command.output_xml.exists() else 0,
        )
        _event(
            db,
            scan,
            'scan.initial_discovery_nmap_completed',
            'Nmap discovery completed',
            40,
            scan.current_step,
            artifact_id=artifact.id,
        )
        _event(
            db,
            scan,
            'scan.initial_discovery_parse_started',
            'Nmap XML parsing started',
            40,
            'Parsing Nmap XML',
            artifact_id=artifact.id,
        )
        db.commit()

        if _is_stopping(scan):
            scan.status = 'stopped'
            scan.stopped_at = datetime.utcnow()
            db.commit()
            return

        db.expire_all()
        _event(
            db,
            scan,
            'normalization.started',
            'Normalization started',
            40,
            'Normalizing Nmap XML',
            artifact_id=artifact.id,
            source_type=artifact.artifact_type,
        )
        norm_result = normalize_artifact(db, artifact)
        _event(
            db,
            scan,
            'normalization.completed',
            'Normalization completed',
            65,
            'Normalization completed',
            artifact_id=artifact.id,
            source_type=artifact.artifact_type,
            counts=norm_result.as_dict(),
            diagnostics_count=norm_result.diagnostics_created,
        )
        scan = scan_service.get_scan(db, scan.id)
        scan.progress_percent = 70
        scan.current_step = 'Nmap parsing completed'
        _event(
            db,
            scan,
            'scan.initial_discovery_parse_completed',
            'Nmap XML parsing completed',
            70,
            scan.current_step,
            artifact_id=artifact.id,
        )
        _event(
            db,
            scan,
            'scan.initial_discovery_recompute_started',
            'Pentest recompute started',
            70,
            'Pentest recompute started',
            artifact_id=artifact.id,
        )
        db.commit()

        PentestOrchestrator(db).recompute(scan.id)
        scan = scan_service.get_scan(db, scan.id)
        scan.progress_percent = 90
        scan.current_step = 'Pentest recompute completed'
        _event(
            db,
            scan,
            'scan.initial_discovery_recompute_completed',
            'Pentest recompute completed',
            90,
            scan.current_step,
            artifact_id=artifact.id,
        )
        scan.progress_percent = 100
        scan.status = 'completed'
        scan.finished_at = datetime.utcnow()
        scan.current_step = 'Initial discovery completed'
        if step:
            step.status = 'completed'
            step.progress_percent = 100
            step.finished_at = datetime.utcnow()
        _event(
            db,
            scan,
            'scan.initial_discovery_completed',
            'Initial discovery completed',
            100,
            scan.current_step,
            artifact_id=artifact.id,
        )
        db.commit()
    except Exception as exc:
        if scan is not None:
            scan.status = 'failed'
            scan.finished_at = datetime.utcnow()
            scan.current_step = 'Initial discovery failed'
            if step:
                step.status = 'failed'
                step.finished_at = datetime.utcnow()
            _event(
                db,
                scan,
                'scan.initial_discovery_failed',
                'Initial discovery failed',
                scan.progress_percent or 0,
                scan.current_step,
                error=str(exc),
            )
            db.commit()
    finally:
        db.close()
