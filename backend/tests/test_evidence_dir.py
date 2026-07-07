import tempfile

import pytest

from app.core.config import get_settings
from app.core.paths import EVIDENCE_SUBDIRS, EvidencePathError, ensure_evidence_dir_writable, get_evidence_root
from app.tool_automation.executor import (
    ToolExecutionRequest,
    compute_command_hash,
    execute_tool_request,
    load_runs,
    tool_runs_dir,
)


def test_evidence_dir_uses_environment_and_creates_subdirs(tmp_path, monkeypatch):
    evidence_dir = tmp_path / 'custom-evidence'
    monkeypatch.setenv('EVIDENCE_DIR', str(evidence_dir))
    get_settings.cache_clear()

    root = get_evidence_root()

    assert root == evidence_dir.resolve()
    for child in EVIDENCE_SUBDIRS:
        assert (root / child).is_dir()


def test_evidence_dir_is_writable(tmp_path):
    root = ensure_evidence_dir_writable(tmp_path / 'evidence')

    marker = root / 'write-ok.txt'
    marker.write_text('ok', encoding='utf-8')

    assert marker.read_text(encoding='utf-8') == 'ok'


def test_evidence_dir_error_is_clear_when_not_writable(tmp_path, monkeypatch):
    def fail_named_tempfile(*args, **kwargs):
        raise PermissionError('denied')

    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', fail_named_tempfile)

    with pytest.raises(EvidencePathError) as exc:
        ensure_evidence_dir_writable(tmp_path / 'evidence')

    message = str(exc.value)
    assert 'Evidence directory is not writable:' in message
    assert 'The container should initialize it automatically.' in message
    assert 'EVIDENCE_DIR' in message


def test_tool_run_storage_uses_evidence_dir(tmp_path, monkeypatch):
    evidence_dir = tmp_path / 'evidence'
    monkeypatch.setenv('EVIDENCE_DIR', str(evidence_dir))
    monkeypatch.delenv('OPENAD_TOOL_RUN_DIR', raising=False)
    monkeypatch.delenv('OPENAD_FINDINGS_DIR', raising=False)
    get_settings.cache_clear()

    assert tool_runs_dir() == evidence_dir.resolve() / 'tool-runs'

    argv = ['nmap', '-sV', '10.0.0.5']
    monkeypatch.setattr('app.tool_automation.executor.shutil.which', lambda _: '/bin/tool')

    class Result:
        return_code = 0
        status = 'completed'
        stdout_tail = ''
        stderr_tail = ''

    monkeypatch.setattr('app.tool_automation.executor.run_process', lambda argv, **kwargs: Result())

    result = execute_tool_request(
        ToolExecutionRequest(
            'nmap_safe_discovery',
            'nmap_safe_discovery',
            '10.0.0.5',
            {'target': '10.0.0.5'},
            compute_command_hash(argv),
            True,
            True,
            scope=['10.0.0.0/24'],
        ),
        argv,
        'nmap -sV 10.0.0.5',
    )

    assert (evidence_dir / 'tool-runs' / f'{result.run_id}.json').is_file()
    assert load_runs()[0]['run_id'] == result.run_id
