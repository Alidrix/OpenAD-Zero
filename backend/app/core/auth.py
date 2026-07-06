"""Local API-token authentication helpers for HTTP and WebSocket routes.

The localhost bypass intentionally uses only the peer address reported by the
ASGI server (`request.client.host` / `websocket.client.host`). It does not trust
`X-Forwarded-For` or other proxy-supplied headers by default, because those can
be spoofed by direct clients unless a trusted proxy layer sanitizes them.
"""

from __future__ import annotations

import hmac
from ipaddress import ip_address, ip_network
from typing import Annotated

from fastapi import Depends, HTTPException, Request, WebSocket, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)
LOCALHOST_NAMES = {'localhost'}
LOCALHOST_NETWORKS = (ip_network('127.0.0.0/8'), ip_network('::1/128'))


def redact_token(token: str | None) -> str:
    if not token:
        return '<empty>'
    if len(token) <= 8:
        return '<redacted>'
    return f'{token[:4]}...{token[-4:]}'


def _auth_enabled() -> bool:
    return get_settings().openadzero_auth_enabled


def _configured_token() -> str:
    return get_settings().openadzero_api_token


def validate_auth_configuration() -> None:
    settings = get_settings()
    if settings.openadzero_auth_enabled and not settings.openadzero_api_token:
        raise RuntimeError('OPENADZERO_AUTH_ENABLED=true requires OPENADZERO_API_TOKEN to be configured')


def _is_localhost_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.strip().lower().removeprefix('[').removesuffix(']')
    if normalized in LOCALHOST_NAMES:
        return True
    try:
        ip = ip_address(normalized)
    except ValueError:
        return False
    return any(ip in network for network in LOCALHOST_NETWORKS)


def is_request_from_localhost(request: Request) -> bool:
    return _is_localhost_host(request.client.host if request.client else None)


def _localhost_bypass_allowed(request: Request) -> bool:
    settings = get_settings()
    return settings.openadzero_allow_unauthenticated_localhost and is_request_from_localhost(request)


def _token_matches(token: str | None) -> bool:
    expected = _configured_token()
    if not expected or token is None:
        return False
    return hmac.compare_digest(token, expected)


def _credentials_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if credentials and credentials.scheme.lower() == 'bearer':
        return credentials.credentials
    return None


def optional_api_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> bool:
    if not _auth_enabled():
        return True
    validate_auth_configuration()
    if _localhost_bypass_allowed(request):
        return True
    return _token_matches(_credentials_token(credentials))


def require_api_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> bool:
    if optional_api_token(request, credentials):
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Valid API bearer token required',
        headers={'WWW-Authenticate': 'Bearer'},
    )


def _websocket_localhost_bypass_allowed(websocket: WebSocket) -> bool:
    settings = get_settings()
    return settings.openadzero_allow_unauthenticated_localhost and _is_localhost_host(
        websocket.client.host if websocket.client else None
    )


def _websocket_bearer_token(websocket: WebSocket) -> str | None:
    auth_header = websocket.headers.get('authorization')
    if not auth_header:
        return None
    scheme, _, token = auth_header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return None
    return token


async def require_ws_token(websocket: WebSocket) -> bool:
    if not _auth_enabled():
        return True
    validate_auth_configuration()
    if _websocket_localhost_bypass_allowed(websocket):
        return True
    token = websocket.query_params.get('token') or _websocket_bearer_token(websocket)
    if _token_matches(token):
        return True
    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason='Valid API bearer token required')
