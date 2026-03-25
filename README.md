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

Use either `REDIS_URL` or the host/port/password fields. If `REDIS_URL` is set, it takes precedence.

If no Redis connection settings are provided, refresh tokens continue to use the Mongo-backed repository.
