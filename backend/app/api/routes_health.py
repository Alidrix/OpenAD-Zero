import shutil
import subprocess

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.auth import require_api_token
from app.core.config import get_settings
from app.core.version import get_app_version
from app.db.session import engine
from app.queue.connection import get_redis_connection

router = APIRouter()


@router.get('/health')
def health():
    return {'status': 'ok', 'service': 'openadzero-api'}


@router.get('/version')
def version():
    return {'name': 'OpenAD Zero', 'version': get_app_version(), 'release_stage': 'release-candidate'}


@router.get('/health/db', dependencies=[Depends(require_api_token)])
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'unavailable', 'error': str(exc)}


@router.get('/health/redis', dependencies=[Depends(require_api_token)])
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


@router.get('/health/tools', dependencies=[Depends(require_api_token)])
def health_tools():
    settings = get_settings()
    return {
        'nmap': tool_status('nmap'),
        'netexec': tool_status('nxc'),
        'nuclei': tool_status('nuclei'),
        'bloodhound': {'enabled': settings.bloodhound_enabled, 'configured': bool(settings.bloodhound_api_token)},
    }


@router.get('/health/worker', dependencies=[Depends(require_api_token)])
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


@router.get('/auth/status')
def auth_status():
    settings = get_settings()
    return {
        'auth_enabled': settings.openadzero_auth_enabled,
        'localhost_bypass_enabled': settings.openadzero_allow_unauthenticated_localhost,
        'token_configured': bool(settings.openadzero_api_token),
    }
