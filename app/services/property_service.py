from app.models.property_model import Property
from app.repositories.property_repository import PropertyRepository
from app.services.base_service import BaseService


class PropertyService(BaseService):

    def __init__(self, repository: PropertyRepository):
        super().__init__(repository.db)
        self.repository = repository

    async def create(
        self,
        property_data: dict,
        session=None,
    ):
        self.timestamps(property_data, is_new=True)
        result = await self.repository.insert_one(property_data, session=session)
        return str(result.inserted_id)

