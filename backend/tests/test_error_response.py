from app.core.errors import error_response


def test_error_response_format_defaults_details():
    assert error_response('not_found', 'Missing') == {
        'error': {'code': 'not_found', 'message': 'Missing', 'details': {}}
    }


def test_error_response_preserves_details():
    assert error_response('invalid', 'Bad input', {'field': 'scope'}) == {
        'error': {'code': 'invalid', 'message': 'Bad input', 'details': {'field': 'scope'}}
    }
