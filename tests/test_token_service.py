import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import asyncio

from app.repositories.redis_token_repository import RedisTokenRepository
from app.services.token_service import TokenService
from app.models.token_model import Token
from app.repositories.token_repository import TokenRepository


class FakeCollection:
    def __init__(self):
        self.storage = {}

    async def insert_one(self, doc):
        _id = str(len(self.storage) + 1)
        doc_copy = doc.copy()
        doc_copy["_id"] = _id
        self.storage[_id] = doc_copy
        return SimpleNamespace(inserted_id=_id)

    async def find_one(self, query):
        for doc in self.storage.values():
            if doc.get("token") == query.get("token"):
                return doc
        return None

    async def update_one(self, query, update):
        for k, doc in self.storage.items():
            if doc.get("token") == query.get("token"):
                doc.update(update.get("$set", {}))
                return SimpleNamespace(matched_count=1)
        return SimpleNamespace(matched_count=0)


class FakeDB(dict):
    def __init__(self):
        super().__init__()
        self[Token.COLLECTION_NAME] = FakeCollection()


class FakeRedis:
    def __init__(self):
        self.storage = {}

    async def set(self, key, value, ex=None):
        self.storage[key] = {"value": value, "ex": ex}
        return True

    async def get(self, key):
        item = self.storage.get(key)
        if not item:
            return None
        return item["value"]

    async def delete(self, key):
        if key in self.storage:
            del self.storage[key]
            return 1
        return 0


@pytest.mark.asyncio
async def test_create_verify_revoke(monkeypatch):
    # Patch JWTHandler.create_refresh_token and decode_token
    monkeypatch.setattr("app.services.token_service.JWTHandler.create_refresh_token", lambda data, additional_claims=None, expires_at=None: ("token123", datetime.now(timezone.utc) + timedelta(days=7)))
    monkeypatch.setattr("app.services.token_service.JWTHandler.decode_token", lambda token: {"sub": "1", "type": "refresh"})

    db = FakeDB()
    svc = TokenService(TokenRepository(db))

    token_obj = await svc.create_token(identity="1", additional_claims={"email": "a@b"})
    assert token_obj.token == "token123"

    is_valid, obj, err = await svc.verify_token("token123")
    assert is_valid and obj is not None

    await svc.revoke_token("token123")
    is_valid2, obj2, err2 = await svc.verify_token("token123")
    assert not is_valid2


@pytest.mark.asyncio
async def test_create_verify_revoke_with_redis_session_store(monkeypatch):
    monkeypatch.setattr("app.services.token_service.JWTHandler.create_refresh_token", lambda data, additional_claims=None, expires_at=None: ("redis-token", datetime.now(timezone.utc) + timedelta(days=7)))
    monkeypatch.setattr("app.services.token_service.JWTHandler.decode_token", lambda token: {"sub": "1", "type": "refresh"})

    db = FakeDB()
    redis_repository = RedisTokenRepository(FakeRedis(), key_prefix="test_refresh")
    svc = TokenService(redis_repository)

    token_obj = await svc.create_token(identity="1", additional_claims={"email": "redis@test.dev"})
    assert token_obj.token == "redis-token"
    assert db[Token.COLLECTION_NAME].storage == {}

    is_valid, obj, err = await svc.verify_token("redis-token")
    assert is_valid and obj is not None
    assert obj.additional_claims["email"] == "redis@test.dev"

    await svc.revoke_token("redis-token")
    is_valid2, obj2, err2 = await svc.verify_token("redis-token")
    assert not is_valid2
