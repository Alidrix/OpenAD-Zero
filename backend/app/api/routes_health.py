import shutil
import subprocess

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.queue.connection import get_redis_connection

router = APIRouter()


@router.get('/health')
def health():
    return {'status': 'ok', 'service': 'openadzero-api'}


@router.get('/health/db')
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'unavailable', 'error': str(exc)}


@router.get('/health/redis')
def health_redis():
    try:
        get_redis_connection().ping()
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'unavailable', 'error': str(exc)}


def tool_status(binary: str):
    path = shutil.which(binary)
    if not path:
        return {'available': False, 'version': None}
    try:
        r = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=5)
        version = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else 'available'
    except Exception:
        version = 'available'
    return {'available': True, 'version': version}


@router.get('/health/tools')
def health_tools():
    settings = get_settings()
    return {
        'nmap': tool_status('nmap'),
        'netexec': tool_status('nxc'),
        'nuclei': tool_status('nuclei'),
        'bloodhound': {'enabled': settings.bloodhound_enabled, 'configured': bool(settings.bloodhound_api_token)},
    }


@router.get('/health/worker')
def health_worker():
    try:
        r = get_redis_connection()
        r.ping()
        return {
            'redis_available': True,
            'queues': {
                'openadzero-default': r.llen('rq:queue:openadzero-default'),
                'openadzero-scans': r.llen('rq:queue:openadzero-scans'),
            },
        }
    except Exception as exc:
        return {'redis_available': False, 'queues': {'openadzero-default': 0, 'openadzero-scans': 0}, 'error': str(exc)}
