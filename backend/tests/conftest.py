import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.db import models

@pytest.fixture
def db_session():
    engine=create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db=Session()
    try:
        yield db
    finally:
        db.close(); Base.metadata.drop_all(engine); engine.dispose()

@pytest.fixture
def client(db_session, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    app.dependency_overrides[get_db]=lambda: db_session
    monkeypatch.setattr('app.queue.connection.get_redis_connection', lambda: type('R',(),{'ping':lambda self: True,'llen':lambda self,k: 0})())
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()

@pytest.fixture
def demo_mission(db_session):
    from app.demo.seed_demo import seed_demo
    return seed_demo(db_session)

@pytest.fixture
def demo_host(db_session, demo_mission):
    return db_session.query(models.Host).filter_by(mission_id=demo_mission.id).first()

@pytest.fixture
def demo_finding(db_session, demo_mission):
    return db_session.query(models.Finding).filter_by(mission_id=demo_mission.id).first()

@pytest.fixture
def demo_evidence(db_session, demo_mission):
    return db_session.query(models.Evidence).filter_by(mission_id=demo_mission.id).first()
