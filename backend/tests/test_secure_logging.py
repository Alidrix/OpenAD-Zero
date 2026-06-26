from app.core.logging import redact_dict, redact_value


def test_redact_value_preserves_none_and_redacts_other_values():
    assert redact_value(None) is None
    assert redact_value('secret') == '***REDACTED***'


def test_redact_dict_masks_sensitive_values_and_preserves_safe_values():
    data = {
        'token': 'abc',
        'password': 'pw',
        'database_url': 'postgres://user:pass@db/app',
        'name': 'mission',
        'nested': {'bloodhound_api_token': 'bh', 'count': 3},
    }

    assert redact_dict(data) == {
        'token': '***REDACTED***',
        'password': '***REDACTED***',
        'database_url': '***REDACTED***',
        'name': 'mission',
        'nested': {'bloodhound_api_token': '***REDACTED***', 'count': 3},
    }
