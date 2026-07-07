from pathlib import Path


def test_initial_discovery_uses_runner_wrapper_backed_by_process_runner():
    source = Path('app/workers/initial_discovery_jobs.py').read_text()
    runner = Path('app/jobs/runner.py').read_text()
    assert 'run_command' in source
    assert 'from app.core.process_runner import run_process' in runner
