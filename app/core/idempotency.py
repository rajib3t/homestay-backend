import asyncio
import base64
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from fastapi import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.redis import get_redis

IDEMPOTENCY_REPLAY_HEADER = "X-Idempotent-Replayed"
_IGNORED_RESPONSE_HEADERS = {
    "content-length",
    "content-type",
    IDEMPOTENCY_REPLAY_HEADER.lower(),
}


@dataclass
class IdempotencyRecord:
    fingerprint: str
    state: str
    status_code: Optional[int] = None
    body: Optional[str] = None
    media_type: Optional[str] = None
    headers: List[Tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "fingerprint": self.fingerprint,
            "state": self.state,
            "status_code": self.status_code,
            "body": self.body,
            "media_type": self.media_type,
            "headers": self.headers,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IdempotencyRecord":
        return cls(
            fingerprint=data["fingerprint"],
            state=data["state"],
            status_code=data.get("status_code"),
            body=data.get("body"),
            media_type=data.get("media_type"),
            headers=[tuple(item) for item in data.get("headers", [])],
        )


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records = {}
        self._lock = asyncio.Lock()

    def _purge_expired(self, key: Optional[str] = None) -> None:
        now = time.time()

        if key is not None:
            stored = self._records.get(key)
            if stored and stored["expires_at"] <= now:
                self._records.pop(key, None)
            return

        expired_keys = [
            storage_key
            for storage_key, stored in self._records.items()
            if stored["expires_at"] <= now
        ]
        for storage_key in expired_keys:
            self._records.pop(storage_key, None)

    async def read(self, key: str) -> Optional[IdempotencyRecord]:
        async with self._lock:
            self._purge_expired(key)
            stored = self._records.get(key)
            if not stored:
                return None
            return stored["record"]

    async def reserve_processing(self, key: str, fingerprint: str, ttl_seconds: int) -> bool:
        async with self._lock:
            self._purge_expired(key)
            if key in self._records:
                return False

            self._records[key] = {
                "record": IdempotencyRecord(fingerprint=fingerprint, state="processing"),
                "expires_at": time.time() + ttl_seconds,
            }
            return True

    async def save_response(self, key: str, record: IdempotencyRecord, ttl_seconds: int) -> None:
        async with self._lock:
            self._records[key] = {
                "record": record,
                "expires_at": time.time() + ttl_seconds,
            }

    async def release(self, key: str) -> None:
        async with self._lock:
            self._records.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._records.clear()


class RedisIdempotencyStore:
    def __init__(self, redis_client, key_prefix: str) -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _build_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}"

    async def read(self, key: str) -> Optional[IdempotencyRecord]:
        payload = await self.redis.get(self._build_key(key))
        if not payload:
            return None
        return IdempotencyRecord.from_dict(json.loads(payload))

    async def reserve_processing(self, key: str, fingerprint: str, ttl_seconds: int) -> bool:
        record = IdempotencyRecord(fingerprint=fingerprint, state="processing")
        return bool(
            await self.redis.set(
                self._build_key(key),
                json.dumps(record.to_dict()),
                ex=ttl_seconds,
                nx=True,
            )
        )

    async def save_response(self, key: str, record: IdempotencyRecord, ttl_seconds: int) -> None:
        await self.redis.set(
            self._build_key(key),
            json.dumps(record.to_dict()),
            ex=ttl_seconds,
        )

    async def release(self, key: str) -> None:
        await self.redis.delete(self._build_key(key))


_memory_store = InMemoryIdempotencyStore()


def get_idempotency_store():
    redis_client = get_redis()
    if redis_client is not None:
        return RedisIdempotencyStore(redis_client, settings.IDEMPOTENCY_PREFIX)
    return _memory_store


async def clear_in_memory_idempotency_store() -> None:
    await _memory_store.clear()


def build_storage_key(request: Request, idempotency_key: str) -> str:
    return f"{request.method.upper()}:{request.url.path}:{idempotency_key}"


def build_request_fingerprint(request: Request, body: bytes) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    content_type = request.headers.get("content-type", "")
    fingerprint_source = "|".join(
        [request.method.upper(), request.url.path, request.url.query, content_type, body_hash]
    )
    return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()


async def extract_response_body(response: Response) -> bytes:
    body = getattr(response, "body", None)
    if body is not None:
        return bytes(body)

    body_chunks = []
    async for chunk in response.body_iterator:
        body_chunks.append(chunk)
    return b"".join(body_chunks)


def _copyable_headers(response: Response) -> List[Tuple[str, str]]:
    copied_headers = []
    for header_name, header_value in getattr(response, "raw_headers", []):
        decoded_name = header_name.decode("latin-1")
        if decoded_name.lower() in _IGNORED_RESPONSE_HEADERS:
            continue
        copied_headers.append((decoded_name, header_value.decode("latin-1")))
    return copied_headers


def build_response_record(
    *,
    fingerprint: str,
    response: Response,
    body: bytes,
) -> IdempotencyRecord:
    return IdempotencyRecord(
        fingerprint=fingerprint,
        state="completed",
        status_code=response.status_code,
        body=base64.b64encode(body).decode("ascii"),
        media_type=response.media_type,
        headers=_copyable_headers(response),
    )


def build_response_from_record(record: IdempotencyRecord, replayed: bool) -> Response:
    raw_body = base64.b64decode(record.body.encode("ascii")) if record.body else b""
    response = Response(
        content=raw_body,
        status_code=record.status_code or 200,
        media_type=record.media_type,
    )
    for header_name, header_value in record.headers:
        response.headers.append(header_name, header_value)
    response.headers[IDEMPOTENCY_REPLAY_HEADER] = "true" if replayed else "false"
    return response


def rebuild_response(response: Response, body: bytes, replayed: bool) -> Response:
    rebuilt = Response(
        content=body,
        status_code=response.status_code,
        media_type=response.media_type,
        background=response.background,
    )
    for header_name, header_value in _copyable_headers(response):
        rebuilt.headers.append(header_name, header_value)
    rebuilt.headers[IDEMPOTENCY_REPLAY_HEADER] = "true" if replayed else "false"
    return rebuilt