from sqlalchemy import inspect, text
from app.db.session import Base, engine
from app.db import models

def init_db():
    Base.metadata.create_all(bind=engine)
    # create_all does not alter existing MVP databases; keep lightweight additive hardening.
    try:
        insp=inspect(engine)
        cols={c['name'] for c in insp.get_columns('jobs')}
        additions={
            'rq_job_id':'VARCHAR(255)', 'queued_at':'TIMESTAMP', 'cancel_requested_at':'TIMESTAMP',
            'last_heartbeat_at':'TIMESTAMP', 'attempts':'INTEGER DEFAULT 0', 'max_attempts':'INTEGER DEFAULT 1',
            'error_message':'TEXT'
        }
        with engine.begin() as conn:
            for name, ddl in additions.items():
                if name not in cols: conn.execute(text(f'ALTER TABLE jobs ADD COLUMN {name} {ddl}'))
    except Exception:
        pass
