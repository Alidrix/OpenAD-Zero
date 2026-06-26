import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import models  # noqa
from app.db.session import Base


@pytest.fixture(autouse=True)
def isolated_evidence_dir(tmp_path, monkeypatch):
    from app.core.config import get_settings

    evidence_root = tmp_path / 'evidence'
    monkeypatch.setenv('EVIDENCE_DIR', str(evidence_root))
    monkeypatch.setenv('TESTING', 'true')

    get_settings.cache_clear()
    yield evidence_root
    get_settings.cache_clear()


@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
