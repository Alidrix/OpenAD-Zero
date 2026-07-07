import inspect

from app.workers import approved_action_jobs


def test_worker_uses_shell_false_and_argv_list():
    source = inspect.getsource(approved_action_jobs.run_approved_action)
    assert 'run_process(' in source and 'ctx.argv' in source
    assert 'subprocess.run(' not in source
    assert 'shell=True' not in source
