from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.schema_health import check_schema
from app.db.session import engine

logger = logging.getLogger(__name__)

WEAK_VALUES = {'change-me', 'openadzero', 'password', 'admin', 'neo4j', 'neo4j/password'}


def _is_weak(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized in WEAK_VALUES
        or normalized.startswith('change-me')
        or normalized.endswith('/change-me-neo4j')
    )


def validate_secret_strength_for_environment() -> None:
    settings = get_settings()
    env = settings.openadzero_env
    candidates = {
        'OPENADZERO_API_TOKEN': settings.openadzero_api_token if settings.openadzero_auth_enabled else None,
        'BLOODHOUND_API_TOKEN': settings.bloodhound_api_token if settings.bloodhound_enabled else None,
        'POSTGRES_PASSWORD': settings.postgres_password,
        'NEO4J_PASSWORD': settings.neo4j_password,
    }
    weak = [name for name, value in candidates.items() if value is not None and _is_weak(value)]
    if env == 'prod-like' and weak:
        raise RuntimeError(f'Weak or empty secret values are not allowed in prod-like mode: {", ".join(sorted(weak))}')
    if env == 'dev' and weak:
        logger.warning(
            'Weak development placeholder secrets detected; replace them before prod-like use: %s',
            ', '.join(sorted(weak)),
        )


def validate_auth_exposure_policy() -> None:
    settings = get_settings()
    if settings.openadzero_env == 'prod-like' and not settings.openadzero_auth_enabled:
        raise RuntimeError('OPENADZERO_ENV=prod-like requires OPENADZERO_AUTH_ENABLED=true')
    if settings.openadzero_auth_enabled and not settings.openadzero_api_token:
        raise RuntimeError(
            'OPENADZERO_AUTH_ENABLED=true requires a non-empty OPENADZERO_API_TOKEN or OPENADZERO_API_TOKEN_FILE'
        )
    if settings.openadzero_env == 'dev' and not settings.openadzero_auth_enabled:
        logger.warning('Authentication is disabled in dev; do not expose the API beyond a trusted local lab network.')


def validate_schema_policy() -> None:
    settings = get_settings()
    if not settings.openadzero_require_schema_ready:
        return
    health = check_schema(engine)
    if not health['ok']:
        raise RuntimeError(f'Database schema is not ready: {health["migration_hint"]}')


def run_startup_checks() -> None:
    validate_secret_strength_for_environment()
    validate_auth_exposure_policy()
    validate_schema_policy()
