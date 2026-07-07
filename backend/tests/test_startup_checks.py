import logging

import pytest

from app.core.config import get_settings
from app.core.startup_checks import (
    run_startup_checks,
    validate_auth_exposure_policy,
    validate_secret_strength_for_environment,
)


def test_auth_disabled_in_dev_warns(monkeypatch, caplog):
    monkeypatch.setenv('OPENADZERO_ENV', 'dev')
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'false')
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        validate_auth_exposure_policy()
    assert 'Authentication is disabled in dev' in caplog.text


def test_auth_disabled_in_prod_like_refused(monkeypatch):
    monkeypatch.setenv('OPENADZERO_ENV', 'prod-like')
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'false')
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        validate_auth_exposure_policy()


def test_auth_enabled_empty_token_refused(monkeypatch):
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.delenv('OPENADZERO_API_TOKEN', raising=False)
    monkeypatch.delenv('OPENADZERO_API_TOKEN_FILE', raising=False)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        validate_auth_exposure_policy()


def test_weak_secret_refused_in_prod_like(monkeypatch):
    monkeypatch.setenv('OPENADZERO_ENV', 'prod-like')
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', 'change-me-token')
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        validate_secret_strength_for_environment()


def test_weak_secret_tolerated_in_dev(monkeypatch, caplog):
    monkeypatch.setenv('OPENADZERO_ENV', 'dev')
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', 'change-me-token')
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        validate_secret_strength_for_environment()
    assert 'change-me-token' not in caplog.text


def test_startup_checks_do_not_log_secret_values(monkeypatch, caplog):
    monkeypatch.setenv('OPENADZERO_ENV', 'dev')
    monkeypatch.setenv('OPENADZERO_AUTH_ENABLED', 'true')
    monkeypatch.setenv('OPENADZERO_API_TOKEN', 'change-me-super-secret')
    get_settings.cache_clear()
    with caplog.at_level(logging.WARNING):
        run_startup_checks()
    assert 'change-me-super-secret' not in caplog.text
