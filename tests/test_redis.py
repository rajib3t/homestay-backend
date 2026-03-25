import pytest

from app.core import redis as redis_module


class FakeRedisClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.ping_called = False
        self.closed = False

    async def ping(self):
        self.ping_called = True

    async def aclose(self):
        self.closed = True


@pytest.mark.asyncio
async def test_connect_to_redis_uses_host_port_password(monkeypatch):
    created_clients = []

    class FakeRedisFactory:
        def __init__(self, **kwargs):
            client = FakeRedisClient(**kwargs)
            created_clients.append(client)
            self._client = client

        def __getattr__(self, name):
            return getattr(self._client, name)

        @classmethod
        def from_url(cls, *args, **kwargs):
            raise AssertionError("REDIS_URL should not be used when host config is provided")

    monkeypatch.setattr(redis_module.settings, "REDIS_URL", None)
    monkeypatch.setattr(redis_module.settings, "REDIS_HOST", "127.0.0.1")
    monkeypatch.setattr(redis_module.settings, "REDIS_PORT", 6379)
    monkeypatch.setattr(redis_module.settings, "REDIS_PASSWORD", "mypassword")
    monkeypatch.setattr(redis_module.settings, "REDIS_DB", 0)
    monkeypatch.setattr(redis_module, "Redis", FakeRedisFactory)

    redis_module.redis_connection.client = None
    await redis_module.connect_to_redis()

    assert len(created_clients) == 1
    client = created_clients[0]
    assert client.kwargs == {
        "host": "127.0.0.1",
        "port": 6379,
        "password": "mypassword",
        "db": 0,
        "decode_responses": True,
    }
    assert client.ping_called is True
    assert redis_module.get_redis() is not None

    await redis_module.close_redis_connection()
    assert client.closed is True
    assert redis_module.get_redis() is None


@pytest.mark.asyncio
async def test_connect_to_redis_skips_when_not_configured(monkeypatch):
    class FakeRedisFactory:
        @classmethod
        def from_url(cls, *args, **kwargs):
            raise AssertionError("Redis should not be created without configuration")

        def __init__(self, **kwargs):
            raise AssertionError("Redis should not be created without configuration")

    monkeypatch.setattr(redis_module.settings, "REDIS_URL", None)
    monkeypatch.setattr(redis_module.settings, "REDIS_HOST", None)
    monkeypatch.setattr(redis_module, "Redis", FakeRedisFactory)

    redis_module.redis_connection.client = None
    await redis_module.connect_to_redis()

    assert redis_module.get_redis() is None