SENSITIVE_KEYS = {
    'token',
    'api_token',
    'password',
    'secret',
    'authorization',
    'cookie',
    'database_url',
    'redis_url',
    'bloodhound_api_token',
}


def redact_value(value: object) -> object:
    if value is None:
        return None
    return '***REDACTED***'


def redact_dict(data: dict) -> dict:
    clean = {}
    for key, value in data.items():
        lower = str(key).lower()
        if any(s in lower for s in SENSITIVE_KEYS):
            clean[key] = '***REDACTED***'
        elif isinstance(value, dict):
            clean[key] = redact_dict(value)
        else:
            clean[key] = value
    return clean
