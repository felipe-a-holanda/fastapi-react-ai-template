{% raw %}
"""Unit tests for auth utilities and exception handling."""
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from jose import jwt

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.exceptions import AppError, app_exception_handler


# --- Password hashing ---


def test_hash_password_returns_non_plaintext():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert len(hashed) > 0


def test_verify_password_correct():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mysecret")
    assert verify_password("wrongpass", hashed) is False


# --- JWT tokens ---


def test_create_access_token_has_correct_type():
    token = create_access_token(42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_create_refresh_token_has_correct_type():
    token = create_refresh_token(42)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_decode_invalid_token_returns_none():
    assert decode_token("this.is.not.valid") is None


def test_decode_expired_token_returns_none():
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(hours=1), "type": "access"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    assert decode_token(expired) is None


def test_decode_valid_token_returns_payload():
    token = create_access_token(99)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "99"


# --- AppError and exception handler ---


def test_app_error_stores_attributes():
    err = AppError(status_code=404, detail="Not found")
    assert err.status_code == 404
    assert err.detail == "Not found"


@pytest.mark.asyncio
async def test_app_exception_handler_returns_json_response():
    mock_request = MagicMock()
    err = AppError(status_code=422, detail="Invalid input")
    response = await app_exception_handler(mock_request, err)
    assert response.status_code == 422
    body = json.loads(response.body)
    assert body["detail"] == "Invalid input"
{% endraw %}
