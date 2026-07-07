import sys

from app.core.process_runner import run_process


def test_run_process_redacts_secrets_from_tails(tmp_path, monkeypatch):
    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()
    secret = 'SuperSecret123!'
    result = run_process(
        [sys.executable, '-c', f"print('password={secret} token={secret} Authorization: Bearer {secret}')"],
        tmp_path / 'run',
        redaction_patterns=[secret],
    )
    assert secret not in result.stdout_tail
    assert '********' in result.stdout_tail
