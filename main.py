from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
import logging

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.core.logging_config import configure_logging
from app.core.redis import connect_to_redis, close_redis_connection
from app.core.exceptions import AppException
from app.api.router import api_router
from app.infrastructure.event_bus.worker import worker_loop
from app.infrastructure.event_bus.outbox_publisher import OutboxPublisher, outbox_loop
from app.repositories.outbox_repository import OutboxRepository
import asyncio
from app.core.config import settings  # however you expose settings
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
        tasks: list[asyncio.Task] = []  # single collection — cancel all in one place

        try:
            await connect_to_mongo()
            logger.info("MongoDB connected")

            await connect_to_redis()
            logger.info("Redis connected")

            db = get_database()

            # Create indexes — do this before starting background tasks
            try:
                from app.core.create_indexes import IndexCreator
                await IndexCreator.ensure_indexes(db)
            except Exception:
                logger.exception("Index creation failed")

            # Start background tasks — all tracked in one list
            outbox_repo = OutboxRepository(db)
            outbox_publisher = OutboxPublisher(outbox_repo)
            

            if settings.ENV == "development":
                tasks.append(asyncio.create_task(worker_loop(), name="worker_loop"))
                tasks.append(asyncio.create_task(outbox_loop(outbox_publisher), name="outbox_loop"))
                logger.info("Background tasks started (dev mode)")
            else:
                logger.info("Background tasks skipped — use run_worker.py in production")

        except Exception:
            logger.exception("Startup failure")
            raise

        yield  # App runs here

        # Shutdown — cancel and await every task, even if startup only partially succeeded
        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Background tasks stopped")

        try:
            await close_redis_connection()
            await close_mongo_connection()
        except Exception:
            logger.exception("Shutdown failure")

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