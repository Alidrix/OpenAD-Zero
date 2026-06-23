from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.events.websocket_manager import manager
router=APIRouter()
@router.websocket('/ws/missions/{mission_id}')
async def ws_mission(websocket: WebSocket, mission_id: str):
    await manager.connect(mission_id, websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(mission_id, websocket)
