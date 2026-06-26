import sys

from sqlalchemy import text

from app.db.session import engine
from app.queue.connection import get_redis_connection


def main() -> int:
    try:
        get_redis_connection().ping()
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return 0
    except Exception as exc:
        print(f'worker healthcheck failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
