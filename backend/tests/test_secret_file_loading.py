import pytest

from app.core.config import Settings, get_settings, read_secret_value


def test_openadzero_api_token_file_loaded(monkeypatch, tmp_path):
    token_file = tmp_path / 'token'
    token_file.write_text('file-token\n')
    monkeypatch.setenv('OPENADZERO_API_TOKEN_FILE', str(token_file))
    monkeypatch.delenv('OPENADZERO_API_TOKEN', raising=False)
    get_settings.cache_clear()
    assert Settings().openadzero_api_token == 'file-token'


def test_openadzero_api_token_file_missing_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv('OPENADZERO_API_TOKEN_FILE', str(tmp_path / 'missing'))
    with pytest.raises(RuntimeError, match='unreadable secret file'):
        read_secret_value('OPENADZERO_API_TOKEN')
