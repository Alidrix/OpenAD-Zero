from fastapi.testclient import TestClient

from app.main import app


def test_lifespan_health_and_expected_routes():
    with TestClient(app) as client:
        response = client.get('/api/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

    paths = set(app.openapi()['paths'])
    assert '/api/health' in paths
    assert '/api/missions' in paths
    assert '/api/capabilities' in paths
    assert '/api/capabilities/{capability_id}' in paths
    assert '/api/health/tools' in paths
