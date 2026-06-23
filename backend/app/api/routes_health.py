import shutil, subprocess
from fastapi import APIRouter
router=APIRouter()
@router.get('/health')
def health(): return {'status':'ok'}
def _tool(binary: str):
    path=shutil.which(binary)
    if not path: return {'available': False, 'version': ''}
    try:
        proc=subprocess.run([binary,'--version'], capture_output=True, text=True, timeout=5)
        version=(proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else ''
    except Exception:
        version=''
    return {'available': True, 'version': version}
@router.get('/health/tools')
def health_tools(): return {'nmap': _tool('nmap'), 'netexec': _tool('nxc')}
