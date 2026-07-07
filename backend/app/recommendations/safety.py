from __future__ import annotations

from app.recommendations.models import V2SafeTemplate


class CatalogSafetyError(ValueError):
    pass


def validate_policy(policy: dict) -> None:
    defaults = policy.get('defaults') or {}
    execution = policy.get('v2_current_execution_policy') or {}
    if defaults.get('allow_automatic_execution') is not False:
        raise CatalogSafetyError('V2 recommendations require allow_automatic_execution=false')
    if execution.get('automatic_execution') is not False:
        raise CatalogSafetyError('V2 recommendations require automatic_execution=false')
    if execution.get('external_tool_execution') is not False:
        raise CatalogSafetyError('V2 recommendations require external_tool_execution=false')


def validate_template(template: V2SafeTemplate, policy: dict) -> None:
    blocked = set(policy.get('blocked_categories') or [])
    allowed_modes = set(policy.get('allowed_modes') or [])
    if template.category in blocked:
        raise CatalogSafetyError(f'Blocked V2 template category: {template.category}')
    if template.mode not in allowed_modes:
        raise CatalogSafetyError(f'Unsupported V2 template mode: {template.mode}')
    if template.mode == 'gated_high_risk' and not template.requires_human_approval:
        raise CatalogSafetyError('gated_high_risk templates require human approval')


def assert_preview_only(policy: dict) -> None:
    validate_policy(policy)
