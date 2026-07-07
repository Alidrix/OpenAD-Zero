from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from app.approvals.run_service import build_run_context
from app.core.config import get_settings
from app.core.paths import get_evidence_root, safe_join_under_root
from app.db.models import ApprovedActionRun, ParsedFinding, ParseDiagnostic, ParsedSignal, ScanArtifact
from app.db.session import SessionLocal
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
    _event(db, ctx, 'approved_action.parsing_started', status=run.status)
    output = (
        (stdout_path.read_text(errors='replace') if stdout_path.exists() else '')
        + '\n'
        + (stderr_path.read_text(errors='replace') if stderr_path.exists() else '')
    )
    created = 0
    if ctx.template_id.startswith('netexec_smb'):
        lowered = output.lower()
        if 'signing:false' in lowered or 'signing disabled' in lowered or 'signing: false' in lowered:
            db.add(
                ParsedSignal(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    signal='smb_signing_disabled',
                    value='true',
                    confidence=0.8,
                )
            )
            created += 1
            db.add(
                ParsedFinding(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    title='SMB signing disabled',
                    description='NetExec output indicates SMB signing is not required.',
                    severity='medium',
                    confidence=0.8,
                    tags_json={'template_id': ctx.template_id},
                )
            )
        if 'anonymous' in lowered or 'null session' in lowered:
            db.add(
                ParsedSignal(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    signal='anonymous_smb',
                    value='true',
                    confidence=0.7,
                )
            )
            created += 1
            db.add(
                ParsedSignal(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    signal='null_session_possible',
                    value='true',
                    confidence=0.7,
                )
            )
            created += 1
        if 'share' in lowered and ('read' in lowered or 'write' in lowered):
            db.add(
                ParsedSignal(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    signal='smb_share_exposed',
                    value='true',
                    confidence=0.7,
                )
            )
            created += 1
    elif ctx.template_id.startswith('nuclei'):
        for line in output.splitlines():
            try:
                item = json.loads(line)
            except Exception:
                continue
            db.add(
                ParsedFinding(
                    scan_id=ctx.scan.id,
                    source_type='approved_action',
                    source_id=run.id,
                    title=str(item.get('template-id') or item.get('info', {}).get('name') or 'Nuclei finding')[:255],
                    description=json.dumps(item, sort_keys=True)[:4000],
                    severity=str(item.get('info', {}).get('severity') or 'info'),
                    confidence=0.8,
                    tags_json={'template_id': ctx.template_id},
                )
            )
            created += 1
    else:
        db.add(
            ParseDiagnostic(
                scan_id=ctx.scan.id,
                source_type='approved_action',
                source_id=run.id,
                level='warning',
                message='parser_missing',
                details_json={'template_id': ctx.template_id},
            )
        )
    if created == 0 and ctx.template_id.startswith(('netexec_smb', 'nuclei')):
        db.add(
            ParseDiagnostic(
                scan_id=ctx.scan.id,
                source_type='approved_action',
                source_id=run.id,
                level='info',
                message='parser_completed_no_findings',
                details_json={'template_id': ctx.template_id},
            )
        )
    db.flush()
    _event(db, ctx, 'approved_action.parsing_completed', status=run.status)


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
        try:
            proc = subprocess.run(
                ctx.argv,
                cwd=str(artifact_dir),
                env={'PATH': '/usr/local/bin:/usr/bin:/bin'},
                capture_output=True,
                text=True,
                timeout=get_settings().openadzero_action_job_timeout_seconds,
                shell=False,
            )
            stdout_path.write_text(_redact(proc.stdout or ''))
            stderr_path.write_text(_redact(proc.stderr or ''))
            run.return_code = proc.returncode
            final = 'completed' if proc.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_redact(exc.stdout or '') if isinstance(exc.stdout, str) else '')
            stderr_path.write_text(_redact(exc.stderr or '') if isinstance(exc.stderr, str) else 'timeout')
            run.return_code = -1
            final = 'timeout'
            run.error_message = 'timeout'
        run.status = final
        run.completed_at = datetime.utcnow()
        ctx.action.status = final if final != 'timeout' else 'failed'
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
