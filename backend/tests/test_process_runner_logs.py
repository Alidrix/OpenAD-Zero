import sys

from app.core.process_runner import run_process


def test_run_process_tail_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    monkeypatch.setenv('OPENADZERO_PROCESS_LOG_TAIL_BYTES', '50')
    from app.core.config import get_settings

    get_settings.cache_clear()
    result = run_process([sys.executable, '-c', "print('A'*200)"], tmp_path / 'run')
    assert len(result.stdout_tail.encode()) <= 60
