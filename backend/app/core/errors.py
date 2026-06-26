def error_response(code: str, message: str, details: dict | None = None) -> dict:
    return {
        'error': {
            'code': code,
            'message': message,
            'details': details or {},
        }
    }
