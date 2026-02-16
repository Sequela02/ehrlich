"""WorkOS JWT authentication middleware for FastAPI."""

from __future__ import annotations

import logging
from typing import Any

import jwt
from fastapi import HTTPException, Query, Request
from jwt import PyJWKClient

from ehrlich.config import get_settings

logger = logging.getLogger(__name__)

_jwks_client: PyJWKClient | None = None


def _get_jwks_client(client_id: str) -> PyJWKClient:
    global _jwks_client  # noqa: PLW0603
    if _jwks_client is None:
        _jwks_client = PyJWKClient(
            f"https://api.workos.com/sso/jwks/{client_id}",
            cache_keys=True,
        )
    return _jwks_client


def _verify_token(token: str) -> dict[str, Any]:
    """Verify a JWT token and return the payload."""
    settings = get_settings()
    if not settings.workos_client_id:
        raise HTTPException(status_code=500, detail="WorkOS not configured")

    jwks_client = _get_jwks_client(settings.workos_client_id)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            leeway=60,
        )
        return {"workos_id": payload["sub"], "email": payload.get("email", "")}
    except jwt.exceptions.PyJWTError as e:
        logger.warning("JWT validation failed: %s", type(e).__name__)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


async def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI dependency: extract and verify JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return _verify_token(auth_header[7:])


async def get_current_user_sse(
    request: Request,
    token: str | None = Query(default=None),
) -> dict[str, Any]:
    """JWT verification supporting both header and query param (for SSE).

    EventSource API does not support custom headers, so SSE endpoints
    accept the JWT via ``?token=<jwt>`` query parameter as a fallback.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header[7:]
    elif token:
        jwt_token = token
    else:
        raise HTTPException(status_code=401, detail="Missing authentication")
    return _verify_token(jwt_token)


async def get_optional_user(request: Request) -> dict[str, Any] | None:
    """FastAPI dependency: returns user dict if authenticated, None otherwise."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
