from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


def test_parsing_api(client):
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
        scan = client.post(
            '/api/v2/scans', json={'name': 'Parsing', 'scan_type': 'manual', 'tool_name': 'manual'}
        ).json()
        sid = scan['id']
        assert client.post(f'/api/v2/scans/{sid}/parse-persisted').status_code == 200
        assert client.get(f'/api/v2/scans/{sid}/parsed/assets').status_code == 200
        assert client.get(f'/api/v2/scans/{sid}/parsed/services').status_code == 200
        assert client.get(f'/api/v2/scans/{sid}/parsed/signals').status_code == 200
        assert client.get(f'/api/v2/scans/{sid}/parsed/diagnostics').status_code == 200
        assert client.post('/api/v2/scans/missing/parse-persisted').status_code == 404
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
