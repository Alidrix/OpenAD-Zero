from pathlib import Path


def test_approved_action_worker_uses_common_process_runner():
    source = Path('app/workers/approved_action_jobs.py').read_text()
    assert 'from app.core.process_runner import run_process' in source
    assert 'subprocess.run' not in source
