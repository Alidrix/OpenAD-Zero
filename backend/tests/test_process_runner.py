import sys
from pathlib import Path

import pytest

from app.core.process_runner import run_process


def test_run_process_executes_argv_and_writes_logs(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    cwd = tmp_path / 'run'
    result = run_process([sys.executable, '-c', "import sys; print('ok'); print('err', file=sys.stderr)"], cwd)
    assert result.status == 'completed'
    assert result.return_code == 0
    assert result.stdout_tail.strip() == 'ok'
    assert result.stderr_tail.strip() == 'err'
    assert Path(result.stdout_path).exists()
    assert Path(result.stderr_path).exists()


def test_run_process_refuses_string_command(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(TypeError):
        run_process('echo ok', tmp_path / 'run')  # type: ignore[arg-type]


def test_run_process_failed_return_code(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    result = run_process([sys.executable, '-c', 'raise SystemExit(7)'], tmp_path / 'run')
    assert result.status == 'failed'
    assert result.return_code == 7


def test_run_process_refuses_cwd_outside_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'evidence'))
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(ValueError):
        run_process([sys.executable, '-c', 'print(1)'], tmp_path / 'outside')
