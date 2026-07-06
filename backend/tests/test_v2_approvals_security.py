from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.session import Base, get_db
from app.main import app


def test_prepare_rejects_forbidden_frontend_command_fields(client):
    for field in ['command', 'argv', 'shell', 'command_hash', 'command_preview']:
        response = client.post('/api/v2/scans/s/pentest/actions/a/approval/prepare', json={field: 'x'})
        assert response.status_code == 422


def test_approval_endpoints_require_auth_when_enabled(monkeypatch):
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', 'approval-token')
    monkeypatch.setenv('OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST', 'false')
    get_settings.cache_clear()
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as c:
            assert c.get('/api/v2/approvals/a').status_code == 401
            assert c.get('/api/v2/approvals/a', headers={'Authorization': 'Bearer approval-token'}).status_code == 404
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        get_settings.cache_clear()


def test_approvals_module_does_not_import_subprocess():
    import app.approvals.service as service

    assert not hasattr(service, 'subprocess')
