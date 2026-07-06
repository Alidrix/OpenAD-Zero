import hmac

from fastapi.testclient import TestClient

from app.core import auth
from app.core.config import get_settings
from app.main import app

TOKEN = 'test-token-1234567890'


def configure(monkeypatch, enabled=True, token=TOKEN, localhost_bypass=False):
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true' if enabled else 'false')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', token)
    monkeypatch.setenv('OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST', 'true' if localhost_bypass else 'false')
    get_settings.cache_clear()


def test_auth_disabled_existing_endpoint_works(client, monkeypatch):
    configure(monkeypatch, enabled=False)
    response = client.get('/api/capabilities')
    assert response.status_code == 200


def test_auth_enabled_missing_token_rejected(monkeypatch):
    configure(monkeypatch)
    with TestClient(app) as client:
        response = client.get('/api/capabilities')
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


def test_auth_enabled_invalid_token_rejected(monkeypatch):
    configure(monkeypatch)
    with TestClient(app) as client:
        response = client.get('/api/capabilities', headers={'Authorization': 'Bearer wrong'})
    assert response.status_code == 401


def test_auth_enabled_valid_token_allowed(monkeypatch):
    configure(monkeypatch)
    with TestClient(app) as client:
        response = client.get('/api/capabilities', headers={'Authorization': f'Bearer {TOKEN}'})
    assert response.status_code == 200


def test_public_health_and_auth_status_do_not_leak_token(monkeypatch):
    configure(monkeypatch)
    with TestClient(app) as client:
        health = client.get('/api/health')
        status = client.get('/api/auth/status')
    assert health.status_code == 200
    assert status.status_code == 200
    assert status.json() == {'auth_enabled': True, 'localhost_bypass_enabled': False, 'token_configured': True}
    assert TOKEN not in status.text


def test_detailed_health_requires_auth(monkeypatch):
    configure(monkeypatch)
    with TestClient(app) as client:
        missing = client.get('/api/health/db')
        valid = client.get('/api/health/db', headers={'Authorization': f'Bearer {TOKEN}'})
    assert missing.status_code == 401
    assert valid.status_code in {200, 500}


def test_token_comparison_uses_constant_time(monkeypatch):
    configure(monkeypatch)
    called = False

    def fake_compare(left, right):
        nonlocal called
        called = True
        return left == right

    monkeypatch.setattr(hmac, 'compare_digest', fake_compare)
    assert auth._token_matches(TOKEN) is True
    assert called is True


def test_localhost_bypass_requires_setting(monkeypatch):
    configure(monkeypatch, localhost_bypass=True)
    with TestClient(app, client=('127.0.0.1', 50000)) as client:
        allowed = client.get('/api/capabilities')
    configure(monkeypatch, localhost_bypass=False)
    with TestClient(app, client=('127.0.0.1', 50000)) as client:
        rejected = client.get('/api/capabilities')
    assert allowed.status_code == 200
    assert rejected.status_code == 401


def test_x_forwarded_for_is_not_trusted(monkeypatch):
    configure(monkeypatch, localhost_bypass=True)
    with TestClient(app, client=('203.0.113.10', 50000)) as client:
        response = client.get('/api/capabilities', headers={'X-Forwarded-For': '127.0.0.1'})
    assert response.status_code == 401
