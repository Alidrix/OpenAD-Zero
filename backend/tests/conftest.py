import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.db import models  # noqa

@pytest.fixture
def db_session():
    engine=create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine)
    db=Session()
    try:
        yield db
    finally:
        db.close(); Base.metadata.drop_all(engine)
