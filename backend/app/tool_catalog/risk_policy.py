from __future__ import annotations

from app.tool_catalog.high_risk_policy import RUN_FORBIDDEN_TOKENS
from app.tool_catalog.models import EXECUTION_MODES

SAFE_AUTO_ALLOWED = {'parsing', 'reporting', 'health_check', 'bounded_read_only', 'prompt10_supported_safe'}
DANGEROUS_KEYWORDS = RUN_FORBIDDEN_TOKENS


def can_support_run(execution_mode: str, supported_for_run: bool, risk_level: str) -> tuple[bool, str]:
    if execution_mode not in EXECUTION_MODES:
        return False, 'invalid execution mode'
    if execution_mode in {'manual_only', 'blocked', 'preview_only', 'planned'} and supported_for_run:
        return False, f'{execution_mode} templates cannot be supported for run'
    if risk_level in {'high', 'critical'} and execution_mode == 'safe_auto':
        return False, 'high-risk templates cannot be safe_auto'
    return True, 'ok'


def classify_execution_allowed(execution_mode: str, supported_for_run: bool) -> tuple[bool, int, str]:
    if execution_mode == 'blocked':
        return False, 403, 'Template is blocked by risk policy'
    if execution_mode == 'manual_only':
        return False, 403, 'Template is manual-only and cannot be executed by automation'
    if execution_mode == 'preview_only':
        return False, 403, 'Template is preview-only and cannot be executed by automation'
    if execution_mode == 'planned':
        return False, 501, 'Template execution is planned but not implemented'
    if not supported_for_run:
        return False, 501, 'Template is not executable yet'
    return True, 200, 'Template is executable after required approval and validation'


def contains_dangerous_keyword(argv: list[str]) -> bool:
    text = ' '.join(argv).casefold()
    return any(keyword in text for keyword in DANGEROUS_KEYWORDS)
