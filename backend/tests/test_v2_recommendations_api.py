from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Job, ScanEvent
from app.db.session import Base, get_db
from app.main import app


def _install_sqlite_override():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return engine, Session


def test_recommendation_catalog_endpoint_returns_catalog(client):
    response = client.get('/api/v2/recommendations/catalog')

    assert response.status_code == 200
    payload = response.json()
    assert payload['templates']
    assert payload['rules']
    assert payload['safety_policy']


def test_recommendation_preview_endpoint_is_preview_only(client):
    response = client.post(
        '/api/v2/recommendations/preview',
        json={
            'template_id': 'v2_netexec_smb_fingerprint_preview',
            'params': {'target': '10.0.0.5'},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['template_id'] == 'v2_netexec_smb_fingerprint_preview'
    assert payload['executable'] is False
    assert payload['automatic_execution_allowed'] is False
    assert 'argv_preview' in payload


def test_recommendation_preview_endpoint_refuses_raw_command(client):
    response = client.post(
        '/api/v2/recommendations/preview',
        json={
            'template_id': 'v2_netexec_smb_fingerprint_preview',
            'params': {'raw_command': 'nxc smb 10.0.0.5'},
        },
    )

    assert response.status_code == 400
    assert 'raw' in response.json()['detail'].lower()


def test_scan_recommendations_endpoint_returns_for_existing_scan(client):
    engine, Session = _install_sqlite_override()
    try:
        created = client.post(
            '/api/v2/scans',
            json={'name': 'Recommendations API', 'scan_type': 'manual'},
        )
        assert created.status_code == 201
        scan_id = created.json()['id']

        db = Session()
        try:
            db.add(
                ScanEvent(
                    scan_id=scan_id,
                    event_type='service.detected',
                    message='SMB 445 open on Windows host',
                    payload_json={'signals': ['smb_open', 'windows_host_detected']},
                )
            )
            db.commit()
        finally:
            db.close()

        response = client.get(f'/api/v2/scans/{scan_id}/recommendations')

        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list)
        assert any(item['template_id'] == 'v2_netexec_smb_fingerprint_preview' for item in payload)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_scan_recommendations_endpoint_404_for_missing_scan(client):
    engine, _Session = _install_sqlite_override()
    try:
        response = client.get('/api/v2/scans/missing-scan/recommendations')

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_recommendation_endpoints_do_not_create_jobs(client):
    engine, Session = _install_sqlite_override()
    try:
        created = client.post(
            '/api/v2/scans',
            json={'name': 'No RQ recommendation', 'scan_type': 'manual'},
        )
        scan_id = created.json()['id']

        assert client.get('/api/v2/recommendations/catalog').status_code == 200
        assert client.get(f'/api/v2/scans/{scan_id}/recommendations').status_code == 200
        assert (
            client.post(
                '/api/v2/recommendations/preview',
                json={
                    'template_id': 'v2_netexec_smb_fingerprint_preview',
                    'params': {'target': '10.0.0.5'},
                },
            ).status_code
            == 200
        )

        db = Session()
        try:
            assert db.query(Job).count() == 0
        finally:
            db.close()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def test_recommendation_router_does_not_import_subprocess():
    import app.api.routes_v2_recommendations as routes

    assert not hasattr(routes, 'subprocess')
