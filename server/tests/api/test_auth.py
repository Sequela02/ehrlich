"""Tests for WorkOS JWT authentication middleware."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ehrlich.api.auth import (
    get_current_user,
    get_current_user_sse,
    get_optional_user,
)

# Generate a test RSA key pair for JWT signing
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def _make_token(
    sub: str = "user_workos_123",
    email: str = "test@example.com",
    algorithm: str = "RS256",
) -> str:
    return pyjwt.encode({"sub": sub, "email": email}, _private_key, algorithm=algorithm)


def _mock_signing_key() -> MagicMock:
    """Create a mock signing key that returns our test public key."""
    mock_key = MagicMock()
    mock_key.key = _public_key
    return mock_key


def _build_test_app() -> FastAPI:
    """Build a minimal FastAPI app with auth dependencies."""
    from fastapi import Depends

    app = FastAPI()

    _user_dep = Depends(get_current_user)
    _optional_dep = Depends(get_optional_user)
    _sse_dep = Depends(get_current_user_sse)

    @app.get("/protected")
    async def protected(user: dict = _user_dep):  # type: ignore[assignment]
        return user

    @app.get("/optional")
    async def optional(user: dict | None = _optional_dep):  # type: ignore[assignment]
        return {"user": user}

    @app.get("/sse")
    async def sse(user: dict = _sse_dep):  # type: ignore[assignment]
        return user

    return app


@pytest.fixture
def app() -> FastAPI:
    return _build_test_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def _patch_workos():
    """Patch WorkOS client ID and JWKS client for test JWT verification."""
    mock_jwks = MagicMock()
    mock_jwks.get_signing_key_from_jwt.return_value = _mock_signing_key()

    settings_patch = patch(
        "ehrlich.api.auth.get_settings",
        return_value=MagicMock(workos_client_id="test_client_id"),
    )
    jwks_patch = patch(
        "ehrlich.api.auth._get_jwks_client",
        return_value=mock_jwks,
    )
    return settings_patch, jwks_patch


class TestGetCurrentUser:
    def test_missing_auth_header_returns_401(self, client: TestClient) -> None:
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing or invalid Authorization header" in response.json()["detail"]

    def test_malformed_header_no_bearer_returns_401(self, client: TestClient) -> None:
        response = client.get("/protected", headers={"Authorization": "Token abc"})
        assert response.status_code == 401

    def test_empty_bearer_returns_401(self, client: TestClient) -> None:
        response = client.get("/protected", headers={"Authorization": "Basic abc123"})
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        settings_patch, jwks_patch = _patch_workos()
        # Make JWKS raise a JWT error for invalid token
        with settings_patch, jwks_patch as mock_jwks_fn:
            mock_jwks_fn.return_value.get_signing_key_from_jwt.side_effect = (
                pyjwt.exceptions.PyJWTError("Invalid token")
            )
            response = client.get(
                "/protected", headers={"Authorization": "Bearer invalid.token.here"}
            )
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    def test_valid_token_returns_user(self, client: TestClient) -> None:
        token = _make_token(sub="user_abc", email="abc@test.com")
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch:
            response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["workos_id"] == "user_abc"
        assert data["email"] == "abc@test.com"

    def test_workos_not_configured_returns_500(self, client: TestClient) -> None:
        with patch(
            "ehrlich.api.auth.get_settings",
            return_value=MagicMock(workos_client_id=""),
        ):
            response = client.get("/protected", headers={"Authorization": "Bearer some.token.here"})
        assert response.status_code == 500
        assert "WorkOS not configured" in response.json()["detail"]


class TestGetOptionalUser:
    def test_no_auth_returns_none(self, client: TestClient) -> None:
        response = client.get("/optional")
        assert response.status_code == 200
        assert response.json() == {"user": None}

    def test_invalid_token_returns_none(self, client: TestClient) -> None:
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch as mock_jwks_fn:
            mock_jwks_fn.return_value.get_signing_key_from_jwt.side_effect = (
                pyjwt.exceptions.PyJWTError("bad")
            )
            response = client.get("/optional", headers={"Authorization": "Bearer bad.token"})
        assert response.status_code == 200
        assert response.json() == {"user": None}

    def test_valid_token_returns_user(self, client: TestClient) -> None:
        token = _make_token(sub="user_opt", email="opt@test.com")
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch:
            response = client.get("/optional", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["workos_id"] == "user_opt"


class TestGetCurrentUserSSE:
    def test_accepts_bearer_header(self, client: TestClient) -> None:
        token = _make_token(sub="user_sse", email="sse@test.com")
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch:
            response = client.get("/sse", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["workos_id"] == "user_sse"

    def test_accepts_query_param(self, client: TestClient) -> None:
        token = _make_token(sub="user_sse_q", email="sseq@test.com")
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch:
            response = client.get(f"/sse?token={token}")
        assert response.status_code == 200
        assert response.json()["workos_id"] == "user_sse_q"

    def test_missing_both_returns_401(self, client: TestClient) -> None:
        response = client.get("/sse")
        assert response.status_code == 401
        assert "Missing authentication" in response.json()["detail"]

    def test_header_takes_precedence_over_query(self, client: TestClient) -> None:
        header_token = _make_token(sub="from_header", email="h@test.com")
        query_token = _make_token(sub="from_query", email="q@test.com")
        settings_patch, jwks_patch = _patch_workos()
        with settings_patch, jwks_patch:
            response = client.get(
                f"/sse?token={query_token}",
                headers={"Authorization": f"Bearer {header_token}"},
            )
        assert response.status_code == 200
        assert response.json()["workos_id"] == "from_header"
