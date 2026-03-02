from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
import logging

from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.logging_config import configure_logging
from app.core.exceptions import AppException
from app.api.router import api_router
from app.core.config import settings


class Application:
    def __init__(self) -> None:
        self.app = FastAPI(lifespan=self._lifespan)

        # Do not register JWT middleware; use dependency-based auth via `get_current_user`.
        # If global checks are needed, re-enable middleware here.
        self._register_exception_handlers()
        self._register_routes()

        # module-level logger for structured logging
        self._logger = logging.getLogger(__name__)

    # ✅ Modern lifespan handler (replaces startup/shutdown)
    @staticmethod
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        logger = logging.getLogger(__name__)

        # Startup
        try:
            await connect_to_mongo()
            logger.info("MongoDB connected")
        except Exception:
            logger.exception("Failed to connect to MongoDB during startup")
            raise

        yield  # Application runs here

        # Shutdown
        try:
            await close_mongo_connection()
            logger.info("MongoDB connection closed")
        except Exception:
            logger.exception("Error while closing MongoDB connection")

    def _register_middleware(self):
        self.app.add_middleware(JWTMiddleware)

    def _register_exception_handlers(self):
        @self.app.exception_handler(AppException)
        async def app_exception_handler(request, exc: AppException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"status": "error", "message": exc.detail},
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            # Return a consistent JSON shape for validation errors
            return JSONResponse(
                status_code=422,
                content={"status": "error", "message": "Validation error", "detail": exc.errors()},
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            # Normalize FastAPI/Starlette HTTPExceptions to our JSON shape
            detail = exc.detail if not isinstance(exc.detail, (list, dict)) else exc.detail
            return JSONResponse(
                status_code=getattr(exc, "status_code", 500),
                content={"status": "error", "message": detail},
            )

    def _register_routes(self):
        self.app.include_router(api_router)

    def get_app(self) -> FastAPI:
        return self.app


configure_logging()

application = Application()
app = application.get_app()