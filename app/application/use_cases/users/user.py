import logging

from app.application.dto.user import UserQuery
from app.application.use_cases.base_use_case import BaseUseCase

logger = logging.getLogger(__name__)


class UserResponseBuilder:
    def __init__(self, storage_service, company_service, address_service):
        self.storage_service = storage_service
        self.company_service = company_service
        self.address_service = address_service

    def build_user_response(self, user_data: dict) -> dict:
        if not user_data:
            return None

        result = user_data.copy()

        image_key = result.get("image")
        if image_key:
            try:
                result["image"] = self.storage_service.generate_presigned_url(image_key)
            except Exception as e:
                logger.error(f"Error generating presigned URL for user image: {e}")
                result["image"] = None  # Explicitly set to None if URL generation fails
        
        company = result.get("company")
        if company:
            company = company.copy()
            if "_id" in company:
                company["id"] = str(company.pop("_id"))

            address = company.get("address")
            if address:
                address = address.copy()
                if "_id" in address:
                    address["id"] = str(address.pop("_id"))
                address.pop("company_id", None)
                address.pop("user_id", None)
                company["address"] = address

            result["company"] = company
        return result
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
    

class GetUserUseCase(BaseUseCase):
    def __init__(
        self,
        user_service,
        company_service,
        address_service,
        storage_service,
        current_user,
        uow
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow
        self.response_builder = UserResponseBuilder(self.storage_service, self.company_service, self.address_service)
    async def execute(self, user_id: str) -> dict:
        logger.info(f"Executing GetUserUseCase for user_id: {user_id}")
        async with self.uow as uow:
            session = uow.get_session()
            user = await self.user_service.get_user(user_id, session=session)

            

        return self.response_builder.build_user_response(user) 