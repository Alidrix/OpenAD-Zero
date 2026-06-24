from redis import Redis
from rq import Queue
from app.core.config import get_settings

def get_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)

def get_default_queue() -> Queue:
    return Queue('openadzero-default', connection=get_redis_connection())

def get_scan_queue() -> Queue:
    return Queue('openadzero-scans', connection=get_redis_connection())
