from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.auth import require_api_token, require_ws_token
from app.db.models import MissionEvent
from app.db.session import SessionLocal, get_db
from app.events.websocket_manager import manager

router = APIRouter()


def serialize_event(e: MissionEvent):
    return {
        'id': e.id,
        'mission_id': e.mission_id,
        'event_type': e.event_type,
        'type': e.event_type,
        'source': e.source,
        'payload_json': e.payload_json,
        'payload': e.payload_json or {},
        'created_at': e.created_at,
    }


def query_events(db, mission_id, after_id=None, limit=200, event_type=None, source=None):
    limit = min(max(limit, 1), 1000)
    q = db.query(MissionEvent).filter_by(mission_id=mission_id)
    if after_id:
        marker = db.get(MissionEvent, after_id)
        if marker:
            q = q.filter(MissionEvent.created_at > marker.created_at)
    if event_type:
        q = q.filter(MissionEvent.event_type == event_type)
    if source:
        q = q.filter(MissionEvent.source == source)
    return q.order_by(MissionEvent.created_at.asc()).limit(limit).all()


@router.get('/api/missions/{mission_id}/events', dependencies=[Depends(require_api_token)])
def list_events(
    mission_id: str,
    after_id: str | None = None,
    limit: int = Query(200, le=1000),
    event_type: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    return [serialize_event(e) for e in query_events(db, mission_id, after_id, limit, event_type, source)]


@router.get('/api/missions/{mission_id}/events/recent', dependencies=[Depends(require_api_token)])
def recent_events(
    mission_id: str,
    limit: int = Query(200, le=1000),
    event_type: str | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    return [serialize_event(e) for e in query_events(db, mission_id, None, limit, event_type, source)]


@router.websocket('/ws/missions/{mission_id}')
async def ws_mission(websocket: WebSocket, mission_id: str):
    await require_ws_token(websocket)
    await manager.connect(mission_id, websocket)
    try:
        if websocket.query_params.get('replay') == 'true':
            db = SessionLocal()
            try:
                for e in query_events(
                    db,
                    mission_id,
                    websocket.query_params.get('after_id'),
                    int(websocket.query_params.get('limit') or 200),
                ):
                    await websocket.send_json(serialize_event(e))
            finally:
                db.close()
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(mission_id, websocket)
