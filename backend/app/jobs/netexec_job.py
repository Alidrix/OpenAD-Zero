from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.process_runner import run_process
from app.db.models import Host, Job, NextAction, Service, SMBFact, SMBShare
from app.db.session import SessionLocal
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.jobs.command_policy import validate_netexec_command
from app.parsers.netexec_smb import parse_netexec_smb_output
from app.planner.next_actions import plan_after_netexec
from app.storage.evidence import job_dir

ALLOWED_TEMPLATES = {
    'netexec_smb_fingerprint',
    'netexec_smb_signing_check',
    'netexec_smb_null_session_check',
    'netexec_smb_null_session_shares',
}


def smb_targets(db: Session, mission_id: str) -> list[str]:
    rows = (
        db.query(Host)
        .join(Service, Service.host_id == Host.id)
        .filter(Host.mission_id == mission_id, Service.port == 445)
        .all()
    )
    return sorted({h.ip for h in rows})


def build_netexec_command(action_type: str, targets: list[str], jd: Path) -> list[str]:
    log = str(jd / 'netexec.log')
    if action_type == 'netexec_smb_fingerprint':
        return ['nxc', 'smb', *targets, '--log', log]
    if action_type == 'netexec_smb_signing_check':
        return ['nxc', 'smb', *targets, '--gen-relay-list', str(jd / 'smb_signing_not_required.txt'), '--log', log]
    if action_type == 'netexec_smb_null_session_check':
        return ['nxc', 'smb', *targets, '-u', '', '-p', '', '--log', log]
    if action_type == 'netexec_smb_null_session_shares':
        return ['nxc', 'smb', *targets, '-u', '', '-p', '', '--shares', '--log', log]
    raise ValueError('Unsupported NetExec template')


async def run_netexec_job(mission_id: str, job_id: str, action_id: str):
    db: Session = SessionLocal()
    settings = get_settings()
    job = db.get(Job, job_id)
    action = db.get(NextAction, action_id)
    try:
        if job.cancel_requested_at:
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            db.commit()
            return
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.commit()
        await publish(
            MissionEvent(
                type='netexec.started',
                mission_id=mission_id,
                payload={'job_id': job_id, 'action_id': action_id, 'profile': job.type},
            )
        )
        targets = smb_targets(db, mission_id)
        jd = job_dir(mission_id, job_id)
        stdout = jd / 'stdout.log'
        stderr = jd / 'stderr.log'
        parsed_path = jd / 'parsed.json'
        findings_path = jd / 'findings.json'
        if not targets:
            msg = 'Aucun hôte SMB détecté par Nmap. Action NetExec annulée proprement.'
            (stdout).write_text(msg + '\n')
            job.status = 'blocked'
            if action:
                action.status = 'blocked'
            db.commit()
            await publish(
                MissionEvent(type='netexec.log', mission_id=mission_id, payload={'job_id': job_id, 'line': msg})
            )
            return
        cmd = build_netexec_command(job.type, targets, jd)
        validate_netexec_command(cmd)
        (jd / 'command.txt').write_text(' '.join(cmd) + '\n')
        job.command_preview = ' '.join(cmd)
        job.stdout_path = str(stdout)
        job.stderr_path = str(stderr)
        job.output_path = str(parsed_path)
        db.commit()
        result = run_process(
            cmd,
            cwd=jd,
            timeout_seconds=getattr(settings, 'netexec_timeout_seconds', 600),
            stdout_path=stdout,
            stderr_path=stderr,
            max_log_bytes=settings.openadzero_process_max_log_bytes,
        )
        await publish(
            MissionEvent(
                type=f'process.{result.status}',
                mission_id=mission_id,
                payload={
                    'job_id': job_id,
                    'action_id': action_id,
                    'tool_id': 'nxc',
                    'status': result.status,
                    'return_code': result.return_code,
                    'duration_seconds': result.duration_seconds,
                    'stdout_tail_redacted': result.stdout_tail,
                    'stderr_tail_redacted': result.stderr_tail,
                    'artifact_dir': str(jd),
                    'error_message_redacted': result.error_message,
                },
            )
        )
        job.return_code = result.return_code
        job.completed_at = datetime.utcnow()
        job.status = result.status
        if action:
            action.status = job.status
        output = (
            (stdout.read_text() if stdout.exists() else '')
            + '\n'
            + (stderr.read_text() if stderr.exists() else '')
            + '\n'
            + ((jd / 'netexec.log').read_text() if (jd / 'netexec.log').exists() else '')
        )
        parsed = parse_netexec_smb_output(output)
        parsed_path.write_text(json.dumps(parsed, indent=2))
        for f in parsed['facts']:
            host = db.query(Host).filter_by(mission_id=mission_id, ip=f['ip']).first()
            db.add(SMBFact(mission_id=mission_id, host_id=host.id if host else None, source='netexec', **f))
            await publish(MissionEvent(type='smb.fact.discovered', mission_id=mission_id, payload=f))
        for s in parsed['shares']:
            host = db.query(Host).filter_by(mission_id=mission_id, ip=s['ip']).first()
            db.add(SMBShare(mission_id=mission_id, host_id=host.id if host else None, source='netexec', **s))
            await publish(MissionEvent(type='smb.share.discovered', mission_id=mission_id, payload=s))
        db.commit()
        findings, actions = plan_after_netexec(db, mission_id, parsed['facts'], parsed['shares'], job.type)
        findings_path.write_text(
            json.dumps(
                [
                    {'title': f.title, 'severity': f.severity, 'source': f.source, 'confidence': f.confidence}
                    for f in findings
                ],
                indent=2,
            )
        )
        for f in findings:
            await publish(
                MissionEvent(
                    type='finding.created',
                    mission_id=mission_id,
                    payload={'title': f.title, 'severity': f.severity, 'source': f.source, 'confidence': f.confidence},
                )
            )
        for a in actions:
            await publish(
                MissionEvent(
                    type='planner.next_action',
                    mission_id=mission_id,
                    payload={
                        'id': a.id,
                        'title': a.title,
                        'risk_level': a.risk_level,
                        'requires_approval': a.requires_approval,
                        'command_template_id': a.command_template_id,
                        'status': a.status,
                        'reason': a.reason,
                    },
                )
            )
        try:
            from app.operations.service import safe_sync

            safe_sync(db, mission_id)
        except Exception:
            pass
        db.commit()
    except Exception as e:
        if job:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
        if action:
            action.status = 'failed'
        db.commit()
        await publish(
            MissionEvent(
                type='netexec.log', mission_id=mission_id, payload={'job_id': job_id, 'line': f'[netexec] {e}'}
            )
        )
    finally:
        db.close()
