from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


def test_v2_scan_api_lifecycle(client):
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
        created = client.post('/api/v2/scans', json={'name': 'API scan', 'scan_type': 'manual'}).json()
        scan_id = created['id']
        assert created['status'] == 'draft'

        assert client.get('/api/v2/scans').json()[0]['id'] == scan_id
        assert client.get(f'/api/v2/scans/{scan_id}').json()['name'] == 'API scan'
        assert client.patch(f'/api/v2/scans/{scan_id}/rename', json={'name': 'Renamed'}).json()['name'] == 'Renamed'
        assert client.post(f'/api/v2/scans/{scan_id}/stop').json()['status'] == 'stopped'
        assert client.get(f'/api/v2/scans/{scan_id}/events').status_code == 200
        assert client.get(f'/api/v2/scans/{scan_id}/artifacts').json() == []
        assert client.delete(f'/api/v2/scans/{scan_id}').json()['status'] == 'deleted'
        assert client.get('/api/v2/scans').json() == []
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
