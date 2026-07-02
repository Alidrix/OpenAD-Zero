from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.models import ScanEvent
from app.db.session import SessionLocal
from app.events.scan_websocket_manager import scan_ws_manager, serialize_scan_event
from app.services import scan_service

router = APIRouter()


def query_scan_events(db, scan_id: str, limit: int = 200):
    limit = min(max(limit, 1), 1000)
    return db.query(ScanEvent).filter_by(scan_id=scan_id).order_by(ScanEvent.created_at.asc()).limit(limit).all()


@router.websocket('/ws/v2/scans/{scan_id}')
async def ws_v2_scan(websocket: WebSocket, scan_id: str):
    await scan_ws_manager.connect(scan_id, websocket)
    try:
        if websocket.query_params.get('replay') == 'true':
            db = SessionLocal()
            try:
                scan = scan_service.get_scan(db, scan_id)
                for event in query_scan_events(db, scan_id, int(websocket.query_params.get('limit') or 200)):
                    await websocket.send_json(serialize_scan_event(event, scan))
            finally:
                db.close()
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        scan_ws_manager.disconnect(scan_id, websocket)
    except Exception:
        scan_ws_manager.disconnect(scan_id, websocket)
