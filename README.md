# Homestay Backend

## Redis

Redis support is optional and is used for refresh token session storage when configured.

Required environment variables:

- `MONGO_URI`
- `JWT_SECRET`

Optional Redis environment variables:

- `REDIS_URL=redis://localhost:6379/0`
- `REDIS_HOST=127.0.0.1`
- `REDIS_PORT=6379`
- `REDIS_PASSWORD=mypassword`
- `REDIS_DB=0`
- `REDIS_TOKEN_PREFIX=refresh_token`

Optional idempotency settings:

- `IDEMPOTENCY_PREFIX=idempotency`
- `IDEMPOTENCY_TTL_SECONDS=86400`
- `IDEMPOTENCY_HEADER_NAME=Idempotency-Key`

Use either `REDIS_URL` or the host/port/password fields. If `REDIS_URL` is set, it takes precedence.

If no Redis connection settings are provided, refresh tokens continue to use the Mongo-backed repository.

## Idempotent POST Requests

All POST endpoints now support request replay protection when the client sends an `Idempotency-Key` header.

- The first successful request stores the response for the configured TTL.
- A retried request with the same method, path, body, and key returns the cached response.
- Reusing the same key with a different payload returns `409 Conflict`.
- Requests without an `Idempotency-Key` header keep the previous behavior.

Responses handled through idempotency include the `X-Idempotent-Replayed` header with `false` for the initial response and `true` for cached replays.
