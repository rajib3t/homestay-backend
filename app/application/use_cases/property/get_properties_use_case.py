from app.application.dto.property import PropertyQuery
from app.application.use_cases.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.schemas.property_schema import PropertyListItem


class GetPropertiesUseCase(BaseUseCase):
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
    async def execute(self, params : PropertyQuery):
        async with self.uow as uow:

            session = uow.get_session()

            result = await self.property_service.list(
                query=params,
                session=session
            )

            if not result:
                return {
                    "items": [],
                    "total": 0,
                    "page": params.page,
                    "page_size": params.size
                }

            def normalize_nested_items(items):
                normalized = []
                for item in items or []:
                    normalized.append(
                        {
                            "name": item.get("name", ""),
                            "allowed": item.get("allowed", item.get("allow", True)),
                        }
                    )
                return normalized

            result["items"] = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "price": item["listing_price"],
                    "sale_price": item.get("sale_price", None),
                    "facilities": normalize_nested_items(item.get("facilities", [])),
                    "amenities": normalize_nested_items(item.get("amenities", [])),
                    "city_name": item.get("city_name", ""),
                    "country_name": item.get("country_name", ""),
                    "location_name": item.get("location_name", ""),
                    "feature_image": self.storage_service.generate_presigned_url(item["feature_image"])
                }
                for item in result["items"]
            ]

            # Rename 'size' to 'page_size' to match schema
            result["page_size"] = result.pop("size")

            return result
