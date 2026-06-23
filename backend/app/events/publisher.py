import logging
from app.events.schemas import MissionEvent
from app.events.websocket_manager import manager
log=logging.getLogger('openadzero.events')
async def publish(event: MissionEvent):
    log.info('event %s mission=%s payload=%s', event.type, event.mission_id, event.payload)
    await manager.broadcast(event.mission_id, event.model_dump())
