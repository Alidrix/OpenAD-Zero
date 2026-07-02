from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from app.db.models import Scan, ScanEvent


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_scan_event(event: ScanEvent, scan: Scan | None = None) -> dict[str, Any]:
    payload = event.payload_json or {}
    status = payload.get('status')
    progress_percent = payload.get('progress_percent')
    current_step = payload.get('current_step')
    if scan is not None:
        status = scan.status if status is None else status
        progress_percent = scan.progress_percent if progress_percent is None else progress_percent
        current_step = scan.current_step if current_step is None else current_step
    return {
        'id': event.id,
        'type': event.event_type,
        'scan_id': event.scan_id,
        'status': status,
        'progress_percent': progress_percent,
        'current_step': current_step,
        'event_type': event.event_type,
        'message': event.message,
        'payload': payload,
        'payload_json': payload,
        'created_at': _iso(event.created_at),
    }


class ScanWebSocketManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, scan_id: str, ws: WebSocket):
        await ws.accept()
        self.active[scan_id].append(ws)

    def disconnect(self, scan_id: str, ws: WebSocket):
        if ws in self.active.get(scan_id, []):
            self.active[scan_id].remove(ws)
        if not self.active.get(scan_id):
            self.active.pop(scan_id, None)

    async def broadcast(self, scan_id: str, data: dict[str, Any]):
        dead = []
        for ws in list(self.active.get(scan_id, [])):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(scan_id, ws)


scan_ws_manager = ScanWebSocketManager()
