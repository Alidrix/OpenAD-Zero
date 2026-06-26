from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, mission_id: str, ws: WebSocket):
        await ws.accept()
        self.active[mission_id].append(ws)

    def disconnect(self, mission_id: str, ws: WebSocket):
        if ws in self.active.get(mission_id, []):
            self.active[mission_id].remove(ws)

    async def broadcast(self, mission_id: str, data: dict):
        dead = []
        for ws in list(self.active.get(mission_id, [])):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(mission_id, ws)


manager = WebSocketManager()
