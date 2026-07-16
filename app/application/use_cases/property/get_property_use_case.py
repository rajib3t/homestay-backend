from app.application.use_cases.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService


class GetPropertyUseCase(BaseUseCase):
    def __init__(
            self,
            property_service : PropertyService,
            current_user : CurrentUser,
            storage_service:StorageService,
            uow : MongoUnitOfWork
    ):
        self.property_service = property_service
        self.current_user = current_user
        self.storage_service = storage_service
        self.uow = uow

    async def execute(self, property_id: str)-> dict:
        async with self.uow as uow:
            session = uow.get_session()
            result = await self.property_service.get(
                property_id=property_id,
                session=session
            )
            if result is None:
                return None
            
            if result.get("feature_image"):
                result["feature_image"] = self.storage_service.generate_presigned_url(result["feature_image"])

            if result.get("gallery_images"):
                gallery_urls = []
                for image in result["gallery_images"]:
                    url = self.storage_service.generate_presigned_url(image)
                    gallery_urls.append(url)
                result["gallery_images"] = gallery_urls
            
            if result.get("cover_image"):
                result["cover_image"] = self.storage_service.generate_presigned_url(result["cover_image"])
            return result
