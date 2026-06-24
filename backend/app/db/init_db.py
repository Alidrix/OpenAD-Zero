import logging
import subprocess
import sys
from pathlib import Path
from sqlalchemy import inspect, text
from app.core.config import get_settings
from app.db.session import Base, engine
from app.db import models  # noqa: F401

logger = logging.getLogger(__name__)

def init_db_dev_only() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        insp = inspect(engine)
        cols = {c['name'] for c in insp.get_columns('jobs')}
        additions = {
            'rq_job_id': 'VARCHAR(255)', 'queued_at': 'TIMESTAMP', 'cancel_requested_at': 'TIMESTAMP',
            'last_heartbeat_at': 'TIMESTAMP', 'attempts': 'INTEGER DEFAULT 0', 'max_attempts': 'INTEGER DEFAULT 1',
            'error_message': 'TEXT'
        }
        with engine.begin() as conn:
            for name, ddl in additions.items():
                if name not in cols:
                    conn.execute(text(f'ALTER TABLE jobs ADD COLUMN {name} {ddl}'))
    except Exception:
        logger.exception('dev-only schema hardening skipped')

def run_migrations() -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=backend_dir, check=True)

def init_db() -> None:
    settings = get_settings()
    if settings.openadzero_run_migrations_on_startup:
        run_migrations()
    elif settings.openadzero_auto_create_tables:
        logger.warning('OPENADZERO_AUTO_CREATE_TABLES is enabled; use Alembic migrations for normal runs.')
        init_db_dev_only()
