import os
import signal
import sys
from pathlib import Path

from app.core.process_runner import run_process


def test_run_process_timeout_kills_process_group(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    pidfile = tmp_path / 'run' / 'child.pid'
    code = f"""
import os, subprocess, sys, time
p=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
open({str(pidfile)!r}, 'w').write(str(p.pid))
time.sleep(30)
"""
    result = run_process([sys.executable, '-c', code], tmp_path / 'run', timeout_seconds=1)
    assert result.status == 'timeout'
    assert result.timed_out is True
    pid = int(pidfile.read_text())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        alive = False
    else:
        stat = Path(f'/proc/{pid}/stat')
        alive = stat.exists() and ' Z ' not in stat.read_text(errors='ignore')
        if alive:
            os.kill(pid, signal.SIGKILL)
    assert alive is False
