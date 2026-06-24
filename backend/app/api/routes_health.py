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
