from __future__ import annotations

import asyncio
from datetime import datetime

from app.db.models import Job
from app.db.session import SessionLocal
from app.events.persistent import publish_mission_event


def run_async(coro):
    return asyncio.run(coro)


def run_queued_job(job_id: str) -> dict:
    db = SessionLocal()
    job = db.get(Job, job_id)
    if not job:
        db.close()
        return {'status': 'missing', 'job_id': job_id}
    try:
        if job.cancel_requested_at:
            job.status = 'cancelled'
            job.completed_at = datetime.utcnow()
            db.commit()
            run_async(
                publish_mission_event(
                    db,
                    job.mission_id,
                    'job.cancelled',
                    {'job_id': job.id, 'job_type': job.type, 'tool': job.tool, 'status': job.status},
                    source=job.tool,
                )
            )
            return {'status': 'cancelled', 'job_id': job.id}
        job.status = 'running'
        job.started_at = datetime.utcnow()
        job.last_heartbeat_at = datetime.utcnow()
        job.attempts = (job.attempts or 0) + 1
        db.commit()
        run_async(
            publish_mission_event(
                db,
                job.mission_id,
                'job.running',
                {'job_id': job.id, 'job_type': job.type, 'tool': job.tool, 'status': job.status},
                source=job.tool,
            )
        )
    finally:
        db.close()
    try:
        if job.type == 'nmap_discovery':
            from app.jobs.nmap_job import run_nmap_job

            run_async(run_nmap_job(job.mission_id, job.id))
        elif job.type.startswith('netexec_'):
            from app.jobs.netexec_job import run_netexec_job

            run_async(run_netexec_job(job.mission_id, job.id, getattr(job, 'action_id', None) or ''))
        elif job.type == 'nuclei_web_exposure_scan':
            from app.jobs.nuclei_job import run_nuclei_job

            run_async(run_nuclei_job(job.mission_id, job.id, getattr(job, 'action_id', None) or ''))
        else:
            raise ValueError(f'Unsupported queued job type {job.type}')
    except Exception as exc:
        db = SessionLocal()
        job = db.get(Job, job_id)
        if job:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.error_message = str(exc)[:10000]
            db.commit()
            run_async(
                publish_mission_event(
                    db,
                    job.mission_id,
                    'runner.error',
                    {
                        'job_id': job.id,
                        'job_type': job.type,
                        'tool': job.tool,
                        'status': job.status,
                        'error': job.error_message,
                    },
                    source=job.tool,
                )
            )
        db.close()
        raise
    db = SessionLocal()
    job = db.get(Job, job_id)
    status = job.status if job else 'unknown'
    mid = job.mission_id if job else ''
    if job:
        event_type = (
            'job.timeout'
            if status == 'timeout'
            else (
                'job.completed'
                if status == 'completed'
                else (
                    'job.cancelled'
                    if status == 'cancelled'
                    else 'job.failed'
                    if status == 'failed'
                    else 'job.completed'
                )
            )
        )
        run_async(
            publish_mission_event(
                db,
                mid,
                event_type,
                {'job_id': job.id, 'job_type': job.type, 'tool': job.tool, 'status': job.status},
                source=job.tool,
            )
        )
    db.close()
    return {'status': status, 'job_id': job_id}
