from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
import logging

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.core.logging_config import configure_logging
from app.core.exceptions import AppException
from app.api.router import api_router
from app.core.config import settings


class Application:
    def __init__(self) -> None:
        self.app = FastAPI(lifespan=self._lifespan)

        self._register_middleware()
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
            # Ensure required indexes exist (run once at startup)
            try:
                db = get_database()
                from app.core.create_indexes import IndexCreator

                await IndexCreator.ensure_indexes(db)
            except Exception:
                logger.exception("Failed to create/ensure MongoDB indexes during startup")
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
        # Authentication is enforced with `get_current_user` dependencies.
        return None

    def _register_exception_handlers(self):
        @self.app.exception_handler(AppException)
        async def app_exception_handler(request: Request, exc: AppException):

            # If AppException already provides structured detail
            if isinstance(exc.detail, dict):
                return JSONResponse(
                    status_code=exc.status_code,
                    content=exc.detail
                )

            # fallback (should rarely happen)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "status": "error",
                    "message": exc.detail
                }
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):

            errors = []

            for err in exc.errors():
                field = err["loc"][-1]
                message = err["msg"]

                errors.append({
                    "field": field,
                    "message": message
                })

            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Validation error",
                    "errors": errors
                },
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):

            message = exc.detail

            # If detail is already structured
            if isinstance(message, dict):
                return JSONResponse(
                    status_code=exc.status_code,
                    content=message
                )

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "status": "error",
                    "message": message,
                }
            )

    def _register_routes(self):
        self.app.include_router(api_router)

    def get_app(self) -> FastAPI:
        return self.app


configure_logging()

application = Application()
app = application.get_app()