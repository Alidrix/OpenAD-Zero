import os, tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.db import models  # noqa

@pytest.fixture
def db_session(monkeypatch):
    tmp=tempfile.mkdtemp(prefix='openadzero-test-evidence-')
    monkeypatch.setenv('EVIDENCE_DIR', tmp)
    engine=create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine, expire_on_commit=False)
    db=Session()
    try:
        yield db
    finally:
        db.close(); Base.metadata.drop_all(engine)

@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db]=override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def demo_mission(db_session):
    from app.demo.seed_demo import seed_demo
    from app.db.models import Mission
    res=seed_demo(db_session)
    return db_session.get(Mission, res['mission_id'])

@pytest.fixture
def demo_host(db_session, demo_mission):
    from app.db.models import Host
    return db_session.query(Host).filter_by(mission_id=demo_mission.id).first()

@pytest.fixture
def demo_finding(db_session, demo_mission):
    from app.db.models import Finding
    return db_session.query(Finding).filter_by(mission_id=demo_mission.id).first()

@pytest.fixture
def demo_evidence(db_session, demo_mission):
    from app.db.models import Evidence
    return db_session.query(Evidence).filter_by(mission_id=demo_mission.id).first()
