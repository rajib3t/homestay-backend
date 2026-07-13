from app.models.property_model import Property
from app.repositories.base_repository import BaseRepository


class PropertyRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db)
        self.collection_name = "properties"

    def collection(self):
        return getattr(self.db,  self.collection_name )
    
    

    async def insert_one(self,data: Property, session=None):
        return await self.collection().insert_one(data, session=session)


    
