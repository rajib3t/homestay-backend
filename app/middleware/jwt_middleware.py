from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.security import JWTHandler

class JWTMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        bypass_routes = (
            "/login",
            "/register",
            "/refresh-token",
            "/refresh",
        )

        if any(path.endswith(route) for route in bypass_routes):
            return await call_next(request)

        if path.startswith("/api"):
            auth = request.headers.get("Authorization")
            if not auth:
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "message": "Authorization header is missing"},
                )

            token_parts = auth.split(" ")
            if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "message": "Invalid token format. Use Bearer <token>"},
                )

            try:
                token = token_parts[1]
                payload = JWTHandler.decode_token(token)
                request.state.user = payload.get("sub")
                request.state.user_claims = payload
            except Exception as exc:
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "message": f"Invalid or expired token: {str(exc)}"},
                )

        return await call_next(request)