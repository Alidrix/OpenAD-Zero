import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Job, Mission, MissionEvent
from app.queue.connection import get_scan_queue
from app.queue.registry import ALLOWED_JOB_TYPES

log = logging.getLogger(__name__)


def _persist_queue_event(db: Session, mission_id: str, job: Job) -> None:
    payload = {'job_id': job.id, 'job_type': job.type, 'tool': job.tool, 'status': job.status}
    event = MissionEvent(mission_id=mission_id, event_type='job.queued', source=job.tool, payload_json=payload)
    db.add(event)
    db.commit()
    db.refresh(event)
    try:
        from app.queue.connection import get_redis_connection

        sid = get_redis_connection().xadd(
            f'openadzero:mission:{mission_id}:events',
            {
                'event_id': event.id,
                'event_type': event.event_type,
                'source': event.source,
                'payload_json': json.dumps(payload),
                'created_at': event.created_at.isoformat(),
            },
        )
        event.redis_stream_id = sid.decode() if isinstance(sid, bytes) else str(sid)
        db.commit()
    except Exception as exc:
        log.warning('Redis stream publish failed for queued job event: %s', exc)


def enqueue_job(db: Session, mission_id: str, job_id: str, job_type: str) -> str:
    if job_type not in ALLOWED_JOB_TYPES:
        raise ValueError(f'Unsupported job type: {job_type}')
    job = db.get(Job, job_id)
    if not job:
        mission = db.get(Mission, mission_id)
        if not mission:
            raise ValueError('Mission not found')
        tool = 'nmap' if job_type == 'nmap_discovery' else ('nuclei' if job_type.startswith('nuclei') else 'netexec')
        job = Job(
            id=job_id,
            mission_id=mission_id,
            type=job_type,
            tool=tool,
            status='pending',
            command_preview='queued worker job',
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    rq_job = get_scan_queue().enqueue(
        'app.queue.tasks.run_queued_job', job.id, job_timeout=3600, result_ttl=86400, failure_ttl=86400
    )
    job.rq_job_id = rq_job.id
    job.status = 'queued'
    job.queued_at = datetime.utcnow()
    job.error_message = None
    db.commit()
    db.refresh(job)
    _persist_queue_event(db, mission_id, job)
    return rq_job.id
