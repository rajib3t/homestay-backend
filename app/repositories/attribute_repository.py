from app.repositories.base_repository import BaseRepository


class AttributeRepository(BaseRepository):
    def collection(self, name: str):
        return getattr(self.db, name)

    async def insert_one(self, collection_name: str, data: dict):
        return await self.collection(collection_name).insert_one(data)

    async def find_by_id(self, collection_name: str, item_id):
        return await self.collection(collection_name).find_one({"_id": self.to_object_id(item_id)})

    async def update_by_id(self, collection_name: str, item_id, data: dict):
        return await self.collection(collection_name).update_one(
            {"_id": self.to_object_id(item_id)},
            {"$set": data},
        )

    def find_many(self, collection_name: str, query: dict):
        return self.collection(collection_name).find(query)

    async def count_documents(self, collection_name: str, query: dict):
        return await self.collection(collection_name).count_documents(query)