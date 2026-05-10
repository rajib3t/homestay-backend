from functools import wraps


def handle_api_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Exception in {func.__name__}: {e}")
            from app.utils.api_utils import handle_exception
            handle_exception(e)

    return wrapper