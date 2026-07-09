import asyncio

import pytest
from fastapi import HTTPException

from src.api.auth_dependencies import get_current_user, get_optional_current_user
from src.firebase.auth import AuthenticatedUser, InvalidFirebaseToken

FAKE_USER = AuthenticatedUser(uid="uid-1", email="a@example.com", display_name="A", photo_url=None)


def _fake_verify_ok(token):
    if token == "good-token":
        return FAKE_USER
    raise InvalidFirebaseToken("bad token")


def _run(coro):
    return asyncio.run(coro)


def test_get_current_user_rejects_missing_header(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    monkeypatch.setattr("src.api.auth_dependencies.upsert_user_profile", lambda user: None)

    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(authorization=None))
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_malformed_header(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    monkeypatch.setattr("src.api.auth_dependencies.upsert_user_profile", lambda user: None)

    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(authorization="good-token"))
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    monkeypatch.setattr("src.api.auth_dependencies.upsert_user_profile", lambda user: None)

    with pytest.raises(HTTPException) as exc_info:
        _run(get_current_user(authorization="Bearer bad-token"))
    assert exc_info.value.status_code == 401


def test_get_current_user_accepts_valid_token_and_derives_uid(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    calls = []
    monkeypatch.setattr(
        "src.api.auth_dependencies.upsert_user_profile", lambda user: calls.append(user)
    )

    user = _run(get_current_user(authorization="Bearer good-token"))
    assert user.uid == "uid-1"
    assert calls == [FAKE_USER]


def test_get_optional_current_user_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    result = _run(get_optional_current_user(authorization=None))
    assert result is None


def test_get_optional_current_user_returns_none_for_invalid_token(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    result = _run(get_optional_current_user(authorization="Bearer bad-token"))
    assert result is None


def test_get_optional_current_user_returns_user_for_valid_token(monkeypatch):
    monkeypatch.setattr("src.api.auth_dependencies.verify_id_token", _fake_verify_ok)
    result = _run(get_optional_current_user(authorization="Bearer good-token"))
    assert result == FAKE_USER
