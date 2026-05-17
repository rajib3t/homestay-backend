import logging

from app.application.dto.user import UserQuery
from app.application.use_cases.base_use_case import BaseUseCase

logger = logging.getLogger(__name__)
class GetUsersUseCase(BaseUseCase):
    def __init__(self, user_service, storage_service, current_user, uow):
        self.user_service = user_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, query:UserQuery):

        logger.info(f"Executing GetUsersUseCase with query: {query}")
        async with self.uow as uow:
            session = uow.get_session()
            users = await self.user_service.list_users(query, session=session)
        return users