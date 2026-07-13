
import logging
from app.application.dto.user import UserQuery
from app.application.use_cases.base_use_case import BaseUseCase
from app.application.use_cases.users.image_service import UserImageService
from app.deps.auth import CurrentUser
from app.domain.events.user_events import UserUpdatedEvent
import re
from app.models.user_model import UserUpdate
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
logger = logging.getLogger(__name__)
from app.core.exceptions import AppException


class UserResponseBuilder:
    def __init__(self, storage_service, company_service, address_service):
        self.storage_service = storage_service
        self.company_service = company_service
        self.address_service = address_service
        self.image_service = UserImageService(self.storage_service)

    async def build_user_response(self, user_data: dict) -> dict:
        if not user_data:
            return None

        result = user_data.copy()

        image_key = result.get("image")
        if image_key:
            try:
                result["image"] = self.image_service.resolve_url(image_key)
            except Exception as e:
                logger.error(f"Error generating presigned URL for user image: {e}")
                result["image"] = None  # Explicitly set to None if URL generation fails

        try:
            result["company"] = await self.company_service.get_company_by_user_id(result["id"])
        except Exception:
            pass

        return result
class GetUsersUseCase(BaseUseCase):
    def __init__(
            self, 
            user_service : UserService, 
            company_service :CompanyService, 
            address_service : AddressService, 
            storage_service : StorageService, 
            current_user : CurrentUser, 
            uow
        ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow
        self.response_builder = UserResponseBuilder(self.storage_service, self.company_service, self.address_service)
    async def execute(self, query:UserQuery):
        async with self.uow as uow:
            session = uow.get_session()
            result = await self.user_service.list_users(query, session=session)
            result["items"] = [
                await self.response_builder.build_user_response(user)
                for user in result["items"]
            ]
            return result
    

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

            
            
            return await self.response_builder.build_user_response(user)
    
class UpdateUserProfileImageUseCase(BaseUseCase):
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
        self.image_service = UserImageService(self.storage_service)
        self.uow = uow
        self.response_builder = UserResponseBuilder(self.storage_service, self.company_service, self.address_service)


    async def execute(self, user_id: str, image: str):
            actor_id = str(self.current_user.id)
            logger.info('Image', image)
            async with self.uow as uow:
                session = uow.get_session()
                user = await self.user_service.get_user(user_id, session=session)
                existing_image_key = user.get("image")
                if existing_image_key:
                    upload_path = existing_image_key
                    try:
                        await self.image_service.delete(existing_image_key)
                        logger.info(f"Deleted old profile image from storage: {existing_image_key}")
                    except Exception as e:
                        logger.error(f"Error deleting old profile image: {e}")
                        # Continue with the update even if deletion fails
                else:
                    slug = re.sub(
                        r"[^a-z0-9]+", "-",
                        user.get("first_name", "").lower() + " " + user.get("last_name", "").lower() + " " + str(user.get("id", "")).lower()
                    ).strip("-")
                    upload_path = f"profile_images/{slug}.webp"

                
                image_key = await self.image_service.upload(
                    image_data=image,
                    path=upload_path,
                )

                if image_key:
                    await self.user_service.update_user(user_id, {"image": image_key}, session=session)
                    uow.collect_event(UserUpdatedEvent(user_id, actor_id))
                    updated_user = await self.user_service.get_user(user_id, session=session)
                    return await self.response_builder.build_user_response(updated_user)
                
class UpdateUserUseCase(BaseUseCase):

    def __init__(
        self,
        user_service : UserService,
        company_service,
        address_service,
        storage_service,
        current_user,
        uow,
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow
        self.image_service = UserImageService(self.storage_service)
        self.response_builder = UserResponseBuilder(self.storage_service, self.company_service, self.address_service)

    async def execute(self, user_id: str, payload: UserUpdate) -> dict:
        payload_data = payload.model_dump(exclude_unset=True)
        update_payload = {k: v for k, v in payload_data.items() if k != "company"}
        actor_id = str(self.current_user.id)
        update_payload["updated_by"] = actor_id
        company_data = payload_data.get("company")

        async with self.uow as uow:
            session = uow.get_session()
            
            existing_user = await self.user_service.get_user(user_id, session=session)
            if update_payload.get('image'):
                # If there's an existing image, delete it from storage
                existing_image_key = existing_user.get('image')
                if existing_image_key:
                    upload_path = existing_image_key
                    try:
                        
                        await self.image_service.delete(existing_image_key)
                        logger.info(f"Deleted old profile image from storage: {existing_image_key}")
                    except Exception as e:
                        logger.error(f"Error deleting old profile image: {e}")
                        # Continue with the update even if deletion fails

            # --- STEP 1: Update User ---
            await self.user_service.update_user(
                user_id,
                update_payload,
                session=session
            )
            

            # --- STEP 2: Company + Address ---
            if company_data is not None:
                company_data = company_data.copy()
                address_data = company_data.pop("address", None)

                company_id = await self._upsert_company(
                    user_id, company_data, actor_id, session
                )

                if address_data and company_id:
                    await self._upsert_address(
                        company_id, user_id, address_data, actor_id, session
                    )

            # --- STEP 3: Emit Event (AFTER SUCCESS) ---
            uow.collect_event(UserUpdatedEvent(user_id, actor_id))

        # --- STEP 4: Build Response (outside transaction; do not reuse ended session) ---
        updated_user = await self.user_service.get_user(user_id)
        return await self.response_builder.build_user_response(updated_user)

    async def _build_updated_user_response(self, user_id: str) -> dict:
        user = await self.user_service.get_user(user_id)
        try:
            company = await self.company_service.get_company_by_user_id(user_id)
            if company:
                company = company.copy()
                if "_id" in company:
                    company["id"] = str(company.pop("_id"))
                try:
                    address = await self.address_service.get_address_by_company_id(
                        company["id"]
                    )
                    if address:
                        address = address.copy()
                        if "_id" in address:
                            address["id"] = str(address.pop("_id"))
                        address.pop("company_id", None)
                        address.pop("user_id", None)
                        company["address"] = address
                except Exception:
                    pass
                user["company"] = company
        except Exception:
            pass
        return user



    async def _upsert_company(self, user_id, data, actor_id, session):

        try:
            company = await self.company_service.get_company_by_user_id(
                user_id, include_address=False
            )
            company_id = company["id"]

            if data:
                await self.company_service.update_company(
                    company_id,
                    {**data, "updated_by": actor_id},
                    session=session
                )

            return company_id

        except AppException:
            if not data:
                return None

            return await self.company_service.create_company(
                {**data, "user_id": user_id, "created_by": actor_id},
                session=session
            )
    async def _upsert_address(self, company_id, user_id, data, actor_id, session):

        if not company_id:
            company = await self.company_service.get_company_by_user_id(
                user_id, include_address=False
            )
            company_id = company["id"]

        address = await self.address_service.get_address_by_company_id(company_id)

        if address:
            await self.address_service.update_address(
                address["id"],
                {**data, "updated_by": actor_id},
                session=session
            )
        else:
            await self.address_service.create_address(
                {
                    **data,
                    "company_id": company_id,
                    "user_id": user_id,
                    "created_by": actor_id,
                },
                session=session
            )

class UpdateUserPasswordUseCase(BaseUseCase):
    def __init__(self, user_service, storage_service, company_service, address_service, current_user, uow):
        self.user_service = user_service
        self.storage_service = storage_service
        self.company_service = company_service
        self.address_service = address_service
        self.current_user = current_user
        self.uow = uow
        self.response_builder = UserResponseBuilder(self.storage_service, self.company_service, self.address_service)
    async def execute(self, user_id: str, password: str):
        async with self.uow as uow:
            session = uow.get_session()
            user = await self.user_service.get_user(user_id, session=session)
            
            update_data = {
                "password": password    
            }
            await self.user_service.update_user(user_id, update_data, session=session)
            uow.collect_event(UserUpdatedEvent(user_id, str(self.current_user.id)))
            updated_user = await self.user_service.get_user(user_id, session=session)
            return await self.response_builder.build_user_response(updated_user)