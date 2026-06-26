import logging

from app.core.logging import redact_dict
from app.events.schemas import MissionEvent
from app.events.websocket_manager import manager

log = logging.getLogger('openadzero.events')


async def publish(event: MissionEvent):
    log.info('event %s mission=%s payload=%s', event.type, event.mission_id, redact_dict(event.payload or {}))
    try:
        from app.db.session import SessionLocal
        from app.events.persistent import publish_mission_event

        db = SessionLocal()
        try:
            await publish_mission_event(
                db, event.mission_id, event.type, event.payload, source=(event.payload or {}).get('tool', 'system')
            )
            return
        finally:
            db.close()
    except Exception:
        log.exception('persistent event publish failed, falling back to websocket-only')
    await manager.broadcast(event.mission_id, event.model_dump())
