import json

import pytest
from fastapi import APIRouter, FastAPI, Response

from app.core.idempotency import clear_in_memory_idempotency_store
from app.middleware.idempotency_route import IdempotencyRoute


def create_test_app(counter: dict, *, fail_first_request: bool = False) -> FastAPI:
    app = FastAPI()
    router = APIRouter(route_class=IdempotencyRoute)

    @router.post("/items")
    async def create_item(payload: dict):
        counter["calls"] += 1

        if fail_first_request and counter["calls"] == 1:
            return Response(
                content=json.dumps({"status": "error", "message": "temporary failure"}),
                status_code=500,
                media_type="application/json",
            )

        return {
            "status": "success",
            "data": {
                "calls": counter["calls"],
                "payload": payload,
            },
        }

    app.include_router(router)
    return app


async def invoke_json_request(app: FastAPI, *, body: dict, headers: dict = None):
    response_start = None
    response_body = b""
    encoded_body = json.dumps(body).encode("utf-8")

    header_items = [(b"content-type", b"application/json")]
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/items",
        "raw_path": b"/items",
        "query_string": b"",
        "headers": header_items,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "root_path": "",
        "app": app,
    }

    request_sent = False

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": encoded_body, "more_body": False}

    async def send(message):
        nonlocal response_start, response_body
        if message["type"] == "http.response.start":
            response_start = message
        elif message["type"] == "http.response.body":
            response_body += message.get("body", b"")

    await app(scope, receive, send)

    decoded_headers = {}
    for key, value in response_start["headers"]:
        decoded_headers.setdefault(key.decode("latin-1").lower(), []).append(value.decode("latin-1"))

    return {
        "status_code": response_start["status"],
        "headers": decoded_headers,
        "json": json.loads(response_body.decode("utf-8")),
    }


@pytest.mark.asyncio
async def test_post_requests_with_same_idempotency_key_replay_cached_response():
    await clear_in_memory_idempotency_store()
    counter = {"calls": 0}
    app = create_test_app(counter)

    first_response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "amenity-1"},
    )
    second_response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "amenity-1"},
    )

    assert first_response["status_code"] == 200
    assert second_response["status_code"] == 200
    assert first_response["json"] == second_response["json"]
    assert counter["calls"] == 1
    assert first_response["headers"]["x-idempotent-replayed"] == ["false"]
    assert second_response["headers"]["x-idempotent-replayed"] == ["true"]


@pytest.mark.asyncio
async def test_reusing_same_idempotency_key_with_different_payload_returns_conflict():
    await clear_in_memory_idempotency_store()
    counter = {"calls": 0}
    app = create_test_app(counter)

    first_response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "amenity-2"},
    )
    second_response = await invoke_json_request(
        app,
        body={"name": "pool"},
        headers={"Idempotency-Key": "amenity-2"},
    )

    assert first_response["status_code"] == 200
    assert second_response["status_code"] == 409
    assert counter["calls"] == 1


@pytest.mark.asyncio
async def test_failed_post_requests_are_not_cached():
    await clear_in_memory_idempotency_store()
    counter = {"calls": 0}
    app = create_test_app(counter, fail_first_request=True)

    first_response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "amenity-3"},
    )
    second_response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "amenity-3"},
    )

    assert first_response["status_code"] == 500
    assert second_response["status_code"] == 200
    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_blank_idempotency_key_header_returns_bad_request():
    await clear_in_memory_idempotency_store()
    counter = {"calls": 0}
    app = create_test_app(counter)

    response = await invoke_json_request(
        app,
        body={"name": "wifi"},
        headers={"Idempotency-Key": "   "},
    )

    assert response["status_code"] == 400
    assert counter["calls"] == 0