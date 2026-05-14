from app.repositories.base_repository import BaseRepository


class AttributeRepository(BaseRepository):
    def collection(self, name: str):
        return getattr(self.db, name)

    async def insert_one(self, collection_name: str, data: dict, session=None):
        return await self.collection(collection_name).insert_one(data, session=session)

    async def find_by_id(self, collection_name: str, item_id, session=None):
        return await self.collection(collection_name).find_one({"_id": self.to_object_id(item_id)}, session=session)

    async def update_by_id(self, collection_name: str, item_id, data: dict, session=None):
        return await self.collection(collection_name).update_one(
            {"_id": self.to_object_id(item_id)},
            {"$set": data},
            session=session
        )

    def find_many(self, collection_name: str, query: dict, session=None):
        return self.collection(collection_name).find(
            query,
            session=session
        )

    async def count_documents(self, collection_name: str, query: dict, session=None):
        return await self.collection(collection_name).count_documents(query, session=session)
    

    