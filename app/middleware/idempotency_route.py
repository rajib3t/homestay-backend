from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.idempotency import (
    build_request_fingerprint,
    build_response_from_record,
    build_response_record,
    build_storage_key,
    extract_response_body,
    get_idempotency_store,
    rebuild_response,
)


class IdempotencyRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()
        methods = {method.upper() for method in self.methods or []}

        if "POST" not in methods:
            return original_handler

        async def custom_handler(request: Request) -> Response:
            raw_key = request.headers.get(settings.IDEMPOTENCY_HEADER_NAME)
            if raw_key is None:
                return await original_handler(request)

            idempotency_key = raw_key.strip()
            if not idempotency_key:
                raise AppException(
                    status_code=400,
                    message=f"{settings.IDEMPOTENCY_HEADER_NAME} header cannot be empty",
                    error_code="INVALID_IDEMPOTENCY_KEY",
                    field=settings.IDEMPOTENCY_HEADER_NAME,
                )

            request_body = await request.body()
            fingerprint = build_request_fingerprint(request, request_body)
            storage_key = build_storage_key(request, idempotency_key)
            store = get_idempotency_store()

            cached_record = await store.read(storage_key)
            if cached_record is not None:
                if cached_record.fingerprint != fingerprint:
                    raise AppException(
                        status_code=409,
                        message="Idempotency key has already been used for a different request",
                        error_code="IDEMPOTENCY_KEY_REUSED",
                        field=settings.IDEMPOTENCY_HEADER_NAME,
                    )

                if cached_record.state == "processing":
                    raise AppException(
                        status_code=409,
                        message="A request with this idempotency key is already in progress",
                        error_code="IDEMPOTENCY_REQUEST_IN_PROGRESS",
                        field=settings.IDEMPOTENCY_HEADER_NAME,
                    )

                return build_response_from_record(cached_record, replayed=True)

            reserved = await store.reserve_processing(
                storage_key,
                fingerprint,
                settings.IDEMPOTENCY_TTL_SECONDS,
            )
            if not reserved:
                cached_record = await store.read(storage_key)
                if cached_record is not None and cached_record.fingerprint == fingerprint:
                    if cached_record.state == "completed":
                        return build_response_from_record(cached_record, replayed=True)
                    raise AppException(
                        status_code=409,
                        message="A request with this idempotency key is already in progress",
                        error_code="IDEMPOTENCY_REQUEST_IN_PROGRESS",
                        field=settings.IDEMPOTENCY_HEADER_NAME,
                    )

                raise AppException(
                    status_code=409,
                    message="Idempotency key has already been used for a different request",
                    error_code="IDEMPOTENCY_KEY_REUSED",
                    field=settings.IDEMPOTENCY_HEADER_NAME,
                )

            try:
                response = await original_handler(request)
                response_body = await extract_response_body(response)
                rebuilt_response = rebuild_response(response, response_body, replayed=False)

                if 200 <= response.status_code < 300:
                    await store.save_response(
                        storage_key,
                        build_response_record(
                            fingerprint=fingerprint,
                            response=response,
                            body=response_body,
                        ),
                        settings.IDEMPOTENCY_TTL_SECONDS,
                    )
                else:
                    await store.release(storage_key)

                return rebuilt_response
            except Exception:
                await store.release(storage_key)
                raise

        return custom_handler