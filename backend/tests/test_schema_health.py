from fastapi.testclient import TestClient
from sqlalchemy import Column, MetaData, String, Table, create_engine

from app.db.schema_health import REQUIRED_COLUMNS, REQUIRED_TABLES, check_schema


def _create_required_schema(engine):
    metadata = MetaData()
    for table in REQUIRED_TABLES:
        cols = [Column('id', String, primary_key=True)]
        for col in REQUIRED_COLUMNS.get(table, set()):
            if col != 'id':
                cols.append(Column(col, String))
        Table(table, metadata, *cols)
    metadata.create_all(engine)


def test_schema_health_ok_when_required_tables_exist():
    engine = create_engine('sqlite:///:memory:')
    _create_required_schema(engine)
    health = check_schema(engine)
    assert health['ok'] is True
    assert health['missing_tables'] == []
    assert health['missing_columns'] == {}


def test_schema_health_lists_missing_tables():
    engine = create_engine('sqlite:///:memory:')
    health = check_schema(engine)
    assert health['ok'] is False
    assert 'missions' in health['missing_tables']
    assert health['migration_hint']


def test_schema_health_lists_missing_columns():
    engine = create_engine('sqlite:///:memory:')
    metadata = MetaData()
    for table in REQUIRED_TABLES:
        Table(table, metadata, Column('id', String, primary_key=True))
    metadata.create_all(engine)
    health = check_schema(engine)
    assert health['ok'] is False
    assert 'dedupe_key' in health['missing_columns']['pentest_actions']


def test_schema_health_endpoint_protected_when_auth_enabled(monkeypatch):
    from app.core.config import get_settings
    from app.main import app

    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', 'schema-health-token')
    monkeypatch.setenv('OPENADZERO_ALLOW_UNAUTHENTICATED_LOCALHOST', 'false')
    get_settings.cache_clear()
    with TestClient(app) as client:
        assert client.get('/api/health/schema').status_code == 401
        assert (
            client.get('/api/health/schema', headers={'Authorization': 'Bearer schema-health-token'}).status_code == 200
        )
    get_settings.cache_clear()
