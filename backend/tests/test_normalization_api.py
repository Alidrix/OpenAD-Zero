from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.paths import get_evidence_root, safe_join_under_root
from app.db.models import Scan
from app.db.session import Base, get_db
from app.main import app
from app.services.scan_service import add_scan_artifact

FIX = Path(__file__).parent / 'fixtures/normalization/nmap/sample.xml'


def test_normalization_api(client):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        app.dependency_overrides[get_db] = lambda: db
        s = Scan(name='api', scan_type='manual', tool_name='nmap')
        db.add(s)
        db.commit()
        root = get_evidence_root(create=True)
        dst = safe_join_under_root(root, 'api-nmap.xml')
        dst.write_text(FIX.read_text())
        art = add_scan_artifact(db, s.id, 'nmap_xml', str(dst), None, dst.stat().st_size)
        db.commit()
        assert client.post(f'/api/v2/scans/{s.id}/normalize').status_code == 200
        res = client.post(f'/api/v2/scans/{s.id}/artifacts/{art.id}/normalize')
        assert res.status_code == 200
        assert client.get(f'/api/v2/scans/{s.id}/normalized/summary').json()['assets_count'] == 1
        assert client.get(f'/api/v2/scans/{s.id}/normalized/ad-objects?limit=1&offset=0').status_code == 200
        assert client.post(f'/api/v2/scans/{s.id}/artifacts/nope/normalize').status_code == 404
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(engine)
