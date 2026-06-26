from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.core.logging import redact_dict
from app.db.models import MissionEvent
from app.events.websocket_manager import manager

log = logging.getLogger(__name__)


def _event_dict(event: MissionEvent) -> dict:
    return {
        'id': event.id,
        'mission_id': event.mission_id,
        'event_type': event.event_type,
        'type': event.event_type,
        'source': event.source,
        'payload_json': event.payload_json,
        'payload': event.payload_json or {},
        'created_at': event.created_at.isoformat() if event.created_at else None,
    }


async def publish_mission_event(
    db: Session, mission_id: str, event_type: str, payload: dict, source: str = 'system'
) -> MissionEvent:
    payload = redact_dict(payload or {})
    if payload.get('job_id') and ('log' in event_type or payload.get('line')):
        try:
            from app.db.models import JobLog

            line = str(payload.get('line', ''))[:10000]
            db.add(
                JobLog(
                    mission_id=mission_id,
                    job_id=payload['job_id'],
                    source=source,
                    stream=payload.get('stream', 'stdout'),
                    line=line,
                )
            )
        except Exception:
            log.exception('Job log persistence failed')
    event = MissionEvent(mission_id=mission_id, event_type=event_type, source=source, payload_json=payload)
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
                'payload_json': json.dumps(event.payload_json or {}),
                'created_at': event.created_at.isoformat(),
            },
        )
        event.redis_stream_id = sid.decode() if isinstance(sid, bytes) else str(sid)
        db.commit()
        db.refresh(event)
    except Exception as exc:
        log.warning('Redis stream publish failed for mission %s event %s: %s', mission_id, event.id, exc)
    try:
        await manager.broadcast(mission_id, _event_dict(event))
    except Exception:
        log.exception('WebSocket broadcast failed')
    return event
