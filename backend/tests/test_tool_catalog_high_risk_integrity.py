from app.tool_catalog.high_risk_policy import RUN_FORBIDDEN_TOKENS, validate_template_high_risk_policy
from app.tool_catalog.registry import list_template_metadata


def test_catalog_high_risk_integrity():
    for template in list_template_metadata():
        validate_template_high_risk_policy(template)
        if template.execution_mode in {'manual_only', 'blocked', 'preview_only', 'planned'}:
            assert template.supported_for_run is False
        if template.supported_for_run:
            text = ' '.join(template.argv).casefold().replace('--no-bruteforce', '')
            assert not any(token in text for token in RUN_FORBIDDEN_TOKENS)
