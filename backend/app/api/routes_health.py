import shutil, subprocess
from fastapi import APIRouter
router=APIRouter()
@router.get('/health')
def health(): return {'status':'ok'}

def tool_status(binary: str):
    path=shutil.which(binary)
    if not path: return {'available':False,'version':None}
    try:
        r=subprocess.run([binary,'--version'], capture_output=True, text=True, timeout=5)
        version=(r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else 'available'
    except Exception:
        version='available'
    return {'available':True,'version':version}
@router.get('/health/tools')
def health_tools(): return {'nmap':tool_status('nmap'),'netexec':tool_status('nxc'),'nuclei':tool_status('nuclei')}

@router.get('/health/worker')
def health_worker():
    try:
        from app.queue.connection import get_redis_connection
        r=get_redis_connection(); r.ping()
        return {'redis_available':True,'queue_default_size':r.llen('rq:queue:openadzero-default'),'queue_scans_size':r.llen('rq:queue:openadzero-scans')}
    except Exception as exc:
        return {'redis_available':False,'error':str(exc)}
