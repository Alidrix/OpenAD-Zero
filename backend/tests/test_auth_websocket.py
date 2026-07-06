import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import get_settings
from app.main import app

TOKEN = 'test-token-1234567890'


def configure(monkeypatch):
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', TOKEN)
    monkeypatch.setenv('OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST', 'false')
    get_settings.cache_clear()


def test_mission_websocket_without_token_rejected(monkeypatch):
    configure(monkeypatch)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect('/ws/missions/example'):
        pass
    assert exc.value.code == 1008


def test_mission_websocket_invalid_token_rejected(monkeypatch):
    configure(monkeypatch)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect('/ws/missions/example?token=wrong'):
        pass
    assert exc.value.code == 1008


def test_mission_websocket_valid_token_accepted(monkeypatch):
    configure(monkeypatch)
    client = TestClient(app)
    with client.websocket_connect(f'/ws/missions/example?token={TOKEN}') as websocket:
        websocket.send_text('ping')


def test_v2_scan_websocket_without_token_rejected(monkeypatch):
    configure(monkeypatch)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect('/ws/v2/scans/example'):
        pass
    assert exc.value.code == 1008


def test_v2_scan_websocket_invalid_token_rejected(monkeypatch):
    configure(monkeypatch)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as exc, client.websocket_connect('/ws/v2/scans/example?token=wrong'):
        pass
    assert exc.value.code == 1008
