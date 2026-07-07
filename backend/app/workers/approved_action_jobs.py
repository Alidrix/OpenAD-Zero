from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.approvals.run_service import build_run_context
from app.core.config import get_settings
from app.core.paths import get_evidence_root, safe_join_under_root
from app.core.process_runner import run_process
from app.db.models import ApprovedActionRun, ScanArtifact
from app.db.session import SessionLocal
from app.normalization.service import normalize_artifact
from app.pentest.orchestrator import PentestOrchestrator
from app.services.scan_service import add_scan_event

SECRET_WORDS = ('password', 'token', 'secret', 'ntlm', 'hash', 'credential', 'api_key')


def _redact(text: str) -> str:
    out = text
    for marker in SECRET_WORDS:
        out = out.replace(marker + '=', marker + '=***REDACTED***')
    return out


def _event(db, ctx, event_type: str, **extra: Any) -> None:
    payload = {
        'approval_id': ctx.approval.id,
        'action_id': ctx.action.id,
        'scan_id': ctx.scan.id,
        'tool_id': ctx.tool_id,
        'template_id': ctx.template_id,
    }
    payload.update(
        {k: _redact(str(v)) if k == 'error_message' and v is not None else v for k, v in extra.items() if v is not None}
    )
    add_scan_event(db, ctx.scan.id, event_type, event_type.replace('.', ' ').title(), payload)


def _parse_outputs(db, ctx, stdout_path: Path, stderr_path: Path, run: ApprovedActionRun) -> None:
    _event(db, ctx, 'normalization.started', status=run.status, source_type=ctx.template_id)
    created_artifacts = []
    for path in (stdout_path, stderr_path):
        if path.exists():
            artifact = ScanArtifact(
                scan_id=ctx.scan.id,
                artifact_type=ctx.template_id,
                path=str(path),
                sha256=None,
                size_bytes=path.stat().st_size,
            )
            db.add(artifact)
            db.flush()
            created_artifacts.append(artifact)
    total = None
    for artifact in created_artifacts:
        try:
            result = normalize_artifact(db, artifact)
            total = result if total is None else total.merge(result)
            _event(
                db,
                ctx,
                'normalization.diagnostic',
                artifact_id=artifact.id,
                diagnostics_count=result.diagnostics_created,
            )
        except Exception as exc:
            _event(db, ctx, 'normalization.failed', artifact_id=artifact.id, error_message=str(exc))
            raise
    _event(
        db,
        ctx,
        'normalization.completed',
        status=run.status,
        counts=total.as_dict() if total else {},
        diagnostics_count=total.diagnostics_created if total else 0,
    )


def run_approved_action(approval_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.query(ApprovedActionRun).filter_by(approval_id=approval_id).first()
        ctx = build_run_context(db, approval_id)
        if run is None:
            raise RuntimeError('approved action run row not found')
        if ctx.approval.status != 'consumed' or ctx.action.status not in {'queued', 'running'}:
            raise RuntimeError('approval/action state is not runnable')
        if ctx.command_hash != ctx.approval.command_hash or ctx.command_hash != run.command_hash:
            raise RuntimeError('approval command hash mismatch')
        root = get_evidence_root()
        artifact_dir = safe_join_under_root(root, 'approved-actions', approval_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        ctx = build_run_context(db, approval_id, artifact_dir=str(artifact_dir))
        stdout_path = artifact_dir / 'stdout.log'
        stderr_path = artifact_dir / 'stderr.log'
        (artifact_dir / 'command.masked.json').write_text(json.dumps({'argv': ctx.masked_argv}, indent=2))
        run.status = 'running'
        run.started_at = datetime.utcnow()
        run.artifact_dir = str(artifact_dir)
        run.stdout_path = str(stdout_path)
        run.stderr_path = str(stderr_path)
        ctx.action.status = 'running'
        _event(
            db,
            ctx,
            'approved_action.running',
            status='running',
            rq_job_id=run.rq_job_id,
            artifact_dir=str(artifact_dir),
        )
        db.commit()
        result = run_process(
            ctx.argv,
            cwd=artifact_dir,
            env={'PATH': '/usr/local/bin:/usr/bin:/bin'},
            timeout_seconds=get_settings().openadzero_action_job_timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            redaction_patterns=[str(v) for v in getattr(ctx, 'params', {}).values()]
            if hasattr(ctx, 'params')
            else None,
            max_log_bytes=get_settings().openadzero_process_max_log_bytes,
        )
        run.return_code = result.return_code
        final = result.status
        run.error_message = result.error_message
        _event(
            db,
            ctx,
            f'process.{final}',
            status=final,
            return_code=result.return_code,
            duration_seconds=result.duration_seconds,
            stdout_tail_redacted=result.stdout_tail,
            stderr_tail_redacted=result.stderr_tail,
            artifact_dir=str(artifact_dir),
            error_message_redacted=result.error_message,
        )
        run.status = final
        run.completed_at = datetime.utcnow()
        ctx.action.status = final
        ctx.action.updated_at = datetime.utcnow()
        (artifact_dir / 'metadata.json').write_text(
            json.dumps(
                {
                    'approval_id': approval_id,
                    'action_id': ctx.action.id,
                    'status': final,
                    'return_code': run.return_code,
                },
                indent=2,
            )
        )
        db.add(
            ScanArtifact(
                scan_id=ctx.scan.id,
                artifact_type='approved_action',
                path=str(artifact_dir / 'metadata.json'),
                sha256=None,
                size_bytes=(artifact_dir / 'metadata.json').stat().st_size,
            )
        )
        if final == 'completed':
            _parse_outputs(db, ctx, stdout_path, stderr_path, run)
            PentestOrchestrator(db).recompute(ctx.scan.id)
            _event(db, ctx, 'approved_action.recompute_completed', status=final)
        _event(
            db,
            ctx,
            f'approved_action.{final}',
            status=final,
            return_code=run.return_code,
            artifact_dir=str(artifact_dir),
            error_message=run.error_message,
        )
        db.commit()
    except Exception as exc:
        if 'run' in locals() and run:
            run.status = 'failed'
            run.error_message = _redact(str(exc))
            run.completed_at = datetime.utcnow()
        if 'ctx' in locals():
            ctx.action.status = 'failed'
            _event(db, ctx, 'approved_action.failed', status='failed', error_message=str(exc))
        db.commit()
        raise
    finally:
        db.close()
