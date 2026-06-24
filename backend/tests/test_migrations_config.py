from pathlib import Path
from app.core.config import Settings

def test_schema_lifecycle_settings_exist():
    settings = Settings()
    assert hasattr(settings, 'openadzero_auto_create_tables')
    assert hasattr(settings, 'openadzero_run_migrations_on_startup')

def test_alembic_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'alembic.ini').exists()
    assert (root / 'alembic' / 'env.py').exists()
    assert list((root / 'alembic' / 'versions').glob('*.py'))
