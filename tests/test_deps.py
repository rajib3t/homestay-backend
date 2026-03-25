import pytest
from types import SimpleNamespace

from app.deps import get_current_user, get_token_service
from app.core.exceptions import AppException
from app.repositories.redis_token_repository import RedisTokenRepository


class FakeRequest:
    def __init__(self, headers=None, cookies=None):
        self.headers = headers or {}
        self.cookies = cookies or {}


def test_get_current_user_missing_token():
    req = FakeRequest()
    with pytest.raises(AppException):
        get_current_user(req)


def test_get_current_user_header(monkeypatch):
    # Patch JWTHandler.decode_token to return a valid payload
    monkeypatch.setattr("app.deps.JWTHandler.decode_token", lambda token: {"sub": "user123", "type": "access"})
    req = FakeRequest(headers={"Authorization": "Bearer sometoken"})
    user = get_current_user(req)
    assert user == "user123"


def test_get_current_user_cookie(monkeypatch):
    monkeypatch.setattr("app.deps.JWTHandler.decode_token", lambda token: {"sub": "cookie-user", "type": "access"})
    req = FakeRequest(cookies={"access_token": "cookietoken"})
    user = get_current_user(req)
    assert user == "cookie-user"


def test_get_token_service_uses_redis_when_available(monkeypatch):
    fake_redis = object()

    monkeypatch.setattr("app.deps.get_redis", lambda: fake_redis)
    service = get_token_service(db={})

    assert isinstance(service.session_repository, RedisTokenRepository)
    assert service.session_repository.redis is fake_redis
